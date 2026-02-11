from __future__ import annotations

from datetime import datetime, UTC
import json
from pathlib import Path
from typing import Any
from uuid import uuid4


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_patch_proposal(run_root: Path, run_id: str) -> dict[str, Any]:
    run_dir = run_root / run_id
    consensus_file = run_dir / "index" / "consensus.json"
    consensus_records = _read_json(consensus_file) if consensus_file.exists() else []

    latest_non_veto = None
    for item in reversed(consensus_records):
        if not item.get("vetoed", False):
            latest_non_veto = item
            break

    if latest_non_veto is None:
        return {
            "proposal_id": f"proposal-{uuid4().hex[:12]}",
            "run_id": run_id,
            "summary": "insufficient consensus evidence",
            "diff_preview": "",
            "related_consensus": "",
            "risk_level": "high",
            "evidence_min_set": [],
            "merge_policy": "manual-review-only",
            "auto_merge": False,
            "status": "blocked",
            "generated_at": datetime.now(UTC).isoformat(),
        }

    claim = str(latest_non_veto.get("winning_claim", ""))
    return {
        "proposal_id": f"proposal-{uuid4().hex[:12]}",
        "run_id": run_id,
        "summary": f"proposed fix for: {claim}",
        "diff_preview": "TODO: generate patch diff from analyzer output",
        "related_consensus": latest_non_veto.get("consensus_id", ""),
        "risk_level": "medium",
        "evidence_min_set": latest_non_veto.get("evidence_refs", []),
        "merge_policy": "manual-review-only",
        "auto_merge": False,
        "status": "ready",
        "generated_at": datetime.now(UTC).isoformat(),
    }


def write_patch_proposal(run_root: Path, run_id: str, payload: dict[str, Any]) -> Path:
    output = run_root / run_id / "index" / "patch-proposal.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
