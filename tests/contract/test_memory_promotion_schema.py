from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from src.memory.memory_store import MemoryStore
from src.memory.promotion_engine import MemoryPromotionEngine


class MemoryPromotionSchemaContractTest(unittest.TestCase):
    def test_decision_payload_matches_required_fields(self) -> None:
        root = Path(__file__).resolve().parents[2]
        schema_file = root / "specs" / "001-debug-loop" / "contracts" / "memory-promotion.schema.json"
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        required_fields = set(schema["required"])

        with tempfile.TemporaryDirectory() as tmp_dir:
            run_root = Path(tmp_dir) / "runs"
            store = MemoryStore(run_root=run_root, run_id="run-test-001")
            candidate = store.create_record(
                memory_tier="candidate",
                content="candidate content",
                evidence_refs=["e-1"],
                memory_id="candidate-001",
            )
            engine = MemoryPromotionEngine(threshold=0.7)
            decision, _ = engine.evaluate_and_apply(
                store=store,
                candidate_memory_id=candidate.memory_id,
                repro_count=2,
                consensus_score=0.9,
                evidence_refs=["e-1"],
            )

            missing = required_fields - set(decision.keys())
            self.assertFalse(missing)
            self.assertTrue(decision["approved"])
            self.assertEqual("long", decision["promotion_target"])
            self.assertTrue(decision["gate_checks"]["repro_gate_passed"])
            self.assertTrue(decision["gate_checks"]["consensus_gate_passed"])


if __name__ == "__main__":
    unittest.main()
