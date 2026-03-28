"""
Push-up Form Detector with Audio Feedback
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
LEFT_ANKLE = 27
RIGHT_ANKLE = 28

# Thresholds
GOOD_ELBOW_ANGLE = 90          # Elbow at 90° at bottom
START_ELBOW_ANGLE = 160        # Start position
MAX_ELBOW_ANGLE = 170
BODY_STRAIGHT_THRESHOLD = 15   # Degrees deviation from straight line

class PushupDetector:
    def __init__(self, audio_feedback=None):
        self.rep_count = 0
        self.is_going_down = False
        self.feedback = []
        self.audio = audio_feedback
        self.last_error = None
        self.was_good_form = True
        self.start_shoulder_y = None
        
    def process_frame(self, frame, landmarks, frame_shape):
        """Process push-up frame and return feedback"""
        self.feedback = []
        
        # Get key landmarks (using left side for simplicity)
        shoulder = get_landmark_coords(landmarks, LEFT_SHOULDER, frame_shape)
        elbow = get_landmark_coords(landmarks, LEFT_ELBOW, frame_shape)
        wrist = get_landmark_coords(landmarks, LEFT_WRIST, frame_shape)
        hip = get_landmark_coords(landmarks, LEFT_HIP, frame_shape)
        ankle = get_landmark_coords(landmarks, LEFT_ANKLE, frame_shape)
        
        # Get right side for comparison
        right_shoulder = get_landmark_coords(landmarks, RIGHT_SHOULDER, frame_shape)
        right_hip = get_landmark_coords(landmarks, RIGHT_HIP, frame_shape)
        
        # Check if we have all landmarks
        if None in [shoulder, elbow, wrist, hip, ankle]:
            self.feedback.append("⚠️ Cannot see full body")
            self.feedback.append("Lie sideways to camera")
            return frame, self.feedback
        
        # Calculate angles
        elbow_angle = calculate_angle(shoulder, elbow, wrist)
        
        # Calculate body straightness (shoulder-hip-ankle)
        body_angle = calculate_angle(shoulder, hip, ankle)
        body_straightness = abs(180 - body_angle)
        
        # Draw angles
        draw_angle(frame, elbow, elbow_angle, (0, 255, 0))
        cv2.putText(frame, f"Body: {int(body_angle)}°", 
                    (hip[0] + 10, hip[1] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        # REP COUNTER
        # Detect going down
        if elbow_angle < 120 and not self.is_going_down:
            self.is_going_down = True
        # Detect coming up (completing rep)
        elif elbow_angle > 150 and self.is_going_down:
            self.rep_count += 1
            self.is_going_down = False
            self.feedback.append(f"✅ Push-up {self.rep_count} completed!")
            if self.audio:
                self.audio.rep_completed("pushup", self.rep_count)
        
        # FORM CHECKS
        has_error = False
        
        # 1. Elbow Angle (depth)
        if elbow_angle <= GOOD_ELBOW_ANGLE:
            self.feedback.append("✅ Good depth!")
        elif elbow_angle < 120:
            self.feedback.append("⬇️ Go lower")
            if self.audio and self.last_error != "partial":
                self.audio.form_correction("pushup", "partial")
                self.last_error = "partial"
            has_error = True
        
        # 2. Elbow Position (should be 45°, not flared)
        # Calculate elbow flare using horizontal distance
        if right_shoulder:
            elbow_flare = abs(elbow[1] - right_shoulder[1])
            if elbow_flare > 100:  # Rough threshold
                self.feedback.append("⚠️ Elbows flaring out")
                if self.audio and self.last_error != "elbow_flare":
                    self.audio.form_correction("pushup", "elbow_flare")
                    self.last_error = "elbow_flare"
                has_error = True
            else:
                self.feedback.append("✓ Elbows at good angle")
        
        # 3. Body Straightness (no sagging or piking)
        if body_straightness < BODY_STRAIGHT_THRESHOLD:
            self.feedback.append("✓ Body straight")
        elif body_angle < 170:
            self.feedback.append("⚠️ Hips sagging - tighten core")
            if self.audio and self.last_error != "hips_sagging":
                self.audio.form_correction("pushup", "hips_sagging")
                self.last_error = "hips_sagging"
            has_error = True
        elif body_angle > 190:
            self.feedback.append("⚠️ Hips too high - lower them")
            if self.audio and self.last_error != "hips_piking":
                self.audio.form_correction("pushup", "hips_piking")
                self.last_error = "hips_piking"
            has_error = True
        
        # 4. Shoulder and Hip Alignment (should be level)
        if right_shoulder and right_hip:
            shoulder_diff = abs(shoulder[1] - right_shoulder[1])
            hip_diff = abs(hip[1] - right_hip[1])
            
            if shoulder_diff > 30:
                self.feedback.append("⚠️ Shoulders uneven")
            if hip_diff > 30:
                self.feedback.append("⚠️ Hips uneven")
        
        # Reset error tracking if form is good
        if not has_error:
            self.last_error = None
            if not self.was_good_form and self.audio:
                self.audio.set_good_form("pushup")
            self.was_good_form = True
        else:
            self.was_good_form = False
        
        # Add rep counter
        cv2.putText(frame, f"REPS: {self.rep_count}", 
                    (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        
        # Draw body line guide
        cv2.line(frame, (shoulder[0], shoulder[1]), (ankle[0], ankle[1]), 
                (0, 255, 0), 2)
        
        return frame, self.feedback
    
    def reset(self):
        self.rep_count = 0
        self.is_going_down = False
        self.feedback = []
        self.last_error = None