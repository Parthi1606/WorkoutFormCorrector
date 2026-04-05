'''
"""
exercises/lunge.py
------------------
Form checks and rep counter config for the forward lunge (SIDE VIEW).

The user stands sideways to the camera, so only one side is reliably
visible. The rep metric is the FRONT (leading) knee angle:
  - starts near full extension (~155–175°) at standing
  - descends to ~80–100° at the bottom of the lunge
  - returns to full extension to complete the rep

Exports
-------
THRESHOLDS     : dict  — all tunable values
COUNTER_CONFIG : dict  — tells RepCounter how to count reps
check_form()   : called every frame by Session.process()
reset()        : call between sets / sessions to clear module state
"""

import numpy as np
from utils import lm, joint_angle, torso_angle, midpoint, xy, active_side as detect_side

# ─── Phase constants ───────────────────────────────────────────────────────────
# Used internally to gate checks to the phase where they are meaningful.
PHASE_STANDING = "standing"   # knee angle ≥ start_threshold
PHASE_DESCENT  = "descent"    # knee angle falling, not yet at bottom
PHASE_BOTTOM   = "bottom"     # knee angle ≤ end_threshold
PHASE_ASCENT   = "ascent"     # knee angle rising back toward standing


# ─── Thresholds ───────────────────────────────────────────────────────────────
THRESHOLDS = {
    # Torso uprightness (degrees from vertical)
    # In side view, torso_angle() should return lean in the sagittal plane.
    "torso_angle_max":          35.0,   # max forward lean at any phase
    "torso_delta_max":          20.0,   # max change from standing baseline (collapse)

    # Knee angles (degrees)
    "knee_start_min":          155.0,   # front knee considered "standing" above this
    "knee_depth_min":           80.0,   # front knee must reach at least this angle at bottom
    "knee_depth_max":          100.0,   # front knee should not exceed this at bottom
                                        # (<80° = too deep, >100° = not deep enough)

    # Front knee forward travel (ratio relative to torso length)
    # Positive = knee ahead of ankle in direction of lunge.
    # In side view the sign is consistent: front is always toward the lunge direction.
    "knee_forward_max":         0.10,   # knee should not travel more than 10% of torso length
                                        # past the ankle

    # Step length (ratio relative to torso length)
    "step_length_min":          0.8,    # too short → knee overload
    "step_length_max":          2.2,    # too long  → instability / balance loss

    # Foot stability after landing (ratio relative to torso length)
    "foot_shift_max":           0.05,   # front foot should not slide after planting

    # Hip drive direction during ascent (ratio relative to torso length)
    # Positive = hips shifted backward compared to standing baseline.
    "hip_backward_shift_max":   0.06,   # no pushing off back leg

    # Velocity / control (normalised units/frame)
    "step_velocity_max":        0.08,   # controlled step-out
    "ascent_velocity_max":      0.07,   # controlled rise
    "bottom_velocity_max":      0.03,   # stable at bottom

    # Back knee height at bottom (image y-coord; y increases downward in MediaPipe)
    # A higher value means the knee is lower in the frame (closer to ground).
    "back_knee_ground_max":     0.65,   # back knee should reach this y at bottom

    # Phase-transition hysteresis (degrees)
    # Prevents flickering at phase boundaries.
    "phase_hysteresis":          5.0,
}

# ─── Rep counter config ───────────────────────────────────────────────────────
# Front knee angle drives the rep counter:
#   Standing  → angle ≥ 155° (start_threshold)
#   Bottom    → angle ≤  95° (end_threshold)
#   Direction → "down" (angle decreases as user lunges forward)
COUNTER_CONFIG = {
    "start_threshold": 155.0,
    "end_threshold":    95.0,
    "direction":       "down",
}

# ─── Module-level state ───────────────────────────────────────────────────────
# All mutable state lives here so reset() can clear it cleanly.
_state = {
    "prev_ankle_x":   None,   # for step velocity
    "prev_knee_angle": None,  # for phase transition
    "phase":          PHASE_STANDING,
    "active_side":    None,   # track side changes
}

def reset():
    """Call between sets or sessions to clear all internal state."""
    _state["prev_ankle_x"]    = None
    _state["prev_knee_angle"] = None
    _state["phase"]           = PHASE_STANDING
    _state["active_side"]     = None

# ─── Phase detection ──────────────────────────────────────────────────────────
def _update_phase(knee_angle: float) -> str:
    """
    Update and return the current rep phase based on the front knee angle.
    Uses hysteresis to prevent flickering at boundaries.
    """
    hyst  = THRESHOLDS["phase_hysteresis"]
    start = COUNTER_CONFIG["start_threshold"]
    end   = COUNTER_CONFIG["end_threshold"]
    phase = _state["phase"]
    prev  = _state["prev_knee_angle"]

    if phase == PHASE_STANDING:
        if knee_angle < start - hyst:
            phase = PHASE_DESCENT
    elif phase == PHASE_DESCENT:
        if knee_angle <= end + hyst:
            phase = PHASE_BOTTOM
        elif knee_angle >= start - hyst:
            phase = PHASE_STANDING  # stepped back without going deep
    elif phase == PHASE_BOTTOM:
        if prev is not None and knee_angle > prev + hyst:
            phase = PHASE_ASCENT
    elif phase == PHASE_ASCENT:
        if knee_angle >= start - hyst:
            phase = PHASE_STANDING

    _state["phase"]           = phase
    _state["prev_knee_angle"] = knee_angle
    return phase

# ─── Helper ───────────────────────────────────────────────────────────────────
def _check(label: str, passed: bool, value: float, message: str,
           active: bool = True) -> dict:
    """
    Build a form-check result dict.

    Parameters
    ----------
    active : bool
        If False the check is not applicable in the current phase.
        It will be marked ok=True with no message so the UI can
        optionally grey it out rather than show a false failure.
    """
    return {
        "label":   label,
        "ok":      True if not active else passed,
        "value":   round(value, 3),
        "message": "" if (not active or passed) else message,
        "active":  active,
    }

# ─── Form checks ──────────────────────────────────────────────────────────────
def check_form(landmarks: list, baselines: dict) -> tuple:
    """
    Run all form checks for one frame of a forward lunge (side view).

    Side-view assumption
    --------------------
    The user faces left or right (perpendicular to the camera). MediaPipe
    still returns both-side landmarks but only the visible side is reliable.
    `active_side` (the leading / front leg) is determined by whichever knee
    is further from the camera (lower visibility score on the far side), which
    is what detect_side() already does.  All x-axis directions below are
    expressed in normalised image coordinates (0 = left edge, 1 = right edge).

    Parameters
    ----------
    landmarks : list      33 MediaPipe landmark objects.
    baselines : dict      Shared with Session; written on first valid frame.

    Returns
    -------
    checks      : list[dict]   One dict per check: {label, ok, value, message, active}
    metric      : float        Front knee angle — drives the rep counter.
    active_side : str          "LEFT" or "RIGHT" (leading leg).
    """
    # ── Side detection & state reset on side change ───────────────────────
    side = detect_side(landmarks)
    if _state["active_side"] is not None and _state["active_side"] != side:
        # User switched legs; old baselines are now invalid.
        baselines.clear()
        reset()
    _state["active_side"] = side

    back = "RIGHT" if side == "LEFT" else "LEFT"

    # ── Key landmarks ──────────────────────────────────────────────────────
    f_shoulder = lm(landmarks, f"{side}_SHOULDER")
    f_hip      = lm(landmarks, f"{side}_HIP")
    f_knee     = lm(landmarks, f"{side}_KNEE")
    f_ankle    = lm(landmarks, f"{side}_ANKLE")

    b_hip      = lm(landmarks, f"{back}_HIP")
    b_knee     = lm(landmarks, f"{back}_KNEE")
    b_ankle    = lm(landmarks, f"{back}_ANKLE")

    # ── Torso length — averaged over both sides for stability ──────────────
    # In side view one shoulder/hip may be partially occluded; averaging
    # makes the denominator more robust against single-landmark jitter.
    l_shoulder = lm(landmarks, "LEFT_SHOULDER")
    r_shoulder = lm(landmarks, "RIGHT_SHOULDER")
    l_hip      = lm(landmarks, "LEFT_HIP")
    r_hip      = lm(landmarks, "RIGHT_HIP")

    shoulder_y = (l_shoulder.y + r_shoulder.y) / 2.0
    hip_y      = (l_hip.y      + r_hip.y)      / 2.0
    torso_len  = abs(hip_y - shoulder_y) or 0.1

    # ── Computed values ────────────────────────────────────────────────────
    front_knee_angle = joint_angle(f_hip, f_knee, f_ankle)
    back_knee_angle  = joint_angle(b_hip, b_knee, b_ankle)
    t_angle          = torso_angle(landmarks)

    # Step length: horizontal distance between front and back ankle,
    # normalised by torso length.
    step_len = abs(f_ankle.x - b_ankle.x) / torso_len

    # Front knee forward travel.
    # In side view the lunge direction is consistent (person faces one way),
    # so (f_knee.x - f_ankle.x) has the correct sign without needing abs().
    # If the person faces left their knee moves in -x; if right, in +x.
    # We use the signed value so the threshold catches the right direction.
    # Determine lunge direction from the step: front ankle is further in the
    # lunge direction than the back ankle.
    lunge_dir = np.sign(f_ankle.x - b_ankle.x)   # +1 right, -1 left
    knee_over_ankle = lunge_dir * (f_knee.x - f_ankle.x) / torso_len
    # Positive = knee ahead of (past) ankle in lunge direction.

    # Back knee height (y increases downward in MediaPipe image coords).
    back_knee_y = b_knee.y

    # Hip midpoint x for ascent push-direction check.
    hip_x_avg = (f_hip.x + b_hip.x) / 2.0

    # Step velocity: front ankle x-displacement frame-over-frame.
    if _state["prev_ankle_x"] is not None:
        step_velocity = abs(f_ankle.x - _state["prev_ankle_x"])
    else:
        step_velocity = 0.0
    _state["prev_ankle_x"] = f_ankle.x

    # Phase (must be updated before gating checks).
    phase = _update_phase(front_knee_angle)

    # ── Capture baselines on first frame ───────────────────────────────────
    # Use a sentinel key so this is triggered exactly once per session,
    # regardless of what else Session may have stored in baselines.
    if "lunge_initialized" not in baselines:
        baselines["lunge_initialized"] = True
        baselines["torso_angle"]       = t_angle
        baselines["ankle_x"]           = f_ankle.x
        baselines["hip_x"]             = hip_x_avg

    torso_delta  = abs(t_angle - baselines["torso_angle"])
    foot_shift   = abs(f_ankle.x - baselines["ankle_x"]) / torso_len

    # Hip backward shift: how far hips moved backward from standing baseline.
    # Positive = hips shifted backward (pushing off back leg during ascent).
    hip_backward = lunge_dir * (baselines["hip_x"] - hip_x_avg) / torso_len

    # ── Phase flags for check gating ──────────────────────────────────────
    is_standing = phase == PHASE_STANDING
    is_stepping = phase == PHASE_DESCENT                      # foot in the air / stepping out
    is_at_bottom = phase == PHASE_BOTTOM
    is_ascending = phase == PHASE_ASCENT
    in_lunge     = phase in (PHASE_DESCENT, PHASE_BOTTOM, PHASE_ASCENT)

    # ── Checks ────────────────────────────────────────────────────────────
    checks = [

        # ── Section 1: Torso — always active ─────────────────────────────
        _check(
            "Upright torso",
            t_angle <= THRESHOLDS["torso_angle_max"],
            t_angle,
            "keep your chest up — don't lean forward",
            active=True,
        ),
        _check(
            "No torso collapse",
            torso_delta <= THRESHOLDS["torso_delta_max"],
            torso_delta,
            "your torso dropped forward — brace your core",
            active=in_lunge,   # only meaningful once the lunge has started
        ),

        # ── Section 2: Step — active during descent only ──────────────────
        _check(
            "Controlled step",
            step_velocity <= THRESHOLDS["step_velocity_max"],
            step_velocity,
            "step forward with control — don't stomp",
            active=is_stepping,
        ),
        _check(
            "Step length",
            THRESHOLDS["step_length_min"] <= step_len <= THRESHOLDS["step_length_max"],
            step_len,
            "step is too short — take a longer stride"
            if step_len < THRESHOLDS["step_length_min"]
            else "step is too wide — bring it in",
            active=in_lunge,
        ),
        _check(
            "Front foot stable",
            foot_shift <= THRESHOLDS["foot_shift_max"],
            foot_shift,
            "keep your front foot planted — don't let it slide",
            active=in_lunge,
        ),

        # ── Section 3 + 4: Descent / bottom ──────────────────────────────
        _check(
            "Front knee alignment",
            knee_over_ankle <= THRESHOLDS["knee_forward_max"],
            knee_over_ankle,
            "front knee is travelling too far past your ankle",
            active=in_lunge,
        ),
        _check(
            "Lunge depth — deep enough",
            front_knee_angle <= THRESHOLDS["knee_depth_max"],
            front_knee_angle,
            "lower deeper into the lunge",
            active=is_at_bottom,   # only flag at the bottom, not while standing
        ),
        _check(
            "Lunge depth — not too deep",
            front_knee_angle >= THRESHOLDS["knee_depth_min"],
            front_knee_angle,
            "you are going too deep — protect your knee",
            active=is_at_bottom,
        ),
        _check(
            "Back knee lowering",
            back_knee_y >= THRESHOLDS["back_knee_ground_max"],
            back_knee_y,
            "lower your back knee toward the ground",
            active=is_at_bottom,   # irrelevant when standing
        ),
        _check(
            "Stable at bottom",
            step_velocity <= THRESHOLDS["bottom_velocity_max"],
            step_velocity,
            "hold the bottom position — avoid bouncing",
            active=is_at_bottom,
        ),

        # ── Section 5: Ascent ─────────────────────────────────────────────
        _check(
            "Drive through front leg",
            hip_backward <= THRESHOLDS["hip_backward_shift_max"],
            hip_backward,
            "push through your front foot to stand — don't push off the back leg",
            active=is_ascending,
        ),
        _check(
            "Controlled ascent",
            step_velocity <= THRESHOLDS["ascent_velocity_max"],
            step_velocity,
            "rise with control — don't spring up",
            active=is_ascending,
        ),
    ]

    return checks, front_knee_angle, side


'''

"""
exercises/lunge.py
------------------
Form checks and rep counter config for the forward lunge (SIDE VIEW).

The user stands sideways to the camera, so only one side is reliably
visible. The rep metric is the FRONT (leading) knee angle:
  - starts near full extension (~155–175°) at standing
  - descends to ~80–100° at the bottom of the lunge
  - returns to full extension to complete the rep

Exports
-------
THRESHOLDS     : dict  — all tunable values
COUNTER_CONFIG : dict  — tells RepCounter how to count reps
check_form()   : called every frame by Session.process()
reset()        : call between sets / sessions to clear module state

Rep validity
------------
check_form() returns a fourth value: rep_valid (bool).
RepCounter should only increment when rep_valid is True at the moment
the rep completes (knee returns to start_threshold from below).
A rep is valid only if during descent/bottom both:
  - front_knee_angle dropped below THRESHOLDS["rep_valid_knee_max"] (120°)
  - back_knee_y      rose    above THRESHOLDS["back_knee_ground_max"] (0.65)
This prevents walks / shallow steps from being counted as reps.
"""
"""
exercises/lunge.py
------------------
Form checks and rep counter config for the forward lunge (SIDE VIEW).

The user stands sideways to the camera, so only one side is reliably
visible. The rep metric is the FRONT (leading) knee angle:
  - starts near full extension (~155–175°) at standing
  - descends to ~80–100° at the bottom of the lunge
  - returns to full extension to complete the rep

Exports
-------
THRESHOLDS     : dict  — all tunable values
COUNTER_CONFIG : dict  — tells RepCounter how to count reps
check_form()   : called every frame by Session.process()
reset()        : call between sets / sessions to clear module state

Rep validity
------------
check_form() returns a fourth value: rep_valid (bool).
RepCounter should only increment when rep_valid is True at the moment
the rep completes (knee returns to start_threshold from below).
A rep is valid only if during descent/bottom both:
  - front_knee_angle dropped below THRESHOLDS["rep_valid_knee_max"] (120°)
  - back_knee_y reached THRESHOLDS["back_knee_ground_max"] (0.65)
This prevents walks / shallow steps from being counted as reps.
"""

"""
exercises/lunge.py
------------------
Form checks and rep counter config for the forward lunge (SIDE VIEW).

The user stands sideways to the camera, so only one side is reliably
visible. The rep metric is the FRONT (leading) knee angle:
  - starts near full extension (~155–175°) at standing
  - descends to ~80–100° at the bottom of the lunge
  - returns to full extension to complete the rep

Exports
-------
THRESHOLDS     : dict  — all tunable values
COUNTER_CONFIG : dict  — tells RepCounter how to count reps
check_form()   : called every frame by Session.process()
reset()        : call between sets / sessions to clear module state

Rep validity
------------
check_form() returns a fourth value: rep_valid (bool).
RepCounter should only increment when rep_valid is True at the moment
the rep completes.

A rep is valid only if during the rep:
  1. the front knee went below THRESHOLDS["rep_valid_knee_max"]
  2. the back knee reached THRESHOLDS["back_knee_ground_max"]
  3. the front foot returned close to its original standing position

This prevents shallow steps, walks, and "down-up without step-back"
from being counted as valid reps.
"""

"""
exercises/lunge.py
------------------
Forward lunge logic for a SIDE-VIEW camera setup.

Movement model
--------------
A valid rep must follow this sequence:

1) standing_start  : user begins in a stable upright stance
2) step_out        : front foot steps forward
3) lowering        : body lowers into the lunge
4) bottom          : lunge bottom is reached with valid depth
5) rising          : user drives up through the front leg
6) step_back       : front foot returns close to the original standing position
7) standing_start  : stable finish

A rep is valid only if all required gates are satisfied in the same sequence.
"""
import numpy as np
from utils import lm, joint_angle, torso_angle, active_side as detect_side

# ─── Visibility threshold ─────────────────────────────────────────────────────
VIS_MIN = 0.50

# ─── Phases ───────────────────────────────────────────────────────────────────
PHASE_STANDING_START = "standing_start"
PHASE_STEP_OUT       = "step_out"
PHASE_LOWERING       = "lowering"
PHASE_BOTTOM         = "bottom"
PHASE_RISING         = "rising"
PHASE_STEP_BACK      = "step_back"

# ─── Thresholds ───────────────────────────────────────────────────────────────
THRESHOLDS = {
    # Torso
    "torso_angle_max":            35.0,
    "torso_delta_max":            20.0,

    # Front knee angle
    "knee_start_min":            155.0,
    "knee_lowering_start_max":   145.0,
    "knee_bottom_min":            80.0,
    "knee_bottom_max":           100.0,

    # Rep-valid depth gate
    "rep_valid_knee_max":        120.0,

    # Front knee vs toes
    "knee_forward_max":           0.20,

    # Back knee to ground
    "back_knee_ground_max":       0.65,

    # Step / return distances
    "step_out_min":               0.18,
    "return_to_start_max":        0.14,   # was 0.08 — loosened for beginners

    # Foot stability after landing
    "foot_shift_max":             0.10,
    "plant_velocity_max":         0.025,

    # Hip drive
    "hip_backward_shift_max":     0.06,

    # Velocity
    "step_velocity_max":          0.08,
    "rise_velocity_max":          0.07,
    "bottom_velocity_max":        0.03,

    # Hysteresis / stability
    "phase_hysteresis":            5.0,
    "standing_stability_frames":   3,
    "plant_stability_frames":      2,

    "foot_shift_grace_frames":     8,
    "return_grace_frames":         12,     # ~400ms buffer before "return to start" error fires
    "ankle_smoothing_alpha":       0.35,
    "rising_to_stepback_knee_min": 150.0,
}

# ─── Rep counter config ───────────────────────────────────────────────────────
COUNTER_CONFIG = {
    "start_threshold": 155.0,
    "end_threshold":    95.0,
    "direction":       "down",
}

# ─── Module state ─────────────────────────────────────────────────────────────
_state = {
    "phase": PHASE_STANDING_START,
    "active_side": None,

    # Previous-frame tracking
    "prev_front_ankle_x": None,
    "prev_front_ankle_y": None,
    "prev_knee_angle": None,

    # Stable standing start tracking
    "standing_stable_frames": 0,

    # Foot plant tracking
    "plant_stable_frames": 0,
    "front_foot_planted_x": None,

    # Start-of-rep anchors
    "start_front_ankle_x": None,
    "start_hip_x": None,
    "start_torso_angle": None,

    # Anchor captured at the moment of entering PHASE_STEP_BACK
    "step_back_anchor_x": None,

    # Rep gates
    "gate_step_out_passed": False,
    "gate_knee_passed": False,
    "gate_depth_passed": False,
    "gate_return_passed": False,
    "rep_valid": False,

    # Smoothed ankle tracking
    "smoothed_front_ankle_x": None,
    "smoothed_front_ankle_y": None,

    # Debounce counters
    "foot_shift_bad_frames": 0,
    "return_bad_frames": 0,
}

def reset():
    """Reset all module state between sessions/sets."""
    _state["phase"] = PHASE_STANDING_START
    _state["active_side"] = None

    _state["prev_front_ankle_x"] = None
    _state["prev_front_ankle_y"] = None
    _state["prev_knee_angle"] = None

    _state["standing_stable_frames"] = 0

    _state["plant_stable_frames"] = 0
    _state["front_foot_planted_x"] = None

    _state["start_front_ankle_x"] = None
    _state["start_hip_x"] = None
    _state["start_torso_angle"] = None

    _state["step_back_anchor_x"] = None  # NEW

    _state["gate_step_out_passed"] = False
    _state["gate_knee_passed"] = False
    _state["gate_depth_passed"] = False
    _state["gate_return_passed"] = False
    _state["rep_valid"] = False

    _state["smoothed_front_ankle_x"] = None
    _state["smoothed_front_ankle_y"] = None

    _state["foot_shift_bad_frames"] = 0
    _state["return_bad_frames"] = 0

def _vis(lm_obj) -> bool:
    return getattr(lm_obj, "visibility", 1.0) >= VIS_MIN

def _check(label: str, passed: bool, value: float, message: str, active: bool = True) -> dict:
    return {
        "label": label,
        "ok": True if not active else passed,
        "value": round(value, 3),
        "message": "" if (not active or passed) else message,
        "active": active,
    }

def _clear_rep_gates():
    _state["gate_step_out_passed"] = False
    _state["gate_knee_passed"] = False
    _state["gate_depth_passed"] = False
    _state["gate_return_passed"] = False
    _state["rep_valid"] = False
    _state["plant_stable_frames"] = 0
    _state["front_foot_planted_x"] = None
    _state["foot_shift_bad_frames"] = 0
    _state["return_bad_frames"] = 0
    _state["step_back_anchor_x"] = None  # NEW

def _can_capture_start(f_ankle_visible, f_hip_visible, t_angle, front_knee_angle, step_dist, step_vel) -> bool:
    if not (f_ankle_visible and f_hip_visible):
        return False
    if front_knee_angle < THRESHOLDS["knee_start_min"]:
        return False
    if abs(step_dist) > THRESHOLDS["return_to_start_max"]:
        return False
    if t_angle > THRESHOLDS["torso_angle_max"]:
        return False
    if step_vel > THRESHOLDS["plant_velocity_max"]:
        return False
    return True

def _update_phase(front_knee_angle, back_knee_y, step_dist, return_dist, step_vel, smooth_x):
    """
    Finite-state phase update.
    smooth_x is passed in so PHASE_RISING can anchor step_back_anchor_x
    at the exact moment of transition.
    """
    phase = _state["phase"]
    prev_knee = _state["prev_knee_angle"]
    hyst = THRESHOLDS["phase_hysteresis"]

    if phase == PHASE_STANDING_START:
        if _state["gate_return_passed"]:
            _clear_rep_gates()
            _state["gate_return_passed"] = False

        if step_dist >= THRESHOLDS["step_out_min"]:
            _state["gate_step_out_passed"] = True
            _state["phase"] = PHASE_STEP_OUT

    elif phase == PHASE_STEP_OUT:
        if front_knee_angle <= THRESHOLDS["knee_lowering_start_max"]:
            _state["phase"] = PHASE_LOWERING
        elif return_dist <= THRESHOLDS["return_to_start_max"] and step_dist < THRESHOLDS["step_out_min"]:
            _state["phase"] = PHASE_STANDING_START
            _clear_rep_gates()

    elif phase == PHASE_LOWERING:
        if front_knee_angle <= THRESHOLDS["rep_valid_knee_max"]:
            _state["gate_knee_passed"] = True
        if back_knee_y >= THRESHOLDS["back_knee_ground_max"]:
            _state["gate_depth_passed"] = True

        if front_knee_angle <= COUNTER_CONFIG["end_threshold"] + hyst:
            _state["phase"] = PHASE_BOTTOM

    elif phase == PHASE_BOTTOM:
        if front_knee_angle <= THRESHOLDS["rep_valid_knee_max"]:
            _state["gate_knee_passed"] = True
        if back_knee_y >= THRESHOLDS["back_knee_ground_max"]:
            _state["gate_depth_passed"] = True

        if prev_knee is not None and front_knee_angle > prev_knee + hyst:
            _state["phase"] = PHASE_RISING

    elif phase == PHASE_RISING:
        if (
            front_knee_angle >= THRESHOLDS["rising_to_stepback_knee_min"]
            and step_vel <= THRESHOLDS["rise_velocity_max"]
        ):
            _state["phase"] = PHASE_STEP_BACK
            # Anchor the foot position at the moment we start stepping back.
            # return_dist will measure from start_front_ankle_x (the pre-rep
            # standing position), so this anchor is used to detect intent to
            # return rather than as the distance reference itself.
            if smooth_x is not None:
                _state["step_back_anchor_x"] = smooth_x

    elif phase == PHASE_STEP_BACK:
        if return_dist <= THRESHOLDS["return_to_start_max"]:
            _state["gate_return_passed"] = True
        if return_dist <= THRESHOLDS["return_to_start_max"] and step_vel <= THRESHOLDS["plant_velocity_max"]:
            _state["phase"] = PHASE_STANDING_START

    _state["prev_knee_angle"] = front_knee_angle

def check_form(landmarks: list, baselines: dict) -> tuple:
    """
    Returns
    -------
    checks, metric, active_side, rep_valid
    """
    detected_side = detect_side(landmarks)

    # Allow side lock only when not inside an active rep sequence
    if _state["phase"] == PHASE_STANDING_START and _state["active_side"] is None:
        _state["active_side"] = detected_side

    side = _state["active_side"] or detected_side
    back = "RIGHT" if side == "LEFT" else "LEFT"

    # Key landmarks
    f_shoulder = lm(landmarks, f"{side}_SHOULDER")
    f_hip      = lm(landmarks, f"{side}_HIP")
    f_knee     = lm(landmarks, f"{side}_KNEE")
    f_ankle    = lm(landmarks, f"{side}_ANKLE")
    f_foot     = lm(landmarks, f"{side}_FOOT_INDEX")

    b_hip      = lm(landmarks, f"{back}_HIP")
    b_knee     = lm(landmarks, f"{back}_KNEE")
    b_ankle    = lm(landmarks, f"{back}_ANKLE")

    l_shoulder = lm(landmarks, "LEFT_SHOULDER")
    r_shoulder = lm(landmarks, "RIGHT_SHOULDER")
    l_hip      = lm(landmarks, "LEFT_HIP")
    r_hip      = lm(landmarks, "RIGHT_HIP")

    # Visibility
    f_ankle_visible = _vis(f_ankle)
    f_knee_visible  = _vis(f_knee)
    f_hip_visible   = _vis(f_hip)
    f_foot_visible  = _vis(f_foot)
    b_knee_visible  = _vis(b_knee)
    b_ankle_visible = _vis(b_ankle)

    # Torso length normalization
    shoulder_y = (l_shoulder.y + r_shoulder.y) / 2.0
    hip_y      = (l_hip.y + r_hip.y) / 2.0
    torso_len  = abs(hip_y - shoulder_y) or 0.1

    # Angles / values
    front_knee_angle = joint_angle(f_hip, f_knee, f_ankle)
    t_angle          = torso_angle(landmarks)
    back_knee_y      = b_knee.y if b_knee_visible else 0.0

    # Direction
    if f_ankle_visible and b_ankle_visible:
        lunge_dir = np.sign(f_ankle.x - b_ankle.x)
    else:
        lunge_dir = np.sign(f_hip.x - b_hip.x)
    if lunge_dir == 0:
        lunge_dir = 1.0

    # Knee vs toe
    knee_over_toe = (
        lunge_dir * (f_knee.x - f_foot.x) / torso_len
        if (f_knee_visible and f_foot_visible) else 0.0
    )

    hip_x_avg = (f_hip.x + b_hip.x) / 2.0

    # Smooth front ankle to reduce landmark jitter
    if f_ankle_visible:
        alpha = THRESHOLDS["ankle_smoothing_alpha"]

        if _state["smoothed_front_ankle_x"] is None:
            _state["smoothed_front_ankle_x"] = f_ankle.x
            _state["smoothed_front_ankle_y"] = f_ankle.y
        else:
            _state["smoothed_front_ankle_x"] = (
                alpha * f_ankle.x + (1 - alpha) * _state["smoothed_front_ankle_x"]
            )
            _state["smoothed_front_ankle_y"] = (
                alpha * f_ankle.y + (1 - alpha) * _state["smoothed_front_ankle_y"]
            )

        smooth_x = _state["smoothed_front_ankle_x"]
        smooth_y = _state["smoothed_front_ankle_y"]
    else:
        smooth_x = None
        smooth_y = None

    # Step velocity from smoothed ankle
    if (
        f_ankle_visible
        and smooth_x is not None
        and smooth_y is not None
        and _state["prev_front_ankle_x"] is not None
        and _state["prev_front_ankle_y"] is not None
    ):
        dx = smooth_x - _state["prev_front_ankle_x"]
        dy = smooth_y - _state["prev_front_ankle_y"]
        step_vel = float(np.sqrt(dx * dx + dy * dy))
    else:
        step_vel = 0.0

    if f_ankle_visible and smooth_x is not None and smooth_y is not None:
        _state["prev_front_ankle_x"] = smooth_x
        _state["prev_front_ankle_y"] = smooth_y

    # Capture a real standing-start baseline before rep logic begins
    if _state["start_front_ankle_x"] is None:
        if _can_capture_start(
            f_ankle_visible=f_ankle_visible,
            f_hip_visible=f_hip_visible,
            t_angle=t_angle,
            front_knee_angle=front_knee_angle,
            step_dist=0.0,
            step_vel=step_vel,
        ):
            _state["standing_stable_frames"] += 1
        else:
            _state["standing_stable_frames"] = 0

        if _state["standing_stable_frames"] >= THRESHOLDS["standing_stability_frames"]:
            _state["start_front_ankle_x"] = smooth_x
            _state["start_hip_x"] = hip_x_avg
            _state["start_torso_angle"] = t_angle
        else:
            waiting = [_check("Waiting for stable standing start", True, 0.0, "", active=False)]
            return waiting, front_knee_angle, side, False

    step_dist = (
        abs(smooth_x - _state["start_front_ankle_x"]) / torso_len
        if f_ankle_visible and smooth_x is not None and _state["start_front_ankle_x"] is not None else 0.0
    )

    # return_dist: during STEP_BACK measure how close the foot has returned to
    # the original standing position. Outside STEP_BACK, mirror step_dist so
    # the STEP_OUT abort logic continues to work unchanged.
    if (
        _state["phase"] == PHASE_STEP_BACK
        and _state["step_back_anchor_x"] is not None
        and f_ankle_visible
        and smooth_x is not None
        and _state["start_front_ankle_x"] is not None
    ):
        return_dist = abs(smooth_x - _state["start_front_ankle_x"]) / torso_len
    else:
        return_dist = step_dist

    # Phase update — pass smooth_x so the transition to STEP_BACK can anchor
    _update_phase(front_knee_angle, back_knee_y, step_dist, return_dist, step_vel, smooth_x)
    phase = _state["phase"]

    is_standing  = phase == PHASE_STANDING_START
    is_step_out  = phase == PHASE_STEP_OUT
    is_lowering  = phase == PHASE_LOWERING
    is_bottom    = phase == PHASE_BOTTOM
    is_rising    = phase == PHASE_RISING
    is_step_back = phase == PHASE_STEP_BACK

    in_loaded_lunge = phase in (PHASE_LOWERING, PHASE_BOTTOM, PHASE_RISING, PHASE_STEP_BACK)

    # Plant detection only after step-out, not during initial step movement
    if phase in (PHASE_LOWERING, PHASE_BOTTOM, PHASE_RISING):
        if step_vel <= THRESHOLDS["plant_velocity_max"] and f_ankle_visible:
            _state["plant_stable_frames"] += 1
        else:
            _state["plant_stable_frames"] = 0

        if (
            _state["front_foot_planted_x"] is None
            and _state["plant_stable_frames"] >= THRESHOLDS["plant_stability_frames"]
            and f_ankle_visible
            and smooth_x is not None
        ):
            _state["front_foot_planted_x"] = smooth_x
    else:
        _state["plant_stable_frames"] = 0

    if is_standing:
        _state["front_foot_planted_x"] = None

    torso_delta = abs(t_angle - _state["start_torso_angle"]) if _state["start_torso_angle"] is not None else 0.0

    foot_shift = (
        abs(smooth_x - _state["front_foot_planted_x"]) / torso_len
        if (f_ankle_visible and smooth_x is not None and _state["front_foot_planted_x"] is not None) else 0.0
    )

    hip_backward = (
        lunge_dir * (_state["start_hip_x"] - hip_x_avg) / torso_len
        if _state["start_hip_x"] is not None else 0.0
    )

    # Final rep validity: full sequence gates
    _state["rep_valid"] = (
        _state["gate_step_out_passed"]
        and _state["gate_knee_passed"]
        and _state["gate_depth_passed"]
        and _state["gate_return_passed"]
    )

    # Debounce planted-foot glitching
    if (is_bottom or is_rising) and _state["front_foot_planted_x"] is not None:
        if foot_shift > THRESHOLDS["foot_shift_max"]:
            _state["foot_shift_bad_frames"] += 1
        else:
            _state["foot_shift_bad_frames"] = 0
    else:
        _state["foot_shift_bad_frames"] = 0

    foot_shift_ok = (
        _state["foot_shift_bad_frames"] < THRESHOLDS["foot_shift_grace_frames"]
    )

    # Debounce return-to-start error
    if is_step_back:
        if return_dist > THRESHOLDS["return_to_start_max"]:
            _state["return_bad_frames"] += 1
        else:
            _state["return_bad_frames"] = 0
    else:
        _state["return_bad_frames"] = 0

    return_to_start_ok = (
        _state["return_bad_frames"] < THRESHOLDS["return_grace_frames"]
    )

    checks = [
        _check(
            "Upright torso",
            t_angle <= THRESHOLDS["torso_angle_max"],
            t_angle,
            "keep your chest up — don't lean forward",
            active=True,
        ),
        _check(
            "No torso collapse",
            torso_delta <= THRESHOLDS["torso_delta_max"],
            torso_delta,
            "your torso dropped forward — brace your core",
            active=in_loaded_lunge,
        ),
        _check(
            "Controlled step",
            step_vel <= THRESHOLDS["step_velocity_max"],
            step_vel,
            "step forward with control — don't stomp",
            active=is_step_out,
        ),
        _check(
            "Front foot stable",
            foot_shift_ok,
            foot_shift,
            "keep your front foot planted — don't let it slide",
            active=(is_bottom or is_rising) and f_ankle_visible and _state["front_foot_planted_x"] is not None,
        ),
        _check(
            "Front knee alignment",
            knee_over_toe <= THRESHOLDS["knee_forward_max"],
            knee_over_toe,
            "front knee is travelling too far past your toes",
            active=phase in (PHASE_LOWERING, PHASE_BOTTOM, PHASE_RISING) and f_knee_visible and f_foot_visible,
        ),
        _check(
            "Lunge depth — deep enough",
            front_knee_angle <= THRESHOLDS["knee_bottom_max"],
            front_knee_angle,
            "lower deeper into the lunge",
            active=is_bottom,
        ),
        _check(
            "Lunge depth — not too deep",
            front_knee_angle >= THRESHOLDS["knee_bottom_min"],
            front_knee_angle,
            "you are going too deep — protect your knee",
            active=is_bottom,
        ),
        _check(
            "Back knee lowering",
            back_knee_y >= THRESHOLDS["back_knee_ground_max"],
            back_knee_y,
            "lower your back knee toward the ground",
            active=is_bottom and b_knee_visible,
        ),
        _check(
            "Stable at bottom",
            step_vel <= THRESHOLDS["bottom_velocity_max"],
            step_vel,
            "hold the bottom position — avoid bouncing",
            active=is_bottom and f_ankle_visible,
        ),
        _check(
            "Drive through front leg",
            hip_backward <= THRESHOLDS["hip_backward_shift_max"],
            hip_backward,
            "push through your front foot to stand — don't push off the back leg",
            active=is_rising,
        ),
        _check(
            "Controlled rise",
            step_vel <= THRESHOLDS["rise_velocity_max"],
            step_vel,
            "rise with control — don't spring up",
            active=is_rising and f_ankle_visible,
        ),
    ]

    # After a fully completed rep and stable standing, unlock side
    # and clear start anchors so the next rep captures a fresh baseline
    if is_standing and _state["gate_return_passed"]:
        _state["active_side"] = None
        _state["start_front_ankle_x"] = None
        _state["start_hip_x"] = None
        _state["start_torso_angle"] = None
        _state["standing_stable_frames"] = 0

    return checks, front_knee_angle, side, _state["rep_valid"]