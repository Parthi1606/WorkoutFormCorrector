"""
audio.py
--------
Non-blocking audio feedback using pyttsx3.

The server never calls pyttsx3 directly. Instead it calls:
    audio.say("keep your back straight")

That puts the message on a queue and returns immediately.
A background thread picks it up and speaks whenever it's free.

Cooldown system
---------------
Each unique message has a cooldown period (default 4 seconds).
If "knees caving in" is spoken, it won't repeat for 4 seconds even
if the fault persists every frame. Without this, one bad rep triggers
the same cue hundreds of times.

Priority system
---------------
Rep completion cues ("great rep", "watch your form") jump the queue
so they aren't delayed behind a backlog of form cues.
"""

import queue
import threading
import time
import pyttsx3


# ─── Cooldowns (seconds) per message ────────────────────────────────────────
# Tune these based on how annoying they get in practice.

DEFAULT_COOLDOWN = 4.0

COOLDOWNS = {
    # Rep events — shorter cooldown so they always feel responsive
    "great rep":        1.5,
    "watch your form":  1.5,
    "good work":        2.0,

    # Form cues — longer so they don't become white noise
    "keep your back straight":      2.0,
    "chest up":                     5.0,
    "knees over toes":              5.0,
    "knees caving in":              4.0,
    "elbow drifting":               4.0,
    "lower all the way down":       5.0,
    "control the descent":          4.0,
    "keep your core tight":         6.0,
    "hips dropping":                4.0,
    "lock out at the top":          4.0,
}


class AudioFeedback:
    """
    Manages a background thread that speaks queued messages via pyttsx3.

    Usage:
        audio = AudioFeedback()
        audio.start()

        audio.say("knees caving in")   # non-blocking, returns instantly
        audio.say("great rep", priority=True)

        audio.stop()                   # call on shutdown
    """

    def __init__(self, rate: int = 165, volume: float = 1.0):
        """
        rate   : words per minute (default 165 — natural conversational pace)
        volume : 0.0 to 1.0
        """
        self._queue:     queue.PriorityQueue = queue.PriorityQueue()
        self._cooldowns: dict[str, float]    = {}   # message → last spoken time
        self._lock       = threading.Lock()
        self._stop_event = threading.Event()
        self._thread     = threading.Thread(target=self._worker, daemon=True)
        self._rate       = rate
        self._volume     = volume

    def start(self):
        """Start the background audio thread. Call once at server startup."""
        self._thread.start()

    def stop(self):
        """Signal the audio thread to finish and exit. Call on server shutdown."""
        self._stop_event.set()
        # Unblock the queue.get() so the thread can exit cleanly
        self._queue.put((0, time.time(), "__STOP__"))

    def say(self, message: str, priority: bool = False):
        """
        Queue a message to be spoken.

        priority=True  → spoken before any queued form cues.
                         Use for rep completion events.
        priority=False → normal form feedback cue.

        This method is thread-safe and returns immediately.
        """
        with self._lock:
            now       = time.time()
            cooldown  = COOLDOWNS.get(message, DEFAULT_COOLDOWN)
            last_said = self._cooldowns.get(message, 0)

            if now - last_said < cooldown:
                return  # still in cooldown, discard

            self._cooldowns[message] = now

        # PriorityQueue sorts by first tuple element (lower = higher priority)
        prio = 0 if priority else 1
        self._queue.put((prio, time.time(), message))

    def _worker(self):
        """
        Background thread: pulls messages from the queue and speaks them.
        Runs until stop() is called.
        """
        engine = pyttsx3.init()
        engine.setProperty("rate",   self._rate)
        engine.setProperty("volume", self._volume)

        while not self._stop_event.is_set():
            try:
                # Block until a message arrives (timeout lets us check stop_event)
                _prio, _ts, message = self._queue.get(timeout=0.5)
                if message == "__STOP__":
                    break
                engine.say(message)
                engine.runAndWait()
            except queue.Empty:
                continue    # no message yet, loop back and check stop_event
            except Exception as e:
                # Never crash the audio thread — just log and keep going
                print(f"[audio] error: {e}")

        engine.stop()


# ─── Module-level singleton ───────────────────────────────────────────────────
# Import and use this directly:
#   from audio import audio
#   audio.say("great rep", priority=True)

audio = AudioFeedback()
