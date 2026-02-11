from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ConsensusVetoPathIntegrationTest(unittest.TestCase):
    def _run_cli(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, "-m", "src.cli.main", *args]
        return subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_consensus_veto_and_success_paths(self) -> None:
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
                "run-consensus-001",
                "--run-root",
                str(run_root),
                "--format",
                "json",
            )
            self.assertEqual(0, start.returncode, msg=start.stderr)

            veto = self._run_cli(
                root,
                "analyze",
                "consensus",
                "--run-id",
                "run-consensus-001",
                "--run-root",
                str(run_root),
                "--required-evidence",
                "trace.captured",
                "--required-evidence",
                "symbol.required",
                "--format",
                "json",
            )
            self.assertEqual(3, veto.returncode, msg=veto.stderr)
            veto_payload = json.loads(veto.stdout)
            self.assertTrue(veto_payload["consensus"]["vetoed"])

            success = self._run_cli(
                root,
                "analyze",
                "consensus",
                "--run-id",
                "run-consensus-001",
                "--run-root",
                str(run_root),
                "--required-evidence",
                "trace.captured",
                "--format",
                "json",
            )
            self.assertEqual(0, success.returncode, msg=success.stderr)
            success_payload = json.loads(success.stdout)
            self.assertFalse(success_payload["consensus"]["vetoed"])
            self.assertTrue(success_payload["consensus"]["winning_claim"])


if __name__ == "__main__":
    unittest.main()
