from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from src.cli.command_registry import ToolRegistryError
from src.cli.command_registry import build_default_registry
from src.core.agent_dispatcher import AgentDispatcher
from src.core.agent_dispatcher import AgentDispatcherError
from src.core.consensus_engine import ConsensusEngine
from src.core.run_store import RunStoreError
from src.core.run_store import append_consensus_record
from src.core.run_store import append_workflow_record
from src.core.run_store import create_run
from src.core.run_store import default_run_root
from src.core.run_store import load_run
from src.core.run_store import run_event_count
from src.core.run_store import run_events_path
from src.core.run_store import transition_run
from src.core.state_machine import CorePhase
from src.core.workflow_runtime import WorkflowError
from src.core.workflow_runtime import list_workflows
from src.core.workflow_runtime import load_workflow_definition
from src.core.workflow_runtime import run_workflow
from src.memory.compression_codec import CompressionCodec
from src.report.evidence_bundle import build_evidence_bundle
from src.report.evidence_bundle import write_evidence_bundle
from src.report.patch_proposal import build_patch_proposal
from src.report.patch_proposal import write_patch_proposal


TOOL_EXECUTOR = {
    "hlapi.ingest": "src.cli.commands.hlapi_ingest",
    "hlapi.discovery": "src.cli.commands.hlapi_discovery",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="idk", description="IntelliDbgKit CLI")
    subcommands = parser.add_subparsers(dest="command", required=True)

    run_parser = subcommands.add_parser("run", help="Run lifecycle")
    run_subcommands = run_parser.add_subparsers(dest="run_command", required=True)

    run_start = run_subcommands.add_parser("start", help="Start debug run")
    run_start.add_argument("--project", required=True)
    run_start.add_argument("--target", required=True)
    run_start.add_argument("--run-id", default="")
    run_start.add_argument("--run-root", default="")
    run_start.add_argument("--trigger", default="manual")
    run_start.add_argument("--format", choices=("text", "json"), default="text")

    run_status = run_subcommands.add_parser("status", help="Show run status")
    run_status.add_argument("--run-id", required=True)
    run_status.add_argument("--run-root", default="")
    run_status.add_argument("--format", choices=("text", "json"), default="text")

    run_stop = run_subcommands.add_parser("stop", help="Stop debug run")
    run_stop.add_argument("--run-id", required=True)
    run_stop.add_argument("--run-root", default="")
    run_stop.add_argument("--reason", default="manual stop")
    run_stop.add_argument("--format", choices=("text", "json"), default="text")

    workflow_parser = subcommands.add_parser("workflow", help="Workflow control")
    workflow_subcommands = workflow_parser.add_subparsers(dest="workflow_command", required=True)

    workflow_list = workflow_subcommands.add_parser("list", help="List workflows")
    workflow_list.add_argument("--format", choices=("text", "json"), default="text")

    workflow_show = workflow_subcommands.add_parser("show", help="Show workflow definition")
    workflow_show.add_argument("workflow_id")
    workflow_show.add_argument("--format", choices=("text", "json"), default="text")

    workflow_run = workflow_subcommands.add_parser("run", help="Run workflow skeleton")
    workflow_run.add_argument("workflow_id")
    workflow_run.add_argument("--run-id", required=True)
    workflow_run.add_argument("--run-root", default="")
    workflow_run.add_argument("--evidence", action="append", default=[])
    workflow_run.add_argument("--format", choices=("text", "json"), default="text")

    verify_parser = subcommands.add_parser("verify", help="Verification commands")
    verify_subcommands = verify_parser.add_subparsers(dest="verify_command", required=True)

    verify_compression = verify_subcommands.add_parser("compression", help="Verify compression roundtrip")
    verify_compression.add_argument("--run-id", required=True)
    verify_compression.add_argument("--run-root", default="")
    verify_compression.add_argument("--roundtrip", action="store_true")
    verify_compression.add_argument("--format", choices=("text", "json"), default="text")

    analyze_parser = subcommands.add_parser("analyze", help="Analysis commands")
    analyze_subcommands = analyze_parser.add_subparsers(dest="analyze_command", required=True)

    analyze_consensus = analyze_subcommands.add_parser("consensus", help="Run consensus skeleton")
    analyze_consensus.add_argument("--run-id", required=True)
    analyze_consensus.add_argument("--run-root", default="")
    analyze_consensus.add_argument("--topic", default="root-cause")
    analyze_consensus.add_argument("--agents", default="codex,copilot,gemini")
    analyze_consensus.add_argument("--required-evidence", action="append", default=["trace.captured"])
    analyze_consensus.add_argument("--format", choices=("text", "json"), default="text")

    report_parser = subcommands.add_parser("report", help="Report generation")
    report_subcommands = report_parser.add_subparsers(dest="report_command", required=True)

    report_evidence = report_subcommands.add_parser("evidence-bundle", help="Generate evidence bundle")
    report_evidence.add_argument("--run-id", required=True)
    report_evidence.add_argument("--run-root", default="")
    report_evidence.add_argument("--format", choices=("text", "json"), default="text")

    patch_parser = subcommands.add_parser("patch", help="Patch proposal")
    patch_subcommands = patch_parser.add_subparsers(dest="patch_command", required=True)

    patch_suggest = patch_subcommands.add_parser("suggest", help="Generate patch proposal")
    patch_suggest.add_argument("--run-id", required=True)
    patch_suggest.add_argument("--run-root", default="")
    patch_suggest.add_argument("--format", choices=("text", "json"), default="text")

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


def _resolve_run_root(raw_value: str) -> Path:
    if raw_value:
        path = Path(raw_value).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path
    return default_run_root(Path.cwd())


def _print_run_text(run_payload: dict[str, Any], event_count: int) -> None:
    print(f"run_id: {run_payload['run_id']}")
    print(f"project_name: {run_payload['project_name']}")
    print(f"target_id: {run_payload['target_id']}")
    print(f"state: {run_payload['state']}")
    print(f"started_at: {run_payload['started_at']}")
    print(f"finished_at: {run_payload.get('finished_at') or '-'}")
    print(f"event_count: {event_count}")


def _print_workflow_list_text(workflow_ids: list[str]) -> None:
    for workflow_id in workflow_ids:
        print(workflow_id)


def _print_workflow_run_text(payload: dict[str, Any], output_file: Path) -> None:
    print(f"workflow_run_id: {payload['workflow_run_id']}")
    print(f"workflow_id: {payload['workflow_id']}")
    print(f"run_id: {payload['run_id']}")
    print(f"status: {payload['status']}")
    print(f"blocked_reason: {payload.get('blocked_reason') or '-'}")
    print(f"output_file: {output_file}")


def _load_jsonl_lines(path: Path) -> list[str]:
    lines: list[str] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            text = line.strip()
            if not text:
                continue
            lines.append(text)
    return lines


def _register_mock_agents(dispatcher: AgentDispatcher) -> None:
    def codex_handler(context: dict[str, Any]) -> dict[str, Any]:
        _ = context
        return {
            "claim": "root cause hypothesis accepted",
            "confidence": 0.82,
            "evidence_refs": ["trace.captured", "symbol.mapped"],
        }

    def copilot_handler(context: dict[str, Any]) -> dict[str, Any]:
        _ = context
        return {
            "claim": "root cause hypothesis accepted",
            "confidence": 0.77,
            "evidence_refs": ["trace.captured", "source.linked"],
        }

    def gemini_handler(context: dict[str, Any]) -> dict[str, Any]:
        _ = context
        return {
            "claim": "fallback path missing guard check",
            "confidence": 0.66,
            "evidence_refs": ["trace.captured"],
        }

    dispatcher.register("codex", codex_handler)
    dispatcher.register("copilot", copilot_handler)
    dispatcher.register("gemini", gemini_handler)


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

    if args.command == "run":
        run_root = _resolve_run_root(args.run_root)
        if args.run_command == "start":
            try:
                run_payload = create_run(
                    project_name=args.project,
                    target_id=args.target,
                    run_root=run_root,
                    run_id=args.run_id,
                    trigger=args.trigger,
                )
            except RunStoreError as error:
                print(str(error), file=sys.stderr)
                return 2
            events = run_event_count(run_root, run_payload["run_id"])
            if args.format == "json":
                _print_json(
                    {
                        "run": run_payload,
                        "event_count": events,
                        "run_root": str(run_root),
                    }
                )
                return 0
            _print_run_text(run_payload, events)
            return 0

        if args.run_command == "status":
            try:
                run_payload = load_run(run_root, args.run_id)
            except RunStoreError as error:
                print(str(error), file=sys.stderr)
                return 2
            events = run_event_count(run_root, args.run_id)
            if args.format == "json":
                _print_json(
                    {
                        "run": run_payload,
                        "event_count": events,
                        "run_root": str(run_root),
                    }
                )
                return 0
            _print_run_text(run_payload, events)
            return 0

        if args.run_command == "stop":
            try:
                run_payload = transition_run(
                    run_root=run_root,
                    run_id=args.run_id,
                    to_phase=CorePhase.REPORT,
                    reason=args.reason,
                )
            except RunStoreError as error:
                print(str(error), file=sys.stderr)
                return 2
            events = run_event_count(run_root, args.run_id)
            if args.format == "json":
                _print_json(
                    {
                        "run": run_payload,
                        "event_count": events,
                        "run_root": str(run_root),
                    }
                )
                return 0
            _print_run_text(run_payload, events)
            return 0

        parser.error("unsupported run command")
        return 2

    if args.command == "workflow":
        if args.workflow_command == "list":
            workflow_ids = list_workflows()
            if args.format == "json":
                _print_json({"workflows": workflow_ids})
                return 0
            _print_workflow_list_text(workflow_ids)
            return 0

        if args.workflow_command == "show":
            try:
                definition = load_workflow_definition(args.workflow_id)
            except WorkflowError as error:
                print(str(error), file=sys.stderr)
                return 2
            if args.format == "json":
                _print_json(definition)
                return 0
            print(f"workflow_id: {definition['workflow_id']}")
            print(f"name: {definition['name']}")
            print(f"version: {definition['version']}")
            print(f"step_count: {len(definition.get('steps', []))}")
            return 0

        if args.workflow_command == "run":
            run_root = _resolve_run_root(args.run_root)
            try:
                load_run(run_root, args.run_id)
            except RunStoreError as error:
                print(str(error), file=sys.stderr)
                return 2
            try:
                definition = load_workflow_definition(args.workflow_id)
            except WorkflowError as error:
                print(str(error), file=sys.stderr)
                return 2
            workflow_run_payload = run_workflow(
                definition=definition,
                run_id=args.run_id,
                evidence=set(args.evidence),
            )
            output_file = append_workflow_record(
                run_root=run_root,
                run_id=args.run_id,
                workflow_run=workflow_run_payload,
            )
            if args.format == "json":
                _print_json(
                    {
                        "workflow_run": workflow_run_payload,
                        "output_file": str(output_file),
                    }
                )
            else:
                _print_workflow_run_text(workflow_run_payload, output_file)
            if workflow_run_payload["status"] == "blocked":
                return 3
            return 0

        parser.error("unsupported workflow command")
        return 2

    if args.command == "verify":
        if args.verify_command == "compression":
            run_root = _resolve_run_root(args.run_root)
            try:
                load_run(run_root, args.run_id)
            except RunStoreError as error:
                print(str(error), file=sys.stderr)
                return 2
            events_file = run_events_path(run_root, args.run_id)
            if not events_file.exists():
                print(f"events file not found: {events_file}", file=sys.stderr)
                return 2
            raw_lines = _load_jsonl_lines(events_file)
            codec = CompressionCodec()
            payload = codec.compress(run_id=args.run_id, raw_lines=raw_lines)
            roundtrip_ok = True
            if args.roundtrip:
                restored = codec.decompress(payload)
                roundtrip_ok = restored == raw_lines
            payload["roundtrip_ok"] = roundtrip_ok
            output_file = run_root / args.run_id / "index" / "compression.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            if args.format == "json":
                _print_json({"compression": payload, "output_file": str(output_file)})
            else:
                print(f"run_id: {args.run_id}")
                print(f"raw_count: {len(raw_lines)}")
                print(f"roundtrip_ok: {roundtrip_ok}")
                print(f"output_file: {output_file}")
            if args.roundtrip and not roundtrip_ok:
                return 3
            return 0

        parser.error("unsupported verify command")
        return 2

    if args.command == "analyze":
        if args.analyze_command == "consensus":
            run_root = _resolve_run_root(args.run_root)
            try:
                load_run(run_root, args.run_id)
            except RunStoreError as error:
                print(str(error), file=sys.stderr)
                return 2
            dispatcher = AgentDispatcher()
            _register_mock_agents(dispatcher)
            agent_ids = [item.strip() for item in args.agents.split(",") if item.strip()]
            try:
                results = dispatcher.dispatch(
                    agent_ids=agent_ids,
                    context={"run_id": args.run_id, "topic": args.topic},
                )
            except AgentDispatcherError as error:
                print(str(error), file=sys.stderr)
                return 2
            engine = ConsensusEngine()
            consensus_payload = engine.evaluate(
                run_id=args.run_id,
                topic=args.topic,
                agent_results=results,
                required_evidence=set(args.required_evidence),
            )
            output_file = append_consensus_record(
                run_root=run_root,
                run_id=args.run_id,
                consensus_payload=consensus_payload,
            )
            if args.format == "json":
                _print_json({"consensus": consensus_payload, "output_file": str(output_file)})
            else:
                print(f"run_id: {args.run_id}")
                print(f"topic: {args.topic}")
                print(f"vetoed: {consensus_payload['vetoed']}")
                print(f"winning_claim: {consensus_payload.get('winning_claim') or '-'}")
                print(f"output_file: {output_file}")
            if consensus_payload["vetoed"]:
                return 3
            return 0

        parser.error("unsupported analyze command")
        return 2

    if args.command == "report":
        if args.report_command == "evidence-bundle":
            run_root = _resolve_run_root(args.run_root)
            try:
                load_run(run_root, args.run_id)
            except RunStoreError as error:
                print(str(error), file=sys.stderr)
                return 2
            payload = build_evidence_bundle(run_root=run_root, run_id=args.run_id)
            output_file = write_evidence_bundle(run_root=run_root, run_id=args.run_id, payload=payload)
            if args.format == "json":
                _print_json({"evidence_bundle": payload, "output_file": str(output_file)})
            else:
                print(f"run_id: {args.run_id}")
                print(f"event_count: {payload['event_count']}")
                print(f"auto_merge: {payload['auto_merge']}")
                print(f"output_file: {output_file}")
            return 0

        parser.error("unsupported report command")
        return 2

    if args.command == "patch":
        if args.patch_command == "suggest":
            run_root = _resolve_run_root(args.run_root)
            try:
                load_run(run_root, args.run_id)
            except RunStoreError as error:
                print(str(error), file=sys.stderr)
                return 2
            payload = build_patch_proposal(run_root=run_root, run_id=args.run_id)
            output_file = write_patch_proposal(run_root=run_root, run_id=args.run_id, payload=payload)
            if args.format == "json":
                _print_json({"patch_proposal": payload, "output_file": str(output_file)})
            else:
                print(f"run_id: {args.run_id}")
                print(f"status: {payload['status']}")
                print(f"auto_merge: {payload['auto_merge']}")
                print(f"output_file: {output_file}")
            return 0

        parser.error("unsupported patch command")
        return 2

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
