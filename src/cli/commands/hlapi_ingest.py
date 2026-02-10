from __future__ import annotations

import argparse
from datetime import datetime, UTC

from src.ingestion.hlapi_writer import write_hlapi_obsidian
from src.ingestion.xlsx_loader import load_hlapi_testcases


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import HLAPI XLSX and write Obsidian artifacts")
    parser.add_argument("--source", required=True, help="Path to HLAPI xlsx file")
    parser.add_argument("--vault", required=True, help="Obsidian vault root directory")
    parser.add_argument("--project", required=True, help="Project name under vault")
    parser.add_argument("--run-id", default="", help="Run id; default generated")
    parser.add_argument("--start-sheet", default="QoS_LLAPI", help="Start sheet name")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    run_id = args.run_id or datetime.now(UTC).strftime("run-%Y%m%d-%H%M%S")

    testcases = load_hlapi_testcases(args.source, start_sheet=args.start_sheet)
    output = write_hlapi_obsidian(
        testcases=testcases,
        vault_root=args.vault,
        project=args.project,
        run_id=run_id,
        source_file=args.source,
    )
    print(f"run_id={output['run_id']}")
    print(f"testcase_count={output['testcase_count']}")
    print(f"output_root={output['output_root']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
