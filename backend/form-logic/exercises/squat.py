from utils import lm, joint_angle, torso_angle, midpoint
import numpy as np

# ─── Notes ────────────────────────────────────────────────────────────────────
#
#   User faces SIDEWAYS to the camera.
#   This means:
#     - We rely on ONE visible side (left or right) for most checks
#     - Knee cave / valgus checks are NOT possible (lateral view)
#     - Knee-over-toe, torso lean, depth are all highly reliable from this angle
#     - We auto-detect which side is facing the camera (visible side)
#
# ─────────────────────────────────────────────────────────────────────────────


# ─── Thresholds ──────────────────────────────────────────────────────────────

THRESHOLDS = {
    # Standing
    "knee_hyperextend_min":    178.0,   # above this = locked knees

    # Descent
    "torso_descent_max":       55.0,    # max torso lean during descent
    "torso_bottom_max":        65.0,    # more lean allowed at the very bottom
    "knee_forward_max":        0.10,    # knee x past ankle x (normalized) — tighter from side view
    "heel_lift_max":           0.015,   # ankle y movement = heel lift (stricter from side)
    "hip_drop_max":            0.12,    # max hip drop per frame (speed of descent)

    # Depth
    "hip_depth_max":           125.0,   # hip angle at or below = at depth
    "near_bottom_knee":        115.0,   # knee angle below this = near bottom, check depth

    # Ascent
    "hip_rise_max":            0.12,    # max hip rise per frame (speed of ascent)
    "hip_shoulder_sync_max":   0.06,    # hips and shoulders should rise together

    # Bounce
    "bounce_velocity_max":     0.05,    # sudden upward hip movement at bottom

    # Finish
    "torso_finish_max":        15.0,    # must be upright when standing
    "hip_return_tolerance":    0.04,    # how close hip_y must be to start to count as "standing"

    # Side detection
    "side_visibility_min":     0.6,     # landmark visibility threshold
}

# ─── Rep Counter Config ───────────────────────────────────────────────────────

COUNTER_CONFIG = {
    "start_threshold": 170.0,   # knee angle = standing
    "end_threshold":    95.0,   # knee angle = at bottom
    "direction":       "down",
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _check(label, passed, value, message, priority=1):
    """
    priority: 1 = high (safety/form), 2 = medium, 3 = low (polish)
    Lower number = shown first to beginner.
    """
    return {
        "label":    label,
        "ok":       passed,
        "value":    round(float(value), 3),
        "message":  "" if passed else message,
        "priority": priority,
    }


def _detect_side(landmarks):
    """
    Returns 'LEFT' or 'RIGHT' — whichever side is more visible to the camera.
    When user stands sideways, one side faces the camera and has higher visibility scores.
    """
    l_vis = (
        lm(landmarks, "LEFT_HIP").visibility +
        lm(landmarks, "LEFT_KNEE").visibility +
        lm(landmarks, "LEFT_ANKLE").visibility
    )
    r_vis = (
        lm(landmarks, "RIGHT_HIP").visibility +
        lm(landmarks, "RIGHT_KNEE").visibility +
        lm(landmarks, "RIGHT_ANKLE").visibility
    )
    return "LEFT" if l_vis >= r_vis else "RIGHT"


def _knee_angle(landmarks, side):
    hip   = lm(landmarks, f"{side}_HIP")
    knee  = lm(landmarks, f"{side}_KNEE")
    ankle = lm(landmarks, f"{side}_ANKLE")
    return joint_angle(hip, knee, ankle)


def _hip_angle(landmarks, side):
    shoulder = lm(landmarks, f"{side}_SHOULDER")
    hip      = lm(landmarks, f"{side}_HIP")
    knee     = lm(landmarks, f"{side}_KNEE")
    return joint_angle(shoulder, hip, knee)


# ─── Phase Tracker ───────────────────────────────────────────────────────────

def _get_phase(knee_angle, prev_phase):
    """
    Derive squat phase from knee angle and previous phase.
    Phases: standing → descending → bottom → ascending → standing
    """
    if knee_angle >= COUNTER_CONFIG["start_threshold"]:
        return "standing"
    elif knee_angle <= COUNTER_CONFIG["end_threshold"]:
        return "bottom"
    elif prev_phase in ("standing", "descending"):
        return "descending"
    else:
        return "ascending"


# ─── Main Logic ──────────────────────────────────────────────────────────────

def check_form(landmarks, baselines):

    # ── Detect which side faces camera ───────────────────────────────
    side = _detect_side(landmarks)
    opp  = "RIGHT" if side == "LEFT" else "LEFT"

    # ── Key landmarks (visible/facing side) ──────────────────────────
    shoulder = lm(landmarks, f"{side}_SHOULDER")
    hip      = lm(landmarks, f"{side}_HIP")
    knee     = lm(landmarks, f"{side}_KNEE")
    ankle    = lm(landmarks, f"{side}_ANKLE")

    # ── Core angles ──────────────────────────────────────────────────
    knee_ang = _knee_angle(landmarks, side)
    hip_ang  = _hip_angle(landmarks, side)
    t_angle  = torso_angle(landmarks)

    # ── Phase ────────────────────────────────────────────────────────
    prev_phase = baselines.get("phase", "standing")
    phase      = _get_phase(knee_ang, prev_phase)

    # ── Initialise baselines on first frame ──────────────────────────
    if "hip_y_start" not in baselines:
        baselines["hip_y_start"]      = hip.y
        baselines["hip_y_prev"]       = hip.y
        baselines["ankle_y_prev"]     = ankle.y
        baselines["shoulder_y_prev"]  = shoulder.y
        baselines["at_depth"]         = False
        baselines["phase"]            = "standing"

    # ── Per-frame deltas ─────────────────────────────────────────────
    hip_y_delta      = hip.y       - baselines["hip_y_prev"]        # +ve = moving down
    ankle_y_delta    = abs(ankle.y - baselines["ankle_y_prev"])     # any ankle movement
    shoulder_y_delta = abs(shoulder.y - baselines["shoulder_y_prev"])

    # ── Depth tracking ───────────────────────────────────────────────
    at_depth = hip_ang <= THRESHOLDS["hip_depth_max"]
    if at_depth:
        baselines["at_depth"] = True

    # Reset at_depth latch when fully standing again — fixes bounce bug
    if phase == "standing" and baselines.get("at_depth"):
        baselines["at_depth"] = False

    near_bottom = knee_ang <= THRESHOLDS["near_bottom_knee"]

    # ── Knee-over-toe (reliable from side view) ───────────────────────
    # Positive = knee x is ahead of ankle x (too far forward)
    knee_forward = knee.x - ankle.x
    # Note: if user faces LEFT, knee moving right = forward. Vice versa.
    # Flip sign for right-facing user so positive always means "too far forward"
    if side == "RIGHT":
        knee_forward = ankle.x - knee.x

    # ── Sync check (hips and shoulders rise together on ascent) ──────
    hip_vel       = abs(hip_y_delta)
    shoulder_vel  = shoulder_y_delta
    sync_diff     = abs(hip_vel - shoulder_vel)

    # ── Bounce detection ─────────────────────────────────────────────
    # Bounce = sudden upward snap from bottom before completing the rep
    bounce = (
        baselines["at_depth"]
        and hip_y_delta < -THRESHOLDS["bounce_velocity_max"]  # sudden upward
        and knee_ang > COUNTER_CONFIG["end_threshold"] + 10   # not fully at bottom
    )

    # ── Has the user returned to standing? ───────────────────────────
    hip_returned = abs(hip.y - baselines["hip_y_start"]) <= THRESHOLDS["hip_return_tolerance"]

    # ── Update baselines ─────────────────────────────────────────────
    baselines["hip_y_prev"]      = hip.y
    baselines["ankle_y_prev"]    = ankle.y
    baselines["shoulder_y_prev"] = shoulder.y
    baselines["phase"]           = phase

    # ─── Checks ───────────────────────────────────────────────────────
    #
    #   Checks are phase-aware:
    #     - Some only make sense during descent, some only at bottom, etc.
    #     - When a check is not relevant for the current phase, it passes silently.
    #   Priority 1 = most important for beginners (shown first)
    #
    # ─────────────────────────────────────────────────────────────────

    checks = [

        # ── Always active ────────────────────────────────────────────

        _check("Knees soft",
               knee_ang < THRESHOLDS["knee_hyperextend_min"],
               knee_ang,
               "don't lock your knees",
               priority=1),

        _check("Heels grounded",
               ankle_y_delta <= THRESHOLDS["heel_lift_max"],
               ankle_y_delta,
               "keep your heels on the ground",
               priority=1),

        # ── Descent + bottom ────────────────────────────────────────

        _check("Chest up",
               phase not in ("descending", "bottom") or t_angle <= THRESHOLDS["torso_descent_max"],
               t_angle,
               "keep your chest up, don't lean forward",
               priority=1),

        _check("Knee position",
               phase not in ("descending", "bottom") or knee_forward <= THRESHOLDS["knee_forward_max"],
               knee_forward,
               "knees too far forward — push hips back more",
               priority=1),

        _check("Controlled descent",
               phase != "descending" or hip_y_delta <= THRESHOLDS["hip_drop_max"],
               hip_y_delta,
               "slow down — control your descent",
               priority=2),

        # ── Bottom only ──────────────────────────────────────────────

        _check("Depth",
               not near_bottom or at_depth,
               hip_ang,
               "squat a little deeper — aim for thighs parallel to floor",
               priority=2),

        _check("No bounce",
               not bounce,
               hip_y_delta,
               "don't bounce at the bottom — pause briefly",
               priority=1),

        # ── Ascent only ──────────────────────────────────────────────

        _check("Chest up on way up",
               phase != "ascending" or t_angle <= THRESHOLDS["torso_descent_max"],
               t_angle,
               "chest is dropping — drive through your heels and keep chest up",
               priority=1),

        _check("Hips and shoulders together",
               phase != "ascending" or sync_diff <= THRESHOLDS["hip_shoulder_sync_max"],
               sync_diff,
               "hips rising faster than shoulders — don't good-morning the squat",
               priority=2),

        _check("Controlled ascent",
               phase != "ascending" or abs(hip_y_delta) <= THRESHOLDS["hip_rise_max"],
               abs(hip_y_delta),
               "slow down — control your ascent",
               priority=3),

        # ── Finish ───────────────────────────────────────────────────

        # Only fires when the person has actually returned to standing
        _check("Stand fully upright",
               not hip_returned or t_angle <= THRESHOLDS["torso_finish_max"],
               t_angle,
               "stand up straight at the top",
               priority=2),

    ]

    # Sort by priority so the most important failing check surfaces first
    checks.sort(key=lambda c: (c["ok"], c["priority"]))

    return checks, knee_ang, side