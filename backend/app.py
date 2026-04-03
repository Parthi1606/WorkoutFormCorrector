"""
app.py
------
RepRight REST API.

Endpoints
---------
POST /auth/google          Verify Google token, upsert user, return JWT
GET  /stats/{user_id}      Aggregate stats for profile screen
GET  /stats/{user_id}/breakdown  Per-exercise breakdown
POST /sessions/save        Save a completed session + exercise log + update stats

Run alongside the WebSocket server:
    uvicorn app:app --host 0.0.0.0 --port 8001
(WebSocket server stays on port 8000)
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

import jwt 
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from database.deps import get_db
from database.models.user import User
from database.models.session import SessionModel
from database.models.exercise import Exercise
from database.models.exercise_log import ExerciseLog
from database.models.user_stats import UserStats

# ── Config ────────────────────────────────────────────────────────────────────

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
JWT_SECRET       = os.getenv("JWT_SECRET", "repright-dev-secret-change-in-prod")
JWT_ALGORITHM    = "HS256"
JWT_EXPIRE_DAYS  = 30

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="RepRight REST API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_jwt(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> int:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    return decode_jwt(credentials.credentials)


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class GoogleAuthRequest(BaseModel):
    id_token: str           # ID token from Google Sign-In on the mobile app


class SaveSessionRequest(BaseModel):
    user_id:     int
    exercise_key: str       # e.g. "bicep_curl" — matches EXERCISE_REGISTRY keys
    total_reps:  int
    valid_reps:  int
    duration:    int        # seconds
    started_at:  str        # ISO 8601
    ended_at:    str        # ISO 8601


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post("/auth/google")
def google_auth(body: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Verify a Google ID token sent from the mobile app.
    If the user doesn't exist, create them.
    Returns a JWT the app stores and sends with every subsequent request.
    """
    try:
        import requests as pyrequests
        from google.auth.transport.requests import Request as GoogleRequest
        
        session = pyrequests.Session()
        google_request = GoogleRequest(session=session)
        
        info = id_token.verify_oauth2_token(
        body.id_token,
        google_request,
        "597817830458-07ognj6gmmljt7a2v62akc4j7bqiqjas.apps.googleusercontent.com",  # hardcode to test
    )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Google token: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token verification failed: {e}")

    email     = info["email"]
    name      = info.get("name", email.split("@")[0])
    avatar    = info.get("picture", None)

    # Upsert user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(name=name, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_jwt(user.user_id)

    return {
        "token":   token,
        "user_id": user.user_id,
        "name":    user.name,
        "email":   user.email,
    }


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.get("/stats/{user_id}")
def get_user_stats(
    user_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
):
    """
    Aggregate stats for the profile screen header:
    total_reps, avg form score, total sessions, streak (days).
    """
    rows = (
        db.query(UserStats)
        .filter(UserStats.user_id == user_id)
        .all()
    )

    total_reps     = sum(r.total_reps     for r in rows)
    total_sessions = sum(r.total_sessions for r in rows)

    # Weighted average accuracy across all exercises
    if rows:
        weighted = sum(r.avg_accuracy * r.total_reps for r in rows)
        total_w  = sum(r.total_reps for r in rows) or 1
        avg_form = round(weighted / total_w, 1)
    else:
        avg_form = 0.0

    # Simple streak: count consecutive days that have at least one session
    streak = _calculate_streak(user_id, db)

    return {
        "total_reps":     total_reps,
        "total_sessions": total_sessions,
        "avg_form":       avg_form,
        "streak":         streak,
    }


@app.get("/stats/{user_id}/breakdown")
def get_exercise_breakdown(
    user_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
):
    """
    Per-exercise stats for the profile breakdown section.
    Returns a list ordered by total_sessions descending.
    """
    rows = (
        db.query(UserStats, Exercise)
        .join(Exercise, UserStats.exercise_id == Exercise.exercise_id)
        .filter(UserStats.user_id == user_id)
        .order_by(UserStats.total_sessions.desc())
        .all()
    )

    return [
        {
            "exercise_key":    ex.exercise_key,
            "exercise_name":   ex.name,
            "total_reps":      stat.total_reps,
            "total_sessions":  stat.total_sessions,
            "avg_accuracy":    round(stat.avg_accuracy, 1),
        }
        for stat, ex in rows
    ]


# ── Session save ──────────────────────────────────────────────────────────────

@app.post("/sessions/save")
def save_session(
    body: SaveSessionRequest,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
):
    """
    Called when the user ends an exercise session.
    1. Creates a Session record
    2. Creates an ExerciseLog record
    3. Upserts UserStats for that user + exercise pair
    """
    # Resolve exercise_id from key
    exercise = (
        db.query(Exercise)
        .filter(Exercise.exercise_key == body.exercise_key)
        .first()
    )
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Exercise '{body.exercise_key}' not found")

    accuracy = round(
        (body.valid_reps / body.total_reps * 100) if body.total_reps > 0 else 0.0, 1
    )

    # 1. Session record
    session_record = SessionModel(
        user_id    = body.user_id,
        started_at = datetime.fromisoformat(body.started_at),
        ended_at   = datetime.fromisoformat(body.ended_at),
    )
    db.add(session_record)
    db.flush()  # get session_id before commit

    # 2. Exercise log
    log = ExerciseLog(
        session_id  = session_record.session_id,
        exercise_id = exercise.exercise_id,
        reps        = body.total_reps,
        accuracy    = accuracy,
        duration    = body.duration,
        started_at  = datetime.fromisoformat(body.started_at),
        ended_at    = datetime.fromisoformat(body.ended_at),
    )
    db.add(log)

    # 3. Upsert UserStats
    stat = (
        db.query(UserStats)
        .filter(
            UserStats.user_id     == body.user_id,
            UserStats.exercise_id == exercise.exercise_id,
        )
        .first()
    )

    if stat:
        # Running weighted average for accuracy
        prev_total = stat.total_reps
        new_total  = prev_total + body.total_reps
        if new_total > 0:
            stat.avg_accuracy = round(
                (stat.avg_accuracy * prev_total + accuracy * body.total_reps) / new_total, 1
            )
        stat.total_reps     += body.total_reps
        stat.total_sessions += 1
        stat.last_updated    = datetime.now(timezone.utc)
    else:
        stat = UserStats(
            user_id     = body.user_id,
            exercise_id = exercise.exercise_id,
            total_reps  = body.total_reps,
            total_sessions = 1,
            avg_accuracy   = accuracy,
        )
        db.add(stat)

    db.commit()

    return {
        "message":    "Session saved",
        "session_id": session_record.session_id,
        "accuracy":   accuracy,
    }


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "RepRight API is running"}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _calculate_streak(user_id: int, db: Session) -> int:
    """
    Count consecutive calendar days (ending today) that have at least one session.
    """
    sessions = (
        db.query(func.date(SessionModel.started_at).label("day"))
        .filter(SessionModel.user_id == user_id)
        .distinct()
        .order_by(func.date(SessionModel.started_at).desc())
        .all()
    )

    if not sessions:
        return 0

    streak    = 0
    check_day = datetime.now(timezone.utc).date()

    for (day,) in sessions:
        if day == check_day:
            streak    += 1
            check_day -= timedelta(days=1)
        elif day < check_day:
            break  # gap found

    return streak
