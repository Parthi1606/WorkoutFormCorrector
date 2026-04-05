"""
exercises/bent_over_row.py
--------------------------
Form checks and rep counter config for the dumbbell bent-over row.
Single arm, side view. Active arm detected via elbow z-value.

The rep metric is the elbow angle:
  - starts near full extension (~150°+)
  - pulls to ~80-90° at the top (wrist near hip/lower rib)
  - returns to full extension to complete the rep

Exports
-------
THRESHOLDS     : dict  — all tunable values
COUNTER_CONFIG : dict  — tells RepCounter how to count reps
check_form()   : called every frame by Session.process()
"""

# -*- coding: utf-8 -*-
from utils import lm, joint_angle, torso_angle, midpoint, xy, active_side as detect_side
import numpy as np

# ─── Thresholds ───────────────────────────────────────────────────────────────
THRESHOLDS = {
    # Torso / hinge
    "torso_hinge_min":          25.0,
    "torso_hinge_max":          65.0,
    "torso_delta_max":          40.0,
    "torso_swing_max":           0.18,

    # Knee flexion
    "knee_angle_min":          100.0,
    "knee_angle_max":          168.0,

    # Elbow / arm
    "elbow_top_max":            90.0,

    # Elbow path
    "elbow_upward_ratio_max":    1.5,

    # Wrist endpoint
    "wrist_reach_min":           0.10,
    "wrist_overshoot_max":       0.20,

    # Shoulder shrug
    "shoulder_elevation_max":    0.09,

    # Velocity / control
    "pull_velocity_max":         0.12,
    "descent_velocity_max":      0.12,
}

# ─── Rep counter config ───────────────────────────────────────────────────────
COUNTER_CONFIG = {
    "start_threshold": 150.0,
    "end_threshold":    90.0,
    "direction":       "down",
}

# ─── Helper ───────────────────────────────────────────────────────────────────
def _check(label: str, passed: bool, value: float, message: str) -> dict:
    return {
        "label":   label,
        "ok":      passed,
        "value":   round(value, 3),
        "message": "" if passed else message,
    }

# ─── Per-frame velocity tracking ─────────────────────────────────────────────
_prev_elbow_x = None
_prev_elbow_y = None
_prev_wrist_y = None

def reset_velocity_tracker():
    """Call this when a new session or set starts to avoid stale velocity."""
    global _prev_elbow_x, _prev_elbow_y, _prev_wrist_y
    _prev_elbow_x = None
    _prev_elbow_y = None
    _prev_wrist_y = None

# ─── Form checks ──────────────────────────────────────────────────────────────
def check_form(landmarks: list, baselines: dict) -> tuple:
    global _prev_elbow_x, _prev_elbow_y, _prev_wrist_y

    side   = detect_side(landmarks)
    prefix = side

    # ── Key landmarks ─────────────────────────────────────────────────────
    shoulder = lm(landmarks, f"{prefix}_SHOULDER")
    elbow    = lm(landmarks, f"{prefix}_ELBOW")
    wrist    = lm(landmarks, f"{prefix}_WRIST")
    hip      = lm(landmarks, f"{prefix}_HIP")
    knee     = lm(landmarks, f"{prefix}_KNEE")
    ankle    = lm(landmarks, f"{prefix}_ANKLE")

    # ── Visibility flags ──────────────────────────────────────────────────
    ankle_visible = ankle.visibility > 0.5
    wrist_visible = wrist.visibility > 0.5

    # ── Computed values ───────────────────────────────────────────────────
    elbow_angle     = joint_angle(shoulder, elbow, wrist)
    knee_angle      = joint_angle(hip, knee, ankle) if ankle_visible else None
    t_angle         = torso_angle(landmarks)
    torso_len       = abs(shoulder.y - hip.y) or 0.1
    wrist_above_hip = (hip.y - wrist.y) / torso_len if wrist_visible else 0.0

    # ── Capture baselines on first frame ──────────────────────────────────
    if not baselines:
        baselines["torso_angle"] = t_angle
        baselines["shoulder_y"]  = shoulder.y
        baselines["hip_x"]       = hip.x
        baselines["hit_top"]     = False

    # Continuously update baselines outside the pull phase
    if elbow_angle > 130.0:
        baselines["torso_angle"] = t_angle
        baselines["hip_x"]       = hip.x
        baselines["shoulder_y"]  = shoulder.y

    # Track whether wrist cleared hip during this rep
    if wrist_visible and wrist_above_hip >= THRESHOLDS["wrist_reach_min"]:
        baselines["hit_top"] = True

    # ── Delta / drift values ──────────────────────────────────────────────
    torso_delta   = abs(t_angle - baselines["torso_angle"])
    hip_x_delta   = abs(hip.x - baselines["hip_x"]) / torso_len
    shoulder_rise = baselines["shoulder_y"] - shoulder.y

    # ── Elbow path ────────────────────────────────────────────────────────
    if _prev_elbow_x is not None:
        d_elbow_x = abs(elbow.x - _prev_elbow_x)
        d_elbow_y = max(0.0, _prev_elbow_y - elbow.y)

        pull_velocity = np.sqrt(d_elbow_x**2 + d_elbow_y**2) / torso_len

        if d_elbow_x > 0.01:
            elbow_up_ratio = d_elbow_y / d_elbow_x
        else:
            elbow_up_ratio = 0.0

        wrist_drop_vel = max(0.0, wrist.y - (_prev_wrist_y or wrist.y)) / torso_len if wrist_visible else 0.0
    else:
        pull_velocity  = 0.0
        elbow_up_ratio = 0.0
        wrist_drop_vel = 0.0

    _prev_elbow_x = elbow.x
    _prev_elbow_y = elbow.y
    _prev_wrist_y = wrist.y if wrist_visible else _prev_wrist_y

    # ── Checks ────────────────────────────────────────────────────────────
    checks = [

        # ── Section 1: Hinge position ─────────────────────────────────────
        _check(
            "Hip hinge position",
            THRESHOLDS["torso_hinge_min"] <= t_angle <= THRESHOLDS["torso_hinge_max"],
            t_angle,
            "hinge further forward from your hips"
            if t_angle < THRESHOLDS["torso_hinge_min"]
            else "you're bent too far — lift your chest slightly",
        ),
        _check(
            "Knee flexion",
            # Pass silently if ankle not visible — no data to judge
            not ankle_visible or (
                THRESHOLDS["knee_angle_min"] <= knee_angle <= THRESHOLDS["knee_angle_max"]
            ),
            knee_angle if knee_angle is not None else 0.0,
            "soften your knees slightly"
            if (knee_angle or 0.0) > THRESHOLDS["knee_angle_max"]
            else "don't bend your knees too much — this is a hinge, not a squat",
        ),
        _check(
            "Shoulder set",
            shoulder_rise <= THRESHOLDS["shoulder_elevation_max"],
            shoulder_rise,
            "keep your shoulder down — don't shrug",
        ),

        # ── Section 2: Pull phase ─────────────────────────────────────────
        _check(
            "Elbow drives back",
            elbow_up_ratio <= THRESHOLDS["elbow_upward_ratio_max"],
            elbow_up_ratio,
            "drive your elbow back, not upward",
        ),
        _check(
            "Controlled pull",
            pull_velocity <= THRESHOLDS["pull_velocity_max"],
            pull_velocity,
            "pull with control — no yanking",
        ),
        _check(
            "Torso stable",
            torso_delta <= THRESHOLDS["torso_delta_max"] or elbow_angle > 130.0,
            torso_delta,
            "keep your torso still — don't swing or rise",
        ),
        _check(
            "No hip sway",
            hip_x_delta <= THRESHOLDS["torso_swing_max"],
            hip_x_delta,
            "hips are moving — drive with your arm, not your body",
        ),

        # ── Section 3: Top position ───────────────────────────────────────
        _check(
            "No overpull",
            not wrist_visible or wrist_above_hip <= THRESHOLDS["wrist_overshoot_max"] or elbow_angle > 100.0,
            wrist_above_hip,
            "don't pull past your hip — squeeze at the top",
        ),

        # ── Section 4: Lowering ───────────────────────────────────────────
        _check(
            "Controlled descent",
            not wrist_visible or wrist_drop_vel <= THRESHOLDS["descent_velocity_max"],
            wrist_drop_vel,
            "lower the weight slowly — don't drop it",
        ),
    ]

    return checks, elbow_angle, side
