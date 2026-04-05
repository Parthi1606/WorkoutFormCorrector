"""
server.py
---------
FastAPI WebSocket server. Entry point for the entire backend.

Run with:
    uvicorn server:app --host 0.0.0.0 --port 8000

WebSocket endpoint:
    ws://your-server:8000/session/{exercise_name}

    exercise_name must be one of the keys in session.EXERCISE_REGISTRY:
        bicep_curl, squat, shoulder_press, lunge, pushup, bent_over_row, plank

Frame format (phone → server):
    {
        "landmarks": [
            {"x": 0.512, "y": 0.331, "z": -0.05, "visibility": 0.99},
            ... 33 total, in MediaPipe landmark order
        ]
    }

Response format (server → phone), sent after every frame:
    {
        "phase":        "moving",
        "rep_count":    3,
        "valid_reps":   2,
        "active_side":  "LEFT",
        "checks": [
            {"label": "Upright torso", "ok": true,  "value": 4.2,  "message": ""},
            {"label": "Elbow stable",  "ok": false, "value": 0.18, "message": "elbow drifting"}
        ],
        "rep_event":  "invalid",
        "faults":     ["elbow drifting"],
        "hold_seconds": null
    }

Error response:
    {"error": "description of what went wrong"}
"""

import json
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from starlette.websockets import WebSocketState

from audio import audio
from session import Session

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
log = logging.getLogger(__name__)

# ─── App setup ────────────────────────────────────────────────────────────────

app = FastAPI(title="Pose Feedback API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


# ─── Startup / shutdown ───────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    audio.start()
    log.info("Audio thread started.")


@app.on_event("shutdown")
async def shutdown():
    audio.stop()
    log.info("Audio thread stopped.")


# ─── Landmark parsing ─────────────────────────────────────────────────────────

class _Landmark:
    """
    Lightweight stand-in for a MediaPipe landmark object.
    MediaPipe runs on the phone; the server receives plain JSON dicts.
    We wrap them in this class so utils.py (which reads .x .y .z) works
    without any changes.
    """
    __slots__ = ("x", "y", "z", "visibility")

    def __init__(self, d: dict):
        self.x          = float(d.get("x", 0))
        self.y          = float(d.get("y", 0))
        self.z          = float(d.get("z", 0))
        self.visibility = float(d.get("visibility", 0))


def _parse_landmarks(raw: list) -> list:
    """Convert the raw JSON landmark list into _Landmark objects."""
    if len(raw) != 33:
        raise ValueError(f"Expected 33 landmarks, got {len(raw)}")
    return [_Landmark(d) for d in raw]


# ─── WebSocket endpoint ───────────────────────────────────────────────────────

@app.websocket("/session/{exercise_name}")
async def exercise_session(websocket: WebSocket,exercise_name: str,):
    """
    One WebSocket connection = one user's exercise session.

    The connection lifecycle:
      1. Client connects  → server creates a Session for that exercise.
      2. Client sends frames (JSON) → server processes and replies.
      3. Client disconnects → session is garbage collected.

    If the exercise_name is invalid the connection is immediately closed
    with a 4000 code and an error message.
    """
    
    await websocket.accept()
    log.info(f"Connection opened — exercise: {exercise_name}")

    # ── Create session ────────────────────────────────────────────────
    try:
        session = Session(exercise_name)
    except ValueError as e:
        await websocket.send_text(json.dumps({"error": str(e)}))
        await websocket.close(code=4000)
        log.warning(f"Rejected connection: {e}")
        return

    # ── Frame loop ────────────────────────────────────────────────────
    try:
        while True:
            raw_text = await websocket.receive_text()

            # Parse incoming JSON
            try:
                payload = json.loads(raw_text)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "invalid JSON"}))
                continue

            # Parse landmarks
            try:
                landmarks = _parse_landmarks(payload.get("landmarks", []))
            except ValueError as e:
                await websocket.send_text(json.dumps({"error": str(e)}))
                continue

            # Process the frame
            try:
                result = session.process(landmarks)
            except Exception as e:
                log.exception("Error processing frame")
                await websocket.send_text(json.dumps({"error": "processing error"}))
                continue

            await websocket.send_text(json.dumps(result))

    except WebSocketDisconnect:
        log.info(f"Connection closed — exercise: {exercise_name}")
