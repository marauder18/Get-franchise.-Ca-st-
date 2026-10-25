from __future__ import annotations

import csv
import json
from pathlib import Path

from professionalize_reports import iter_report_paths


ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ROOT / "food franchises"
EXPORT_DATE = "2026-07-18"
SYNC_DATE = "July 19, 2026"
PRIMARY_APPENDIX_MARKER = "12. PRIMARY-SOURCE FRANCHISE UPDATE (2026-07-19)"

BRAND_CSV = ROOT / f"GETFRANCHISE_BRAND_DATA_{EXPORT_DATE}.csv"
OVERRIDE_JSON = ROOT / f"PRIMARY_SOURCE_OVERRIDES_{EXPORT_DATE}.json"
SYNC_SUMMARY = ROOT / "PRIMARY_SOURCE_REPORT_SYNC_2026-07-19.md"


def load_brand_rows() -> dict[str, dict[str, str]]:
    with BRAND_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows: dict[str, dict[str, str]] = {}
        for row in reader:
            rows[row["report_file"]] = row
            report_path = row.get("report_path")
            if report_path:
                rows[report_path] = row
        return rows


def load_overrides() -> dict[str, dict[str, object]]:
    return json.loads(OVERRIDE_JSON.read_text(encoding="utf-8"))


def build_report_index() -> dict[str, Path]:
    return {path.name: path for path in iter_report_paths()}


def split_gaps(raw_value: str) -> list[str]:
    return [gap.strip() for gap in raw_value.split(" | ") if gap.strip()]


def unique_source_urls(override: dict[str, object]) -> list[str]:
    evidence = override.get("evidence", [])
    urls = {item["source_url"] for item in evidence if item.get("source_url")}
    return sorted(urls)


def key_evidence_lines(override: dict[str, object]) -> list[str]:
    evidence = override.get("evidence", [])
    lines: list[str] = []
    for item in evidence[:6]:
        lines.append(f"- {item['field_key']}: {item['field_value']}")
    return lines


def format_section(row: dict[str, str], override: dict[str, object]) -> str:
    gaps = split_gaps(row.get("top_critical_gaps", ""))
    urls = unique_source_urls(override)
    evidence_lines = key_evidence_lines(override)

    lines = [
        "",
        PRIMARY_APPENDIX_MARKER,
        f"Update Date: {SYNC_DATE}",
        "Sync Status: Official-source override loaded into the structured GetFranchise exports.",
        (
            "Current Structured Status: "
            f"{row['evidence_grade']} grade | "
            f"{row['source_count']} unique sources | "
            f"{row['official_brand_source_count']} official brand/company sources | "
            f"{row['research_track']}"
        ),
        f"Decision Posture: {row['decision_posture']}",
        "",
        "Official Fee View",
        f"- Total investment: {row['total_investment_range']}",
        f"- Franchise fee: {row['franchise_fee']}",
        f"- Royalty: {row['royalty_percent']}",
        f"- Marketing fee: {row['marketing_fund_percent']}",
        f"- Minimum liquid capital: {row['min_liquid_capital']}",
        "",
        "What Official Sources Now Confirm",
    ]

    lines.extend(evidence_lines or ["- No discrete override evidence items were loaded."])

    lines.append("")
    lines.append("Remaining Hard Stops")
    lines.extend([f"- {gap}" for gap in gaps[:6]] or ["- No structured gap list available."])

    lines.append("")
    lines.append("Official Source URLs")
    lines.extend([f"- {url}" for url in urls] or ["- No official URLs captured in the override file."])

    return "\n".join(lines).rstrip() + "\n"


def strip_old_section(text: str) -> str:
    return text.split(PRIMARY_APPENDIX_MARKER)[0].rstrip() + "\n"


def write_summary(rows: list[dict[str, str]]) -> None:
    lines = [
        "# Primary Source Report Sync - 2026-07-19",
        "",
        f"- Reports updated: {len(rows)}",
        "- These report updates mirror the current official-source override layer already loaded into the structured exports.",
        "- They do not replace disclosure review, franchise agreement review, or unit-level financial diligence.",
        "",
        "| Brand | Grade | Source Count | Research Track |",
        "| --- | --- | ---: | --- |",
    ]

    for row in sorted(rows, key=lambda item: item["brand"]):
        lines.append(
            f"| {row['brand']} | {row['evidence_grade']} | {row['source_count']} | {row['research_track']} |"
        )

    SYNC_SUMMARY.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    brand_rows = load_brand_rows()
    overrides = load_overrides()
    report_index = build_report_index()
    updated_rows: list[dict[str, str]] = []

    for report_file, override in overrides.items():
        row = brand_rows.get(report_file)
        report_path = row.get("report_path") if row else ""
        path = ROOT / Path(report_path) if report_path else report_index.get(report_file, REPORTS_DIR / report_file)
        if report_path and not path.exists():
            path = report_index.get(report_file, path)
        if not path.exists() or not row:
            continue

        base_text = strip_old_section(path.read_text(encoding="utf-8"))
        section = format_section(row, override)
        path.write_text(base_text + section, encoding="utf-8")
        updated_rows.append(row)

    write_summary(updated_rows)


if __name__ == "__main__":
    main()
