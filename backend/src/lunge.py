"""
Lunge Form Detector with Audio Feedback
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
GOOD_KNEE_ANGLE = 90          # Front knee should be at 90°
MIN_KNEE_ANGLE = 70           # Too deep
MAX_KNEE_ANGLE = 110          # Too shallow
BACK_KNEE_MIN_ANGLE = 150     # Back leg should be relatively straight
FORWARD_LEAN_MAX = 15         # Max forward lean in degrees

class LungeDetector:
    def __init__(self, audio_feedback=None):
        self.rep_count = 0
        self.is_lunging = False
        self.feedback = []
        self.use_left_leg = True  # Track left leg by default
        self.audio = audio_feedback
        
        # Track state for audio
        self.last_error = None
        self.was_good_form = True
        self.form_stable_count = 0
        
    def process_frame(self, frame, landmarks, frame_shape):
        """Process lunge frame and return feedback"""
        self.feedback = []
        
        # Choose which leg to track
        if self.use_left_leg:
            hip_idx = LEFT_HIP
            knee_idx = LEFT_KNEE
            ankle_idx = LEFT_ANKLE
            back_knee_idx = RIGHT_KNEE
            back_ankle_idx = RIGHT_ANKLE
        else:
            hip_idx = RIGHT_HIP
            knee_idx = RIGHT_KNEE
            ankle_idx = RIGHT_ANKLE
            back_knee_idx = LEFT_KNEE
            back_ankle_idx = LEFT_ANKLE
        
        # Get landmark coordinates
        hip = get_landmark_coords(landmarks, hip_idx, frame_shape)
        knee = get_landmark_coords(landmarks, knee_idx, frame_shape)
        ankle = get_landmark_coords(landmarks, ankle_idx, frame_shape)
        back_knee = get_landmark_coords(landmarks, back_knee_idx, frame_shape)
        back_ankle = get_landmark_coords(landmarks, back_ankle_idx, frame_shape)
        shoulder = get_landmark_coords(landmarks, LEFT_SHOULDER, frame_shape)
        
        # Check if we have all landmarks
        if None in [hip, knee, ankle, back_knee, shoulder]:
            self.feedback.append("⚠️ Cannot see full body")
            self.feedback.append("Stand sideways to camera")
            return frame, self.feedback
        
        # Calculate angles
        knee_angle = calculate_angle(hip, knee, ankle)
        back_knee_angle = calculate_angle(hip, back_knee, back_ankle) if back_knee else None
        torso_angle = calculate_angle(shoulder, hip, knee)
        
        # Draw angles
        draw_angle(frame, knee, knee_angle, (0, 255, 0))
        cv2.putText(frame, f"Torso: {int(torso_angle)}°", 
                    (hip[0] + 10, hip[1] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        # REP COUNTER
        # Detect when in lunge position
        if knee_angle < MAX_KNEE_ANGLE and not self.is_lunging:
            self.is_lunging = True
        # Detect when returning to start
        elif knee_angle > 150 and self.is_lunging:
            self.rep_count += 1
            self.is_lunging = False
            self.feedback.append(f"✅ Lunge {self.rep_count} completed!")
            if self.audio:
                self.audio.rep_completed("lunge", self.rep_count)
        
        # FORM CHECKS
        has_error = False
        
        # 1. Front Knee Position (should be at 90°)
        if GOOD_KNEE_ANGLE - 10 <= knee_angle <= GOOD_KNEE_ANGLE + 10:
            self.feedback.append("✅ Good knee angle!")
        elif knee_angle < MIN_KNEE_ANGLE:
            self.feedback.append("⚠️ Knee past toes - too deep")
            if self.audio and self.last_error != "knee_past_toes":
                self.audio.form_correction("lunge", "knee_past_toes")
                self.last_error = "knee_past_toes"
            has_error = True
        elif knee_angle > MAX_KNEE_ANGLE:
            self.feedback.append("⬇️ Go deeper")
            if self.audio and self.last_error != "shallow":
                self.audio.form_correction("lunge", "shallow")
                self.last_error = "shallow"
            has_error = True
        
        # 2. Torso Position (should be upright)
        forward_lean = abs(90 - torso_angle)
        if forward_lean < FORWARD_LEAN_MAX:
            self.feedback.append("✓ Torso upright")
        else:
            self.feedback.append("⚠️ Leaning forward too much")
            if self.audio and self.last_error != "forward_lean":
                self.audio.form_correction("lunge", "forward_lean")
                self.last_error = "forward_lean"
            has_error = True
        
        # 3. Back Leg Position
        if back_knee_angle and back_knee_angle > 160:
            self.feedback.append("✓ Back leg straight")
        elif back_knee_angle:
            self.feedback.append("⚠️ Back knee bent - keep leg straight")
            if self.audio and self.last_error != "back_knee_bent":
                self.audio.form_correction("lunge", "back_knee_bent")
                self.last_error = "back_knee_bent"
            has_error = True
        
        # 4. Knee Tracking (front knee should align with ankle)
        knee_past_toes = knee[0] > ankle[0] + 30 if self.use_left_leg else knee[0] < ankle[0] - 30
        if knee_past_toes:
            self.feedback.append("⚠️ Knee past toes")
            has_error = True
        
        # 5. Balance Check
        hip_shift = abs(hip[0] - ankle[0])
        if hip_shift > 50:
            self.feedback.append("⚠️ Unstable - center your weight")
        
        # Reset error tracking if form is good
        if not has_error:
            self.last_error = None
            if not self.was_good_form and self.audio:
                self.audio.set_good_form("lunge")
            self.was_good_form = True
        else:
            self.was_good_form = False
        
        # Add rep counter
        cv2.putText(frame, f"REPS: {self.rep_count}", 
                    (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        
        # Draw guide line for knee position
        cv2.line(frame, (ankle[0], ankle[1]), (knee[0], knee[1]), (0, 255, 0), 2)
        
        return frame, self.feedback
    
    def reset(self):
        self.rep_count = 0
        self.is_lunging = False
        self.feedback = []
        self.last_error = None
    
    def switch_leg(self):
        self.use_left_leg = not self.use_left_leg
        self.reset()
        return "Left leg" if self.use_left_leg else "Right leg"