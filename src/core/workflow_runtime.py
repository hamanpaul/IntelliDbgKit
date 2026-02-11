from __future__ import annotations

from datetime import datetime, UTC
import json
from pathlib import Path
from typing import Any


class WorkflowError(ValueError):
    pass


def _workflow_root() -> Path:
    return Path(__file__).resolve().parents[2] / "specs" / "001-debug-loop" / "workflows"


def list_workflows() -> list[str]:
    root = _workflow_root()
    if not root.exists():
        return []
    workflow_ids: list[str] = []
    for file in sorted(root.glob("*.json")):
        payload = json.loads(file.read_text(encoding="utf-8"))
        workflow_ids.append(str(payload.get("workflow_id", file.stem)))
    return workflow_ids


def load_workflow_definition(workflow_id: str) -> dict[str, Any]:
    root = _workflow_root()
    if not root.exists():
        raise WorkflowError("workflow root not found")
    for file in sorted(root.glob("*.json")):
        payload = json.loads(file.read_text(encoding="utf-8"))
        if payload.get("workflow_id") == workflow_id:
            return payload
    raise WorkflowError(f"workflow not found: {workflow_id}")


def _guard_lookup(definition: dict[str, Any]) -> dict[str, dict[str, str]]:
    guards = definition.get("guards", [])
    table: dict[str, dict[str, str]] = {}
    for item in guards:
        guard_id = str(item.get("guard_id", ""))
        if guard_id:
            table[guard_id] = {
                "expression": str(item.get("expression", "")),
                "reason": str(item.get("reason", "")),
                "on_block": str(item.get("on_block", "halt")),
            }
    return table


def _evaluate_expression(expression: str, evidence: set[str]) -> bool:
    marker = "has_evidence:"
    if not expression.startswith(marker):
        return False
    key = expression[len(marker) :].strip()
    if not key:
        return False
    return key in evidence


def run_workflow(
    definition: dict[str, Any],
    run_id: str,
    evidence: set[str] | None = None,
) -> dict[str, Any]:
    evidence_set = set(evidence or set())
    guards = _guard_lookup(definition)
    started_at = datetime.now(UTC).isoformat()
    workflow_run: dict[str, Any] = {
        "workflow_run_id": f"{run_id}:{definition['workflow_id']}:{started_at}",
        "workflow_id": definition["workflow_id"],
        "run_id": run_id,
        "status": "running",
        "blocked_reason": "",
        "started_at": started_at,
        "finished_at": "",
        "steps": [],
    }

    for step in definition.get("steps", []):
        step_status = "success"
        step_reason = ""
        for guard_id in step.get("guards", []):
            guard = guards.get(guard_id)
            if guard is None:
                step_status = "blocked"
                step_reason = f"guard not found: {guard_id}"
                break
            if not _evaluate_expression(guard["expression"], evidence_set):
                step_status = "blocked"
                step_reason = guard["reason"] or f"guard failed: {guard_id}"
                break

        workflow_run["steps"].append(
            {
                "step_id": step["step_id"],
                "name": step["name"],
                "plugin_ref": step["plugin_ref"],
                "action": step["action"],
                "status": step_status,
                "reason": step_reason,
            }
        )

        if step_status == "blocked":
            workflow_run["status"] = "blocked"
            workflow_run["blocked_reason"] = step_reason
            workflow_run["finished_at"] = datetime.now(UTC).isoformat()
            return workflow_run

    workflow_run["status"] = "success"
    workflow_run["finished_at"] = datetime.now(UTC).isoformat()
    return workflow_run
