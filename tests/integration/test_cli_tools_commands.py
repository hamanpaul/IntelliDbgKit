from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


class CliToolsCommandsTest(unittest.TestCase):
    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        root = Path(__file__).resolve().parents[2]
        command = [sys.executable, "-m", "src.cli.main", *args]
        return subprocess.run(
            command,
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_tools_list_json(self) -> None:
        result = self._run_cli("tools", "list", "--format", "json")
        self.assertEqual(0, result.returncode, msg=result.stderr)
        payload = json.loads(result.stdout)
        tool_ids = {item["tool_id"] for item in payload}
        self.assertIn("hlapi.ingest", tool_ids)
        self.assertIn("hlapi.discovery", tool_ids)

    def test_tools_show_accepts_alias(self) -> None:
        result = self._run_cli("tools", "show", "ingest", "--format", "json")
        self.assertEqual(0, result.returncode, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("hlapi.ingest", payload["tool_id"])
        self.assertTrue(payload["examples"])

    def test_tools_exec_forwards_help_argument(self) -> None:
        result = self._run_cli("tools", "exec", "hlapi.discovery", "--", "--help")
        self.assertEqual(0, result.returncode, msg=result.stderr)
        self.assertIn("Generate minimal HLAPI discovery records", result.stdout)

    def test_tools_show_unknown_tool_returns_error(self) -> None:
        result = self._run_cli("tools", "show", "unknown.tool")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("unknown tool", result.stderr)


if __name__ == "__main__":
    unittest.main()
