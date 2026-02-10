from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EventValidationError(ValueError):
    pass


def _load_event_schema() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    schema_path = root / "specs" / "001-debug-loop" / "contracts" / "event-schema.json"
    with schema_path.open("r", encoding="utf-8") as file:
        return json.load(file)


class EventBus:
    def __init__(self) -> None:
        self._schema = _load_event_schema()
        self._required_fields = set(self._schema["required"])
        self._allowed_fields = set(self._schema["properties"].keys())
        self._events: list[dict[str, Any]] = []

    @property
    def events(self) -> list[dict[str, Any]]:
        return list(self._events)

    def validate(self, event: dict[str, Any]) -> None:
        missing = self._required_fields - set(event.keys())
        if missing:
            missing_fields = ", ".join(sorted(missing))
            raise EventValidationError(f"missing fields: {missing_fields}")
        unknown = set(event.keys()) - self._allowed_fields
        if unknown:
            unknown_fields = ", ".join(sorted(unknown))
            raise EventValidationError(f"unknown fields: {unknown_fields}")

    def publish(self, event: dict[str, Any]) -> dict[str, Any]:
        self.validate(event)
        self._events.append(event)
        return event
