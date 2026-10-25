from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPORT_DATE = "2026-07-18"
BRAND_JSON = ROOT / f"GETFRANCHISE_BRAND_DATA_{EXPORT_DATE}.json"
QUEUE_CSV = ROOT / f"GETFRANCHISE_NON_FOOD_RESEARCH_QUEUE_{EXPORT_DATE}.csv"
SUMMARY_MD = ROOT / f"GETFRANCHISE_NON_FOOD_RESEARCH_QUEUE_{EXPORT_DATE}.md"


GRADE_RANK = {"A": 0, "A-": 1, "B+": 2, "B": 3, "C+": 4, "C": 5, "D": 6, "F": 7}


def priority_reason(row: dict[str, object]) -> str:
    reasons: list[str] = []
    if int(row.get("official_brand_source_count") or 0) < 3:
        reasons.append("add official franchise/company sources")
    if int(row.get("verified_core_fee_fields") or 0) < 3:
        reasons.append("verify investment, fee, royalty, and marketing fields")
    if str(row.get("evidence_grade", "")) in {"D", "F"}:
        reasons.append("replace estimated fields with cited public evidence")
    if str(row.get("fdd_summary", "")).lower().startswith("canadian disclosure package missing"):
        reasons.append("request Canadian disclosure package/FDD-equivalent summary")
    return " | ".join(reasons) or "manual diligence review"


def main() -> None:
    rows = json.loads(BRAND_JSON.read_text(encoding="utf-8"))
    non_food = [row for row in rows if not str(row.get("report_path", "")).startswith("food franchises/")]
    queue = sorted(
        non_food,
        key=lambda row: (
            GRADE_RANK.get(str(row.get("evidence_grade", "")), 99),
            -(int(row.get("source_count") or 0)),
            str(row.get("brand", "")),
        ),
        reverse=True,
    )

    fieldnames = [
        "brand",
        "category",
        "report_file",
        "report_path",
        "evidence_grade",
        "source_count",
        "official_brand_source_count",
        "verified_core_fee_fields",
        "research_track",
        "priority_reason",
        "contact_information",
        "official_brand_sources",
        "top_critical_gaps",
    ]
    with QUEUE_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in queue:
            writer.writerow(
                {
                    **{field: row.get(field, "") for field in fieldnames},
                    "priority_reason": priority_reason(row),
                }
            )

    grade_counts: dict[str, int] = {}
    for row in non_food:
        grade = str(row.get("evidence_grade", "Not Graded"))
        grade_counts[grade] = grade_counts.get(grade, 0) + 1

    lines = [
        f"# GetFranchise Non-Food Research Queue - {EXPORT_DATE}",
        "",
        f"- Non-food brands: {len(non_food)}",
        "- Food franchises are excluded from this queue.",
        "- This queue prioritizes real source work instead of inflating evidence grades.",
        "",
        "## Evidence Grade Snapshot",
    ]
    for grade, count in sorted(grade_counts.items(), key=lambda item: GRADE_RANK.get(item[0], 99)):
        lines.append(f"- `{grade}`: {count}")
    lines.extend(
        [
            "",
            "## Next Source Pass",
            "- Start with F and D rows that have fewer than 3 official brand/company sources.",
            "- Prefer official franchise pages, CFA listings, franchisor FAQs, Canadian disclosure/FDD-equivalent documents, government registries, and official press pages.",
            "- Keep estimates labelled as estimates until a source gives the exact Canadian value.",
        ]
    )
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
