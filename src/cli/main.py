from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any

from src.cli.command_registry import ToolRegistryError
from src.cli.command_registry import build_default_registry


TOOL_EXECUTOR = {
    "hlapi.ingest": "src.cli.commands.hlapi_ingest",
    "hlapi.discovery": "src.cli.commands.hlapi_discovery",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="idk", description="IntelliDbgKit CLI")
    subcommands = parser.add_subparsers(dest="command", required=True)

    tools_parser = subcommands.add_parser("tools", help="Tool catalog")
    tools_subcommands = tools_parser.add_subparsers(dest="tools_command", required=True)

    list_parser = tools_subcommands.add_parser("list", help="List registered tools")
    list_parser.add_argument("--format", choices=("text", "json"), default="text")

    show_parser = tools_subcommands.add_parser("show", help="Show tool details")
    show_parser.add_argument("tool_id")
    show_parser.add_argument("--format", choices=("text", "json"), default="text")

    doctor_parser = tools_subcommands.add_parser("doctor", help="Show tool health")
    doctor_parser.add_argument("--format", choices=("text", "json"), default="text")

    exec_parser = tools_subcommands.add_parser("exec", help="Execute registered tool")
    exec_parser.add_argument("tool_id")
    exec_parser.add_argument("tool_args", nargs=argparse.REMAINDER)

    return parser


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _print_tool_list_text(cards: list[dict[str, Any]]) -> None:
    print("tool_id\tstatus\tcategory\taliases")
    for card in cards:
        aliases = ",".join(card["aliases"]) if card["aliases"] else "-"
        print(f"{card['tool_id']}\t{card['status']}\t{card['category']}\t{aliases}")


def _print_tool_show_text(card: dict[str, Any]) -> None:
    print(f"tool_id: {card['tool_id']}")
    print(f"category: {card['category']}")
    print(f"status: {card['status']}")
    print(f"risk_level: {card['risk_level']}")
    print(f"adapter: {card['adapter']}")
    print(f"description: {card['description']}")
    print(f"help_command: {card['help_command']}")
    print(f"input_schema_ref: {card['input_schema_ref'] or '-'}")
    print(f"output_schema_ref: {card['output_schema_ref'] or '-'}")
    aliases = ", ".join(card["aliases"]) if card["aliases"] else "-"
    print(f"aliases: {aliases}")
    print("examples:")
    for example in card["examples"]:
        print(f"  - {example}")
    if card["health_reason"]:
        print(f"health_reason: {card['health_reason']}")


def _print_doctor_text(rows: list[dict[str, str]]) -> None:
    print("tool_id\tstatus\tadapter\trisk_level\thealth_reason")
    for row in rows:
        print(
            f"{row['tool_id']}\t{row['status']}\t{row['adapter']}\t{row['risk_level']}\t{row['health_reason']}"
        )


def _strip_remainder_prefix(tool_args: list[str]) -> list[str]:
    if tool_args and tool_args[0] == "--":
        return tool_args[1:]
    return tool_args


def _execute_tool(tool_id: str, tool_args: list[str]) -> int:
    module_name = TOOL_EXECUTOR.get(tool_id)
    if module_name is None:
        print(f"tool execution is not wired: {tool_id}", file=sys.stderr)
        return 2
    command = [sys.executable, "-m", module_name] + tool_args
    completed = subprocess.run(command, check=False)
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    registry = build_default_registry()

    if args.command != "tools":
        parser.error("unsupported command")

    if args.tools_command == "list":
        cards = [card.to_dict() for card in registry.list_cards()]
        if args.format == "json":
            _print_json(cards)
            return 0
        _print_tool_list_text(cards)
        return 0

    if args.tools_command == "show":
        try:
            card = registry.resolve(args.tool_id).to_dict()
        except ToolRegistryError as error:
            print(str(error), file=sys.stderr)
            return 2
        if args.format == "json":
            _print_json(card)
            return 0
        _print_tool_show_text(card)
        return 0

    if args.tools_command == "doctor":
        rows = registry.doctor()
        if args.format == "json":
            _print_json(rows)
            return 0
        _print_doctor_text(rows)
        return 0

    if args.tools_command == "exec":
        try:
            card = registry.resolve(args.tool_id)
        except ToolRegistryError as error:
            print(str(error), file=sys.stderr)
            return 2
        if card.status == "blocked":
            print(f"tool is blocked: {card.tool_id}", file=sys.stderr)
            return 2
        tool_args = _strip_remainder_prefix(args.tool_args)
        return _execute_tool(card.tool_id, tool_args)

    parser.error("unsupported tools command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
