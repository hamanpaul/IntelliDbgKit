from __future__ import annotations

import unittest

from src.core.consensus_engine import ConsensusEngine


class ConsensusScoringUnitTest(unittest.TestCase):
    def test_selects_highest_weighted_claim(self) -> None:
        engine = ConsensusEngine()
        payload = engine.evaluate(
            run_id="run-test-001",
            topic="root-cause",
            agent_results=[
                {
                    "agent_id": "a1",
                    "claim": "claim-A",
                    "confidence": 0.8,
                    "evidence_refs": ["trace.captured"],
                },
                {
                    "agent_id": "a2",
                    "claim": "claim-A",
                    "confidence": 0.7,
                    "evidence_refs": ["trace.captured"],
                },
                {
                    "agent_id": "a3",
                    "claim": "claim-B",
                    "confidence": 0.9,
                    "evidence_refs": ["trace.captured"],
                },
            ],
            required_evidence={"trace.captured"},
        )
        self.assertFalse(payload["vetoed"])
        self.assertEqual("claim-A", payload["winning_claim"])
        self.assertGreater(payload["weighted_score"], 1.0)
        self.assertTrue(payload["dissenting_claims"])


if __name__ == "__main__":
    unittest.main()
