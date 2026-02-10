from __future__ import annotations

from collections import Counter
from collections import defaultdict
import json
from pathlib import Path
import re
import shutil
from typing import Any


SENSITIVE_PATTERN = re.compile(
    r"(?i)(password|passwd|token|secret|key)\s*[:=]\s*([^\s,;]+)"
)


def _mask_text(value: str) -> str:
    if not isinstance(value, str):
        return value
    return SENSITIVE_PATTERN.sub(r"\1=***", value)


def _masked_case(record: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, str):
            output[key] = _mask_text(value)
            continue
        if isinstance(value, list):
            output[key] = [_mask_text(item) if isinstance(item, str) else item for item in value]
            continue
        output[key] = value
    return output


def _ensure_dirs(base: Path) -> dict[str, Path]:
    paths = {
        "notes_testcases": base / "notes" / "testcases",
        "notes_rootcause": base / "notes" / "root-cause",
        "notes_patch": base / "notes" / "patch-proposal",
        "assets_raw": base / "assets" / "raw",
        "assets_logs": base / "assets" / "logs",
        "index": base / "index",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def _sheet_markdown(sheet: str, records: list[dict[str, Any]]) -> str:
    lines = [
        f"# {sheet}",
        "",
        f"- case_count: {len(records)}",
        "- backlinks:",
        "  - [[../run-summary]]",
        "  - [[../trace-index]]",
        "",
        "| case_id | object_path | parameter_name | hlapi_command | llapi_support | result_status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in records:
        lines.append(
            "| {case_id} | {object_path} | {parameter_name} | {hlapi_command} | {llapi_support} | {result_status} |".format(
                case_id=row.get("case_id", ""),
                object_path=row.get("object_path", ""),
                parameter_name=row.get("parameter_name", ""),
                hlapi_command=row.get("hlapi_command", ""),
                llapi_support=row.get("llapi_support", ""),
                result_status=row.get("result_status", ""),
            )
        )
    lines.extend(["", "## Case Links", ""])
    for row in records:
        lines.append(
            f"- {row.get('case_id', '')}: [[../run-summary]] [[../trace-index]] [[../root-cause/{row.get('case_id', '')}]] [[../patch-proposal/{row.get('case_id', '')}]]"
        )
    lines.append("")
    return "\n".join(lines)


def write_hlapi_obsidian(
    testcases: list[dict[str, Any]],
    vault_root: str | Path,
    project: str,
    run_id: str,
    source_file: str | Path,
) -> dict[str, Any]:
    base = Path(vault_root) / project / run_id
    dirs = _ensure_dirs(base)

    masked_cases = [_masked_case(case) for case in testcases]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in masked_cases:
        grouped[case["source_sheet"]].append(case)

    for sheet, rows in grouped.items():
        markdown = _sheet_markdown(sheet, rows)
        output_file = dirs["notes_testcases"] / f"{sheet}.md"
        output_file.write_text(markdown, encoding="utf-8")

    source_path = Path(source_file)
    if source_path.exists():
        destination = dirs["assets_raw"] / source_path.name
        shutil.copy2(source_path, destination)

    status_counter = Counter(case.get("result_status", "unknown") for case in masked_cases)
    run_summary = "\n".join(
        [
            "# run-summary",
            "",
            f"- run_id: {run_id}",
            f"- testcase_count: {len(masked_cases)}",
            f"- pass: {status_counter.get('pass', 0)}",
            f"- fail: {status_counter.get('fail', 0)}",
            f"- not-supported: {status_counter.get('not-supported', 0)}",
            f"- skip: {status_counter.get('skip', 0)}",
            f"- unknown: {status_counter.get('unknown', 0)}",
        ]
    )
    (base / "notes" / "run-summary.md").write_text(run_summary, encoding="utf-8")

    trace_index = "\n".join(
        [
            "# trace-index",
            "",
            f"- run_id: {run_id}",
            "- query: case_id -> trace events",
            "",
        ]
    )
    (base / "notes" / "trace-index.md").write_text(trace_index, encoding="utf-8")

    lineage = [
        {
            "case_id": case["case_id"],
            "source_file": case["source_file"],
            "source_sheet": case["source_sheet"],
            "source_row": case["source_row"],
        }
        for case in masked_cases
    ]
    (dirs["index"] / "hlapi-testcases.json").write_text(
        json.dumps(masked_cases, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (dirs["index"] / "lineage.json").write_text(
        json.dumps(lineage, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    run_meta = {
        "run_id": run_id,
        "project": project,
        "testcase_count": len(masked_cases),
        "source_file": str(source_path),
    }
    (dirs["index"] / "run.json").write_text(
        json.dumps(run_meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "run_id": run_id,
        "output_root": str(base),
        "testcase_count": len(masked_cases),
        "sheets": sorted(grouped.keys()),
    }
