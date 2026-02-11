from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CiDeliveryPolicyIntegrationTest(unittest.TestCase):
    def _run_cli(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, "-m", "src.cli.main", *args]
        return subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_evidence_bundle_and_patch_proposal_keep_manual_merge_policy(self) -> None:
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
                "run-ci-001",
                "--run-root",
                str(run_root),
                "--format",
                "json",
            )
            self.assertEqual(0, start.returncode, msg=start.stderr)

            consensus = self._run_cli(
                root,
                "analyze",
                "consensus",
                "--run-id",
                "run-ci-001",
                "--run-root",
                str(run_root),
                "--required-evidence",
                "trace.captured",
                "--format",
                "json",
            )
            self.assertEqual(0, consensus.returncode, msg=consensus.stderr)

            evidence = self._run_cli(
                root,
                "report",
                "evidence-bundle",
                "--run-id",
                "run-ci-001",
                "--run-root",
                str(run_root),
                "--format",
                "json",
            )
            self.assertEqual(0, evidence.returncode, msg=evidence.stderr)
            evidence_payload = json.loads(evidence.stdout)
            self.assertFalse(evidence_payload["evidence_bundle"]["auto_merge"])
            self.assertEqual("manual-review-only", evidence_payload["evidence_bundle"]["merge_policy"])

            patch = self._run_cli(
                root,
                "patch",
                "suggest",
                "--run-id",
                "run-ci-001",
                "--run-root",
                str(run_root),
                "--format",
                "json",
            )
            self.assertEqual(0, patch.returncode, msg=patch.stderr)
            patch_payload = json.loads(patch.stdout)
            self.assertFalse(patch_payload["patch_proposal"]["auto_merge"])
            self.assertEqual("manual-review-only", patch_payload["patch_proposal"]["merge_policy"])


if __name__ == "__main__":
    unittest.main()
