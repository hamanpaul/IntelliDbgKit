from __future__ import annotations

import json
from pathlib import Path
import unittest


class ContractSyntaxTest(unittest.TestCase):
    def test_all_contract_json_files_are_parseable(self) -> None:
        root = Path(__file__).resolve().parents[2]
        contract_dir = root / "specs" / "001-debug-loop" / "contracts"
        files = sorted(contract_dir.glob("*.json"))
        self.assertTrue(files)
        for file in files:
            json.loads(file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
