from __future__ import annotations

import unittest

from src.memory.compression_codec import CompressionCodec


class CompressionRoundtripIntegrationTest(unittest.TestCase):
    def test_roundtrip_recovers_original_lines(self) -> None:
        raw_lines = [
            "workflow run trace-capture-flow",
            "workflow run trace-capture-flow",
            "missing evidence trace.captured",
            "missing evidence trace.captured",
            "root cause hypothesis accepted",
        ]
        codec = CompressionCodec()
        payload = codec.compress(run_id="run-test-001", raw_lines=raw_lines)
        restored = codec.decompress(payload)

        self.assertEqual(raw_lines, restored)
        self.assertLess(len(payload["dedup_lines"]), len(raw_lines))
        step_flags = [item["roundtrip_ok"] for item in payload["step_results"]]
        self.assertTrue(all(step_flags))


if __name__ == "__main__":
    unittest.main()
