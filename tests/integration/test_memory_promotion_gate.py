from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from src.memory.memory_store import MemoryStore
from src.memory.promotion_engine import MemoryPromotionEngine


class MemoryPromotionGateIntegrationTest(unittest.TestCase):
    def test_candidate_stays_pending_when_gate_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_root = Path(tmp_dir) / "runs"
            store = MemoryStore(run_root=run_root, run_id="run-test-001")
            candidate = store.create_record(
                memory_tier="candidate",
                content="candidate pending",
                evidence_refs=["e-1"],
                memory_id="candidate-pending",
            )
            engine = MemoryPromotionEngine(threshold=0.8)
            decision, promoted = engine.evaluate_and_apply(
                store=store,
                candidate_memory_id=candidate.memory_id,
                repro_count=1,
                consensus_score=0.95,
                evidence_refs=["e-1"],
            )

            self.assertFalse(decision["approved"])
            self.assertEqual("pending", decision["promotion_target"])
            self.assertIsNone(promoted)
            self.assertFalse(store.list_records(memory_tier="long"))

    def test_candidate_promotes_to_long_when_dual_gate_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_root = Path(tmp_dir) / "runs"
            store = MemoryStore(run_root=run_root, run_id="run-test-002")
            candidate = store.create_record(
                memory_tier="candidate",
                content="candidate approved",
                evidence_refs=["e-2"],
                memory_id="candidate-approved",
            )
            engine = MemoryPromotionEngine(threshold=0.7)
            decision, promoted = engine.evaluate_and_apply(
                store=store,
                candidate_memory_id=candidate.memory_id,
                repro_count=2,
                consensus_score=0.85,
                evidence_refs=["e-2"],
            )

            self.assertTrue(decision["approved"])
            self.assertEqual("long", decision["promotion_target"])
            self.assertIsNotNone(promoted)
            self.assertEqual("candidate-approved", promoted.promoted_from)
            long_records = store.list_records(memory_tier="long")
            self.assertEqual(1, len(long_records))

            link_file = run_root / "run-test-002" / "index" / "long-memory-links.json"
            self.assertTrue(link_file.exists())
            links = json.loads(link_file.read_text(encoding="utf-8"))
            self.assertEqual("candidate-approved", links[0]["candidate_memory_id"])


if __name__ == "__main__":
    unittest.main()
