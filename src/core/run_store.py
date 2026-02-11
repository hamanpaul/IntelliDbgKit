from __future__ import annotations

from datetime import datetime, UTC
import json
from pathlib import Path
from time import time_ns
from typing import Any

from src.core.event_bus import EventBus
from src.core.state_machine import CorePhase
from src.core.state_machine import CoreStateMachine


class RunStoreError(ValueError):
    pass


def default_run_root(base: Path | None = None) -> Path:
    root = (base or Path.cwd()) / "tmp" / "runs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _run_id_now() -> str:
    return datetime.now(UTC).strftime("run-%Y%m%d-%H%M%S")


def _run_dir(run_root: Path, run_id: str) -> Path:
    return run_root / run_id


def _run_meta_path(run_root: Path, run_id: str) -> Path:
    return _run_dir(run_root, run_id) / "index" / "run.json"


def _events_path(run_root: Path, run_id: str) -> Path:
    return _run_dir(run_root, run_id) / "assets" / "events.raw.jsonl"


def run_events_path(run_root: Path, run_id: str) -> Path:
    return _events_path(run_root, run_id)


def _ensure_layout(run_root: Path, run_id: str) -> Path:
    run_dir = _run_dir(run_root, run_id)
    (run_dir / "index").mkdir(parents=True, exist_ok=True)
    (run_dir / "assets").mkdir(parents=True, exist_ok=True)
    (run_dir / "workflows").mkdir(parents=True, exist_ok=True)
    return run_dir


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_event(path: Path, event: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False))
        file.write("\n")


def create_run(
    project_name: str,
    target_id: str,
    run_root: Path,
    run_id: str = "",
    trigger: str = "manual",
) -> dict[str, Any]:
    resolved_run_id = run_id or _run_id_now()
    run_dir = _ensure_layout(run_root, resolved_run_id)
    run_meta_file = _run_meta_path(run_root, resolved_run_id)
    if run_meta_file.exists():
        raise RunStoreError(f"run already exists: {resolved_run_id}")

    machine = CoreStateMachine()
    started_at = datetime.now(UTC).isoformat()
    payload: dict[str, Any] = {
        "run_id": resolved_run_id,
        "project_name": project_name,
        "target_id": target_id,
        "started_at": started_at,
        "finished_at": "",
        "state": machine.phase.value,
        "trigger": trigger,
        "summary_note": "",
        "core_state": machine.snapshot(),
    }
    _write_json(run_meta_file, payload)

    event_bus = EventBus()
    bootstrap_event = {
        "event_id": f"{resolved_run_id}-e1",
        "run_id": resolved_run_id,
        "ts_ns": time_ns(),
        "phase": machine.phase.value,
        "source": "host",
        "tool": "idk.run",
        "target_id": target_id,
        "severity": "info",
        "payload": {
            "action": "run.start",
            "project_name": project_name,
            "run_dir": str(run_dir),
        },
    }
    event_bus.publish(bootstrap_event)
    _append_event(_events_path(run_root, resolved_run_id), bootstrap_event)
    return payload


def load_run(run_root: Path, run_id: str) -> dict[str, Any]:
    path = _run_meta_path(run_root, run_id)
    if not path.exists():
        raise RunStoreError(f"run not found: {run_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_run(run_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    run_id = str(payload.get("run_id", ""))
    if not run_id:
        raise RunStoreError("run_id is required")
    _ensure_layout(run_root, run_id)
    _write_json(_run_meta_path(run_root, run_id), payload)
    return payload


def run_event_count(run_root: Path, run_id: str) -> int:
    path = _events_path(run_root, run_id)
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                count += 1
    return count


def transition_run(
    run_root: Path,
    run_id: str,
    to_phase: CorePhase,
    reason: str,
) -> dict[str, Any]:
    payload = load_run(run_root, run_id)
    snapshot = payload.get("core_state", {})
    machine = CoreStateMachine.from_snapshot(snapshot)
    audit = machine.transition(to_phase=to_phase, reason=reason)
    payload["state"] = machine.phase.value
    payload["core_state"] = machine.snapshot()
    if to_phase == CorePhase.REPORT and not payload.get("finished_at"):
        payload["finished_at"] = datetime.now(UTC).isoformat()
    save_run(run_root, payload)

    event_bus = EventBus()
    transition_event = {
        "event_id": f"{run_id}-e{run_event_count(run_root, run_id) + 1}",
        "run_id": run_id,
        "ts_ns": time_ns(),
        "phase": machine.phase.value,
        "source": "host",
        "tool": "idk.run",
        "target_id": payload["target_id"],
        "severity": "info",
        "payload": {
            "action": "run.transition",
            "from_phase": audit.from_phase.value,
            "to_phase": audit.to_phase.value,
            "reason": reason,
        },
    }
    event_bus.publish(transition_event)
    _append_event(_events_path(run_root, run_id), transition_event)
    return payload


def append_workflow_record(
    run_root: Path,
    run_id: str,
    workflow_run: dict[str, Any],
) -> Path:
    run_dir = _ensure_layout(run_root, run_id)
    workflow_dir = run_dir / "workflows"
    started_at = str(workflow_run.get("started_at", ""))
    token = started_at.replace(":", "").replace("-", "").replace(".", "")
    workflow_id = str(workflow_run.get("workflow_id", "workflow"))
    filename = f"{token}-{workflow_id}.json"
    output = workflow_dir / filename
    output.write_text(json.dumps(workflow_run, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def append_consensus_record(
    run_root: Path,
    run_id: str,
    consensus_payload: dict[str, Any],
) -> Path:
    run_dir = _ensure_layout(run_root, run_id)
    output = run_dir / "index" / "consensus.json"
    payload: list[dict[str, Any]] = []
    if output.exists():
        payload = json.loads(output.read_text(encoding="utf-8"))
    payload.append(consensus_payload)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
