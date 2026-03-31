"""
rep_counter.py
--------------
A generic rep-counting state machine. It knows nothing about which
exercise is running — it just watches a single metric (e.g. elbow angle)
cross two thresholds.

How to configure it for each exercise:

    Bicep curl (elbow angle drives the rep):
        start_threshold = 150   # arm is extended (rep can begin)
        end_threshold   = 60    # arm is fully curled (top of rep)
        direction       = "down"  # metric must DECREASE to reach top

    Squat (knee angle drives the rep):
        start_threshold = 160   # legs are straight (rep can begin)
        end_threshold   = 90    # legs are bent (bottom of squat)
        direction       = "down"

    Shoulder press (elbow angle drives the rep):
        start_threshold = 90    # arms at shoulder height
        end_threshold   = 160   # arms fully extended overhead
        direction       = "up"  # metric must INCREASE to reach top

    Plank:
        Use type = "hold" — no rep counting, just time tracking.

States
------
IDLE     → waiting for a stable start position
MOVING   → metric is heading toward the top/bottom
TOP      → metric has crossed the end threshold (peak of rep)
LOWERING → metric is returning to start position
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional


class Phase(Enum):
    IDLE     = "idle"
    MOVING   = "moving"
    TOP      = "top"
    LOWERING = "lowering"


@dataclass
class RepCounter:
    """
    Parameters
    ----------
    start_threshold : float
        The metric value that indicates the start/end position.
        e.g. elbow angle ≥ 150° for a curl.

    end_threshold : float
        The metric value that indicates the top/bottom of the rep.
        e.g. elbow angle ≤ 60° for a curl.

    direction : str
        "down" if the metric decreases to reach the top (curl, squat).
        "up"   if the metric increases to reach the top (shoulder press).
    """
    start_threshold: float
    end_threshold:   float
    direction:       str        # "up" or "down"

    # ── Counters ──────────────────────────────────────────────────────
    total_reps: int = 0
    valid_reps: int = 0
    phase:      Phase = Phase.IDLE

    # ── Per-rep fault log ─────────────────────────────────────────────
    # Faults are collected during a rep. A rep is only "valid" if this
    # list is empty when the rep completes.
    _faults: list = field(default_factory=list)

    def _at_start(self, metric: float) -> bool:
        """Is the metric at the start/rest position?"""
        if self.direction == "down":
            return metric >= self.start_threshold
        return metric <= self.start_threshold

    def _at_top(self, metric: float) -> bool:
        """Has the metric reached the top/bottom of the rep?"""
        if self.direction == "down":
            return metric <= self.end_threshold
        return metric >= self.end_threshold

    def _past_start_returning(self, metric: float) -> bool:
        """During lowering, has the metric returned to start?"""
        return self._at_start(metric)

    def record_fault(self, message: str):
        """
        Log a form fault for the current rep.
        Duplicates are ignored so a persistent fault (e.g. knees caving
        every frame for 2 seconds) only appears once in the log.
        """
        if message and message not in self._faults:
            self._faults.append(message)

    def update(self, metric: float) -> Optional[str]:
        """
        Feed the current frame's metric value into the state machine.

        Returns a string if a rep just completed:
            "valid"   → rep was clean
            "invalid" → rep had faults (caller can read self.last_faults)

        Returns None every other frame.

        Call this once per frame AFTER running your form checks and
        calling record_fault() for any that failed.
        """
        event = None

        if self.phase == Phase.IDLE:
            # Only start a rep once the joint is at the start position.
            # This prevents counting half-reps if the user connects
            # mid-exercise.
            if self._at_start(metric):
                self._faults = []           # clear faults from last rep
            if not self._at_start(metric):
                self.phase = Phase.MOVING

        elif self.phase == Phase.MOVING:
            if self._at_top(metric):
                self.phase = Phase.TOP

        elif self.phase == Phase.TOP:
            # Brief pause at top — wait for the metric to start returning
            if not self._at_top(metric):
                self.phase = Phase.LOWERING

        elif self.phase == Phase.LOWERING:
            if self._past_start_returning(metric):
                event = self._complete_rep()

        return event

    def _complete_rep(self) -> str:
        self.total_reps += 1
        if not self._faults:
            self.valid_reps += 1
            result = "valid"
        else:
            result = "invalid"

        self.last_faults = list(self._faults)   # expose for the caller to read
        self._faults     = []
        self.phase       = Phase.IDLE
        return result

    @property
    def phase_label(self) -> str:
        return self.phase.value
