from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from src.ingestion.hlapi_writer import write_hlapi_obsidian
from src.ingestion.xlsx_loader import load_hlapi_testcases


class XlsxToMarkdownMappingTest(unittest.TestCase):
    def test_load_xlsx_and_write_obsidian(self) -> None:
        root = Path(__file__).resolve().parents[2]
        source = root / "docs" / "6.3.0GA_prplware_v403_LLAPI_Test_Report.xlsx"
        self.assertTrue(source.exists())

        cases = load_hlapi_testcases(source, start_sheet="QoS_LLAPI")
        self.assertGreater(len(cases), 100)

        sheets = {case["source_sheet"] for case in cases}
        self.assertIn("QoS_LLAPI", sheets)
        self.assertIn("Wifi_LLAPI", sheets)

        status_set = {case["result_status"] for case in cases}
        self.assertTrue(status_set.issubset({"pass", "fail", "not-supported", "skip", "unknown"}))

        first = cases[0]
        self.assertIn("case_id", first)
        self.assertIn("source_row", first)
        self.assertIn("hlapi_command", first)

        with tempfile.TemporaryDirectory() as tmp_dir:
            output = write_hlapi_obsidian(
                testcases=cases,
                vault_root=tmp_dir,
                project="IntelliDbgKit",
                run_id="run-test-001",
                source_file=source,
            )
            self.assertEqual("run-test-001", output["run_id"])
            output_root = Path(output["output_root"])
            self.assertTrue((output_root / "notes" / "run-summary.md").exists())
            self.assertTrue((output_root / "notes" / "trace-index.md").exists())
            self.assertTrue((output_root / "index" / "hlapi-testcases.json").exists())
            self.assertTrue((output_root / "index" / "lineage.json").exists())

            sample_sheet = output_root / "notes" / "testcases" / "QoS_LLAPI.md"
            self.assertTrue(sample_sheet.exists())
            content = sample_sheet.read_text(encoding="utf-8")
            self.assertIn("[[../run-summary]]", content)
            self.assertIn("[[../trace-index]]", content)


if __name__ == "__main__":
    unittest.main()
