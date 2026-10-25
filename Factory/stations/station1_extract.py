"""Station 1: extract only source-ledger values from an existing local report."""
from __future__ import annotations

import argparse
from pathlib import Path

from common import log, now, parse_gates, parse_source_fields, read_contract, require_valid, section_issues, sha256_file, slugify, write_json
from config import LOG_DIR, RAW_DIR, REPORTS_DIR, ensure_workspace


def find_report(franchise: str, reports_dir: Path = REPORTS_DIR) -> Path:
    wanted = slugify(franchise)
    matches = [path for path in reports_dir.rglob("*.txt") if slugify(path.stem) == wanted]
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected exactly one local report for {franchise!r}; found {len(matches)}")
    return matches[0]


def extract(franchise: str, reports_dir: Path = REPORTS_DIR, raw_dir: Path = RAW_DIR, log_dir: Path = LOG_DIR) -> Path:
    ensure_workspace()
    read_contract("extraction_prompt.txt")
    report = find_report(franchise, reports_dir)
    text = report.read_text(encoding="utf-8")
    issues = section_issues(text)
    if issues:
        raise ValueError("; ".join(issues))
    slug = slugify(franchise)
    document = {
        "schema_version": "1.0",
        "franchise": franchise.strip(),
        "slug": slug,
        "report_path": str(report.resolve()),
        "source_file_sha256": sha256_file(report),
        "extracted_at": now(),
        "fields": parse_source_fields(text),
        "evidence_gates": parse_gates(text),
    }
    require_valid(document, "franchise_raw.schema.json")
    output = raw_dir / f"{slug}.json"
    write_json(output, document)
    log(log_dir / f"{slug}.extract.log", {"station": "extract", "status": "done", "report": str(report), "fields": len(document["fields"])})
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract source-safe values from one local franchise report. No network access.")
    parser.add_argument("franchise")
    args = parser.parse_args()
    print(extract(args.franchise))


if __name__ == "__main__":
    main()
