from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common import GATES
from validate_existing import validate_one


def report(gate_result: str = "PASS") -> str:
    headings = "\n".join(f"{number}. SECTION {number}" for number in range(1, 8))
    gates = "\n".join(f"- {gate}: {gate_result}" for gate in GATES)
    return (
        f"{headings}\n8. EVIDENCE STATUS\n{gates}\n9. SOURCES\nTotal Source Count: 1\n"
        "Source-Backed Evidence Loaded\n- profile.founded: 2000 | Source: https://example.test/a | Date: 2026 | Reliability: 90 | Investor scoring use: Yes\n"
    )


class ExistingValidationTests(unittest.TestCase):
    def test_known_good_file_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "good.txt"
            path.write_text(report(), encoding="utf-8")
            self.assertEqual(validate_one(path)["issues"], [])

    def test_missing_evidence_gate_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.txt"
            path.write_text(report().replace(f"- {GATES[0]}: PASS\n", ""), encoding="utf-8")
            issues = validate_one(path)["issues"]
            self.assertTrue(any(issue["issue"] == "evidence_gate" for issue in issues))


if __name__ == "__main__":
    unittest.main()
