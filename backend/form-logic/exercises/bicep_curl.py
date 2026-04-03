"""
exercises/bicep_curl.py
-----------------------
Form checks and rep counter config for the bicep curl.

Exports
-------
THRESHOLDS      : dict — all tunable values in one place
COUNTER_CONFIG  : dict — tells RepCounter how to count reps
check_form()    : the form checking function called every frame
"""

from utils import lm, joint_angle, torso_angle, active_side as detect_side

# ─── Thresholds ───────────────────────────────────────────────────────────────

THRESHOLDS = {
    "torso_angle_max":        12.0,   # degrees from vertical — upright spine
    "shoulder_diff_max":       0.04,  # normalized y-diff — level shoulders
    "shoulder_elevation_max":  0.05,  # normalized y-rise — no shrugging
    "elbow_drift_max":         0.10,  # normalized x-drift — elbow stays put
    "wrist_deviation_max":    30.0,   # degrees — wrist stays neutral
    "elbow_start_min":        150.0,  # degrees — full extension before curl
    "elbow_lock_min":         175.0,  # degrees — hyperextension warning
}

# ─── Rep counter config ───────────────────────────────────────────────────────

COUNTER_CONFIG = {
    "start_threshold": 150.0,   # elbow angle ≥ 150° → arm is extended (start)
    "end_threshold":    60.0,   # elbow angle ≤ 60°  → arm is curled (top)
    "direction":       "down",  # angle decreases as arm curls up
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _check(label: str, passed: bool, value: float, message: str) -> dict:
    """Build a standardised check result dict."""
    return {
        "label":   label,
        "ok":      passed,
        "value":   round(value, 3),
        "message": "" if passed else message,
    }


# ─── Form checks ──────────────────────────────────────────────────────────────

def check_form(landmarks: list, baselines: dict) -> tuple:
    """
    Run all form checks for one frame of a bicep curl.

    Parameters
    ----------
    landmarks : list
        33 MediaPipe landmark objects.

    baselines : dict
        Mutable dict shared with Session. We write baseline values into
        it on the first frame (when it's empty) and read from it on
        subsequent frames to detect drift.

    Returns
    -------
    checks : list[dict]
        One dict per check: {label, ok, value, message}

    metric : float
        The value that drives the rep counter — elbow angle.

    active_side : str
        "LEFT" or "RIGHT"
    """

    side = detect_side(landmarks)
    prefix = side  # "LEFT" or "RIGHT"

    # Fetch the three key landmarks for the active arm
    shoulder = lm(landmarks, f"{prefix}_SHOULDER")
    elbow    = lm(landmarks, f"{prefix}_ELBOW")
    wrist    = lm(landmarks, f"{prefix}_WRIST")
    hip      = lm(landmarks, f"{prefix}_HIP")

    # ── Capture baselines on the first frame of each rep ──────────────
    if not baselines:
        baselines["elbow_x"]      = elbow.x
        baselines["shoulder_y"]   = shoulder.y
        baselines["torso_angle"]  = torso_angle(landmarks)

    # ── Compute values ────────────────────────────────────────────────
    elbow_angle   = joint_angle(shoulder, elbow, wrist)
    t_angle       = torso_angle(landmarks)

    torso_length  = abs(shoulder.y - hip.y) or 0.1
    elbow_drift   = abs(elbow.x - baselines["elbow_x"]) / torso_length
    shoulder_rise = baselines["shoulder_y"] - shoulder.y  # positive = shrugging

    ls = lm(landmarks, "LEFT_SHOULDER")
    rs = lm(landmarks, "RIGHT_SHOULDER")
    shoulder_diff = abs(ls.y - rs.y)

    # ── Run checks ────────────────────────────────────────────────────
    checks = [
        _check(
            "Upright torso",
            t_angle <= THRESHOLDS["torso_angle_max"],
            t_angle,
            "keep your back straight",
        ),
        _check(
            "Shoulders level",
            shoulder_diff <= THRESHOLDS["shoulder_diff_max"],
            shoulder_diff,
            "level your shoulders",
        ),
        _check(
            "Elbow stable",
            elbow_drift <= THRESHOLDS["elbow_drift_max"],
            elbow_drift,
            "elbow drifting",
        ),
        _check(
            "No shrugging",
            shoulder_rise <= THRESHOLDS["shoulder_elevation_max"],
            shoulder_rise,
            "keep your shoulder down",
        ),
        _check(
            "No hyperextension",
            elbow_angle < THRESHOLDS["elbow_lock_min"],
            elbow_angle,
            "soft bend at the bottom — don't lock out",
        ),
    ]

    return checks, elbow_angle, side
