"""
Plank Form Detector with Audio Feedback
"""

import cv2
import time
from pose_utils import calculate_angle, get_landmark_coords

# Landmark indices
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_ANKLE = 27
RIGHT_ANKLE = 28

class PlankDetector:
    def __init__(self, audio_feedback=None):
        self.good_form_time = 0
        self.start_time = None
        self.feedback = []
        self.form_was_good = False
        self.total_time = 0
        self.audio = audio_feedback
        
        # Track state for audio
        self.last_error = None
        self.good_form_announced = False
        
    def process_frame(self, frame, landmarks, frame_shape):
        self.feedback = []
        
        # Get landmarks
        left_shoulder = get_landmark_coords(landmarks, LEFT_SHOULDER, frame_shape)
        right_shoulder = get_landmark_coords(landmarks, RIGHT_SHOULDER, frame_shape)
        left_hip = get_landmark_coords(landmarks, LEFT_HIP, frame_shape)
        right_hip = get_landmark_coords(landmarks, RIGHT_HIP, frame_shape)
        left_ankle = get_landmark_coords(landmarks, LEFT_ANKLE, frame_shape)
        right_ankle = get_landmark_coords(landmarks, RIGHT_ANKLE, frame_shape)
        
        # Calculate average positions
        if left_shoulder and right_shoulder:
            shoulder = ((left_shoulder[0] + right_shoulder[0]) // 2,
                       (left_shoulder[1] + right_shoulder[1]) // 2)
        else:
            shoulder = None
            
        if left_hip and right_hip:
            hip = ((left_hip[0] + right_hip[0]) // 2,
                  (left_hip[1] + right_hip[1]) // 2)
        else:
            hip = None
            
        if left_ankle and right_ankle:
            ankle = ((left_ankle[0] + right_ankle[0]) // 2,
                    (left_ankle[1] + right_ankle[1]) // 2)
        else:
            ankle = None
        
        # Check if we have all landmarks
        if None in [shoulder, hip, ankle]:
            self.feedback.append("⚠️ Cannot see full body")
            self.feedback.append("Lie sideways to camera")
            if self.start_time:
                self.start_time = None
            return frame, self.feedback
        
        # Calculate body straightness
        body_angle = calculate_angle(shoulder, hip, ankle)
        
        # Draw angle and guideline
        cv2.putText(frame, f"Body angle: {int(body_angle)}°", 
                    (hip[0] + 10, hip[1] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.line(frame, (shoulder[0], shoulder[1]), (ankle[0], ankle[1]), 
                (0, 255, 0), 2)
        
        # FORM CHECKS
        is_good_form = False
        has_error = False
        
        # Check body alignment
        if 170 <= body_angle <= 190:
            is_good_form = True
            self.feedback.append("✅ Perfect plank position!")
            self.feedback.append("✓ Body straight, core engaged")
            
            # Announce good form when first achieved
            if not self.good_form_announced and self.audio:
                self.audio.speak("Good form! Hold the plank")
                self.good_form_announced = True
        elif body_angle < 170:
            self.feedback.append("⚠️ Hips too low (sagging)")
            self.feedback.append("✓ Tighten core and lift hips")
            if self.audio and self.last_error != "sagging":
                self.audio.speak("Tighten your core, lift your hips")
                self.last_error = "sagging"
            has_error = True
        elif body_angle > 190:
            self.feedback.append("⚠️ Hips too high (piking)")
            self.feedback.append("✓ Lower hips to straighten body")
            if self.audio and self.last_error != "piking":
                self.audio.speak("Lower your hips to straighten your body")
                self.last_error = "piking"
            has_error = True
        
        # Timer for hold time
        if is_good_form:
            if self.start_time is None:
                self.start_time = time.time()
                self.form_was_good = True
            else:
                self.good_form_time = time.time() - self.start_time
                self.total_time = self.good_form_time
                
            # Announce time milestones
            if self.audio and int(self.good_form_time) > 0:
                if int(self.good_form_time) in [10, 20, 30, 45, 60]:
                    self.audio.speak(f"{int(self.good_form_time)} seconds, keep going!")
        else:
            if self.form_was_good:
                self.start_time = None
                self.form_was_good = False
                self.good_form_announced = False
        
        # Additional checks
        if left_shoulder and right_shoulder:
            shoulder_diff = abs(left_shoulder[1] - right_shoulder[1])
            if shoulder_diff > 30:
                self.feedback.append("⚠️ Shoulders uneven")
                if self.audio and self.last_error != "shoulders":
                    self.audio.speak("Level your shoulders")
                    self.last_error = "shoulders"
                has_error = True
            else:
                self.feedback.append("✓ Shoulders level")
        
        if left_hip and right_hip:
            hip_diff = abs(left_hip[1] - right_hip[1])
            if hip_diff > 30:
                self.feedback.append("⚠️ Hips uneven")
        
        # Reset error tracking if form is good
        if not has_error and is_good_form:
            self.last_error = None
        
        # Display timer
        if self.good_form_time > 0:
            minutes = int(self.good_form_time // 60)
            seconds = int(self.good_form_time % 60)
            timer_text = f"Hold: {minutes:02d}:{seconds:02d}"
            cv2.putText(frame, timer_text, (10, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Form indicator
        if is_good_form:
            cv2.rectangle(frame, (frame.shape[1] - 110, 10), 
                         (frame.shape[1] - 10, 40), (0, 255, 0), -1)
            cv2.putText(frame, "GOOD FORM", (frame.shape[1] - 105, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        else:
            cv2.rectangle(frame, (frame.shape[1] - 110, 10), 
                         (frame.shape[1] - 10, 40), (0, 0, 255), -1)
            cv2.putText(frame, "FIX FORM", (frame.shape[1] - 100, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame, self.feedback
    
    def reset(self):
        self.good_form_time = 0
        self.start_time = None
        self.form_was_good = False
        self.feedback = []
        self.last_error = None
        self.good_form_announced = False
    
    def get_total_time(self):
        return self.total_time