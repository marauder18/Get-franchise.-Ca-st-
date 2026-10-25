from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATABASE_FILE = ROOT / "getfranchise.sqlite"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def print_rows(rows: list[sqlite3.Row], columns: list[str]) -> None:
    if not rows:
        print("No rows found.")
        return

    widths = {
        column: max(len(column), *(len("" if row[column] is None else str(row[column])) for row in rows))
        for column in columns
    }
    print(" | ".join(column.ljust(widths[column]) for column in columns))
    print("-+-".join("-" * widths[column] for column in columns))
    for row in rows:
        print(" | ".join(("" if row[column] is None else str(row[column])).ljust(widths[column]) for column in columns))


def category_summary(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT category, brand_count, average_screening_score, deep_dive_count, rebuild_count, verify_fee_count
        FROM v_category_summary
        ORDER BY category
        """
    ).fetchall()
    print_rows(rows, ["category", "brand_count", "average_screening_score", "deep_dive_count", "rebuild_count", "verify_fee_count"])


def deep_dive(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT brand, category, generic_screening_score, evidence_grade, source_count, verified_core_fee_fields
        FROM v_deep_dive_candidates
        ORDER BY source_count DESC, generic_screening_score DESC
        """
    ).fetchall()
    print_rows(rows, ["brand", "category", "generic_screening_score", "evidence_grade", "source_count", "verified_core_fee_fields"])


def rebuild_queue(conn: sqlite3.Connection, limit: int) -> None:
    rows = conn.execute(
        """
        SELECT brand, category, evidence_grade, source_count, verified_core_fee_fields, report_path
        FROM v_source_rebuild_queue
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    print_rows(rows, ["brand", "category", "evidence_grade", "source_count", "verified_core_fee_fields", "report_path"])


def search_reports(conn: sqlite3.Connection, query: str, limit: int) -> None:
    rows = conn.execute(
        """
        SELECT brands.brand, brands.category, brands.evidence_grade, brands.report_path
        FROM reports_fts
        JOIN brands ON brands.rowid = reports_fts.rowid
        WHERE reports_fts MATCH ?
        LIMIT ?
        """,
        (query, limit),
    ).fetchall()
    print_rows(rows, ["brand", "category", "evidence_grade", "report_path"])


def brand_detail(conn: sqlite3.Connection, brand: str) -> None:
    rows = conn.execute(
        """
        SELECT brand, category, generic_screening_score, evidence_grade, research_track,
               source_count, verified_core_fee_fields, cross_border_caution, report_path
        FROM brands
        WHERE brand LIKE ?
        ORDER BY source_depth_rank
        """,
        (f"%{brand}%",),
    ).fetchall()
    print_rows(
        rows,
        [
            "brand",
            "category",
            "generic_screening_score",
            "evidence_grade",
            "research_track",
            "source_count",
            "verified_core_fee_fields",
            "cross_border_caution",
            "report_path",
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the GetFranchise SQLite research database.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("summary", help="Show category-level portfolio summary.")
    subparsers.add_parser("deep-dive", help="Show strongest manual diligence candidates.")

    rebuild = subparsers.add_parser("rebuild-queue", help="Show brands that need primary-source rebuild or fee verification.")
    rebuild.add_argument("--limit", type=int, default=25)

    search = subparsers.add_parser("search", help="Full-text search report bodies.")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=20)

    brand = subparsers.add_parser("brand", help="Find a brand by name.")
    brand.add_argument("name")

    args = parser.parse_args()
    with connect() as conn:
        if args.command == "summary":
            category_summary(conn)
        elif args.command == "deep-dive":
            deep_dive(conn)
        elif args.command == "rebuild-queue":
            rebuild_queue(conn, args.limit)
        elif args.command == "search":
            search_reports(conn, args.query, args.limit)
        elif args.command == "brand":
            brand_detail(conn, args.name)


if __name__ == "__main__":
    main()
