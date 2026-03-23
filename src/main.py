"""
Main Application - Workout Form Correction Tool with Audio Feedback
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

# Initialize detectors with audio
bicep_detector = BicepCurlDetector(audio_feedback=audio)
squat_detector = SquatDetector(audio_feedback=audio)
plank_detector = PlankDetector(audio_feedback=audio)

def show_menu():
    print("\n" + "="*50)
    print("WORKOUT FORM CORRECTION TOOL")
    print("="*50)
    print("Select Exercise:")
    print("1. Bicep Curl")
    print("2. Squat")
    print("3. Plank")
    print("q. Quit")
    print("="*50)
    return input("Enter choice (1-3 or q): ")

def main():
    # Get exercise choice
    choice = show_menu()
    
    if choice == 'q':
        print("Exiting...")
        return
    
    if choice not in ['1', '2', '3']:
        print("Invalid choice. Please run again.")
        return
    
    # Set exercise name and detector
    if choice == "1":
        exercise_name = "Bicep Curl"
        detector = bicep_detector
        has_arm_switch = True
    elif choice == "2":
        exercise_name = "Squat"
        detector = squat_detector
        has_arm_switch = False
    else:
        exercise_name = "Plank"
        detector = plank_detector
        has_arm_switch = False
    
    # Announce exercise start
    audio.exercise_start(exercise_name)
    
    print(f"\nStarting {exercise_name}...")
    print("Instructions:")
    print("- Press 'q' to quit")
    print("- Press 'r' to reset")
    if has_arm_switch:
        print("- Press 'a' to switch arms/sides")
    print("- Stand 5-6 feet from camera")
    print("- Make sure full body is visible")
    print("\nStarting in 3 seconds...")
    
    # Countdown
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
    
    # For frame rate calculation
    frame_count = 0
    start_time = cv2.getTickCount()
    
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
            
            # Show tracking info
            if choice == "1" and hasattr(detector, 'use_left_arm'):
                arm_text = "Left Arm" if detector.use_left_arm else "Right Arm"
                cv2.putText(frame, f"Tracking: {arm_text}", (10, 70), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            elif choice == "2" and hasattr(detector, 'use_left_side'):
                side_text = "Left Side" if detector.use_left_side else "Right Side"
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
        if has_arm_switch:
            instructions += " | a: Switch Side"
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
            audio.reset()
            print("Counter reset")
        elif key == ord('a') and has_arm_switch:
            if choice == "1":
                arm = detector.switch_arm()
                print(f"Switched to {arm}")
                audio.speak(f"Switched to {arm}")
            elif choice == "2":
                side = detector.switch_side()
                print(f"Switched to {side}")
                audio.speak(f"Switched to {side}")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    pose.close()
    
    # Final summary
    if choice == "3" and hasattr(detector, 'get_total_time'):
        total_time = detector.get_total_time()
        if total_time > 0:
            print(f"\nTotal plank hold time: {int(total_time)} seconds")
            audio.speak(f"Great workout! You held the plank for {int(total_time)} seconds")
    
    print("\nApplication closed. Thank you for using Workout Form Corrector!")

if __name__ == "__main__":
    main()