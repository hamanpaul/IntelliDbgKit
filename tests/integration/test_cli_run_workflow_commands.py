from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CliRunWorkflowCommandsTest(unittest.TestCase):
    def _run_cli(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, "-m", "src.cli.main", *args]
        return subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_run_lifecycle_and_workflow(self) -> None:
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_root = Path(tmp_dir) / "runs"

            start = self._run_cli(
                root,
                "run",
                "start",
                "--project",
                "IntelliDbgKit",
                "--target",
                "board-01",
                "--run-id",
                "run-cli-001",
                "--run-root",
                str(run_root),
                "--format",
                "json",
            )
            self.assertEqual(0, start.returncode, msg=start.stderr)
            start_payload = json.loads(start.stdout)
            self.assertEqual("run-cli-001", start_payload["run"]["run_id"])
            self.assertEqual("BOOTSTRAP", start_payload["run"]["state"])

            status = self._run_cli(
                root,
                "run",
                "status",
                "--run-id",
                "run-cli-001",
                "--run-root",
                str(run_root),
                "--format",
                "json",
            )
            self.assertEqual(0, status.returncode, msg=status.stderr)
            status_payload = json.loads(status.stdout)
            self.assertGreaterEqual(status_payload["event_count"], 1)

            workflows = self._run_cli(root, "workflow", "list", "--format", "json")
            self.assertEqual(0, workflows.returncode, msg=workflows.stderr)
            workflow_payload = json.loads(workflows.stdout)
            self.assertIn("trace-capture-flow", workflow_payload["workflows"])

            blocked = self._run_cli(
                root,
                "workflow",
                "run",
                "root-cause-flow",
                "--run-id",
                "run-cli-001",
                "--run-root",
                str(run_root),
                "--format",
                "json",
            )
            self.assertEqual(3, blocked.returncode, msg=blocked.stderr)
            blocked_payload = json.loads(blocked.stdout)
            self.assertEqual("blocked", blocked_payload["workflow_run"]["status"])

            success = self._run_cli(
                root,
                "workflow",
                "run",
                "root-cause-flow",
                "--run-id",
                "run-cli-001",
                "--run-root",
                str(run_root),
                "--evidence",
                "trace.captured",
                "--format",
                "json",
            )
            self.assertEqual(0, success.returncode, msg=success.stderr)
            success_payload = json.loads(success.stdout)
            self.assertEqual("success", success_payload["workflow_run"]["status"])

            verify = self._run_cli(
                root,
                "verify",
                "compression",
                "--run-id",
                "run-cli-001",
                "--run-root",
                str(run_root),
                "--roundtrip",
                "--format",
                "json",
            )
            self.assertEqual(0, verify.returncode, msg=verify.stderr)
            verify_payload = json.loads(verify.stdout)
            self.assertTrue(verify_payload["compression"]["roundtrip_ok"])

            stop = self._run_cli(
                root,
                "run",
                "stop",
                "--run-id",
                "run-cli-001",
                "--run-root",
                str(run_root),
                "--reason",
                "integration stop",
                "--format",
                "json",
            )
            self.assertEqual(0, stop.returncode, msg=stop.stderr)
            stop_payload = json.loads(stop.stdout)
            self.assertEqual("REPORT", stop_payload["run"]["state"])


if __name__ == "__main__":
    unittest.main()
