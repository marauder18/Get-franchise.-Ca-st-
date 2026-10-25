from __future__ import annotations

import csv
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent
EXPORT_DATE = "2026-07-18"
DATABASE_FILE = ROOT / "getfranchise.sqlite"
MANIFEST_FILE = ROOT / "GETFRANCHISE_DATABASE_MANIFEST.md"
BRAND_CSV = ROOT / f"GETFRANCHISE_BRAND_DATA_{EXPORT_DATE}.csv"
EVIDENCE_CSV = ROOT / f"GETFRANCHISE_SOURCE_EVIDENCE_{EXPORT_DATE}.csv"
PRIORITY_CSV = ROOT / f"GETFRANCHISE_RESEARCH_PRIORITY_{EXPORT_DATE}.csv"


BRAND_FIELDS = [
    "brand",
    "report_file",
    "report_path",
    "source_depth_rank",
    "category",
    "generic_screening_score",
    "risk_level",
    "growth_outlook",
    "investment_tier",
    "confidence_level",
    "investment_goal_fit",
    "founded",
    "headquarters",
    "canadian_owned",
    "industry",
    "cuisine",
    "total_investment_range",
    "franchise_fee",
    "royalty_percent",
    "marketing_fund_percent",
    "min_liquid_capital",
    "market_saturation",
    "threat_level",
    "operational_difficulty",
    "franchisor_confirmation",
    "source_count",
    "evidence_grade",
    "decision_posture",
    "rejected_fields",
    "verified_core_fee_fields",
    "official_brand_source_count",
    "government_or_law_source_count",
    "cross_border_caution",
    "research_track",
    "top_critical_gaps",
    "official_brand_sources",
    "government_or_law_sources",
]


EVIDENCE_FIELDS = [
    "brand",
    "report_file",
    "report_path",
    "field_key",
    "field_value",
    "source_url",
    "source_domain",
    "source_type",
    "source_date",
    "source_reliability",
    "investor_scoring_use",
]


PRIORITY_FIELDS = [
    "brand",
    "report_file",
    "report_path",
    "research_track",
    "evidence_grade",
    "source_depth_rank",
    "source_count",
    "official_brand_source_count",
    "verified_core_fee_fields",
    "cross_border_caution",
    "decision_posture",
    "priority_reason",
]


INTEGER_FIELDS = {
    "source_depth_rank",
    "generic_screening_score",
    "source_count",
    "rejected_fields",
    "verified_core_fee_fields",
    "official_brand_source_count",
    "government_or_law_source_count",
    "source_reliability",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def to_int(value: str | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def normalize_row(row: dict[str, str], fields: Iterable[str]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for field in fields:
        value = row.get(field, "")
        normalized[field] = to_int(value) if field in INTEGER_FIELDS else value.strip()
    return normalized


def brand_id_from_name(brand: str) -> str:
    return (
        brand.lower()
        .replace("&", "and")
        .replace("+", "plus")
        .replace("/", " ")
        .replace(".", "")
        .replace(",", "")
        .replace("'", "")
        .replace("(", "")
        .replace(")", "")
        .replace("-", " ")
        .strip()
        .replace(" ", "_")
    )


def execute_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;

        DROP VIEW IF EXISTS v_deep_dive_candidates;
        DROP VIEW IF EXISTS v_source_rebuild_queue;
        DROP VIEW IF EXISTS v_category_summary;
        DROP VIEW IF EXISTS v_under_320k_screening_candidates;
        DROP TABLE IF EXISTS source_evidence;
        DROP TABLE IF EXISTS research_priorities;
        DROP TABLE IF EXISTS reports_fts;
        DROP TABLE IF EXISTS brands;
        DROP TABLE IF EXISTS categories;
        DROP TABLE IF EXISTS database_metadata;

        CREATE TABLE database_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE categories (
            category TEXT PRIMARY KEY,
            brand_count INTEGER NOT NULL DEFAULT 0,
            average_screening_score REAL,
            deep_dive_count INTEGER NOT NULL DEFAULT 0,
            rebuild_count INTEGER NOT NULL DEFAULT 0,
            verify_fee_count INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE brands (
            brand_id TEXT PRIMARY KEY,
            brand TEXT NOT NULL UNIQUE,
            report_file TEXT NOT NULL,
            report_path TEXT NOT NULL,
            source_depth_rank INTEGER,
            category TEXT NOT NULL,
            generic_screening_score INTEGER,
            risk_level TEXT,
            growth_outlook TEXT,
            investment_tier TEXT,
            confidence_level TEXT,
            investment_goal_fit TEXT,
            founded TEXT,
            headquarters TEXT,
            canadian_owned TEXT,
            industry TEXT,
            cuisine TEXT,
            total_investment_range TEXT,
            franchise_fee TEXT,
            royalty_percent TEXT,
            marketing_fund_percent TEXT,
            min_liquid_capital TEXT,
            market_saturation TEXT,
            threat_level TEXT,
            operational_difficulty TEXT,
            franchisor_confirmation TEXT,
            source_count INTEGER DEFAULT 0,
            evidence_grade TEXT,
            decision_posture TEXT,
            rejected_fields INTEGER,
            verified_core_fee_fields INTEGER DEFAULT 0,
            official_brand_source_count INTEGER DEFAULT 0,
            government_or_law_source_count INTEGER DEFAULT 0,
            cross_border_caution TEXT,
            research_track TEXT,
            top_critical_gaps TEXT,
            official_brand_sources TEXT,
            government_or_law_sources TEXT,
            report_text TEXT,
            FOREIGN KEY (category) REFERENCES categories(category)
        );

        CREATE TABLE source_evidence (
            evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id TEXT NOT NULL,
            brand TEXT NOT NULL,
            field_key TEXT NOT NULL,
            field_value TEXT,
            source_url TEXT,
            source_domain TEXT,
            source_type TEXT,
            source_date TEXT,
            source_reliability INTEGER,
            investor_scoring_use TEXT,
            report_path TEXT,
            FOREIGN KEY (brand_id) REFERENCES brands(brand_id)
        );

        CREATE TABLE research_priorities (
            priority_id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id TEXT NOT NULL,
            brand TEXT NOT NULL,
            research_track TEXT NOT NULL,
            evidence_grade TEXT,
            source_depth_rank INTEGER,
            source_count INTEGER DEFAULT 0,
            official_brand_source_count INTEGER DEFAULT 0,
            verified_core_fee_fields INTEGER DEFAULT 0,
            cross_border_caution TEXT,
            decision_posture TEXT,
            priority_reason TEXT,
            report_path TEXT,
            FOREIGN KEY (brand_id) REFERENCES brands(brand_id)
        );

        CREATE VIRTUAL TABLE reports_fts USING fts5(
            brand,
            category,
            report_text,
            content='brands',
            content_rowid='rowid'
        );

        CREATE INDEX idx_brands_category ON brands(category);
        CREATE INDEX idx_brands_research_track ON brands(research_track);
        CREATE INDEX idx_brands_evidence_grade ON brands(evidence_grade);
        CREATE INDEX idx_brands_score ON brands(generic_screening_score DESC);
        CREATE INDEX idx_brands_source_depth ON brands(source_depth_rank);
        CREATE INDEX idx_brands_cross_border ON brands(cross_border_caution);
        CREATE INDEX idx_evidence_brand_id ON source_evidence(brand_id);
        CREATE INDEX idx_evidence_source_type ON source_evidence(source_type);
        CREATE INDEX idx_evidence_domain ON source_evidence(source_domain);
        CREATE INDEX idx_priorities_track_rank ON research_priorities(research_track, source_depth_rank);

        CREATE VIEW v_deep_dive_candidates AS
        SELECT
            brand,
            category,
            generic_screening_score,
            evidence_grade,
            source_count,
            verified_core_fee_fields,
            cross_border_caution,
            report_path,
            decision_posture
        FROM brands
        WHERE research_track = 'deep_dive_candidate'
        ORDER BY source_depth_rank;

        CREATE VIEW v_source_rebuild_queue AS
        SELECT
            brand,
            category,
            evidence_grade,
            source_count,
            official_brand_source_count,
            verified_core_fee_fields,
            top_critical_gaps,
            report_path
        FROM brands
        WHERE research_track IN ('rebuild_from_primary_sources', 'find_official_brand_sources', 'verify_core_franchise_fees')
        ORDER BY
            CASE research_track
                WHEN 'rebuild_from_primary_sources' THEN 1
                WHEN 'find_official_brand_sources' THEN 2
                WHEN 'verify_core_franchise_fees' THEN 3
                ELSE 4
            END,
            source_depth_rank;

        CREATE VIEW v_category_summary AS
        SELECT
            category,
            COUNT(*) AS brand_count,
            ROUND(AVG(generic_screening_score), 1) AS average_screening_score,
            SUM(CASE WHEN research_track = 'deep_dive_candidate' THEN 1 ELSE 0 END) AS deep_dive_count,
            SUM(CASE WHEN research_track = 'rebuild_from_primary_sources' THEN 1 ELSE 0 END) AS rebuild_count,
            SUM(CASE WHEN research_track = 'verify_core_franchise_fees' THEN 1 ELSE 0 END) AS verify_fee_count,
            SUM(CASE WHEN evidence_grade IN ('B', 'C+') THEN 1 ELSE 0 END) AS stronger_evidence_count
        FROM brands
        GROUP BY category
        ORDER BY category;

        CREATE VIEW v_under_320k_screening_candidates AS
        SELECT
            brand,
            category,
            generic_screening_score,
            total_investment_range,
            franchise_fee,
            evidence_grade,
            verified_core_fee_fields,
            cross_border_caution,
            report_path
        FROM brands
        WHERE
            total_investment_range LIKE '%$%'
            AND total_investment_range NOT LIKE '%USD%'
            AND total_investment_range NOT LIKE '%million%'
            AND total_investment_range NOT LIKE '%Not Verified%'
            AND total_investment_range NOT LIKE '%Estimated%'
        ORDER BY generic_screening_score DESC, source_depth_rank;
        """
    )


def insert_rows(conn: sqlite3.Connection, brand_rows: list[dict[str, str]], evidence_rows: list[dict[str, str]], priority_rows: list[dict[str, str]]) -> None:
    category_names = sorted({row["category"] for row in brand_rows})
    conn.executemany(
        "INSERT INTO categories(category) VALUES (?)",
        [(category,) for category in category_names],
    )

    brand_records: list[dict[str, object]] = []
    brand_id_by_name: dict[str, str] = {}
    for row in brand_rows:
        normalized = normalize_row(row, BRAND_FIELDS)
        brand_id = brand_id_from_name(str(normalized["brand"]))
        normalized["brand_id"] = brand_id
        report_path = ROOT / str(normalized["report_path"])
        normalized["report_text"] = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
        brand_id_by_name[str(normalized["brand"])] = brand_id
        brand_records.append(normalized)

    brand_columns = ["brand_id", *BRAND_FIELDS, "report_text"]
    brand_placeholders = ", ".join(f":{column}" for column in brand_columns)
    conn.executemany(
        f"INSERT INTO brands({', '.join(brand_columns)}) VALUES ({brand_placeholders})",
        brand_records,
    )

    evidence_records: list[dict[str, object]] = []
    for row in evidence_rows:
        normalized = normalize_row(row, EVIDENCE_FIELDS)
        normalized["brand_id"] = brand_id_by_name[str(normalized["brand"])]
        evidence_records.append(normalized)

    evidence_columns = [
        "brand_id",
        "brand",
        "field_key",
        "field_value",
        "source_url",
        "source_domain",
        "source_type",
        "source_date",
        "source_reliability",
        "investor_scoring_use",
        "report_path",
    ]
    evidence_placeholders = ", ".join(f":{column}" for column in evidence_columns)
    conn.executemany(
        f"INSERT INTO source_evidence({', '.join(evidence_columns)}) VALUES ({evidence_placeholders})",
        evidence_records,
    )

    priority_records: list[dict[str, object]] = []
    for row in priority_rows:
        normalized = normalize_row(row, PRIORITY_FIELDS)
        normalized["brand_id"] = brand_id_by_name[str(normalized["brand"])]
        priority_records.append(normalized)

    priority_columns = [
        "brand_id",
        "brand",
        "research_track",
        "evidence_grade",
        "source_depth_rank",
        "source_count",
        "official_brand_source_count",
        "verified_core_fee_fields",
        "cross_border_caution",
        "decision_posture",
        "priority_reason",
        "report_path",
    ]
    priority_placeholders = ", ".join(f":{column}" for column in priority_columns)
    conn.executemany(
        f"INSERT INTO research_priorities({', '.join(priority_columns)}) VALUES ({priority_placeholders})",
        priority_records,
    )

    conn.execute(
        """
        INSERT INTO reports_fts(rowid, brand, category, report_text)
        SELECT rowid, brand, category, report_text FROM brands
        """
    )

    conn.execute(
        """
        UPDATE categories
        SET
            brand_count = (SELECT COUNT(*) FROM brands WHERE brands.category = categories.category),
            average_screening_score = (SELECT ROUND(AVG(generic_screening_score), 1) FROM brands WHERE brands.category = categories.category),
            deep_dive_count = (SELECT COUNT(*) FROM brands WHERE brands.category = categories.category AND research_track = 'deep_dive_candidate'),
            rebuild_count = (SELECT COUNT(*) FROM brands WHERE brands.category = categories.category AND research_track = 'rebuild_from_primary_sources'),
            verify_fee_count = (SELECT COUNT(*) FROM brands WHERE brands.category = categories.category AND research_track = 'verify_core_franchise_fees')
        """
    )


def write_metadata(conn: sqlite3.Connection, brand_count: int, evidence_count: int, priority_count: int) -> None:
    metadata = {
        "database_name": "GetFranchise local research database",
        "database_file": DATABASE_FILE.name,
        "built_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "source_export_date": EXPORT_DATE,
        "brand_rows": str(brand_count),
        "source_evidence_rows": str(evidence_count),
        "research_priority_rows": str(priority_count),
        "purpose": "Queryable local database for franchise screening, source evidence, and research triage.",
        "investment_use": "Screening and diligence planning only; not final investment advice.",
    }
    conn.executemany(
        "INSERT INTO database_metadata(key, value) VALUES (?, ?)",
        sorted(metadata.items()),
    )


def build_database() -> dict[str, int]:
    brand_rows = read_csv(BRAND_CSV)
    evidence_rows = read_csv(EVIDENCE_CSV)
    priority_rows = read_csv(PRIORITY_CSV)

    if DATABASE_FILE.exists():
        DATABASE_FILE.unlink()

    with sqlite3.connect(DATABASE_FILE) as conn:
        conn.row_factory = sqlite3.Row
        execute_schema(conn)
        insert_rows(conn, brand_rows, evidence_rows, priority_rows)
        write_metadata(conn, len(brand_rows), len(evidence_rows), len(priority_rows))
        conn.execute("PRAGMA user_version = 1")
        conn.execute("PRAGMA optimize")

    return {
        "brands": len(brand_rows),
        "source_evidence": len(evidence_rows),
        "research_priorities": len(priority_rows),
    }


def write_manifest(counts: dict[str, int]) -> None:
    manifest = [
        "# GetFranchise SQLite Database Manifest",
        "",
        f"Database file: `{DATABASE_FILE.name}`",
        f"Built from export date: `{EXPORT_DATE}`",
        "",
        "## Tables",
        "- `brands`: one row per franchise brand, with report path, screening fields, source counts, evidence grade, and research track.",
        "- `source_evidence`: one row per source-backed evidence item, linked to `brands.brand_id`.",
        "- `research_priorities`: one row per brand in the research queue, linked to `brands.brand_id`.",
        "- `categories`: one row per normalized category with portfolio rollups.",
        "- `database_metadata`: build metadata and usage warnings.",
        "- `reports_fts`: full-text search index over brand reports.",
        "",
        "## Views",
        "- `v_deep_dive_candidates`: strongest shortlist for manual diligence.",
        "- `v_source_rebuild_queue`: brands needing primary-source rebuild, official sources, or fee verification.",
        "- `v_category_summary`: category-level counts and evidence summary.",
        "- `v_under_320k_screening_candidates`: preliminary CAD-only cost candidates where public ranges look under the target filter.",
        "",
        "## Row Counts",
        f"- Brands: {counts['brands']}",
        f"- Source evidence rows: {counts['source_evidence']}",
        f"- Research priority rows: {counts['research_priorities']}",
        "",
        "## Example Queries",
        "Command-line helpers:",
        "",
        "```powershell",
        "python query_getfranchise_database.py summary",
        "python query_getfranchise_database.py deep-dive",
        "python query_getfranchise_database.py rebuild-queue --limit 25",
        "python query_getfranchise_database.py brand Subway",
        "python query_getfranchise_database.py search disclosure --limit 10",
        "```",
        "",
        "Direct SQL examples:",
        "",
        "```sql",
        "SELECT brand, category, evidence_grade, source_count",
        "FROM v_deep_dive_candidates;",
        "",
        "SELECT category, brand_count, average_screening_score, rebuild_count",
        "FROM v_category_summary",
        "ORDER BY category;",
        "",
        "SELECT brand, field_key, source_domain, source_reliability",
        "FROM source_evidence",
        "WHERE source_type = 'official_brand_or_company'",
        "ORDER BY brand, field_key;",
        "",
        "SELECT brands.brand, brands.category",
        "FROM reports_fts",
        "JOIN brands ON brands.rowid = reports_fts.rowid",
        "WHERE reports_fts MATCH 'disclosure NEAR entity';",
        "```",
        "",
        "## Use Boundary",
        "This is a screening and diligence-planning database. It is not investment-grade until Canadian disclosure packages, signing entities, recurring fees, unit economics, closure/transfer/renewal history, and franchisee interviews are verified.",
    ]
    MANIFEST_FILE.write_text("\n".join(manifest) + "\n", encoding="utf-8")


def main() -> None:
    counts = build_database()
    write_manifest(counts)
    print(json.dumps({"database": str(DATABASE_FILE), **counts}, indent=2))


if __name__ == "__main__":
    main()
