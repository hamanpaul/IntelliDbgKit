from __future__ import annotations

import json
from pathlib import Path
import unittest

from src.memory.compression_codec import CompressionCodec


class CompressionLexiconSchemaContractTest(unittest.TestCase):
    def test_compression_payload_fits_contract_shape(self) -> None:
        root = Path(__file__).resolve().parents[2]
        schema_file = root / "specs" / "001-debug-loop" / "contracts" / "compression-lexicon.schema.json"
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        required_fields = set(schema["required"])

        codec = CompressionCodec()
        payload = codec.compress(
            run_id="run-test-001",
            raw_lines=[
                "workflow run",
                "workflow run",
                "missing evidence trace.captured",
            ],
        )
        missing = required_fields - set(payload.keys())
        self.assertFalse(missing)
        self.assertRegex(payload["lexicon_version"], r"^\d+\.\d+\.\d+$")
        self.assertTrue(payload["entries"])
        self.assertTrue(payload["step_results"])


if __name__ == "__main__":
    unittest.main()
