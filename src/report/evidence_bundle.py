from __future__ import annotations

from datetime import datetime, UTC
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                count += 1
    return count


def build_evidence_bundle(run_root: Path, run_id: str) -> dict[str, Any]:
    run_dir = run_root / run_id
    run_meta_file = run_dir / "index" / "run.json"
    run_meta = _read_json(run_meta_file) if run_meta_file.exists() else {}

    workflow_dir = run_dir / "workflows"
    workflow_files = sorted(file.name for file in workflow_dir.glob("*.json")) if workflow_dir.exists() else []

    consensus_file = run_dir / "index" / "consensus.json"
    consensus_records = _read_json(consensus_file) if consensus_file.exists() else []

    bundle = {
        "bundle_id": f"bundle-{run_id}",
        "run_id": run_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "project_name": run_meta.get("project_name", ""),
        "target_id": run_meta.get("target_id", ""),
        "state": run_meta.get("state", ""),
        "event_count": _count_jsonl(run_dir / "assets" / "events.raw.jsonl"),
        "workflow_runs": workflow_files,
        "consensus_count": len(consensus_records),
        "auto_merge": False,
        "merge_policy": "manual-review-only",
    }
    return bundle


def write_evidence_bundle(run_root: Path, run_id: str, payload: dict[str, Any]) -> Path:
    output = run_root / run_id / "index" / "evidence-bundle.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
