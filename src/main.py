"""
Main Application - Complete Workout Form Correction Tool
Supports: Bicep Curl, Squat, Plank, Lunge, Push-up, Shoulder Press
"""

import cv2
import mediapipe as mp
import sys
import os

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bicep_curl import BicepCurlDetector
from squat import SquatDetector
from plank import PlankDetector
from lunge import LungeDetector
from pushup import PushupDetector
from shoulder_press import ShoulderPressDetector
from pose_utils import draw_skeleton, draw_feedback
from audio_feedback import AudioFeedback

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Define skeleton connections
POSE_CONNECTIONS = mp_pose.POSE_CONNECTIONS

# Initialize Audio Feedback
audio = AudioFeedback()

# Initialize all detectors with audio
detectors = {
    "1": {
        "name": "Bicep Curl",
        "detector": BicepCurlDetector(audio_feedback=audio),
        "has_switch": True,
        "switch_type": "arm"
    },
    "2": {
        "name": "Squat",
        "detector": SquatDetector(audio_feedback=audio),
        "has_switch": True,
        "switch_type": "side"
    },
    "3": {
        "name": "Plank",
        "detector": PlankDetector(audio_feedback=audio),
        "has_switch": False,
        "switch_type": None
    },
    "4": {
        "name": "Lunge",
        "detector": LungeDetector(audio_feedback=audio),
        "has_switch": True,
        "switch_type": "leg"
    },
    "5": {
        "name": "Push-up",
        "detector": PushupDetector(audio_feedback=audio),
        "has_switch": False,
        "switch_type": None
    },
    "6": {
        "name": "Shoulder Press",
        "detector": ShoulderPressDetector(audio_feedback=audio),
        "has_switch": True,
        "switch_type": "arm"
    }
}

def show_menu():
    print("\n" + "="*60)
    print("WORKOUT FORM CORRECTION TOOL - COMPLETE EDITION")
    print("="*60)
    print("Select Exercise:")
    print("1. 💪 Bicep Curl")
    print("2. 🏋️ Squat")
    print("3. 🧘 Plank")
    print("4. 🦵 Lunge")
    print("5. 📈 Push-up")
    print("6. 🔼 Shoulder Press")
    print("q. Quit")
    print("="*60)
    return input("Enter choice (1-6 or q): ")

def main():
    # Get exercise choice
    choice = show_menu()
    
    if choice == 'q':
        print("Exiting...")
        return
    
    if choice not in detectors:
        print("Invalid choice. Please run again.")
        return
    
    # Get selected exercise
    exercise = detectors[choice]
    detector = exercise["detector"]
    exercise_name = exercise["name"]
    has_switch = exercise["has_switch"]
    switch_type = exercise["switch_type"]
    
    # Announce exercise start
    audio.exercise_start(exercise_name.lower().replace(" ", "_"))
    
    print(f"\nStarting {exercise_name}...")
    print("Instructions:")
    print("- Press 'q' to quit")
    print("- Press 'r' to reset")
    if has_switch:
        print(f"- Press 'a' to switch {switch_type}")
    print("- Stand 5-6 feet from camera")
    print("- Make sure full body is visible")
    
    if exercise_name in ["Bicep Curl", "Shoulder Press"]:
        print("- Face sideways to camera")
    elif exercise_name in ["Squat", "Lunge", "Push-up"]:
        print("- Face sideways to camera")
    else:
        print("- Face camera straight on")
    
    print("\nStarting in 3 seconds...")

    for i in range(3, 0, -1):
        print(f"{i}...")
        cv2.waitKey(1000)
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    print("\nCamera opened! Press 'q' to quit")
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Track session data
    session_start = cv2.getTickCount()
    session_reps = 0
    session_form_quality_sum = 0
    session_frames = 0
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        
        # Flip frame horizontally for mirror view
        frame = cv2.flip(frame, 1)
        
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)
        
        # Draw status bar
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (0, 0, 0), -1)
        cv2.putText(frame, f"Exercise: {exercise_name} (Audio Active)", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Audio icon
        cv2.putText(frame, "🔊", (frame.shape[1] - 40, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Process based on selected exercise
        if results.pose_landmarks:
            # Draw skeleton
            frame = draw_skeleton(frame, results.pose_landmarks, POSE_CONNECTIONS, (0, 255, 0), 2)
            
            # Process form detection
            frame, feedback = detector.process_frame(
                frame, results.pose_landmarks, frame.shape
            )
            
            # Draw feedback
            draw_feedback(frame, feedback, position=(10, 150))
            
            # Update session stats
            session_frames += 1
            
            # Get current reps from detector
            current_reps = getattr(detector, 'rep_count', 0)
            if current_reps > session_reps:
                session_reps = current_reps
            
            # Track form quality from feedback
            for msg in feedback:
                if "form_quality" in msg:
                    # Extract form quality if available
                    pass
            
            # Show tracking info
            if has_switch:
                if switch_type == "arm" and hasattr(detector, 'use_left_arm'):
                    side_text = "Left Arm" if detector.use_left_arm else "Right Arm"
                    cv2.putText(frame, f"Tracking: {side_text}", (10, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                elif switch_type == "side" and hasattr(detector, 'use_left_side'):
                    side_text = "Left Side" if detector.use_left_side else "Right Side"
                    cv2.putText(frame, f"Tracking: {side_text}", (10, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                elif switch_type == "leg" and hasattr(detector, 'use_left_leg'):
                    side_text = "Left Leg" if detector.use_left_leg else "Right Leg"
                    cv2.putText(frame, f"Tracking: {side_text}", (10, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        else:
            cv2.putText(frame, "No pose detected", (10, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, "Make sure full body is visible", (10, 130),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Draw instructions at bottom
        cv2.rectangle(frame, (0, frame.shape[0]-60), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
        instructions = "q: Quit | r: Reset"
        if has_switch:
            instructions += f" | a: Switch {switch_type.title()}"
        cv2.putText(frame, instructions, 
                    (10, frame.shape[0] - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Show frame
        cv2.imshow('Workout Form Corrector', frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("\nQuitting...")
            break
        elif key == ord('r'):
            detector.reset()
            session_reps = 0
            session_frames = 0
            session_form_quality_sum = 0
            audio.reset()
            print("Counter reset")
        elif key == ord('a') and has_switch:
            if switch_type == "arm" and hasattr(detector, 'switch_arm'):
                side = detector.switch_arm()
                print(f"Switched to {side}")
                audio.speak(f"Switched to {side}")
            elif switch_type == "side" and hasattr(detector, 'switch_side'):
                side = detector.switch_side()
                print(f"Switched to {side}")
                audio.speak(f"Switched to {side}")
            elif switch_type == "leg" and hasattr(detector, 'switch_leg'):
                side = detector.switch_leg()
                print(f"Switched to {side}")
                audio.speak(f"Switched to {side}")
    
    # Calculate session summary
    session_duration = (cv2.getTickCount() - session_start) / cv2.getTickFrequency()
    avg_form_quality = 75  # Placeholder - you can calculate from form quality data
    
    # Announce workout summary
    audio.workout_summary(exercise_name.lower().replace(" ", "_"), 
                          session_reps, avg_form_quality, int(session_duration))
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    pose.close()
    
    print(f"\n{'='*50}")
    print("WORKOUT SUMMARY")
    print(f"{'='*50}")
    print(f"Exercise: {exercise_name}")
    print(f"Total Reps: {session_reps}")
    print(f"Duration: {int(session_duration//60)}m {int(session_duration%60)}s")
    print(f"Avg Form Quality: {avg_form_quality:.0f}%")
    print(f"{'='*50}")
    print("\nApplication closed. Thank you for using Workout Form Corrector!")

if __name__ == "__main__":
    main()