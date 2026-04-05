"""
exercises/bent_over_row.py
--------------------------
Form checks and rep counter config for the dumbbell bent-over row.
Single arm, side view. Active arm detected via elbow z-value (same
pattern as bicep curl).

The rep metric is the elbow angle:
  - starts near full extension (~160°+)
  - pulls to ~60–80° at the top (wrist near hip/lower rib)
  - returns to full extension to complete the rep

Exports
-------
THRESHOLDS     : dict  — all tunable values
COUNTER_CONFIG : dict  — tells RepCounter how to count reps
check_form()   : called every frame by Session.process()
"""

from utils import lm, joint_angle, torso_angle, midpoint, xy, active_side as detect_side

# ─── Thresholds ───────────────────────────────────────────────────────────────
THRESHOLDS = {
    # Torso / hinge
    "torso_hinge_min":          30.0,   # degrees — must be hinged forward enough
    "torso_hinge_max":          55.0,   # degrees — not collapsed too far forward
    "torso_delta_max":          12.0,   # degrees — torso must stay still during pull
    "torso_swing_max":           0.05,  # normalised hip displacement — no swinging

    # Spine integrity (shoulder–hip smoothness proxy)
    "spine_deviation_max":       0.06,  # normalised — no sudden curvature in torso line

    # Knee flexion
    "knee_angle_min":          145.0,   # degrees — not locked out
    "knee_angle_max":          175.0,   # degrees — not squatting

    # Elbow / arm
    "elbow_start_min":         160.0,   # degrees — full extension before pull
    "elbow_top_max":            80.0,   # degrees — sufficient pull at top
    "elbow_return_min":        155.0,   # degrees — full extension on return (forgiving)

    # Elbow path: backward dominant (not upward)
    "elbow_upward_ratio_max":    0.5,   # elbow dy / elbow dx — upward travel limit

    # Elbow flare (lateral deviation from torso)
    "elbow_flare_max":           0.08,  # normalised distance from torso line

    # Wrist endpoint (waist/lower rib region)
    "wrist_too_high_max":        0.10,  # normalised — wrist should not rise above hip
    "wrist_too_low_min":         0.35,  # normalised y from shoulder — not incomplete

    # Shoulder shrug
    "shoulder_elevation_max":    0.05,  # normalised y-rise from baseline

    # Velocity / control
    "pull_velocity_max":         0.07,  # normalised — no explosive yank
    "descent_velocity_max":      0.07,  # normalised — no dropping

    # Stability (pre-rep)
    "stability_threshold":       0.03,  # normalised displacement — body still at start
}

# ─── Rep counter config ───────────────────────────────────────────────────────
# Elbow angle drives the rep:
#   Extended → ~160°+  (start_threshold)
#   Pulled   → ~60–80° (end_threshold)
#   Direction → "down" (angle decreases as arm pulls up)
COUNTER_CONFIG = {
    "start_threshold": 150.0,   # elbow ≥ 150° → arm extended (rep can begin / end)
    "end_threshold":    80.0,   # elbow ≤ 80°  → sufficient pull reached
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
_prev_elbow_x  = None
_prev_elbow_y  = None
_prev_wrist_y  = None
_prev_hip_x    = None

def _reset_velocity_tracker():
    global _prev_elbow_x, _prev_elbow_y, _prev_wrist_y, _prev_hip_x
    _prev_elbow_x = None
    _prev_elbow_y = None
    _prev_wrist_y = None
    _prev_hip_x   = None

# ─── Form checks ──────────────────────────────────────────────────────────────
def check_form(landmarks: list, baselines: dict) -> tuple:
    """
    Run all form checks for one frame of a dumbbell bent-over row (side view).

    Parameters
    ----------
    landmarks : list      33 MediaPipe landmark objects.
    baselines : dict      Shared with Session; written on first frame, read after.

    Returns
    -------
    checks      : list[dict]   One dict per check: {label, ok, value, message}
    metric      : float        Elbow angle — drives the rep counter.
    active_side : str          "LEFT" or "RIGHT".
    """
    global _prev_elbow_x, _prev_elbow_y, _prev_wrist_y, _prev_hip_x

    side   = detect_side(landmarks)
    prefix = side

    # ── Key landmarks ─────────────────────────────────────────────────────
    shoulder = lm(landmarks, f"{prefix}_SHOULDER")
    elbow    = lm(landmarks, f"{prefix}_ELBOW")
    wrist    = lm(landmarks, f"{prefix}_WRIST")
    hip      = lm(landmarks, f"{prefix}_HIP")
    knee     = lm(landmarks, f"{prefix}_KNEE")
    ankle    = lm(landmarks, f"{prefix}_ANKLE")

    opp      = "RIGHT" if side == "LEFT" else "LEFT"
    opp_shoulder = lm(landmarks, f"{opp}_SHOULDER")
    opp_hip      = lm(landmarks, f"{opp}_HIP")

    # ── Computed values ───────────────────────────────────────────────────
    elbow_angle  = joint_angle(shoulder, elbow, wrist)
    knee_angle   = joint_angle(hip, knee, ankle)
    t_angle      = torso_angle(landmarks)
    torso_len    = abs(shoulder.y - hip.y) or 0.1

    # Torso stability: change from baseline
    torso_delta  = abs(t_angle - baselines.get("torso_angle", t_angle))

    # Hip swing: horizontal displacement from baseline
    hip_x_delta  = abs(hip.x - baselines.get("hip_x", hip.x)) / torso_len

    # Shoulder elevation: y-rise from baseline (smaller y = higher in image)
    shoulder_rise = baselines.get("shoulder_y", shoulder.y) - shoulder.y

    # Elbow flare: horizontal distance of elbow from the shoulder–hip line
    # Project elbow onto the shoulder→hip vector and measure perpendicular offset
    import numpy as np
    sh = xy(shoulder)
    hi = xy(hip)
    el = xy(elbow)
    torso_vec  = hi - sh
    torso_norm = np.linalg.norm(torso_vec)
    if torso_norm > 0:
        t_hat = torso_vec / torso_norm
        proj  = sh + np.dot(el - sh, t_hat) * t_hat
        elbow_flare = np.linalg.norm(el - proj) / torso_len
    else:
        elbow_flare = 0.0

    # Elbow path: ratio of upward travel to backward travel (pull phase)
    if _prev_elbow_x is not None:
        d_elbow_x = abs(elbow.x - _prev_elbow_x)           # backward travel
        d_elbow_y = max(0.0, _prev_elbow_y - elbow.y)      # upward travel (y decreases upward)
        pull_velocity   = d_elbow_x / torso_len
        elbow_up_ratio  = d_elbow_y / (d_elbow_x + 1e-6)   # avoid div/0
        wrist_drop_vel  = max(0.0, wrist.y - (_prev_wrist_y or wrist.y)) / torso_len
    else:
        pull_velocity   = 0.0
        elbow_up_ratio  = 0.0
        wrist_drop_vel  = 0.0

    _prev_elbow_x = elbow.x
    _prev_elbow_y = elbow.y
    _prev_wrist_y = wrist.y
    _prev_hip_x   = hip.x

    # Wrist endpoint: check relative to hip y (should stay near hip/lower rib)
    wrist_above_hip = (hip.y - wrist.y) / torso_len    # positive = wrist above hip

    # Spine proxy: check if shoulder–hip angle deviates sharply
    # (a rounded back will show an abrupt angle break vs a flat line)
    mid_torso_x = (shoulder.x + hip.x) / 2.0
    mid_torso_y = (shoulder.y + hip.y) / 2.0
    opp_sh_xy   = xy(opp_shoulder)
    opp_hi_xy   = xy(opp_hip)
    spine_mid   = (opp_sh_xy + opp_hi_xy) / 2.0
    spine_dev   = abs(mid_torso_y - spine_mid[1]) / torso_len

    # ── Capture baselines on first frame ──────────────────────────────────
    if not baselines:
        baselines["torso_angle"]  = t_angle
        baselines["shoulder_y"]   = shoulder.y
        baselines["hip_x"]        = hip.x
        baselines["elbow_x"]      = elbow.x

    # ── Checks ────────────────────────────────────────────────────────────
    checks = [

        # ── Section 1: Start / hinge position ────────────────────────────
        _check(
            "Hip hinge position",
            THRESHOLDS["torso_hinge_min"] <= t_angle <= THRESHOLDS["torso_hinge_max"],
            t_angle,
            "hinge further forward from your hips"
            if t_angle < THRESHOLDS["torso_hinge_min"]
            else "you're bent too far — lift your chest slightly",
        ),
        _check(
            "Flat back",
            spine_dev <= THRESHOLDS["spine_deviation_max"],
            spine_dev,
            "keep your back flat — avoid rounding",
        ),
        _check(
            "Knee flexion",
            THRESHOLDS["knee_angle_min"] <= knee_angle <= THRESHOLDS["knee_angle_max"],
            knee_angle,
            "soften your knees slightly"
            if knee_angle > THRESHOLDS["knee_angle_max"]
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
            "Elbow close to body",
            elbow_flare <= THRESHOLDS["elbow_flare_max"],
            elbow_flare,
            "keep your elbow tucked close to your side",
        ),
        _check(
            "Controlled pull",
            pull_velocity <= THRESHOLDS["pull_velocity_max"],
            pull_velocity,
            "pull with control — no yanking",
        ),
        _check(
            "Torso stable",
            torso_delta <= THRESHOLDS["torso_delta_max"],
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
            "Pull reaches waist",
            wrist_above_hip <= THRESHOLDS["wrist_too_high_max"],
            wrist_above_hip,
            "don't pull past your hip — squeeze at the top",
        ),

        # ── Section 4: Lowering ───────────────────────────────────────────
        _check(
            "Controlled descent",
            wrist_drop_vel <= THRESHOLDS["descent_velocity_max"],
            wrist_drop_vel,
            "lower the weight slowly — don't drop it",
        ),
    ]

    return checks, elbow_angle, side
