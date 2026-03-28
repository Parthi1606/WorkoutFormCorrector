"""
Shoulder Press Form Detector with Audio Feedback
"""

import cv2
import numpy as np
from pose_utils import calculate_angle, get_landmark_coords, draw_angle

# Landmark indices
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24

# Thresholds
FULL_EXTENSION = 170          # Full extension at top
BOTTOM_POSITION = 80          # Bottom position (elbows at 90°)
MAX_ARCH = 15                 # Maximum back arch in degrees

class ShoulderPressDetector:
    def __init__(self, audio_feedback=None):
        self.rep_count = 0
        self.is_pressing = False
        self.feedback = []
        self.use_left_arm = True
        self.audio = audio_feedback
        self.last_error = None
        self.was_good_form = True
        
    def process_frame(self, frame, landmarks, frame_shape):
        """Process shoulder press frame and return feedback"""
        self.feedback = []
        
        # Choose which arm to track
        if self.use_left_arm:
            shoulder_idx = LEFT_SHOULDER
            elbow_idx = LEFT_ELBOW
            wrist_idx = LEFT_WRIST
        else:
            shoulder_idx = RIGHT_SHOULDER
            elbow_idx = RIGHT_ELBOW
            wrist_idx = RIGHT_WRIST
        
        # Get landmarks
        shoulder = get_landmark_coords(landmarks, shoulder_idx, frame_shape)
        elbow = get_landmark_coords(landmarks, elbow_idx, frame_shape)
        wrist = get_landmark_coords(landmarks, wrist_idx, frame_shape)
        hip = get_landmark_coords(landmarks, LEFT_HIP, frame_shape)
        
        # Check if we have all landmarks
        if None in [shoulder, elbow, wrist, hip]:
            self.feedback.append("⚠️ Cannot see full arm")
            self.feedback.append("Face camera straight on")
            return frame, self.feedback
        
        # Calculate angles
        elbow_angle = calculate_angle(shoulder, elbow, wrist)
        
        # Calculate back arch (shoulder-hip vertical alignment)
        back_arch = abs(shoulder[1] - hip[1])
        
        # Draw angle
        draw_angle(frame, elbow, elbow_angle, (0, 255, 0))
        
        # REP COUNTER
        # Detect pressing up
        if elbow_angle > BOTTOM_POSITION + 20 and not self.is_pressing:
            self.is_pressing = True
        # Detect returning to start
        elif elbow_angle < BOTTOM_POSITION + 30 and self.is_pressing:
            self.rep_count += 1
            self.is_pressing = False
            self.feedback.append(f"✅ Shoulder Press {self.rep_count} completed!")
            if self.audio:
                self.audio.rep_completed("shoulder_press", self.rep_count)
        
        # FORM CHECKS
        has_error = False
        
        # 1. Range of Motion
        if elbow_angle > FULL_EXTENSION:
            self.feedback.append("✅ Full extension!")
        elif elbow_angle > 150:
            self.feedback.append("⬆️ Press up fully")
            if self.audio and self.last_error != "partial":
                self.audio.form_correction("shoulder_press", "partial")
                self.last_error = "partial"
            has_error = True
        elif elbow_angle < BOTTOM_POSITION:
            self.feedback.append("⬇️ Lower to 90°")
            has_error = True
        
        # 2. Elbow Position (should be slightly forward, not flared)
        elbow_flare = abs(elbow[0] - shoulder[0])
        if elbow_flare > 80:
            self.feedback.append("⚠️ Elbows flaring out")
            if self.audio and self.last_error != "elbow_flare":
                self.audio.form_correction("shoulder_press", "elbow_flare")
                self.last_error = "elbow_flare"
            has_error = True
        else:
            self.feedback.append("✓ Elbow position good")
        
        # 3. Back Arch
        if back_arch < 50:
            self.feedback.append("✓ Back straight")
        else:
            self.feedback.append("⚠️ Arching back - tighten core")
            if self.audio and self.last_error != "arch_back":
                self.audio.form_correction("shoulder_press", "arch_back")
                self.last_error = "arch_back"
            has_error = True
        
        # Reset error tracking
        if not has_error:
            self.last_error = None
            if not self.was_good_form and self.audio:
                self.audio.set_good_form("shoulder_press")
            self.was_good_form = True
        else:
            self.was_good_form = False
        
        # Add rep counter
        cv2.putText(frame, f"REPS: {self.rep_count}", 
                    (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        
        return frame, self.feedback
    
    def reset(self):
        self.rep_count = 0
        self.is_pressing = False
        self.feedback = []
        self.last_error = None
    
    def switch_arm(self):
        self.use_left_arm = not self.use_left_arm
        self.reset()
        return "Left arm" if self.use_left_arm else "Right arm"