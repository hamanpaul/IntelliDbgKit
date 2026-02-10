from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from src.ingestion.hlapi_discovery import parse_discovery_lines
from src.ingestion.hlapi_discovery import write_discovery_records


class HlapiDiscoveryMinimalTest(unittest.TestCase):
    def test_parse_and_write_discovery_records(self) -> None:
        lines = [
            "Device.WiFi.Radio.1.Channel rw",
            "Device.WiFi.SSID.1.Enable read",
            "Device.WiFi.AccessPoint.1.Security.ModeEnabled w",
        ]
        records = parse_discovery_lines(
            lines=lines,
            run_id="run-20260210-001",
            target_id="board-prplos-01",
            collector="ubus-cli",
        )
        self.assertEqual(3, len(records))

        first = records[0]
        required_keys = {
            "discovery_id",
            "run_id",
            "target_id",
            "collected_at",
            "collector",
            "object_path",
            "access_mode",
            "probe_command",
            "support_state",
        }
        self.assertTrue(required_keys.issubset(first.keys()))
        self.assertEqual("rw", first["access_mode"])
        self.assertEqual("supported", first["support_state"])

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / "discovery.json"
            write_discovery_records(records, output_file)
            self.assertTrue(output_file.exists())
            loaded = json.loads(output_file.read_text(encoding="utf-8"))
            self.assertEqual(3, len(loaded))
            self.assertEqual("Device.WiFi.Radio.1.Channel", loaded[0]["object_path"])


if __name__ == "__main__":
    unittest.main()
