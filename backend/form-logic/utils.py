"""
utils.py
--------
Pure geometry helpers. No exercise logic, no MediaPipe imports beyond
the landmark enum. Every other file in the project imports from here.
"""

import math
import numpy as np
import mediapipe as mp

_PL = mp.solutions.pose.PoseLandmark


# ─── Landmark access ─────────────────────────────────────────────────────────

def lm(landmarks: list, name: str):
    """
    Fetch a single landmark by name.

    Usage:
        shoulder = lm(landmarks, "LEFT_SHOULDER")
        print(shoulder.x, shoulder.y, shoulder.z)

    landmarks is the raw list from MediaPipe (33 items).
    name is any PoseLandmark enum name, e.g. "LEFT_HIP".
    """
    return landmarks[_PL[name].value]


def xy(landmark) -> np.ndarray:
    """
    Return a landmark's (x, y) as a numpy array.
    Useful for 2-D vector math (most form checks only need x and y).

    Usage:
        v = xy(lm(landmarks, "LEFT_SHOULDER"))
    """
    return np.array([landmark.x, landmark.y])


def midpoint(a, b) -> np.ndarray:
    """
    Return the (x, y) midpoint between two landmarks.

    Usage:
        hip_center = midpoint(
            lm(landmarks, "LEFT_HIP"),
            lm(landmarks, "RIGHT_HIP")
        )
    """
    return (xy(a) + xy(b)) / 2


# ─── Angle calculation ────────────────────────────────────────────────────────

def angle_between_vectors(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Angle in degrees between two 2-D vectors.
    Returns 0.0 if either vector has zero magnitude (safe for degenerate poses).

    This is the building block for joint angle calculations.
    """
    mag1, mag2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if mag1 == 0 or mag2 == 0:
        return 0.0
    # Clamp dot product to [-1, 1] to avoid floating-point errors in acos
    cos_theta = np.clip(np.dot(v1, v2) / (mag1 * mag2), -1.0, 1.0)
    return math.degrees(math.acos(cos_theta))


def joint_angle(a, b, c) -> float:
    """
    Angle at joint B, formed by the points A-B-C.

    This is the most common operation in form checking:
        - Elbow angle:  joint_angle(shoulder, elbow, wrist)
        - Knee angle:   joint_angle(hip, knee, ankle)
        - Hip angle:    joint_angle(shoulder, hip, knee)

    Each argument is a raw landmark object (has .x and .y attributes).
    Returns degrees in range [0, 180].
    """
    # Vector from B toward A, and from B toward C
    v_ba = xy(a) - xy(b)
    v_bc = xy(c) - xy(b)
    return angle_between_vectors(v_ba, v_bc)


def torso_angle(landmarks: list) -> float:
    """
    Angle between the torso (hip midpoint → shoulder midpoint) and the
    vertical axis. 0° means perfectly upright. 90° means horizontal.

    Used by: squat, lunge, bicep curl, bent-over row, plank.
    """
    ls = lm(landmarks, "LEFT_SHOULDER")
    rs = lm(landmarks, "RIGHT_SHOULDER")
    lh = lm(landmarks, "LEFT_HIP")
    rh = lm(landmarks, "RIGHT_HIP")

    shoulder_mid = midpoint(ls, rs)
    hip_mid      = midpoint(lh, rh)

    torso_vec    = shoulder_mid - hip_mid          # points upward when standing
    vertical_vec = np.array([0.0, -1.0])           # upward in image coords
    return angle_between_vectors(torso_vec, vertical_vec)


def active_side(landmarks: list) -> str:
    """
    Detect which side (LEFT or RIGHT) is closer to the camera using the
    elbow z-value. Smaller z = closer to camera in MediaPipe's convention.

    Used for unilateral exercises: bicep curl, lunge, bent-over row.
    """
    left_z  = lm(landmarks, "LEFT_ELBOW").z
    right_z = lm(landmarks, "RIGHT_ELBOW").z
    return "LEFT" if left_z < right_z else "RIGHT"
