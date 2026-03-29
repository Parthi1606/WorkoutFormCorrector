"""
Bicep Curl Form Detector with Audio Feedback
"""

import cv2
import numpy as np
from pose_utils import calculate_angle, get_landmark_coords, draw_angle

# Landmark indices
LEFT_SHOULDER = 11
LEFT_ELBOW = 13
LEFT_WRIST = 15
RIGHT_SHOULDER = 12
RIGHT_ELBOW = 14
RIGHT_WRIST = 16

# Thresholds
ELBOW_GOOD_ANGLE = 30
ELBOW_EXTENDED = 160
SHOULDER_RISE_THRESHOLD = 0.03
ELBOW_DRIFT_THRESHOLD = 0.05

class BicepCurlDetector:
    def __init__(self, audio_feedback=None):
        self.rep_count = 0
        self.is_curling = False
        self.shoulder_start_y = None
        self.elbow_start_x = None
        self.feedback = []
        self.use_left_arm = True
        self.audio = audio_feedback
        
        # Track state for audio triggers
        self.last_error = None
        self.was_good_form = True
        self.last_rep_count = 0
        
    def process_frame(self, frame, landmarks, frame_shape):
        """
        Process a single frame and return feedback
        """
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
        
        # Get landmark coordinates
        shoulder = get_landmark_coords(landmarks, shoulder_idx, frame_shape)
        elbow = get_landmark_coords(landmarks, elbow_idx, frame_shape)
        wrist = get_landmark_coords(landmarks, wrist_idx, frame_shape)
        
        # Check if we have all landmarks
        if None in [shoulder, elbow, wrist]:
            self.feedback.append("⚠️ Cannot see full arm")
            self.feedback.append("Stand sideways to camera")
            return frame, self.feedback
        
        # Calculate elbow angle
        angle = calculate_angle(shoulder, elbow, wrist)
        
        # Draw angle on frame
        draw_angle(frame, elbow, angle)
        
        # Initialize tracking on first frame
        if self.shoulder_start_y is None:
            self.shoulder_start_y = shoulder[1]
            self.elbow_start_x = elbow[0]
        
        # Calculate movements
        shoulder_rise = (self.shoulder_start_y - shoulder[1]) / frame_shape[0]
        elbow_drift = abs(elbow[0] - self.elbow_start_x) / frame_shape[1]
        
        # REP COUNTER
        if angle < ELBOW_GOOD_ANGLE + 20 and not self.is_curling:
            self.is_curling = True
        elif angle > ELBOW_EXTENDED and self.is_curling:
            self.rep_count += 1
            self.is_curling = False
            self.feedback.append(f"✅ Rep {self.rep_count} completed!")
            
            # Audio feedback for rep completion
            if self.audio:
                if self.rep_count % 5 == 0:
                    self.audio.speak(f"Great job! {self.rep_count} reps completed!")
                else:
                    self.audio.speak(f"Good rep! {self.rep_count} total")
        
        # FORM CHECKS
        has_error = False
        
        # Range of motion
        if angle < ELBOW_GOOD_ANGLE:
            self.feedback.append("✅ Full contraction!")
        elif angle < 90:
            self.feedback.append("⬆️ Curl up more - aim for 90°")
            if self.audio and self.last_error != "curl_up":
                self.audio.speak("Curl up higher")
                self.last_error = "curl_up"
            has_error = True
        elif angle > 120 and angle < 160:
            self.feedback.append("⬇️ Lower the weight more")
            if self.audio and self.last_error != "lower":
                self.audio.speak("Lower the weight fully")
                self.last_error = "lower"
            has_error = True
        elif angle > 160:
            self.feedback.append("⬇️ Fully extend arm at bottom")
            has_error = True
        
        # Shoulder movement
        if shoulder_rise > SHOULDER_RISE_THRESHOLD:
            self.feedback.append("⚠️ Shoulder rising - keep stable")
            if self.audio and self.last_error != "shoulder":
                self.audio.speak("Keep your shoulder stable, don't shrug")
                self.last_error = "shoulder"
            has_error = True
        else:
            self.feedback.append("✓ Shoulders stable")
        
        # Elbow drift
        if elbow_drift > ELBOW_DRIFT_THRESHOLD:
            self.feedback.append("⚠️ Elbow drifting - keep tucked")
            if self.audio and self.last_error != "elbow":
                self.audio.speak("Keep your elbow tucked at your side")
                self.last_error = "elbow"
            has_error = True
        else:
            self.feedback.append("✓ Elbow position good")
        
        # Reset error tracking if form is good
        if not has_error:
            self.last_error = None
            if self.was_good_form == False and self.audio:
                self.audio.speak("Good form! Keep it up")
            self.was_good_form = True
        else:
            self.was_good_form = False
        
        # Add rep counter
        cv2.putText(frame, f"REPS: {self.rep_count}", 
                    (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        
        # Draw movement arrow
        cv2.arrowedLine(frame, (elbow[0], elbow[1]), 
                       (wrist[0], wrist[1]), (0, 255, 255), 2)
        
        return frame, self.feedback
    
    def reset(self):
        self.rep_count = 0
        self.is_curling = False
        self.shoulder_start_y = None
        self.elbow_start_x = None
        self.feedback = []
        self.last_error = None
    
    def switch_arm(self):
        self.use_left_arm = not self.use_left_arm
        self.reset()
        return "Left arm" if self.use_left_arm else "Right arm"