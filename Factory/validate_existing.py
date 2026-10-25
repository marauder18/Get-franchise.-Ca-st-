"""Parallel, offline validation of the existing nine-section franchise reports."""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import re
from collections import Counter
from pathlib import Path
from typing import Any

from common import GATES, SOURCE_RE, section_issues
from config import REPORTS_DIR


def validate_one(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    issues: list[dict[str, str]] = []
    for issue in section_issues(text):
        issues.append({"file": str(path), "issue": "template", "field": issue})
    source_section = text.split("9. SOURCES", 1)[-1] if "9. SOURCES" in text else ""
    declared = re.search(r"(?mi)^Total Source Count:\s*(\d+)", source_section)
    actual_urls = set(re.findall(r"https?://[^\s|)]+", source_section, re.IGNORECASE))
    if not declared:
        issues.append({"file": str(path), "issue": "source_count", "field": "Total Source Count missing"})
    elif int(declared.group(1)) != len(actual_urls):
        issues.append({"file": str(path), "issue": "source_count", "field": f"declared {declared.group(1)}, found {len(actual_urls)} unique URLs"})
    evidence_match = re.search(r"Source-Backed Evidence Loaded\n(?P<body>.*?)(?:\nEvidence Source URLs:|\nResearch Notes:|\nCritical Gaps:|\Z)", text, re.DOTALL)
    if evidence_match:
        for line in evidence_match.group("body").splitlines():
            if line.startswith("- ") and not SOURCE_RE.match(line):
                issues.append({"file": str(path), "issue": "unsourced_claim", "field": line[2:80]})
    for match in re.finditer(r"Estimated \(industry benchmark\).*", text, re.IGNORECASE):
        if not re.search(r"\b\d{1,3}% confidence\b", match.group(0), re.IGNORECASE):
            issues.append({"file": str(path), "issue": "estimated_unlabeled", "field": match.group(0)[:80]})
    for gate in GATES:
        if not re.search(rf"(?m)^- {re.escape(gate)}: (PASS|FAIL)\b", text):
            issues.append({"file": str(path), "issue": "evidence_gate", "field": gate})
    return {"file": str(path), "issues": issues}


def validate_reports(reports_dir: Path = REPORTS_DIR, workers: int | None = None) -> dict[str, Any]:
    files = sorted(reports_dir.rglob("*.txt"))
    with mp.Pool(processes=workers or min(32, max(1, mp.cpu_count()))) as pool:
        results = pool.map(validate_one, files)
    issues = [issue for result in results for issue in result["issues"]]
    passed = sum(1 for result in results if not result["issues"])
    return {"total": len(files), "pass": passed, "fail": len(files) - passed, "issues": issues}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate local franchise reports with no network access.")
    parser.add_argument("--reports-dir", type=Path, default=REPORTS_DIR)
    parser.add_argument("--output", type=Path, default=REPORTS_DIR.parent / "franchises_validation.json")
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args()
    result = validate_reports(args.reports_dir, args.workers)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    categories = Counter(issue["issue"] for issue in result["issues"])
    print(f"total | pass | fail\n{result['total']} | {result['pass']} | {result['fail']}")
    for name, count in sorted(categories.items()):
        print(f"{name} | {count}")
    print(args.output)


if __name__ == "__main__":
    main()
