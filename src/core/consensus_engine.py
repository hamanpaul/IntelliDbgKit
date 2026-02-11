from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any
from uuid import uuid4

from src.core.veto_gate import VetoGate


@dataclass(frozen=True, slots=True)
class ConsensusInput:
    agent_id: str
    claim: str
    confidence: float
    evidence_refs: tuple[str, ...]


class ConsensusEngine:
    def __init__(self) -> None:
        self._veto_gate = VetoGate()

    def evaluate(
        self,
        run_id: str,
        topic: str,
        agent_results: list[dict[str, Any]],
        required_evidence: set[str],
    ) -> dict[str, Any]:
        normalized: list[ConsensusInput] = []
        for item in agent_results:
            normalized.append(
                ConsensusInput(
                    agent_id=str(item["agent_id"]),
                    claim=str(item["claim"]),
                    confidence=float(item["confidence"]),
                    evidence_refs=tuple(str(ref) for ref in item.get("evidence_refs", [])),
                )
            )

        available_evidence: set[str] = set()
        for item in normalized:
            available_evidence.update(item.evidence_refs)

        veto = self._veto_gate.evaluate(required_evidence=required_evidence, available_evidence=available_evidence)
        consensus_id = f"consensus-{uuid4().hex[:12]}"
        base_payload: dict[str, Any] = {
            "consensus_id": consensus_id,
            "run_id": run_id,
            "topic": topic,
            "winning_claim": "",
            "weighted_score": 0.0,
            "evidence_refs": sorted(available_evidence),
            "dissenting_claims": [],
            "vetoed": veto.vetoed,
            "veto_reasons": [],
            "evaluated_at": datetime.now(UTC).isoformat(),
        }

        if veto.vetoed:
            base_payload["veto_reasons"] = [
                {
                    "code": "missing-evidence",
                    "message": reason,
                    "required_evidence": sorted(required_evidence),
                }
                for reason in veto.reasons
            ]
            return base_payload

        claim_scores: dict[str, float] = {}
        claim_evidence: dict[str, set[str]] = {}
        for item in normalized:
            claim_scores[item.claim] = claim_scores.get(item.claim, 0.0) + item.confidence
            claim_evidence.setdefault(item.claim, set()).update(item.evidence_refs)

        sorted_claims = sorted(claim_scores.items(), key=lambda pair: pair[1], reverse=True)
        winning_claim, winning_score = sorted_claims[0]
        dissenting = [
            {"claim": claim, "score": score, "evidence_refs": sorted(claim_evidence.get(claim, set()))}
            for claim, score in sorted_claims[1:]
        ]

        base_payload["winning_claim"] = winning_claim
        base_payload["weighted_score"] = winning_score
        base_payload["dissenting_claims"] = dissenting
        return base_payload
