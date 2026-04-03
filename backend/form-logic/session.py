"""
session.py
----------
One Session object is created per WebSocket connection.

It holds:
  - Which exercise is active
  - The rep counter state for that exercise
  - Per-rep baselines (e.g. elbow position at start of curl)
  - The active side (left/right) for unilateral exercises

It does NOT hold:
  - The WebSocket connection itself (that stays in server.py)
  - The audio engine (that's a singleton in audio.py)
  - Any MediaPipe state (pose estimation runs on the phone)

Processing one frame
--------------------
server.py receives a JSON frame, parses the landmarks, and calls:

    result = session.process(landmarks)

session.process() does three things:
  1. Runs check_form() from the active exercise module
  2. Feeds any faults into the rep counter
  3. Checks if a rep just completed and triggers audio
  4. Returns a dict that gets sent back to the phone as JSON
"""

import time
import importlib
from dataclasses import dataclass, field
from typing import Optional

from rep_counter import RepCounter, Phase
from audio import audio


# ─── Registry ────────────────────────────────────────────────────────────────
# Maps the exercise name (from the WebSocket URL) to its module.
# Add a new exercise by dropping a file in exercises/ and adding it here.

EXERCISE_REGISTRY = {
    "bicep_curl":     "exercises.bicep_curl",
    "squat":          "exercises.squat",
    "shoulder_press": "exercises.shoulder_press",
    "lunge":          "exercises.lunge",
    "pushup":         "exercises.pushup",
    "bent_over_row":  "exercises.bent_over_row",
    "plank":          "exercises.plank",
}


@dataclass
class Session:
    """
    Holds all mutable state for one user's exercise session.

    Parameters
    ----------
    exercise_name : str
        Must be a key in EXERCISE_REGISTRY.

    Raises
    ------
    ValueError if exercise_name is not registered.
    """
    exercise_name: str

    # Set during __post_init__
    _exercise:    object       = field(init=False)
    _counter:     Optional[RepCounter] = field(init=False, default=None)
    _is_hold:     bool         = field(init=False, default=False)
    _hold_start:  Optional[float] = field(init=False, default=None)

    # Baselines captured at the start of each rep (reset after each rep)
    _baselines:   dict         = field(init=False, default_factory=dict)

    # Tracks active side for unilateral exercises
    _active_side: Optional[str] = field(init=False, default=None)

    def __post_init__(self):
        if self.exercise_name not in EXERCISE_REGISTRY:
            raise ValueError(
                f"Unknown exercise '{self.exercise_name}'. "
                f"Valid options: {list(EXERCISE_REGISTRY.keys())}"
            )

        # Dynamically import the exercise module
        module_path      = EXERCISE_REGISTRY[self.exercise_name]
        self._exercise   = importlib.import_module(module_path)

        # Check if this exercise uses hold-timing instead of rep counting
        self._is_hold = getattr(self._exercise, "IS_HOLD", False)

        if not self._is_hold:
            cfg = self._exercise.COUNTER_CONFIG
            self._counter = RepCounter(
                start_threshold = cfg["start_threshold"],
                end_threshold   = cfg["end_threshold"],
                direction       = cfg["direction"],
            )

    def process(self, landmarks: list) -> dict:
        """
        Process one frame of landmark data.

        Parameters
        ----------
        landmarks : list
            The 33-item list of landmark objects from MediaPipe.
            Each item has .x, .y, .z, .visibility attributes.

        Returns
        -------
        dict with keys:
            phase       : str   — current phase (idle / moving / top / lowering / hold)
            rep_count   : int
            valid_reps  : int
            hold_seconds: float — only present for hold exercises
            active_side : str | None — "LEFT" or "RIGHT" for unilateral
            checks      : list of {label, ok, message}
            rep_event   : str | None — "valid" | "invalid" | None
            faults      : list of str — fault messages from last completed rep
        """

        # ── 1. Run form checks ────────────────────────────────────────
        checks, metric, active_side = self._exercise.check_form(
            landmarks,
            baselines=self._baselines,
        )
        self._active_side = active_side

        # ── 2. Update baselines if not yet set for this rep ───────────
        # check_form() may populate baselines (e.g. elbow x at curl start)
        # We pass _baselines by reference so the exercise can write into it.
        # Baselines are reset after each rep completes (see below).

        # ── 3. Feed faults into rep counter / hold timer ──────────────
        rep_event = None
        faults    = []

        if self._is_hold:
            # Hold exercise: just track elapsed time
            all_ok = all(c["ok"] for c in checks)
            if all_ok:
                if self._hold_start is None:
                    self._hold_start = time.time()
            else:
                self._hold_start = None     # reset timer if form breaks

            hold_seconds = (
                time.time() - self._hold_start
                if self._hold_start else 0.0
            )

        else:
            # Rep exercise: feed form faults then update state machine
            for check in checks:
                if not check["ok"]:
                    self._counter.record_fault(check["message"])

            rep_event = self._counter.update(metric)

            if rep_event is not None:
                faults = list(getattr(self._counter, "last_faults", []))
                self._trigger_audio(rep_event, faults)
                self._baselines = {}    # reset baselines for next rep
            else:
                # Trigger in-rep audio cues for the most important fault
                self._trigger_form_cues(checks)

        # ── 4. Build response ─────────────────────────────────────────
        response = {
            "phase":       "hold" if self._is_hold else self._counter.phase_label,
            "rep_count":   0 if self._is_hold else self._counter.total_reps,
            "valid_reps":  0 if self._is_hold else self._counter.valid_reps,
            "active_side": self._active_side,
            "checks":      checks,
            "rep_event":   rep_event,
            "faults":      faults,
        }

        if self._is_hold:
            response["hold_seconds"] = round(hold_seconds, 1)

        return response

    def _trigger_audio(self, rep_event: str, faults: list):
        """Speak a rep-completion cue."""
        if rep_event == "valid":
            audio.say("great rep", priority=True)
        else:
            # Speak the first fault as the primary coaching cue
            if faults:
                audio.say(faults[0], priority=True)
            else:
                audio.say("watch your form", priority=True)

    def _trigger_form_cues(self, checks: list):
        """
        During a rep, speak the most important failing check.
        Only one cue per frame — the first failing check wins.
        The cooldown in audio.py ensures it doesn't repeat immediately.
        """
        for check in checks:
            if not check["ok"] and check.get("message"):
                audio.say(check["message"])
                break   # one cue per frame is enough
