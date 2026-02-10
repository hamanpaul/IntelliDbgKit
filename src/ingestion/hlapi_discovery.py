from __future__ import annotations

from datetime import datetime, UTC
import json
from pathlib import Path
from typing import Any


def _access_mode(raw: str) -> str:
    text = raw.strip().lower()
    if text in {"rw", "wr"}:
        return "rw"
    if text in {"r", "read"}:
        return "read"
    if text in {"w", "write"}:
        return "write"
    return "read"


def _support_state(access_mode: str) -> str:
    if access_mode in {"read", "write", "rw"}:
        return "supported"
    return "unknown"


def parse_discovery_lines(
    lines: list[str],
    run_id: str,
    target_id: str,
    collector: str = "ubus-cli",
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        object_path = parts[0]
        mode = _access_mode(parts[1] if len(parts) > 1 else "read")
        parameter_name = object_path.split(".")[-1] if "." in object_path else ""

        record = {
            "discovery_id": f"discovery-{run_id}-{index}",
            "run_id": run_id,
            "target_id": target_id,
            "collected_at": datetime.now(UTC).isoformat(),
            "collector": collector,
            "object_path": object_path,
            "parameter_name": parameter_name,
            "access_mode": mode,
            "probe_command": f"discovery probe {object_path}",
            "support_state": _support_state(mode),
            "evidence_refs": [f"discovery-line-{index}"],
        }
        records.append(record)
    return records


def write_discovery_records(records: list[dict[str, Any]], output_file: str | Path) -> Path:
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
