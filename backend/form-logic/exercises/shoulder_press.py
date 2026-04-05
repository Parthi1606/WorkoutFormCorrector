"""
exercises/shoulder_press.py
---------------------------
Form checks and rep counter config for the shoulder press.
Supports both Standing and Seated modes — detected once at session start
and locked for the rep sequence.

Exports
-------
THRESHOLDS     : dict  — all tunable values
COUNTER_CONFIG : dict  — tells RepCounter how to count reps
check_form()   : called every frame by Session.process()
"""

from utils import lm, joint_angle, torso_angle

# ─── Thresholds ───────────────────────────────────────────────────────────────
THRESHOLDS = {
    # Torso
    "torso_angle_max":         15.0,   # degrees — upright spine at start + during press
    "torso_lean_delta_max":    10.0,   # degrees — how much lean is allowed to increase during press

    # Elbow
    "elbow_start_max":         100.0,  # degrees — elbows at ~shoulder height at start
    "elbow_lockout_min":       155.0,  # degrees — functional overhead extension (forgiving)

    # Wrist path
    "wrist_drift_max":         0.08,   # normalized x-drift — vertical wrist path

    # Elbow tracking
    "elbow_drift_max":         0.07,   # normalized — no abrupt flare during press

    # Hip drive (standing)
    "hip_drive_max":           0.04,   # normalized y-displacement — no hip pop
    "knee_dip_delta_max":      10.0,   # degrees — allowed drop from starting knee angle

    # Trunk compensation (seated)
    "trunk_comp_delta_max":    12.0,   # degrees torso change — no leaning back
    "hip_lift_max":            0.03,   # normalized y-movement of hip on seat

    # Mode detection
    "knee_angle_standing_min": 150.0,  # degrees — knee nearly straight = standing
    "knee_angle_seated_max":   120.0,  # degrees — knee bent = seated

    # Stability (pre-press)
    "stability_threshold":     0.03,   # normalized displacement — body must be still
}

# ─── Rep counter config ───────────────────────────────────────────────────────
COUNTER_CONFIG = {
    "start_threshold": 90.0,    # elbow angle ≤ 90° → arms at shoulder height (start)
    "end_threshold":   155.0,   # elbow angle ≥ 155° → arms fully pressed overhead (top)
    "direction":       "up",    # angle INCREASES as arms press up
}

# ─── Mode detection ───────────────────────────────────────────────────────────
_locked_mode = None   # module-level lock — reset by Session between exercises

def detect_press_mode(landmarks: list) -> str:
    """
    Classify as 'STANDING' or 'SEATED' based on knee angle.
    Called once per session; result is locked in _locked_mode.
    """
    global _locked_mode
    if _locked_mode is not None:
        return _locked_mode

    left_hip   = lm(landmarks, "LEFT_HIP")
    left_knee  = lm(landmarks, "LEFT_KNEE")
    left_ankle = lm(landmarks, "LEFT_ANKLE")

    k_angle = joint_angle(left_hip, left_knee, left_ankle)

    if k_angle >= THRESHOLDS["knee_angle_standing_min"]:
        _locked_mode = "STANDING"
    elif k_angle <= THRESHOLDS["knee_angle_seated_max"]:
        _locked_mode = "SEATED"
    else:
        # Ambiguous — default to standing until it stabilises
        _locked_mode = "STANDING"

    return _locked_mode

def reset_mode():
    """Call this when a new session starts so mode re-detects cleanly."""
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

# ─── Form checks ──────────────────────────────────────────────────────────────
def check_form(landmarks: list, baselines: dict) -> tuple:
    """
    Run all form checks for one frame of a shoulder press.

    Parameters
    ----------
    landmarks : list
        33 MediaPipe landmark objects.
    baselines : dict
        Shared with Session; written on first frame, read after.

    Returns
    -------
    checks      : list[dict]
    metric      : float
    active_side : str
    """
    mode = detect_press_mode(landmarks)

    # ── Key landmarks ──────────────────────────────────────────────────────
    l_shoulder = lm(landmarks, "LEFT_SHOULDER")
    r_shoulder = lm(landmarks, "RIGHT_SHOULDER")
    l_elbow    = lm(landmarks, "LEFT_ELBOW")
    r_elbow    = lm(landmarks, "RIGHT_ELBOW")
    l_wrist    = lm(landmarks, "LEFT_WRIST")
    r_wrist    = lm(landmarks, "RIGHT_WRIST")
    l_hip      = lm(landmarks, "LEFT_HIP")
    r_hip      = lm(landmarks, "RIGHT_HIP")
    l_knee     = lm(landmarks, "LEFT_KNEE")
    r_knee     = lm(landmarks, "RIGHT_KNEE")
    l_ankle    = lm(landmarks, "LEFT_ANKLE")
    r_ankle    = lm(landmarks, "RIGHT_ANKLE")

    # ── Derived values ────────────────────────────────────────────────────
    l_elbow_angle = joint_angle(l_shoulder, l_elbow, l_wrist)
    r_elbow_angle = joint_angle(r_shoulder, r_elbow, r_wrist)
    elbow_angle   = (l_elbow_angle + r_elbow_angle) / 2.0

    t_angle   = torso_angle(landmarks)
    torso_len = abs(l_shoulder.y - l_hip.y) or 0.1

    wrist_x_avg = (l_wrist.x + r_wrist.x) / 2.0
    elbow_x_avg = (l_elbow.x + r_elbow.x) / 2.0

    l_knee_angle = joint_angle(l_hip, l_knee, l_ankle)
    r_knee_angle = joint_angle(r_hip, r_knee, r_ankle)
    knee_angle_now = (l_knee_angle + r_knee_angle) / 2.0

    # ── Capture baselines on first frame of each rep ──────────────────────
    if not baselines:
        baselines["torso_angle"] = t_angle
        baselines["wrist_x"] = wrist_x_avg
        baselines["elbow_x"] = elbow_x_avg
        baselines["hip_y"] = (l_hip.y + r_hip.y) / 2.0
        baselines["knee_angle"] = knee_angle_now

        # Track whether full lockout was reached at any point in this rep.
        # Session uses this to decide rep validity.
        baselines["hit_lockout"] = False

    # Mark lockout as achieved once the elbows reach the top threshold
    if elbow_angle >= THRESHOLDS["elbow_lockout_min"]:
        baselines["hit_lockout"] = True

    # ── Drift values ───────────────────────────────────────────────────────
    wrist_drift = abs(wrist_x_avg - baselines["wrist_x"]) / torso_len
    elbow_drift = abs(elbow_x_avg - baselines["elbow_x"]) / torso_len
    torso_delta = t_angle - baselines["torso_angle"]
    hip_y_now   = (l_hip.y + r_hip.y) / 2.0
    hip_y_delta = abs(hip_y_now - baselines["hip_y"]) / torso_len

    knee_ok = knee_angle_now >= (
        baselines["knee_angle"] - THRESHOLDS["knee_dip_delta_max"]
    )

    # ── Shared checks ──────────────────────────────────────────────────────
    # Full overhead extension is NOT a live check here.
    # It is enforced later through rep_valid in session.py.
    checks = [
        _check(
            "Upright torso",
            t_angle <= THRESHOLDS["torso_angle_max"],
            t_angle,
            "keep your torso upright",
        ),
        _check(
            "No backward lean",
            torso_delta <= THRESHOLDS["torso_lean_delta_max"],
            torso_delta,
            "don't lean back during the press",
        ),
        _check(
            "Vertical wrist path",
            wrist_drift <= THRESHOLDS["wrist_drift_max"],
            wrist_drift,
            "press the weight straight up",
        ),
        _check(
            "Elbows tracking",
            elbow_drift <= THRESHOLDS["elbow_drift_max"],
            elbow_drift,
            "keep your elbows steady — don't flare",
        ),
    ]

    # ── Mode-specific checks ───────────────────────────────────────────────
    if mode == "STANDING":
        checks += [
            _check(
                "No hip drive",
                hip_y_delta <= THRESHOLDS["hip_drive_max"],
                hip_y_delta,
                "press with your shoulders — no hip pop",
            ),
            _check(
                "Knees stable",
                knee_ok,
                knee_angle_now,
                "keep your knees steady",
            ),
        ]
    else:  # SEATED
        checks += [
            _check(
                "No trunk lean",
                torso_delta <= THRESHOLDS["trunk_comp_delta_max"],
                torso_delta,
                "sit tall — don't lean back",
            ),
            _check(
                "Hips on seat",
                hip_y_delta <= THRESHOLDS["hip_lift_max"],
                hip_y_delta,
                "keep your hips on the seat",
            ),
        ]

    return checks, elbow_angle, "BOTH"