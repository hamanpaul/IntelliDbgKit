from __future__ import annotations

import unittest

from src.cli.command_registry import CommandRegistry
from src.cli.command_registry import ToolRegistryError
from src.cli.command_registry import build_default_registry
from src.cli.tool_card import ToolCard


class CliToolRegistryTest(unittest.TestCase):
    def test_default_registry_contains_hlapi_tools(self) -> None:
        registry = build_default_registry()
        cards = registry.list_cards()
        tool_ids = [card.tool_id for card in cards]
        self.assertIn("hlapi.ingest", tool_ids)
        self.assertIn("hlapi.discovery", tool_ids)

    def test_alias_resolve_returns_tool_card(self) -> None:
        registry = build_default_registry()
        card = registry.resolve("ingest")
        self.assertEqual("hlapi.ingest", card.tool_id)

    def test_register_duplicate_alias_raises(self) -> None:
        first = ToolCard(
            tool_id="tool.first",
            category="support",
            description="first",
            examples=("first --help",),
            help_command="first --help",
            risk_level="low",
            adapter="native",
            aliases=("same",),
        )
        second = ToolCard(
            tool_id="tool.second",
            category="support",
            description="second",
            examples=("second --help",),
            help_command="second --help",
            risk_level="low",
            adapter="native",
            aliases=("same",),
        )
        registry = CommandRegistry(cards=(first,))
        with self.assertRaises(ToolRegistryError):
            registry.register(second)

    def test_doctor_row_contains_health_reason_placeholder(self) -> None:
        registry = build_default_registry()
        rows = registry.doctor()
        self.assertTrue(rows)
        self.assertIn("health_reason", rows[0])


if __name__ == "__main__":
    unittest.main()
