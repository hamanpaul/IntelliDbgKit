from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from src.core.run_store import create_run
from src.core.run_store import load_run
from src.core.run_store import run_event_count
from src.core.run_store import transition_run
from src.core.state_machine import CorePhase


class RunStoreTest(unittest.TestCase):
    def test_create_and_transition_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_root = Path(tmp_dir) / "runs"
            run_payload = create_run(
                project_name="IntelliDbgKit",
                target_id="board-01",
                run_root=run_root,
                run_id="run-test-001",
            )
            self.assertEqual("run-test-001", run_payload["run_id"])
            self.assertEqual("BOOTSTRAP", run_payload["state"])
            self.assertEqual(1, run_event_count(run_root, "run-test-001"))

            updated_payload = transition_run(
                run_root=run_root,
                run_id="run-test-001",
                to_phase=CorePhase.REPORT,
                reason="unit stop",
            )
            self.assertEqual("REPORT", updated_payload["state"])
            self.assertTrue(updated_payload["finished_at"])

            loaded_payload = load_run(run_root=run_root, run_id="run-test-001")
            self.assertEqual("REPORT", loaded_payload["state"])
            self.assertGreaterEqual(run_event_count(run_root, "run-test-001"), 2)


if __name__ == "__main__":
    unittest.main()
