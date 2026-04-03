from utils import lm, joint_angle, torso_angle, midpoint
import numpy as np

# ─── Thresholds (FORGIVING VERSION) ──────────────────────────────────────────

THRESHOLDS = {
    "torso_start_max":         20.0,
    "hip_shoulder_offset_max": 0.12,
    "knee_hyperextend_min":    178.0,

    "torso_descent_max":       55.0,
    "knee_forward_max":        0.28,
    "heel_lift_max":           0.05,
    "hip_drop_max":            0.10,
    "knee_before_hip_max":     0.05,

    "hip_depth_max":           125.0,   # angle-based depth

    "torso_bottom_max":        60.0,
    "bounce_velocity_max":     0.06,

    "hip_shoulder_sync_max":   0.06,
    "hip_rise_max":            0.10,

    "torso_finish_max":        20.0,
    "hip_return_tolerance":    0.05,
}

# ─── Rep Counter ─────────────────────────────────────────────────────────────

COUNTER_CONFIG = {
    "start_threshold": 175.0,
    "end_threshold":    90.0,
    "direction":       "down",
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _check(label, passed, value, message):
    return {
        "label": label,
        "ok": passed,
        "value": round(value, 3),
        "message": "" if passed else message,
    }


def _knee_angle(landmarks, side):
    hip   = lm(landmarks, f"{side}_HIP")
    knee  = lm(landmarks, f"{side}_KNEE")
    ankle = lm(landmarks, f"{side}_ANKLE")
    return joint_angle(hip, knee, ankle)


def _avg_knee_angle(landmarks):
    return (_knee_angle(landmarks, "LEFT") + _knee_angle(landmarks, "RIGHT")) / 2


# ─── Main Logic ──────────────────────────────────────────────────────────────

def check_form(landmarks, baselines):

    # ── Landmarks ────────────────────────────────────────────────────
    ls = lm(landmarks, "LEFT_SHOULDER")
    rs = lm(landmarks, "RIGHT_SHOULDER")
    lh = lm(landmarks, "LEFT_HIP")
    rh = lm(landmarks, "RIGHT_HIP")
    lk = lm(landmarks, "LEFT_KNEE")
    rk = lm(landmarks, "RIGHT_KNEE")
    la = lm(landmarks, "LEFT_ANKLE")
    ra = lm(landmarks, "RIGHT_ANKLE")

    shoulder_mid = midpoint(ls, rs)
    hip_mid      = midpoint(lh, rh)
    knee_mid     = midpoint(lk, rk)
    ankle_mid    = midpoint(la, ra)

    # ── Baselines ─────────────────────────────────────────────
    if not baselines:
        baselines["hip_y_start"]  = hip_mid[1]
        baselines["hip_y_prev"]   = hip_mid[1]
        baselines["knee_x_prev"]  = knee_mid[0]
        baselines["ankle_y_prev"] = ankle_mid[1]
        baselines["at_depth"]     = False

    # ── Core Metrics ──────────────────────────────────────────
    t_angle  = torso_angle(landmarks)
    avg_knee = _avg_knee_angle(landmarks)

    # 🔥 Hip angle for depth
    hip_angle_l = joint_angle(ls, lh, lk)
    hip_angle_r = joint_angle(rs, rh, rk)
    hip_angle   = (hip_angle_l + hip_angle_r) / 2

    hip_at_depth = hip_angle <= THRESHOLDS["hip_depth_max"]

    # 🔥 NEW: Only check depth near bottom
    near_bottom = avg_knee <= 110  # tweak if needed

    # Default: don't complain about depth
    depth_ok = True
    if near_bottom:
        depth_ok = hip_at_depth

    # ── Other Metrics ─────────────────────────────────────────
    hip_shoulder_offset = abs(shoulder_mid[0] - hip_mid[0])
    knee_forward        = max(lk.x - la.x, rk.x - ra.x)

    hip_y_delta   = hip_mid[1] - baselines["hip_y_prev"]
    knee_x_delta  = abs(knee_mid[0] - baselines["knee_x_prev"])
    ankle_y_delta = abs(ankle_mid[1] - baselines["ankle_y_prev"])

    shoulder_y_prev = baselines.get("shoulder_y_prev", shoulder_mid[1])
    hip_vel        = abs(hip_y_delta)
    shoulder_vel   = abs(shoulder_mid[1] - shoulder_y_prev)
    sync_diff      = abs(hip_vel - shoulder_vel)

    # Bounce detection
    if hip_at_depth:
        baselines["at_depth"] = True

    bounce = (
        baselines["at_depth"]
        and hip_y_delta < -THRESHOLDS["bounce_velocity_max"]
        and avg_knee > COUNTER_CONFIG["end_threshold"] + 5
    )

    hip_returned = abs(hip_mid[1] - baselines["hip_y_start"]) <= THRESHOLDS["hip_return_tolerance"]

    # ── Update baselines ─────────────────────────────────────
    baselines["hip_y_prev"]      = hip_mid[1]
    baselines["knee_x_prev"]     = knee_mid[0]
    baselines["ankle_y_prev"]    = ankle_mid[1]
    baselines["shoulder_y_prev"] = shoulder_mid[1]

    # ── Checks ────────────────────────────────────────────────
    checks = [

        _check("Torso control",
               t_angle <= THRESHOLDS["torso_descent_max"],
               t_angle,
               "keep your chest up"),

        _check("Torso alignment",
               hip_shoulder_offset <= THRESHOLDS["hip_shoulder_offset_max"],
               hip_shoulder_offset,
               "don't lean too far forward"),

        _check("Knees soft",
               avg_knee < THRESHOLDS["knee_hyperextend_min"],
               avg_knee,
               "don't lock your knees"),

        _check("Controlled descent",
               hip_y_delta <= THRESHOLDS["hip_drop_max"],
               hip_y_delta,
               "control your descent"),

        _check("Hip initiation",
               knee_x_delta <= THRESHOLDS["knee_before_hip_max"],
               knee_x_delta,
               "start by pushing hips back"),

        _check("Knee position",
               knee_forward <= THRESHOLDS["knee_forward_max"],
               knee_forward,
               "knees too far forward"),

        _check("Heels grounded",
               ankle_y_delta <= THRESHOLDS["heel_lift_max"],
               ankle_y_delta,
               "keep your heels down"),

        # 🔥 FIXED DEPTH CHECK
        _check("Depth",
               depth_ok,
               hip_angle,
               "squat deeper"),

        _check("No bounce",
               not bounce,
               hip_y_delta,
               "don't bounce at bottom"),

        _check("Smooth ascent",
               abs(hip_y_delta) <= THRESHOLDS["hip_rise_max"] or hip_y_delta >= 0,
               hip_y_delta,
               "control your ascent"),

        _check("Full stand",
               t_angle <= THRESHOLDS["torso_finish_max"] or not hip_returned,
               t_angle,
               "stand fully upright"),
    ]

    return checks, avg_knee, "BOTH"