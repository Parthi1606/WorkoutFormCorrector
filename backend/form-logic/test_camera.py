"""
RepRight - Exercise Module Tester
Combines pose skeleton drawing (from src/test_working.py)
with full session/form logic (from form-logic/test_camera.py)
"""

import cv2
import mediapipe as mp

# ─── Version Info ────────────────────────────────────────────────────
print("Starting RepRight Form Tester...")
print(f"MediaPipe version: {mp.__version__}")

# ─── Setup ───────────────────────────────────────────────────────────
mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils
pose = mp_pose.Pose()

from audio import audio
audio.start()

EXERCISE = "plank"  # ✏️ Change this to test: squat, bicep_curl, lunge, pushup, plank, shoulder_press, bent_over_row
from session import Session
session = Session(EXERCISE)

print(f"Testing exercise: {EXERCISE}")
print("Press ESC or Q to quit")

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Cannot open camera")
    exit()

print("✓ Camera opened")

# ─── Main Loop ───────────────────────────────────────────────────────
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Flip for natural mirror view
    frame = cv2.flip(frame, 1)

    # Convert to RGB for MediaPipe
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = pose.process(rgb)

    if result.pose_landmarks:
        # ── Draw skeleton on frame ──────────────────────────────
        mp_draw.draw_landmarks(
            frame,
            result.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )

        landmarks = result.pose_landmarks.landmark

        # ── Run exercise logic ──────────────────────────────────
        output = session.process(landmarks)

        # ── Display session info ────────────────────────────────
        cv2.putText(frame, f"Exercise: {EXERCISE}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        cv2.putText(frame, f"Phase: {output['phase']}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.putText(frame, f"Reps: {output['rep_count']}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.putText(frame, f"Valid: {output['valid_reps']}", (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # ── Show first failing form check ───────────────────────
        for check in output["checks"]:
            if not check["ok"]:
                cv2.putText(frame, f"⚠ {check['message']}", (10, 160),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                break

    else:
        # No pose detected warning
        cv2.putText(frame, "NO POSE DETECTED - Stand in front of camera",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    cv2.imshow(f"RepRight Tester - {EXERCISE}", frame)

    # ESC or Q to quit
    key = cv2.waitKey(1) & 0xFF
    if key == 27 or key == ord('q'):
        break

# ─── Cleanup ─────────────────────────────────────────────────────────
print("Shutting down...")
audio.stop()
cap.release()
cv2.destroyAllWindows()
print("Done!")