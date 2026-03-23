"""
Squat Form Detector with Audio Feedback
"""

import cv2
import numpy as np
from pose_utils import calculate_angle, get_landmark_coords, draw_angle

# Landmark indices
LEFT_HIP = 23
LEFT_KNEE = 25
LEFT_ANKLE = 27
RIGHT_HIP = 24
RIGHT_KNEE = 26
RIGHT_ANKLE = 28
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12

# Thresholds
GOOD_SQUAT_DEPTH = 90
PARTIAL_SQUAT = 110
BACK_ANGLE_MIN = 70
BACK_ANGLE_MAX = 100
KNEE_VALGUS_THRESHOLD = 0.05

class SquatDetector:
    def __init__(self, audio_feedback=None):
        self.rep_count = 0
        self.is_squatting = False
        self.feedback = []
        self.use_left_side = True
        self.min_depth_achieved = False
        self.audio = audio_feedback
        
        # Track state for audio
        self.last_error = None
        self.was_good_form = True
        self.last_rep_count = 0
        
    def process_frame(self, frame, landmarks, frame_shape):
        self.feedback = []
        
        # Choose which side to track
        if self.use_left_side:
            hip_idx = LEFT_HIP
            knee_idx = LEFT_KNEE
            ankle_idx = LEFT_ANKLE
            shoulder_idx = LEFT_SHOULDER
        else:
            hip_idx = RIGHT_HIP
            knee_idx = RIGHT_KNEE
            ankle_idx = RIGHT_ANKLE
            shoulder_idx = RIGHT_SHOULDER
        
        # Get landmark coordinates
        hip = get_landmark_coords(landmarks, hip_idx, frame_shape)
        knee = get_landmark_coords(landmarks, knee_idx, frame_shape)
        ankle = get_landmark_coords(landmarks, ankle_idx, frame_shape)
        shoulder = get_landmark_coords(landmarks, shoulder_idx, frame_shape)
        
        # Get other knee for valgus detection
        if self.use_left_side:
            other_knee_idx = RIGHT_KNEE
        else:
            other_knee_idx = LEFT_KNEE
        other_knee = get_landmark_coords(landmarks, other_knee_idx, frame_shape)
        
        # Check if we have all landmarks
        if None in [hip, knee, ankle, shoulder]:
            self.feedback.append("⚠️ Cannot see full body")
            self.feedback.append("Stand sideways to camera")
            return frame, self.feedback
        
        # Calculate angles
        knee_angle = calculate_angle(hip, knee, ankle)
        back_angle = calculate_angle(shoulder, hip, knee)
        
        # Draw angles
        draw_angle(frame, knee, knee_angle, (0, 255, 0))
        cv2.putText(frame, f"Back: {int(back_angle)}°", 
                    (hip[0] + 10, hip[1] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        # REP COUNTER
        if knee_angle < PARTIAL_SQUAT and not self.is_squatting:
            self.is_squatting = True
            self.min_depth_achieved = False
        
        if self.is_squatting and knee_angle <= GOOD_SQUAT_DEPTH:
            self.min_depth_achieved = True
        
        if self.is_squatting and knee_angle > 160:
            self.rep_count += 1
            self.is_squatting = False
            if self.min_depth_achieved:
                self.feedback.append(f"✅ Good squat! Rep {self.rep_count}")
                if self.audio:
                    if self.rep_count % 5 == 0:
                        self.audio.speak(f"Great job! {self.rep_count} squats!")
                    else:
                        self.audio.speak("Good squat!")
            else:
                self.feedback.append(f"⚠️ Shallow squat! Rep {self.rep_count}")
                if self.audio:
                    self.audio.speak("Squat deeper next time")
        
        # FORM CHECKS
        has_error = False
        
        # Depth Check
        if knee_angle <= GOOD_SQUAT_DEPTH:
            self.feedback.append("✅ Good depth!")
        elif knee_angle <= PARTIAL_SQUAT:
            self.feedback.append("⬇️ Go deeper - aim for 90°")
            if self.audio and self.last_error != "depth":
                self.audio.speak("Go deeper, aim for thighs parallel to ground")
                self.last_error = "depth"
            has_error = True
        else:
            self.feedback.append("⚠️ Too shallow")
            has_error = True
        
        # Back Alignment
        if back_angle < BACK_ANGLE_MIN:
            self.feedback.append("⚠️ Too much forward lean")
            if self.audio and self.last_error != "forward_lean":
                self.audio.speak("Chest up, don't lean forward")
                self.last_error = "forward_lean"
            has_error = True
        elif back_angle > BACK_ANGLE_MAX:
            self.feedback.append("⚠️ Leaning back")
            has_error = True
        else:
            self.feedback.append("✓ Back straight")
        
        # Knee Tracking
        if other_knee is not None:
            if abs(knee[0] - other_knee[0]) < 50:
                self.feedback.append("⚠️ Knees caving in")
                if self.audio and self.last_error != "knees":
                    self.audio.speak("Push your knees outward")
                    self.last_error = "knees"
                has_error = True
            else:
                self.feedback.append("✓ Knee tracking good")
        
        # Heel Check
        knee_past_toes = knee[0] > ankle[0] + 20 if self.use_left_side else knee[0] < ankle[0] - 20
        if knee_past_toes:
            self.feedback.append("⚠️ Knees past toes")
            if self.audio and self.last_error != "toes":
                self.audio.speak("Sit back more, keep weight on heels")
                self.last_error = "toes"
            has_error = True
        else:
            self.feedback.append("✓ Weight on heels")
        
        # Reset error tracking if form is good
        if not has_error:
            self.last_error = None
            if not self.was_good_form and self.audio:
                self.audio.speak("Good form! Keep it up")
            self.was_good_form = True
        else:
            self.was_good_form = False
        
        # Add rep counter
        cv2.putText(frame, f"REPS: {self.rep_count}", 
                    (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        
        # Depth bar
        depth_percentage = min(100, int((180 - knee_angle) / 90 * 100))
        cv2.rectangle(frame, (10, frame.shape[0] - 60), 
                     (10 + depth_percentage * 2, frame.shape[0] - 40), 
                     (0, 255, 0), -1)
        cv2.putText(frame, f"Depth: {depth_percentage}%", (10, frame.shape[0] - 65),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame, self.feedback
    
    def reset(self):
        self.rep_count = 0
        self.is_squatting = False
        self.min_depth_achieved = False
        self.feedback = []
        self.last_error = None
    
    def switch_side(self):
        self.use_left_side = not self.use_left_side
        self.reset()
        return "Left side" if self.use_left_side else "Right side"