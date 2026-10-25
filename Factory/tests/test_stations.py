from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from common import GATES, read_json, validate_document
from integration.website_writer import write_to_website
from stations.station1_extract import extract
from stations.station2_clean import clean
from stations.station3_publish import publish


def complete_report() -> str:
    sections = "\n\n".join(f"{number}. SECTION {number}\nContent" for number in range(1, 8))
    gates = "\n".join(f"- {gate}: PASS" for gate in GATES)
    return (
        f"TEST FRANCHISE\n\n{sections}\n\n8. EVIDENCE STATUS\nEvidence Gates\n{gates}\n\n"
        "9. SOURCES\nTotal Source Count: 1\n"
        "Source-Backed Evidence Loaded\n"
        "- financials.franchise_fee: $100,000 CAD | Source: https://example.test/franchise | Date: 2026-09-20 | Reliability: 90 | Investor scoring use: Yes\n"
        "Evidence Source URLs:\n- example.test | 2026-09-20 | Reliability 90 | https://example.test/franchise\n"
    )


class StationTests(unittest.TestCase):
    def test_factory_writer_keeps_unclassified_sources_out_of_public_shortlist(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            website_data = Path(temp) / "brands.json"
            website_data.write_text("[]", encoding="utf-8")
            fields = [
                {
                    "field_id": "financials.minimum_liquid_capital",
                    "value": "$250,000 CAD",
                    "status": "verified",
                    "source": {"url": "https://example.test/franchise", "date": "2026-09-20", "reliability": 90},
                }
            ]
            gates = [{"name": gate, "result": "PASS"} for gate in GATES]

            write_to_website("Test Franchise", fields, gates, website_data)

            [row] = json.loads(website_data.read_text(encoding="utf-8"))
            self.assertEqual(row["public_profile_status"], "internal_research_queue")
            self.assertEqual(row["ready_candidate"], "No")
            self.assertEqual(row["official_brand_source_count"], 0)
            self.assertEqual(row["verified_core_fee_fields"], 1)
            self.assertEqual(row["min_liquid_capital"], "$250,000 CAD")

    def test_three_station_records_match_schemas(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reports = root / "reports"
            reports.mkdir()
            (reports / "Test Franchise.txt").write_text(complete_report(), encoding="utf-8")
            logs, raw_dir, clean_dir, published_dir = (root / "logs", root / "raw", root / "clean", root / "published")
            raw = extract("Test Franchise", reports, raw_dir, logs)
            self.assertEqual(validate_document(read_json(raw), "franchise_raw.schema.json"), [])
            clean_file = clean(raw, clean_dir, logs)
            self.assertEqual(validate_document(read_json(clean_file), "franchise_clean.schema.json"), [])
            with patch("stations.station3_publish.write_to_website", return_value={"operation": "inserted", "confirmed": True}):
                published = publish(clean_file, published_dir, logs)
            self.assertEqual(validate_document(read_json(published), "franchise_published.schema.json"), [])

    def test_publish_refuses_failed_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            clean_path = root / "failed.json"
            clean_path.write_text(json.dumps({
                "schema_version": "1.0", "franchise": "Test Franchise", "slug": "test-franchise", "raw_path": "raw.json", "cleaned_at": "now",
                "fields": [{"field_id": "financials.franchise_fee", "value": "$100,000", "status": "verified", "source": {"url": "https://example.test", "date": "2026", "reliability": 90}}],
                "evidence_gates": [{"name": gate, "result": "FAIL"} for gate in GATES], "deletions": [],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "all eight evidence gates"):
                publish(clean_path, root / "published", root / "logs")

    def test_publish_does_not_mutate_website_when_record_write_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reports = root / "reports"
            reports.mkdir()
            (reports / "Test Franchise.txt").write_text(complete_report(), encoding="utf-8")
            logs, raw_dir, clean_dir = root / "logs", root / "raw", root / "clean"
            raw = extract("Test Franchise", reports, raw_dir, logs)
            clean_file = clean(raw, clean_dir, logs)
            with patch("stations.station3_publish.write_json", side_effect=OSError("disk full")), patch("stations.station3_publish.write_to_website") as website_write:
                with self.assertRaisesRegex(OSError, "disk full"):
                    publish(clean_file, root / "published", logs)
            website_write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
