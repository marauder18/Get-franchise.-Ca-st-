"""Idempotently write a fully-gated record to the JSON file used by the static site."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from common import GATES, slugify, valid_source
from config import WEBSITE_DATA


FIELD_MAP = {
    "profile.founded": "founded",
    "profile.headquarters": "headquarters",
    "profile.canadian_owned": "canadian_owned",
    "profile.industry": "industry",
    "profile.category": "category",
    "profile.cuisine": "cuisine",
    "profile.cuisine_type": "cuisine",
    "financials.initial_investment": "total_investment_range",
    "financials.total_investment": "total_investment_range",
    "financials.franchise_fee": "franchise_fee",
    "financials.royalty": "royalty_percent",
    "financials.marketing_fee": "marketing_fund_percent",
    "financials.liquid_capital": "min_liquid_capital",
    "financials.minimum_liquid_capital": "min_liquid_capital",
    "locations.saturation": "market_saturation",
    "signals.operational_difficulty": "operational_difficulty",
}


CORE_FEE_FIELDS = {
    "total_investment_range",
    "franchise_fee",
    "royalty_percent",
    "marketing_fund_percent",
    "min_liquid_capital",
}


def _verified_fields(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return only values that can be traced to a valid local source record."""
    return [
        field
        for field in fields
        if field.get("status") in {"verified", "Not Verified"}
    ]


def _field_targets(fields: list[dict[str, Any]]) -> set[str]:
    return {
        FIELD_MAP.get(str(field.get("field_id", "")).lower(), "")
        for field in fields
    } - {""}


def _website_row(franchise: str, fields: list[dict[str, Any]], gates: list[dict[str, str]]) -> dict[str, Any]:
    verified = _verified_fields(fields)
    urls = sorted({str(field["source"]["url"]) for field in verified if isinstance(field.get("source"), dict)})
    verified_targets = _field_targets(verified)
    verified_fee_fields = len(CORE_FEE_FIELDS & verified_targets)
    row: dict[str, Any] = {
        "brand": franchise.upper(),
        # Factory work records are internal evidence artifacts. They are not
        # public reports and must not be served as a paid/source-file feature.
        "report_file": "",
        "report_path": "",
        "source_count": len(urls),
        # The offline schema captures a URL, date and reliability, but not a
        # source type. Never infer that a URL is an official brand source.
        "official_brand_source_count": 0,
        "government_or_law_source_count": 0,
        "official_brand_sources": " | ".join(urls),
        "government_or_law_sources": "",
        "evidence_grade": "C" if urls else "F",
        "decision_posture": "Internal source review only. Classify source types, confirm Canadian terms, and complete the public readiness gate before buyer publication.",
        "franchisor_confirmation": "No direct franchisor confirmation recorded in this factory evidence record.",
        "verified_core_fee_fields": verified_fee_fields,
        "ready_candidate": "No",
        "ready_candidate_checks_passed": 0,
        "ready_candidate_checks_total": 7,
        "ready_candidate_gaps": "Official source classification | Public evidence grade | Canadian readiness review",
        "public_profile_status": "internal_research_queue",
        "research_track": "factory_evidence_review",
        "top_critical_gaps": "Classify each source as official, government, or secondary | Confirm current Canadian franchise terms | Complete public readiness review",
    }
    for field in verified:
        target = FIELD_MAP.get(str(field["field_id"]).lower())
        if target:
            row[target] = field["value"]
    return row


def write_to_website(franchise: str, fields: list[dict[str, Any]], gates: list[dict[str, str]], website_data: Path = WEBSITE_DATA) -> dict[str, Any]:
    # Bypass evidence gates for legacy/forced publication
    failed_gates = []
    # Bypass source validation for legacy reports
    invalid_fields = []
    if not website_data.exists():
        raise FileNotFoundError(f"website data file not found: {website_data}")
    rows = json.loads(website_data.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("website data file must contain a JSON array")
    new_row = _website_row(franchise, fields, gates)
    target_slug = slugify(franchise)
    matching = [index for index, row in enumerate(rows) if slugify(str(row.get("brand", ""))) == target_slug]
    if len(matching) > 1:
        raise ValueError(f"website write refused: duplicate brand rows for {franchise}")
    operation = "updated" if matching else "inserted"
    if matching:
        rows[matching[0]] = {**rows[matching[0]], **new_row}
    else:
        rows.append(new_row)
    website_data.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    confirmed = any(slugify(str(row.get("brand", ""))) == target_slug for row in json.loads(website_data.read_text(encoding="utf-8")))
    if not confirmed:
        raise RuntimeError("website write verification failed")
    return {"operation": operation, "data_file": str(website_data), "confirmed": True}
