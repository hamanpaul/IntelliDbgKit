from __future__ import annotations

from typing import Iterable

from src.cli.tool_card import ToolCard


class ToolRegistryError(ValueError):
    pass


class CommandRegistry:
    def __init__(self, cards: Iterable[ToolCard] | None = None) -> None:
        self._cards: dict[str, ToolCard] = {}
        self._aliases: dict[str, str] = {}
        if cards is None:
            return
        for card in cards:
            self.register(card)

    def register(self, card: ToolCard) -> None:
        if card.tool_id in self._cards:
            raise ToolRegistryError(f"duplicate tool_id: {card.tool_id}")
        self._cards[card.tool_id] = card
        for alias in card.aliases:
            if alias in self._aliases:
                conflict = self._aliases[alias]
                raise ToolRegistryError(f"duplicate alias: {alias} -> {conflict}")
            self._aliases[alias] = card.tool_id

    def resolve(self, tool_key: str) -> ToolCard:
        tool_id = self._aliases.get(tool_key, tool_key)
        card = self._cards.get(tool_id)
        if card is None:
            raise ToolRegistryError(f"unknown tool: {tool_key}")
        return card

    def list_cards(self) -> list[ToolCard]:
        return [self._cards[key] for key in sorted(self._cards.keys())]

    def doctor(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for card in self.list_cards():
            rows.append(
                {
                    "tool_id": card.tool_id,
                    "status": card.status,
                    "adapter": card.adapter,
                    "risk_level": card.risk_level,
                    "health_reason": card.health_reason or "-",
                }
            )
        return rows


def default_cards() -> tuple[ToolCard, ...]:
    ingest = ToolCard(
        tool_id="hlapi.ingest",
        category="support",
        description="Import HLAPI XLSX baseline and write Obsidian notes/index.",
        examples=(
            "python3 -m src.cli.commands.hlapi_ingest --source ./docs/6.3.0GA_prplware_v403_LLAPI_Test_Report.xlsx --vault /tmp/idk-vault --project IntelliDbgKit",
        ),
        help_command="python3 -m src.cli.commands.hlapi_ingest --help",
        risk_level="low",
        adapter="native-python-module",
        input_schema_ref="specs/001-debug-loop/contracts/hlapi-testcase.schema.json",
        output_schema_ref="specs/001-debug-loop/contracts/hlapi-testcase.schema.json",
        aliases=("hlapi-import", "ingest"),
        status="healthy",
    )
    discovery = ToolCard(
        tool_id="hlapi.discovery",
        category="collector",
        description="Collect target-supported HLAPI paths and persist discovery records.",
        examples=(
            "python3 -m src.cli.commands.hlapi_discovery --run-id run-sample --target-id board-01 --input /tmp/idk-discovery-input.txt --output /tmp/idk-discovery-output.json",
        ),
        help_command="python3 -m src.cli.commands.hlapi_discovery --help",
        risk_level="low",
        adapter="native-python-module",
        input_schema_ref="specs/001-debug-loop/contracts/hlapi-discovery.schema.json",
        output_schema_ref="specs/001-debug-loop/contracts/hlapi-discovery.schema.json",
        aliases=("hlapi-scan", "discovery"),
        status="healthy",
    )
    return (ingest, discovery)


def build_default_registry() -> CommandRegistry:
    return CommandRegistry(cards=default_cards())
