"""
exercises/pushup.py
-------------------
Form checks and rep counter config for the push-up (side view).
Supports both Toe Push-Up and Knee Push-Up modes — detected once at
session start and locked for the rep sequence.

The rep metric is the elbow angle:
  - starts near full extension (~150–165°)
  - descends to ~90–120° at the bottom
  - returns to full extension to complete the rep

Exports
-------
THRESHOLDS     : dict  — all tunable values
COUNTER_CONFIG : dict  — tells RepCounter how to count reps
check_form()   : called every frame by Session.process()
reset_mode()   : clears locked push-up mode (TOE/KNEE)
reset_rep_counter() : clears EMA and hysteresis zone state
"""

import numpy as np
from utils import lm, joint_angle, torso_angle, midpoint, xy

# ─── Thresholds ───────────────────────────────────────────────────────────────
THRESHOLDS = {
    # Elbow angles
    "elbow_start_min":          150.0,  # degrees — arms extended at start
    "elbow_depth_max":          120.0,  # degrees — minimum depth (forgiving)
    "elbow_return_min":         145.0,  # degrees — near-extended at top (forgiving)

    # Body alignment (hip sag / pike)
    "alignment_sag_max":         0.06,  # normalised — how far hips drop below line
    "alignment_pike_max":        0.06,  # normalised — how far hips rise above line

    # Elbow flare
    "elbow_flare_max":           0.10,  # normalised x-drift of elbow from baseline

    # Synchronisation (shoulders vs hips vertical velocity delta)
    "sync_delta_max":            0.04,  # normalised units/frame — descent and ascent

    # Velocity / control
    "descent_accel_max":         0.06,  # normalised — no sudden drop
    "ascent_velocity_max":       0.08,  # normalised — no explosive push

    # Stability (pre-rep)
    "stability_threshold":       0.03,  # normalised displacement — body still at start

    # Mode detection
    "knee_elevated_threshold":   0.15,  # normalised — knee y above ankle y = toe push-up

    # Head neutrality
    "head_offset_max":           0.08,  # normalised — ear relative to shoulder line

    # ── Smoothing & hysteresis ────────────────────────────────────────────
    # EMA alpha: lower = smoother but more lag. 0.35 is a good balance
    # for push-ups (~30fps). Raise toward 0.5 if the signal feels sluggish.
    "ema_alpha":                 0.35,

    # Once the angle enters the top or bottom zone, it must clear this
    # many degrees before the opposite boundary becomes active again.
    # This kills phantom reps from wobble at the top between reps.
    "hysteresis_band":           8.0,   # degrees
}

# ─── Rep counter config ───────────────────────────────────────────────────────
# Raised start_threshold to 150° (was 145°) so RepCounter only sees "top
# confirmed" when the user is truly extended, not mid-wobble.
# Lowered end_threshold to 115° (was 120°) so a bounce just touching 120°
# doesn't trigger a false bottom confirmation.
COUNTER_CONFIG = {
    "start_threshold": 150.0,   # elbow ≥ 150° → arms fully extended
    "end_threshold":   115.0,   # elbow ≤ 115° → sufficient depth confirmed
    "direction":       "down",
}

# ─── Mode detection ───────────────────────────────────────────────────────────
_locked_mode = None

def detect_pushup_mode(landmarks: list) -> str:
    """
    Classify as 'TOE' or 'KNEE' push-up based on whether the knee or
    ankle forms the terminal support point.
    Called each frame until a confident classification is locked.
    """
    global _locked_mode
    if _locked_mode is not None:
        return _locked_mode

    left_knee   = lm(landmarks, "LEFT_KNEE")
    left_ankle  = lm(landmarks, "LEFT_ANKLE")
    right_knee  = lm(landmarks, "RIGHT_KNEE")
    right_ankle = lm(landmarks, "RIGHT_ANKLE")

    # In image coords y increases downward.
    # Toe push-up: knee is higher (smaller y) than ankle.
    # Knee push-up: knee is at or below ankle level.
    avg_knee_y  = (left_knee.y  + right_knee.y)  / 2.0
    avg_ankle_y = (left_ankle.y + right_ankle.y) / 2.0

    if avg_ankle_y - avg_knee_y > THRESHOLDS["knee_elevated_threshold"]:
        _locked_mode = "TOE"
    else:
        _locked_mode = "KNEE"

    return _locked_mode

def reset_mode():
    """Clear locked TOE/KNEE mode. Called by Session.__post_init__."""
    global _locked_mode
    _locked_mode = None

# ─── Helper ───────────────────────────────────────────────────────────────────
def _check(label: str, passed: bool, value: float, message: str) -> dict:
    return {
        "label":   label,
        "ok":      passed,
        "value":   round(value, 3),
        "message": "" if passed else message,
    }

def _body_alignment_deviation(landmarks: list, mode: str) -> float:
    """
    Return how far the hips deviate from the shoulder→support line.
    Positive = hips above line (pike).
    Negative = hips below line (sag).
    """
    l_shoulder = lm(landmarks, "LEFT_SHOULDER")
    r_shoulder = lm(landmarks, "RIGHT_SHOULDER")
    l_hip      = lm(landmarks, "LEFT_HIP")
    r_hip      = lm(landmarks, "RIGHT_HIP")

    shoulder_y = (l_shoulder.y + r_shoulder.y) / 2.0
    hip_y      = (l_hip.y      + r_hip.y)      / 2.0
    shoulder_x = (l_shoulder.x + r_shoulder.x) / 2.0
    hip_x      = (l_hip.x      + r_hip.x)      / 2.0

    if mode == "TOE":
        l_ankle   = lm(landmarks, "LEFT_ANKLE")
        r_ankle   = lm(landmarks, "RIGHT_ANKLE")
        support_y = (l_ankle.y + r_ankle.y) / 2.0
        support_x = (l_ankle.x + r_ankle.x) / 2.0
    else:  # KNEE
        l_knee    = lm(landmarks, "LEFT_KNEE")
        r_knee    = lm(landmarks, "RIGHT_KNEE")
        support_y = (l_knee.y + r_knee.y) / 2.0
        support_x = (l_knee.x + r_knee.x) / 2.0

    if abs(support_x - shoulder_x) < 1e-6:
        ideal_hip_y = (shoulder_y + support_y) / 2.0
    else:
        t = (hip_x - shoulder_x) / (support_x - shoulder_x)
        ideal_hip_y = shoulder_y + t * (support_y - shoulder_y)

    # Positive = pike (hips above ideal line), negative = sag
    return ideal_hip_y - hip_y

# ─── Per-frame velocity & smoothing state ────────────────────────────────────
_prev_shoulder_y = None
_prev_hip_y      = None
_ema_elbow_angle = None   # exponential moving average of raw elbow angle
_last_zone       = None   # "top" | "bottom" | None — hysteresis zone tracker

def reset_rep_counter():
    """
    Clear EMA and hysteresis zone state.
    Called by Session.__post_init__ so a new session starts clean.
    """
    global _prev_shoulder_y, _prev_hip_y, _ema_elbow_angle, _last_zone
    _prev_shoulder_y = None
    _prev_hip_y      = None
    _ema_elbow_angle = None
    _last_zone       = None

# ─── Smoothed, hysteresis-gated metric ───────────────────────────────────────
def _smooth_and_gate(raw_angle: float) -> float:
    """
    Two-step signal conditioning before the angle reaches RepCounter:

    Step 1 — EMA smoothing
        Removes frame-to-frame jitter from MediaPipe landmark noise.
        alpha=0.35 means each frame contributes 35% of the new value.

    Step 2 — Hysteresis gating
        Once the angle enters the top zone (≥ 150°) or bottom zone (≤ 115°),
        clamp it there until it clears the zone by `hysteresis_band` degrees.
        RepCounter never sees rapid back-and-forth crossings at the boundary,
        which is the direct cause of phantom reps during the wobble at the top.
    """
    global _ema_elbow_angle, _last_zone

    alpha = THRESHOLDS["ema_alpha"]
    band  = THRESHOLDS["hysteresis_band"]

    # ── Step 1: EMA ───────────────────────────────────────────────────────
    if _ema_elbow_angle is None:
        _ema_elbow_angle = raw_angle
    else:
        _ema_elbow_angle = alpha * raw_angle + (1.0 - alpha) * _ema_elbow_angle

    smoothed = _ema_elbow_angle

    top_threshold    = COUNTER_CONFIG["start_threshold"]   # 150°
    bottom_threshold = COUNTER_CONFIG["end_threshold"]     # 115°

    # ── Step 2: Hysteresis gating ─────────────────────────────────────────
    if _last_zone == "top":
        # Locked at top — only exit when angle drops well below threshold
        if smoothed < top_threshold - band:        # below 142°
            _last_zone = None
        else:
            return top_threshold   # clamp: RepCounter sees a stable 150°

    elif _last_zone == "bottom":
        # Locked at bottom — only exit when angle rises well above threshold
        if smoothed > bottom_threshold + band:     # above 123°
            _last_zone = None
        else:
            return bottom_threshold   # clamp: RepCounter sees a stable 115°

    # Zone entry check
    if smoothed >= top_threshold:
        _last_zone = "top"
        return top_threshold

    if smoothed <= bottom_threshold:
        _last_zone = "bottom"
        return bottom_threshold

    return smoothed

# ─── Form checks ──────────────────────────────────────────────────────────────
def check_form(landmarks: list, baselines: dict) -> tuple:
    """
    Run all form checks for one frame of a push-up (side view).

    Parameters
    ----------
    landmarks : list      33 MediaPipe landmark objects.
    baselines : dict      Shared with Session; written on first frame, read after.

    Returns
    -------
    checks      : list[dict]   One dict per check: {label, ok, value, message}
    metric      : float        Smoothed/gated elbow angle — drives RepCounter.
                               Form checks use the raw angle so feedback is honest.
    active_side : str          Always "BOTH" for this bilateral exercise.

    Note: returns 3 values (no rep_valid). Phantom reps are handled entirely
    by signal conditioning (_smooth_and_gate), not a validity gate.
    """
    global _prev_shoulder_y, _prev_hip_y

    mode = detect_pushup_mode(landmarks)

    # ── Key landmarks ─────────────────────────────────────────────────────
    l_shoulder = lm(landmarks, "LEFT_SHOULDER")
    r_shoulder = lm(landmarks, "RIGHT_SHOULDER")
    l_elbow    = lm(landmarks, "LEFT_ELBOW")
    r_elbow    = lm(landmarks, "RIGHT_ELBOW")
    l_wrist    = lm(landmarks, "LEFT_WRIST")
    r_wrist    = lm(landmarks, "RIGHT_WRIST")
    l_hip      = lm(landmarks, "LEFT_HIP")
    r_hip      = lm(landmarks, "RIGHT_HIP")
    l_ear      = lm(landmarks, "LEFT_EAR")
    r_ear      = lm(landmarks, "RIGHT_EAR")

    # ── Computed values ───────────────────────────────────────────────────
    l_elbow_angle   = joint_angle(l_shoulder, l_elbow, l_wrist)
    r_elbow_angle   = joint_angle(r_shoulder, r_elbow, r_wrist)
    raw_elbow_angle = (l_elbow_angle + r_elbow_angle) / 2.0

    shoulder_y      = (l_shoulder.y + r_shoulder.y) / 2.0
    hip_y           = (l_hip.y      + r_hip.y)      / 2.0
    elbow_x_avg     = (l_elbow.x    + r_elbow.x)    / 2.0
    ear_y           = (l_ear.y      + r_ear.y)       / 2.0
    shoulder_y_avg  = (l_shoulder.y + r_shoulder.y) / 2.0

    torso_len       = abs(shoulder_y - hip_y) or 0.1

    alignment_dev   = _body_alignment_deviation(landmarks, mode)

    # Frame-over-frame velocities
    if _prev_shoulder_y is not None:
        shoulder_vel  = shoulder_y - _prev_shoulder_y   # positive = moving down
        hip_vel       = hip_y      - _prev_hip_y
        sync_delta    = abs(shoulder_vel - hip_vel)
        descent_accel = max(shoulder_vel, 0.0)           # only flag downward
    else:
        shoulder_vel  = 0.0
        hip_vel       = 0.0
        sync_delta    = 0.0
        descent_accel = 0.0

    _prev_shoulder_y = shoulder_y
    _prev_hip_y      = hip_y

    elbow_drift = abs(elbow_x_avg - baselines.get("elbow_x", elbow_x_avg)) / torso_len
    head_offset = abs(ear_y - shoulder_y_avg) / torso_len

    # ── Capture baselines on first frame ──────────────────────────────────
    if not baselines:
        baselines["elbow_x"]    = elbow_x_avg
        baselines["shoulder_y"] = shoulder_y
        baselines["hip_y"]      = hip_y

    # ── Smooth + gate the metric BEFORE handing to RepCounter ─────────────
    # raw_elbow_angle is used in checks below so coaching feedback is honest.
    metric = _smooth_and_gate(raw_elbow_angle)

    # ── Checks ────────────────────────────────────────────────────────────
    checks = [

        # ── Section 2: Start / alignment ──────────────────────────────────
        _check(
            "Body alignment",
            abs(alignment_dev) <= max(
                THRESHOLDS["alignment_sag_max"],
                THRESHOLDS["alignment_pike_max"]
            ),
            alignment_dev,
            "keep hips in line with shoulders"
            if alignment_dev < 0
            else "hips are too high — lower them into line",
        ),
        _check(
            "Head neutral",
            head_offset <= THRESHOLDS["head_offset_max"],
            head_offset,
            "keep your head in line with your body",
        ),

        # ── Section 3: Descent ────────────────────────────────────────────
        _check(
            "Controlled descent",
            descent_accel <= THRESHOLDS["descent_accel_max"],
            descent_accel,
            "lower yourself with control — don't drop",
        ),
        _check(
            "Body moving as one unit",
            sync_delta <= THRESHOLDS["sync_delta_max"],
            sync_delta,
            "keep hips moving with your chest",
        ),
        _check(
            "Elbows tracking",
            elbow_drift <= THRESHOLDS["elbow_flare_max"],
            elbow_drift,
            "try keeping elbows a bit closer to your body",
        ),

        # ── Section 4: Depth ──────────────────────────────────────────────
        _check(
            "Good depth",
            raw_elbow_angle <= THRESHOLDS["elbow_depth_max"],
            raw_elbow_angle,
            "good control — lower a little more",
        ),

        # ── Section 5: Ascent / top ───────────────────────────────────────
        _check(
            "Full arm extension",
            raw_elbow_angle >= THRESHOLDS["elbow_return_min"],
            raw_elbow_angle,
            "push all the way up to finish the rep",
        ),
    ]

    return checks, metric, "BOTH"