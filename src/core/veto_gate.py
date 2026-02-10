from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class VetoDecision:
    vetoed: bool
    reasons: list[str]


class VetoGate:
    def evaluate(self, required_evidence: set[str], available_evidence: set[str]) -> VetoDecision:
        missing = sorted(required_evidence - available_evidence)
        if missing:
            return VetoDecision(vetoed=True, reasons=[f"missing evidence: {item}" for item in missing])
        return VetoDecision(vetoed=False, reasons=[])
