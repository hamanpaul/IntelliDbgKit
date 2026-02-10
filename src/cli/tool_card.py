from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ToolCard:
    tool_id: str
    category: str
    description: str
    examples: tuple[str, ...]
    help_command: str
    risk_level: str
    adapter: str
    input_schema_ref: str = ""
    output_schema_ref: str = ""
    aliases: tuple[str, ...] = ()
    status: str = "healthy"
    health_reason: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "category": self.category,
            "description": self.description,
            "examples": list(self.examples),
            "help_command": self.help_command,
            "risk_level": self.risk_level,
            "adapter": self.adapter,
            "input_schema_ref": self.input_schema_ref,
            "output_schema_ref": self.output_schema_ref,
            "aliases": list(self.aliases),
            "status": self.status,
            "health_reason": self.health_reason,
            "metadata": dict(self.metadata),
        }
