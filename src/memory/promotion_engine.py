from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any
from uuid import uuid4

from src.memory.memory_store import MemoryRecord
from src.memory.memory_store import MemoryStore
from src.memory.memory_store import MemoryStoreError


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    decision_id: str
    candidate_memory_id: str
    run_id: str
    repro_count: int
    consensus_score: float
    threshold: float
    approved: bool
    promotion_target: str
    gate_checks: dict[str, bool]
    reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    evaluated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "candidate_memory_id": self.candidate_memory_id,
            "run_id": self.run_id,
            "repro_count": self.repro_count,
            "consensus_score": self.consensus_score,
            "threshold": self.threshold,
            "approved": self.approved,
            "promotion_target": self.promotion_target,
            "gate_checks": dict(self.gate_checks),
            "reasons": list(self.reasons),
            "evidence_refs": list(self.evidence_refs),
            "evaluated_at": self.evaluated_at,
        }


class MemoryPromotionEngine:
    def __init__(self, threshold: float = 0.7) -> None:
        self.threshold = threshold

    def _gate_checks(self, repro_count: int, consensus_score: float, threshold: float) -> dict[str, bool]:
        return {
            "repro_gate_passed": repro_count >= 2,
            "consensus_gate_passed": consensus_score >= threshold,
        }

    def evaluate(
        self,
        run_id: str,
        candidate_memory_id: str,
        repro_count: int,
        consensus_score: float,
        threshold: float | None = None,
        evidence_refs: tuple[str, ...] | list[str] = (),
    ) -> PromotionDecision:
        resolved_threshold = self.threshold if threshold is None else threshold
        checks = self._gate_checks(repro_count, consensus_score, resolved_threshold)
        approved = checks["repro_gate_passed"] and checks["consensus_gate_passed"]
        reasons: list[str] = []
        if checks["repro_gate_passed"]:
            reasons.append("repro gate passed")
        else:
            reasons.append("repro gate failed: repro_count < 2")
        if checks["consensus_gate_passed"]:
            reasons.append("consensus gate passed")
        else:
            reasons.append("consensus gate failed: score below threshold")
        if approved:
            reasons.append("promotion approved")
        else:
            reasons.append("promotion pending")

        return PromotionDecision(
            decision_id=f"decision-{uuid4().hex[:12]}",
            candidate_memory_id=candidate_memory_id,
            run_id=run_id,
            repro_count=repro_count,
            consensus_score=consensus_score,
            threshold=resolved_threshold,
            approved=approved,
            promotion_target="long" if approved else "pending",
            gate_checks=checks,
            reasons=tuple(reasons),
            evidence_refs=tuple(evidence_refs),
            evaluated_at=datetime.now(UTC).isoformat(),
        )

    def evaluate_and_apply(
        self,
        store: MemoryStore,
        candidate_memory_id: str,
        repro_count: int,
        consensus_score: float,
        threshold: float | None = None,
        evidence_refs: tuple[str, ...] | list[str] = (),
    ) -> tuple[dict[str, Any], MemoryRecord | None]:
        candidate = store.get_record(candidate_memory_id)
        if candidate.memory_tier != "candidate":
            raise MemoryStoreError("promotion target must be candidate tier")
        decision = self.evaluate(
            run_id=store.run_id,
            candidate_memory_id=candidate_memory_id,
            repro_count=repro_count,
            consensus_score=consensus_score,
            threshold=threshold,
            evidence_refs=evidence_refs,
        )
        decision_payload = decision.to_dict()
        store.append_promotion_decision(decision_payload)
        if not decision.approved:
            return decision_payload, None
        promoted = store.promote_candidate_to_long(candidate_memory_id)
        return decision_payload, promoted
