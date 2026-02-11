from __future__ import annotations

import unittest

from src.core.workflow_runtime import list_workflows
from src.core.workflow_runtime import load_workflow_definition
from src.core.workflow_runtime import run_workflow


class WorkflowRuntimeTest(unittest.TestCase):
    def test_list_workflows_contains_trace_capture(self) -> None:
        workflow_ids = list_workflows()
        self.assertIn("trace-capture-flow", workflow_ids)

    def test_run_root_cause_workflow_blocked_without_evidence(self) -> None:
        definition = load_workflow_definition("root-cause-flow")
        output = run_workflow(definition=definition, run_id="run-test-001", evidence=set())
        self.assertEqual("blocked", output["status"])
        self.assertIn("missing evidence", output["blocked_reason"])

    def test_run_root_cause_workflow_success_with_evidence(self) -> None:
        definition = load_workflow_definition("root-cause-flow")
        output = run_workflow(
            definition=definition,
            run_id="run-test-001",
            evidence={"trace.captured"},
        )
        self.assertEqual("success", output["status"])
        self.assertEqual("", output["blocked_reason"])


if __name__ == "__main__":
    unittest.main()
