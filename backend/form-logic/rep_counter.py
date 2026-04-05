"""
rep_counter.py
--------------
A generic rep-counting state machine. It knows nothing about which
exercise is running — it just watches a single metric cross two thresholds.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class Phase(Enum):
    IDLE = "idle"
    MOVING = "moving"
    TOP = "top"
    LOWERING = "lowering"


@dataclass
class RepCounter:
    start_threshold: float
    end_threshold: float
    direction: str  # "up" or "down"

    total_reps: int = 0
    valid_reps: int = 0
    phase: Phase = Phase.IDLE

    # Per-rep fault log.
    _faults: list = field(default_factory=list)
    last_faults: list = field(default_factory=list)

    def _at_start(self, metric: float) -> bool:
        if self.direction == "down":
            return metric >= self.start_threshold
        return metric <= self.start_threshold

    def _at_top(self, metric: float) -> bool:
        if self.direction == "down":
            return metric <= self.end_threshold
        return metric >= self.end_threshold

    def _past_start_returning(self, metric: float) -> bool:
        return self._at_start(metric)

    def record_fault(self, message: str):
        if message and message not in self._faults:
            self._faults.append(message)

    def update(self, metric: float, rep_valid: bool = True) -> Optional[str]:
        """
        Feed the current frame's metric value into the state machine.

        rep_valid:
            Optional per-rep validity gate supplied by the exercise logic.
            If False when the rep completes, the rep is marked invalid even if
            there were no recorded form faults.
        """
        event = None

        if self.phase == Phase.IDLE:
            if self._at_start(metric):
                self._faults = []
            else:
                self.phase = Phase.MOVING

        elif self.phase == Phase.MOVING:
            if self._at_top(metric):
                self.phase = Phase.TOP

        elif self.phase == Phase.TOP:
            if not self._at_top(metric):
                self.phase = Phase.LOWERING

        elif self.phase == Phase.LOWERING:
            if self._past_start_returning(metric):
                event = self._complete_rep(rep_valid)

        return event

    def _complete_rep(self, rep_valid: bool = True) -> str:
        self.total_reps += 1

        if not self._faults and rep_valid:
            self.valid_reps += 1
            result = "valid"
        else:
            result = "invalid"

        self.last_faults = list(self._faults)
        self._faults = []
        self.phase = Phase.IDLE
        return result

    @property
    def phase_label(self) -> str:
        return self.phase.value
