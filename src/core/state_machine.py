from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
from enum import Enum


class CorePhase(str, Enum):
    BOOTSTRAP = "BOOTSTRAP"
    TEST_LOOP = "TEST_LOOP"
    MONITOR = "MONITOR"
    DETECT = "DETECT"
    CONDITION_ANALYSIS = "CONDITION_ANALYSIS"
    REPRODUCE = "REPRODUCE"
    DEBUG_ON = "DEBUG_ON"
    ANALYZE = "ANALYZE"
    ADV_TOOL_DECISION = "ADV_TOOL_DECISION"
    AUTO_ACTION = "AUTO_ACTION"
    REPRO_TRACE = "REPRO_TRACE"
    RUNTIME_PATCH_TEST = "RUNTIME_PATCH_TEST"
    REPORT = "REPORT"
    FAILED = "FAILED"


@dataclass(slots=True)
class TransitionAudit:
    from_phase: CorePhase
    to_phase: CorePhase
    reason: str
    at: str


class CoreStateMachine:
    def __init__(self) -> None:
        self._phase = CorePhase.BOOTSTRAP
        self._audits: list[TransitionAudit] = []

    @property
    def phase(self) -> CorePhase:
        return self._phase

    @property
    def audits(self) -> list[TransitionAudit]:
        return list(self._audits)

    def transition(self, to_phase: CorePhase, reason: str) -> TransitionAudit:
        record = TransitionAudit(
            from_phase=self._phase,
            to_phase=to_phase,
            reason=reason,
            at=datetime.now(UTC).isoformat(),
        )
        self._phase = to_phase
        self._audits.append(record)
        return record
