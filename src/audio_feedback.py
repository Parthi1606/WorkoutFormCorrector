"""
Audio Feedback Module
Provides voice feedback for form corrections
"""

import pyttsx3
import threading
import time

class AudioFeedback:
    def __init__(self):
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        
        # Configure voice properties
        self.engine.setProperty('rate', 150)    # Speed of speech (words per minute)
        self.engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
        
        # Get available voices and select a female voice if available
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        # Track last spoken message to avoid repetition
        self.last_message = ""
        self.last_message_time = 0
        self.message_cooldown = 3  # Don't repeat same message within 3 seconds
        
        # Queue for managing speech (to avoid overlapping)
        self.speech_queue = []
        self.is_speaking = False
        
    def speak(self, message, force=False):
        """
        Speak a message
        If force=True, speak immediately even if on cooldown
        """
        current_time = time.time()
        
        # Check cooldown (don't repeat same message too often)
        if not force and message == self.last_message:
            if current_time - self.last_message_time < self.message_cooldown:
                return
        
        # Update last message tracking
        self.last_message = message
        self.last_message_time = current_time
        
        # Add to queue
        self.speech_queue.append(message)
        
        # Start speaking if not already
        if not self.is_speaking:
            self._process_queue()
    
    def _process_queue(self):
        """Process speech queue in background thread"""
        if not self.speech_queue:
            self.is_speaking = False
            return
        
        self.is_speaking = True
        message = self.speech_queue.pop(0)
        
        # Speak in a separate thread to not block the main program
        def speak_thread():
            self.engine.say(message)
            self.engine.runAndWait()
            self._process_queue()
        
        thread = threading.Thread(target=speak_thread)
        thread.daemon = True
        thread.start()
    
    def feedback_for_exercise(self, exercise, feedback_list, rep_count=None):
        """
        Generate audio feedback based on form feedback
        """
        # Check for critical errors first (most important)
        critical_messages = []
        warning_messages = []
        positive_messages = []
        
        for msg in feedback_list:
            if "⚠️" in msg or "❌" in msg:
                # Extract the actual message without emoji
                clean_msg = msg.replace("⚠️", "").replace("❌", "").strip()
                critical_messages.append(clean_msg)
            elif "✅" in msg or "✓" in msg or "Good" in msg:
                # Positive feedback (only say occasionally)
                if "Rep" in msg:
                    positive_messages.append(msg)
            elif "⬆️" in msg or "⬇️" in msg:
                clean_msg = msg.replace("⬆️", "").replace("⬇️", "").strip()
                warning_messages.append(clean_msg)
        
        # Prioritize messages
        if critical_messages:
            # Only say the most critical one
            self.speak(critical_messages[0])
        elif warning_messages:
            # Only say one warning at a time
            self.speak(warning_messages[0])
        elif positive_messages and rep_count:
            # Say positive feedback for completed reps
            for msg in positive_messages:
                if "completed" in msg:
                    self.speak(f"Good rep! Total {rep_count}")
    
    def rep_completed(self, exercise, rep_count):
        """Voice feedback when rep is completed"""
        if rep_count % 5 == 0:
            # Say every 5th rep for motivation
            self.speak(f"Great job! {rep_count} reps completed!")
        elif rep_count % 3 == 0:
            self.speak(f"Nice rep! Keep going!")
        else:
            self.speak(f"Rep {rep_count}")
    
    def exercise_start(self, exercise):
        """Voice feedback when exercise starts"""
        self.speak(f"Starting {exercise}. Get ready!")
    
    def good_form_achieved(self):
        """Voice feedback when form is good"""
        self.speak("Good form! Keep it up")
    
    def reset(self):
        """Reset feedback tracking"""
        self.last_message = ""
        self.speech_queue = []
        self.is_speaking = False

# Pre-defined feedback messages for common corrections
FORM_FEEDBACK = {
    # Bicep Curl
    "elbow_drift": "Keep your elbow tucked at your side",
    "shoulder_rise": "Keep your shoulder stable, don't shrug",
    "partial_curl": "Curl up higher for full range of motion",
    "no_extension": "Lower the weight fully to extend your arm",
    "wrist_bend": "Keep your wrist straight",
    
    # Squat
    "shallow_squat": "Go deeper, aim for thighs parallel to ground",
    "forward_lean": "Chest up, don't lean forward too much",
    "knees_caving": "Push your knees outward",
    "knees_past_toes": "Sit back more, keep weight on heels",
    "good_depth": "Good depth! Nice squat",
    
    # Plank
    "hips_sagging": "Tighten your core, lift your hips",
    "hips_piking": "Lower your hips to straighten your body",
    "shoulders_uneven": "Level your shoulders",
    "hips_uneven": "Keep your hips level",
    "perfect_plank": "Perfect plank! Hold it"
}