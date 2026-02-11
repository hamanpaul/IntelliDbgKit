from __future__ import annotations

import json
from pathlib import Path
import unittest


class WorkflowDefinitionsContractTest(unittest.TestCase):
    def test_workflow_json_files_follow_minimal_schema_contract(self) -> None:
        root = Path(__file__).resolve().parents[2]
        schema_file = root / "specs" / "001-debug-loop" / "contracts" / "workflow.schema.json"
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        required_fields = set(schema["required"])
        workflow_dir = root / "specs" / "001-debug-loop" / "workflows"
        workflow_files = sorted(workflow_dir.glob("*.json"))
        self.assertTrue(workflow_files)

        for workflow_file in workflow_files:
            payload = json.loads(workflow_file.read_text(encoding="utf-8"))
            missing = required_fields - set(payload.keys())
            self.assertFalse(missing, msg=f"{workflow_file.name} missing {sorted(missing)}")
            self.assertEqual("event-bus-only", payload["core_boundary_policy"])
            self.assertTrue(payload["steps"])
            self.assertTrue(payload["outputs"])


if __name__ == "__main__":
    unittest.main()
