import cv2
import mediapipe as mp
from session import Session

# ─── Setup ───────────────────────────────────────────────────────────

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

from audio import audio
audio.start()

session = Session("squat")  # change this to test different exercises

cap = cv2.VideoCapture(0)

# ─── Main Loop ───────────────────────────────────────────────────────

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Flip for natural mirror view
    frame = cv2.flip(frame, 1)

    # Convert to RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    result = pose.process(rgb)

    if result.pose_landmarks:
        landmarks = result.pose_landmarks.landmark

        # 🔥 Run your logic
        output = session.process(landmarks)

        # ─── Display info on screen ─────────────────────────────

        cv2.putText(frame, f"Phase: {output['phase']}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

        cv2.putText(frame, f"Reps: {output['rep_count']}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

        cv2.putText(frame, f"Valid: {output['valid_reps']}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

        # Show first failing check
        for check in output["checks"]:
            if not check["ok"]:
                cv2.putText(frame, check["message"], (10, 130),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
                break

    cv2.imshow("Form Corrector Test", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
        break

# ─── Cleanup ─────────────────────────────────────────────────────────
audio.stop()
cap.release()
cv2.destroyAllWindows()