"""
exercises/plank.py
------------------
Plank is a hold exercise — no reps, just sustained form over time.

IS_HOLD = True tells Session to use the hold timer instead of RepCounter.
The check_form() signature is identical to rep exercises so Session
doesn't need to know the difference.
"""

from utils import lm, joint_angle, torso_angle as _torso_angle

IS_HOLD = True  # Session checks for this flag

THRESHOLDS = {
    "torso_angle_max":   15.0,   # degrees — hips must not sag or pike
    "hip_sag_max":       10.0,   # degrees below horizontal
    "hip_pike_max":      10.0,   # degrees above horizontal
    "elbow_angle_min":   80.0,   # degrees — elbows roughly at 90°
    "elbow_angle_max":  100.0,
    "neck_alignment":    15.0,   # head not dropped or craned
}


def _check(label, passed, value, message):
    return {"label": label, "ok": passed, "value": round(value, 3), "message": "" if passed else message}


def check_form(landmarks: list, baselines: dict) -> tuple:
    """
    Checks plank form. Returns (checks, metric=0, active_side=None).
    metric is unused for hold exercises but kept for interface consistency.
    """
    ls  = lm(landmarks, "LEFT_SHOULDER")
    rs  = lm(landmarks, "RIGHT_SHOULDER")
    lh  = lm(landmarks, "LEFT_HIP")
    rh  = lm(landmarks, "RIGHT_HIP")
    la  = lm(landmarks, "LEFT_ANKLE")
    ra  = lm(landmarks, "RIGHT_ANKLE")
    le  = lm(landmarks, "LEFT_ELBOW")
    re  = lm(landmarks, "RIGHT_ELBOW")
    lw  = lm(landmarks, "LEFT_WRIST")
    rw  = lm(landmarks, "RIGHT_WRIST")

    torso_ang    = _torso_angle(landmarks)
    l_elbow_ang  = joint_angle(ls, le, lw)
    r_elbow_ang  = joint_angle(rs, re, rw)
    avg_elbow    = (l_elbow_ang + r_elbow_ang) / 2

    # Hip height relative to shoulder-ankle line
    hip_y        = (lh.y + rh.y) / 2
    shoulder_y   = (ls.y + rs.y) / 2
    ankle_y      = (la.y + ra.y) / 2
    # In normalised coords, y increases downward. A sagging hip is HIGHER y
    # than the shoulder-ankle line.
    expected_hip_y = (shoulder_y + ankle_y) / 2
    hip_deviation  = (hip_y - expected_hip_y) * 100  # scale for readability

    checks = [
        _check(
            "Back flat",
            abs(hip_deviation) <= THRESHOLDS["torso_angle_max"],
            abs(hip_deviation),
            "hips dropping" if hip_deviation > 0 else "hips too high",
        ),
        _check(
            "Elbow angle",
            THRESHOLDS["elbow_angle_min"] <= avg_elbow <= THRESHOLDS["elbow_angle_max"],
            avg_elbow,
            "adjust elbow position",
        ),
        _check(
            "Keep your core tight",
            abs(hip_deviation) <= 5.0,
            abs(hip_deviation),
            "keep your core tight",
        ),
    ]

    return checks, 0.0, None
