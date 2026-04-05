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
"""

import time
import importlib
from dataclasses import dataclass, field
from typing import Optional

from rep_counter import RepCounter
from audio import audio


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
    """Holds all mutable state for one user's exercise session."""
    exercise_name: str

    _exercise: object = field(init=False)
    _counter: Optional[RepCounter] = field(init=False, default=None)
    _is_hold: bool = field(init=False, default=False)
    _hold_start: Optional[float] = field(init=False, default=None)
    _baselines: dict = field(init=False, default_factory=dict)
    _active_side: Optional[str] = field(init=False, default=None)

    def __post_init__(self):
        if self.exercise_name not in EXERCISE_REGISTRY:
            raise ValueError(
                f"Unknown exercise '{self.exercise_name}'. "
                f"Valid options: {list(EXERCISE_REGISTRY.keys())}"
            )

        module_path = EXERCISE_REGISTRY[self.exercise_name]
        self._exercise = importlib.import_module(module_path)
        self._is_hold = getattr(self._exercise, "IS_HOLD", False)

        if not self._is_hold:
            cfg = self._exercise.COUNTER_CONFIG
            self._counter = RepCounter(
                start_threshold=cfg["start_threshold"],
                end_threshold=cfg["end_threshold"],
                direction=cfg["direction"],
            )

    def process(self, landmarks: list) -> dict:
        """Process one frame of landmark data."""

        # 1) Run exercise form checks.
        result = self._exercise.check_form(
            landmarks,
            baselines=self._baselines,
        )

        # Exercises may optionally return rep_valid as a 4th item.
        if len(result) == 4:
            checks, metric, active_side, rep_valid = result
        else:
            checks, metric, active_side = result
            rep_valid = True

        self._active_side = active_side

        rep_event = None
        faults = []

        if self._is_hold:
            # Hold exercise: track elapsed time while all checks pass.
            all_ok = all(c["ok"] for c in checks)
            if all_ok:
                if self._hold_start is None:
                    self._hold_start = time.time()
            else:
                self._hold_start = None

            hold_seconds = (
                time.time() - self._hold_start
                if self._hold_start is not None else 0.0
            )

        else:
            # Rep exercise: collect any in-rep faults.
            for check in checks:
                if not check["ok"] and check.get("message"):
                    self._counter.record_fault(check["message"])

            # Shoulder press uses a session baseline gate for lockout.
            if self.exercise_name == "shoulder_press":
                rep_valid = self._baselines.get("hit_lockout", False)

            rep_event = self._counter.update(metric, rep_valid=rep_valid)

            if rep_event is not None:
                faults = list(getattr(self._counter, "last_faults", []))

                # Add shoulder-press-specific completion feedback.
                if self.exercise_name == "shoulder_press" and not rep_valid:
                    if "extend fully overhead" not in faults:
                        faults.insert(0, "extend fully overhead")

                if self.exercise_name == "lunge" and not rep_valid:
                    if not self._exercise._state.get("gate_return_passed", False):
                        if "step back to your starting position" not in faults:
                            faults.insert(0, "step back to your starting position")

                self._trigger_audio(rep_event, faults)
                self._baselines = {}  # reset per-rep baselines
            else:
                self._trigger_form_cues(checks)

        response = {
            "phase": "hold" if self._is_hold else self._counter.phase_label,
            "rep_count": 0 if self._is_hold else self._counter.total_reps,
            "valid_reps": 0 if self._is_hold else self._counter.valid_reps,
            "active_side": self._active_side,
            "checks": checks,
            "rep_event": rep_event,
            "faults": faults,
        }

        if self._is_hold:
            response["hold_seconds"] = round(hold_seconds, 1)

        return response

    def _trigger_audio(self, rep_event: str, faults: list):
        """Speak a rep-completion cue."""
        if rep_event == "valid":
            audio.say("great rep", priority=True)
        else:
            if faults:
                audio.say(faults[0], priority=True)
            else:
                audio.say("watch your form", priority=True)

    def _trigger_form_cues(self, checks: list):
        """
        During a rep, speak the most important failing check.
        Only one cue per frame — the first failing check wins.
        """
        for check in checks:
            if not check["ok"] and check.get("message"):
                audio.say(check["message"])
                break
