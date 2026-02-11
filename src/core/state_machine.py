from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
from enum import Enum
from typing import Any


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

    def to_dict(self) -> dict[str, str]:
        return {
            "from_phase": self.from_phase.value,
            "to_phase": self.to_phase.value,
            "reason": self.reason,
            "at": self.at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TransitionAudit":
        return cls(
            from_phase=CorePhase(payload["from_phase"]),
            to_phase=CorePhase(payload["to_phase"]),
            reason=str(payload["reason"]),
            at=str(payload["at"]),
        )


class CoreStateMachine:
    def __init__(
        self,
        initial_phase: CorePhase = CorePhase.BOOTSTRAP,
        audits: list[TransitionAudit] | None = None,
    ) -> None:
        self._phase = initial_phase
        self._audits = list(audits or [])

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

    def snapshot(self) -> dict[str, Any]:
        return {
            "phase": self.phase.value,
            "audits": [item.to_dict() for item in self._audits],
        }

    @classmethod
    def from_snapshot(cls, payload: dict[str, Any]) -> "CoreStateMachine":
        phase = CorePhase(str(payload.get("phase", CorePhase.BOOTSTRAP.value)))
        audits_payload = payload.get("audits", [])
        audits = [TransitionAudit.from_dict(item) for item in audits_payload]
        return cls(initial_phase=phase, audits=audits)
