from __future__ import annotations

import unittest

from src.core.event_bus import EventBus
from src.core.event_bus import EventValidationError


class EventSchemaTest(unittest.TestCase):
    def test_event_bus_accepts_trace_event_with_optional_compression_fields(self) -> None:
        bus = EventBus()
        event = {
            "event_id": "e-1",
            "run_id": "run-1",
            "ts_ns": 1,
            "phase": "BOOTSTRAP",
            "source": "host",
            "tool": "tracezone",
            "target_id": "board-1",
            "severity": "info",
            "payload": {"msg": "ok"},
            "semantic_tags": ["hlapi-read"],
            "compression_refs": [
                {
                    "tier": "semantic",
                    "token": "[tc_ndev_ev]",
                    "lexicon_id": "lex-1",
                }
            ],
            "links": [
                {
                    "type": "workflow",
                    "target": "trace-capture-flow",
                }
            ],
        }
        bus.publish(event)
        self.assertEqual(1, len(bus.events))

    def test_event_bus_rejects_unknown_field(self) -> None:
        bus = EventBus()
        event = {
            "event_id": "e-1",
            "run_id": "run-1",
            "ts_ns": 1,
            "phase": "BOOTSTRAP",
            "source": "host",
            "tool": "tracezone",
            "target_id": "board-1",
            "severity": "info",
            "payload": {},
            "unknown_field": "bad",
        }
        with self.assertRaises(EventValidationError):
            bus.publish(event)


if __name__ == "__main__":
    unittest.main()
