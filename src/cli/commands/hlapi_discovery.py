from __future__ import annotations

import argparse

from src.ingestion.hlapi_discovery import parse_discovery_lines
from src.ingestion.hlapi_discovery import write_discovery_records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate minimal HLAPI discovery records")
    parser.add_argument("--run-id", required=True, help="Run id")
    parser.add_argument("--target-id", required=True, help="Target board id")
    parser.add_argument("--collector", default="ubus-cli", help="Collector name")
    parser.add_argument("--input", required=True, help="Input text file, one path per line")
    parser.add_argument("--output", required=True, help="Output json file path")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    lines = []
    with open(args.input, "r", encoding="utf-8") as file:
        lines = [line.rstrip("\n") for line in file]
    records = parse_discovery_lines(
        lines=lines,
        run_id=args.run_id,
        target_id=args.target_id,
        collector=args.collector,
    )
    path = write_discovery_records(records, args.output)
    print(f"records={len(records)}")
    print(f"output={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
