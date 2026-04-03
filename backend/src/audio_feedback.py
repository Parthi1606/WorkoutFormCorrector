"""
Audio Feedback Module - Extended for All Exercises
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
        self.engine.setProperty('rate', 150)    # Speed of speech
        self.engine.setProperty('volume', 0.9)  # Volume
        
        # Get available voices
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        # Track last spoken message to avoid repetition
        self.last_message = ""
        self.last_message_time = 0
        self.message_cooldown = 3
        
        # Queue for managing speech
        self.speech_queue = []
        self.is_speaking = False
        
    def speak(self, message, force=False):
        """Speak a message"""
        current_time = time.time()
        
        if not force and message == self.last_message:
            if current_time - self.last_message_time < self.message_cooldown:
                return
    
        self.last_message = message
        self.last_message_time = current_time
        self.speech_queue.append(message)
    
        if not self.is_speaking:
            self._process_queue()
    
    def _process_queue(self):
        """Process speech queue"""
        if not self.speech_queue:
            self.is_speaking = False
            return
        
        self.is_speaking = True
        message = self.speech_queue.pop(0)
    
        def speak_thread():
            self.engine.say(message)
            self.engine.runAndWait()
            self._process_queue()
        
        thread = threading.Thread(target=speak_thread)
        thread.daemon = True
        thread.start()
    
    def exercise_start(self, exercise):
        """Announce exercise start"""
        messages = {
            "bicep_curl": "Starting bicep curls. Keep your elbows tucked at your sides.",
            "squat": "Starting squats. Keep your chest up and back straight.",
            "plank": "Starting plank. Keep your body in a straight line.",
            "lunge": "Starting lunges. Keep your front knee aligned with your ankle.",
            "pushup": "Starting pushups. Keep your body straight and core tight.",
            "shoulder_press": "Starting shoulder press. Keep your core stable.",
            "deadlift": "Starting deadlifts. Keep your back straight.",
            "lateral_raise": "Starting lateral raises. Control the movement.",
            "tricep_extension": "Starting tricep extensions. Keep your elbows pointed up.",
            "leg_raise": "Starting leg raises. Keep your lower back pressed down."
        }
        self.speak(messages.get(exercise, f"Starting {exercise}. Good luck!"))
    
    def rep_completed(self, exercise, rep_count):
        """Celebrate rep completion"""
        if rep_count % 10 == 0:
            self.speak(f"Amazing! {rep_count} reps completed!")
        elif rep_count % 5 == 0:
            self.speak(f"Great job! {rep_count} reps!")
        elif rep_count == 1:
            self.speak("First rep! Keep going!")
        else:
            self.speak(f"Good rep! {rep_count} total")
    
    def form_correction(self, exercise, error_type):
        """Provide form correction feedback"""
        corrections = {
            # Bicep Curl
            "bicep_curl_elbow_drift": "Keep your elbow tucked at your side",
            "bicep_curl_shoulder_rise": "Keep your shoulders stable, don't shrug",
            "bicep_curl_partial_curl": "Curl up higher for full range of motion",
            "bicep_curl_no_extension": "Lower the weight fully to extend your arm",
            "bicep_curl_wrist_bend": "Keep your wrist straight",
            
            # Squat
            "squat_shallow": "Go deeper, aim for thighs parallel to ground",
            "squat_forward_lean": "Chest up, don't lean forward too much",
            "squat_knees_caving": "Push your knees outward",
            "squat_knees_past_toes": "Sit back more, keep weight on heels",
            "squat_back_rounding": "Keep your back straight, don't round",
            
            # Plank
            "plank_hips_sagging": "Tighten your core, lift your hips",
            "plank_hips_piking": "Lower your hips to straighten your body",
            "plank_shoulders_uneven": "Level your shoulders",
            "plank_hips_uneven": "Keep your hips level",
            
            # Lunge
            "lunge_knee_past_toes": "Keep your front knee behind your toes",
            "lunge_knee_touching_ground": "Control the descent, don't drop too fast",
            "lunge_forward_lean": "Keep your torso upright",
            "lunge_back_knee_bent": "Keep your back leg straight",
            "lunge_balance": "Keep your weight centered",
            
            # Push-up
            "pushup_elbow_flare": "Keep your elbows at 45 degrees, not flared out",
            "pushup_hips_sagging": "Keep your body straight, don't let hips drop",
            "pushup_hips_piking": "Keep your body straight, don't lift hips too high",
            "pushup_partial": "Go lower, chest to floor level",
            "pushup_head_position": "Keep your neck neutral, look at the floor",
            
            # Shoulder Press
            "shoulder_press_elbow_flare": "Keep elbows slightly forward, not flared",
            "shoulder_press_arch_back": "Keep your core tight, don't arch your back",
            "shoulder_press_partial": "Extend arms fully at the top",
            "shoulder_press_uneven": "Keep shoulders level",
            
            # Deadlift
            "deadlift_back_rounding": "Keep your back straight, chest up",
            "deadlift_knees_locked": "Keep a slight bend in your knees",
            "deadlift_shoulders_forward": "Keep shoulders over the bar",
            "deadlift_hips_too_low": "Start with hips higher",
            
            # Lateral Raise
            "lateral_raise_swinging": "Control the movement, no swinging",
            "lateral_raise_elbow_bent": "Keep a slight bend in your elbows",
            "lateral_raise_above_shoulder": "Don't raise above shoulder height",
            "lateral_raise_traps": "Don't shrug your shoulders up",
            
            # Tricep Extension
            "tricep_extension_elbow_drift": "Keep your elbows pointed up",
            "tricep_extension_partial": "Extend fully at the top",
            "tricep_extension_swinging": "Control the movement",
            
            # Leg Raise
            "leg_raise_lower_back": "Press your lower back into the floor",
            "leg_raise_legs_bent": "Keep your legs straight",
            "leg_raise_swinging": "Control the movement, no momentum"
        }
        
        key = f"{exercise}_{error_type}"
        message = corrections.get(key, f"Check your {error_type.replace('_', ' ')}")
        self.speak(message)
    
    def set_good_form(self, exercise):
        """Praise good form"""
        messages = {
            "bicep_curl": "Great form! Keep those elbows tucked.",
            "squat": "Perfect squat! Great depth.",
            "plank": "Excellent plank! Core is tight.",
            "lunge": "Good lunge! Nice knee position.",
            "pushup": "Great pushup! Perfect body line.",
            "shoulder_press": "Good shoulder press! Nice control.",
            "deadlift": "Great deadlift! Perfect back position.",
            "lateral_raise": "Good lateral raise! Controlled movement.",
            "tricep_extension": "Great tricep extension! Full range.",
            "leg_raise": "Good leg raise! Core engaged."
        }
        self.speak(messages.get(exercise, "Good form! Keep it up"))
    
    def workout_summary(self, exercise, total_reps, avg_form_quality, duration_seconds):
        """Provide workout summary"""
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        
        summary = f"{exercise.replace('_', ' ')} workout complete! "
        summary += f"{total_reps} reps in {minutes} minutes and {seconds} seconds. "
        summary += f"Average form quality {int(avg_form_quality)} percent. "
        
        if avg_form_quality >= 90:
            summary += "Excellent form! Keep it up!"
        elif avg_form_quality >= 75:
            summary += "Good form! Focus on the corrections mentioned."
        else:
            summary += "Keep practicing! Focus on your form."
        
        self.speak(summary)
    
    def reset(self):
        """Reset feedback tracking"""
        self.last_message = ""
        self.speech_queue = []
        self.is_speaking = False