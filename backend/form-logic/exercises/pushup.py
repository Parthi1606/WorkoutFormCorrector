"""
exercises/pushup.py
-------------------
Form checks and rep counter config for the push-up (side view).
Supports both Toe Push-Up and Knee Push-Up modes — detected once at
session start and locked for the rep sequence.

The rep metric is the elbow angle:
  - starts near full extension (~150–165°)
  - descends to ~90° at the bottom
  - returns to full extension to complete the rep

Exports
-------
THRESHOLDS          : dict  — all tunable values
COUNTER_CONFIG      : dict  — tells RepCounter how to count reps
check_form()        : called every frame by Session.process()
reset_mode()        : clears locked push-up mode (TOE/KNEE)
reset_rep_counter() : clears EMA and hysteresis zone state

Key design decisions
--------------------
REMOVED checks (wrong geometry for side-view camera):
  - Head neutral: ear_x vs shoulder_x always fails from the side — the head
    is physically in front of the shoulders. No reliable signal available.
  - Elbow flare: x-drift from side view measures forward/back swing, not
    outward flare (z-axis). Removed entirely.

GATE-BASED checks (depth + extension):
  - "Good depth" and "Full arm extension" are no longer per-frame faults.
    check_form() writes baselines["hit_depth"] and baselines["hit_top"] —
    one-way latches set the moment the elbow crosses the threshold in the
    correct direction. session.py reads these at rep completion and injects
    a single fault if a gate was never tripped. Same pattern as
    shoulder_press hit_lockout. Eliminates the fault accumulation bug where
    every mid-phase frame added the same message to _faults.

SYNC check:
  - Disabled for KNEE mode. The knee pivot means hips always travel less
    than shoulders — velocity delta is non-zero by kinematics, not bad form.

ALIGNMENT threshold:
  - Mode-dependent: 0.15 for KNEE, 0.10 for TOE. The shoulder→knee line is
    steeper than shoulder→ankle, so the same physical hip wobble produces a
    larger perpendicular deviation in normalised coords.
"""

from utils import lm, joint_angle

# ─── Thresholds ───────────────────────────────────────────────────────────────
THRESHOLDS = {
    # Elbow angle gates (evaluated once at rep end via baselines, not per-frame)
    "elbow_depth_max":         120.0,  # degrees — must be reached during descent
    "elbow_return_min":        145.0,  # degrees — must be reached at top

    # Body alignment — hip deviation from shoulder→support line
    "alignment_max_toe":        0.10,  # normalised — TOE (shoulder→ankle, shallower line)
    "alignment_max_knee":       0.20,  # normalised — KNEE (shoulder→knee, steeper line)

    # Synchronisation — shoulder vs hip velocity delta (TOE only)
    "sync_delta_max":           0.08,  # normalised units/frame

    # Controlled descent — shoulder downward velocity per frame
    "descent_accel_max":        0.10,  # normalised — flags genuine drops only

    # Mode detection
    "knee_elevated_threshold":  0.07,  # normalised y-diff: ankle above knee = TOE

    # Smoothing
    "ema_alpha":                0.35,  # EMA weight per frame (0=no update, 1=raw)
    "hysteresis_band":          8.0,   # degrees — zone lock-in width
}

# ─── Rep counter config ───────────────────────────────────────────────────────
COUNTER_CONFIG = {
    "start_threshold": 150.0,   # elbow ≥ 150° → confirmed at top
    "end_threshold":   115.0,   # elbow ≤ 115° → confirmed at bottom
    "direction":       "down",  # angle decreases as user lowers
}

# ─── Mode detection ───────────────────────────────────────────────────────────
_locked_mode = None

_locked_mode = None
_mode_votes  = []          # accumulate readings before locking
_MODE_WINDOW = 10          # frames required before locking
_MODE_MIN_CONFIDENCE = 0.7 # 70% of votes must agree

def detect_pushup_mode(landmarks: list) -> str:
    global _locked_mode, _mode_votes

    if _locked_mode is not None:
        return _locked_mode

    l_knee  = lm(landmarks, "LEFT_KNEE")
    l_ankle = lm(landmarks, "LEFT_ANKLE")
    r_knee  = lm(landmarks, "RIGHT_KNEE")
    r_ankle = lm(landmarks, "RIGHT_ANKLE")

    avg_knee_y  = (l_knee.y  + r_knee.y)  / 2.0
    avg_ankle_y = (l_ankle.y + r_ankle.y) / 2.0

    vote = (
        "TOE" if avg_ankle_y - avg_knee_y > THRESHOLDS["knee_elevated_threshold"]
        else "KNEE"
    )
    _mode_votes.append(vote)

    if len(_mode_votes) >= _MODE_WINDOW:
        toe_ratio = _mode_votes.count("TOE") / len(_mode_votes)
        if toe_ratio >= _MODE_MIN_CONFIDENCE:
            _locked_mode = "TOE"
        elif toe_ratio <= (1.0 - _MODE_MIN_CONFIDENCE):
            _locked_mode = "KNEE"
        else:
            _mode_votes.pop(0)  # not confident yet — drop oldest, keep sliding

    return _locked_mode or vote  # return best current guess until locked

def reset_mode():
    global _locked_mode, _mode_votes
    _locked_mode = None
    _mode_votes  = []

# ─── Helpers ──────────────────────────────────────────────────────────────────
def _check(label: str, passed: bool, value: float, message: str) -> dict:
    return {
        "label":   label,
        "ok":      passed,
        "value":   round(value, 3),
        "message": "" if passed else message,
    }

def _body_alignment_deviation(landmarks: list, mode: str) -> float:
    """
    Signed deviation of hips from the shoulder→support line.
      Positive = pike (hips above ideal line).
      Negative = sag  (hips below ideal line).
    Support point: ankle (TOE) or knee (KNEE).
    """
    l_shoulder = lm(landmarks, "LEFT_SHOULDER")
    r_shoulder = lm(landmarks, "RIGHT_SHOULDER")
    l_hip      = lm(landmarks, "LEFT_HIP")
    r_hip      = lm(landmarks, "RIGHT_HIP")

    shoulder_y = (l_shoulder.y + r_shoulder.y) / 2.0
    shoulder_x = (l_shoulder.x + r_shoulder.x) / 2.0
    hip_y      = (l_hip.y      + r_hip.y)      / 2.0
    hip_x      = (l_hip.x      + r_hip.x)      / 2.0

    if mode == "TOE":
        l_ankle   = lm(landmarks, "LEFT_ANKLE")
        r_ankle   = lm(landmarks, "RIGHT_ANKLE")
        support_y = (l_ankle.y + r_ankle.y) / 2.0
        support_x = (l_ankle.x + r_ankle.x) / 2.0
    else:
        l_knee    = lm(landmarks, "LEFT_KNEE")
        r_knee    = lm(landmarks, "RIGHT_KNEE")
        support_y = (l_knee.y + r_knee.y) / 2.0
        support_x = (l_knee.x + r_knee.x) / 2.0

    if abs(support_x - shoulder_x) < 1e-6:
        ideal_hip_y = (shoulder_y + support_y) / 2.0
    else:
        t = (hip_x - shoulder_x) / (support_x - shoulder_x)
        ideal_hip_y = shoulder_y + t * (support_y - shoulder_y)

    return ideal_hip_y - hip_y   # positive = pike, negative = sag

# ─── Per-frame velocity & smoothing state ─────────────────────────────────────
_prev_shoulder_y = None
_prev_hip_y      = None
_ema_elbow_angle = None
_last_zone       = None   # "top" | "bottom" | None

def reset_rep_counter():
    """Clear EMA and velocity state. Called by Session.__post_init__."""
    global _prev_shoulder_y, _prev_hip_y, _ema_elbow_angle, _last_zone
    _prev_shoulder_y = None
    _prev_hip_y      = None
    _ema_elbow_angle = None
    _last_zone       = None

# ─── EMA + hysteresis gating ──────────────────────────────────────────────────
def _smooth_and_gate(raw_angle: float) -> float:
    """
    Step 1 — EMA: smooths per-frame jitter from MediaPipe noise.
    Step 2 — Hysteresis: clamps inside a zone until the angle clears it by
             `hysteresis_band` degrees, eliminating phantom reps from wobble
             at the top between reps.
    """
    global _ema_elbow_angle, _last_zone

    alpha = THRESHOLDS["ema_alpha"]
    band  = THRESHOLDS["hysteresis_band"]

    _ema_elbow_angle = (
        raw_angle if _ema_elbow_angle is None
        else alpha * raw_angle + (1.0 - alpha) * _ema_elbow_angle
    )
    smoothed = _ema_elbow_angle

    top_thr = COUNTER_CONFIG["start_threshold"]   # 150°
    bot_thr = COUNTER_CONFIG["end_threshold"]     # 115°

    if _last_zone == "top":
        if smoothed < top_thr - band:   # dropped below 142° — exit zone
            _last_zone = None
        else:
            return top_thr              # clamp: RepCounter sees a stable 150°

    elif _last_zone == "bottom":
        if smoothed > bot_thr + band:   # rose above 123° — exit zone
            _last_zone = None
        else:
            return bot_thr             # clamp: RepCounter sees a stable 115°

    if smoothed >= top_thr:
        _last_zone = "top"
        return top_thr
    if smoothed <= bot_thr:
        _last_zone = "bottom"
        return bot_thr

    return smoothed

# ─── Form checks ──────────────────────────────────────────────────────────────
def check_form(landmarks: list, baselines: dict) -> tuple:
    """
    Run all form checks for one frame of a push-up (side view).

    Parameters
    ----------
    landmarks : list    33 MediaPipe landmark objects.
    baselines : dict    Shared with Session. Written on first frame of each
                        rep; cleared by Session when a rep completes.

    Returns
    -------
    checks      : list[dict]   Per-check result dicts {label, ok, value, message}.
    metric      : float        Smoothed/gated elbow angle for RepCounter.
    active_side : str          Always "BOTH".

    Baseline flags (read by session.py at rep completion):
      hit_depth : bool — True once elbow ≤ elbow_depth_max this rep.
      hit_top   : bool — True once elbow ≥ elbow_return_min this rep.
    """
    global _prev_shoulder_y, _prev_hip_y

    mode = detect_pushup_mode(landmarks)

    # ── Landmarks ─────────────────────────────────────────────────────────
    l_shoulder = lm(landmarks, "LEFT_SHOULDER")
    r_shoulder = lm(landmarks, "RIGHT_SHOULDER")
    l_elbow    = lm(landmarks, "LEFT_ELBOW")
    r_elbow    = lm(landmarks, "RIGHT_ELBOW")
    l_wrist    = lm(landmarks, "LEFT_WRIST")
    r_wrist    = lm(landmarks, "RIGHT_WRIST")
    l_hip      = lm(landmarks, "LEFT_HIP")
    r_hip      = lm(landmarks, "RIGHT_HIP")

    # ── Computed values ───────────────────────────────────────────────────
    l_elbow_angle   = joint_angle(l_shoulder, l_elbow, l_wrist)
    r_elbow_angle   = joint_angle(r_shoulder, r_elbow, r_wrist)
    raw_elbow_angle = (l_elbow_angle + r_elbow_angle) / 2.0

    shoulder_y    = (l_shoulder.y + r_shoulder.y) / 2.0
    hip_y         = (l_hip.y      + r_hip.y)      / 2.0
    alignment_dev = _body_alignment_deviation(landmarks, mode)

    # Frame-over-frame velocities
    if _prev_shoulder_y is not None:
        shoulder_vel  = shoulder_y - _prev_shoulder_y   # positive = descending
        hip_vel       = hip_y      - _prev_hip_y
        sync_delta    = abs(shoulder_vel - hip_vel)
        descent_accel = max(shoulder_vel, 0.0)
    else:
        shoulder_vel  = 0.0
        hip_vel       = 0.0
        sync_delta    = 0.0
        descent_accel = 0.0

    _prev_shoulder_y = shoulder_y
    _prev_hip_y      = hip_y

    # ── Baselines — initialise on first frame of each rep ─────────────────
    if not baselines:
        baselines["hit_depth"] = False  # latch: did elbow reach depth this rep?
        baselines["hit_top"]   = False  # latch: did elbow reach extension this rep?

    # Update latches — one-way, never cleared mid-rep
    if raw_elbow_angle <= THRESHOLDS["elbow_depth_max"]:
        baselines["hit_depth"] = True
    if raw_elbow_angle >= THRESHOLDS["elbow_return_min"]:
        baselines["hit_top"] = True

    # ── Smooth + gate the metric for RepCounter ───────────────────────────
    metric = _smooth_and_gate(raw_elbow_angle)

    # ── Mode-dependent alignment threshold ────────────────────────────────
    alignment_max = (
        THRESHOLDS["alignment_max_knee"]
        if mode == "KNEE"
        else THRESHOLDS["alignment_max_toe"]
    )

    # ── Live checks (per-frame, recorded as faults if they fire) ─────────
    #
    # Only 3 checks remain — all are genuinely observable from a side-view
    # camera and produce valid signals throughout the movement:
    #
    #   1. Body alignment  — hip sag / pike vs shoulder→support line.
    #   2. Controlled descent — shoulder velocity spike = sudden drop.
    #   3. Body sync (TOE only) — shoulders + hips descend together.
    #
    # "Good depth" and "Full arm extension" have been moved to gate checks
    # in session.py (hit_depth / hit_top) so they fire at most once per rep,
    # not on every frame of mid-phase movement.

    checks = [

        _check(
            "Body alignment",
            abs(alignment_dev) <= alignment_max,
            alignment_dev,
            "keep hips in line with your body"
            if alignment_dev < 0
            else "hips are too high — lower them into line",
        ),

        _check(
            "Controlled descent",
            descent_accel <= THRESHOLDS["descent_accel_max"],
            descent_accel,
            "lower yourself with control — don't drop",
        ),

        # Disabled for KNEE — knee pivot makes hip velocity always lag
        # shoulder velocity by design; enforcing sync flags clean form.
        _check(
            "Body moving as one unit",
            sync_delta <= THRESHOLDS["sync_delta_max"] or mode == "KNEE",
            sync_delta,
            "keep hips moving with your chest",
        ),
    ]

    l_knee  = lm(landmarks, "LEFT_KNEE")
    l_ankle = lm(landmarks, "LEFT_ANKLE")
    r_knee  = lm(landmarks, "RIGHT_KNEE")
    r_ankle = lm(landmarks, "RIGHT_ANKLE")
    _dbg_knee_y  = (l_knee.y  + r_knee.y)  / 2.0
    _dbg_ankle_y = (l_ankle.y + r_ankle.y) / 2.0
    print(f"[MODE] locked={_locked_mode}  knee_y={_dbg_knee_y:.3f}  ankle_y={_dbg_ankle_y:.3f}  diff={_dbg_ankle_y - _dbg_knee_y:.3f}  threshold={THRESHOLDS['knee_elevated_threshold']}")

    return checks, metric, "BOTH"