"""Split approved factory fields without creating fields that do not exist."""
from __future__ import annotations

from typing import Any


BASIC_PREFIXES = ("profile.", "company.")
ADVANCED_PREFIXES = ("financials.", "locations.", "operations.", "signals.")


def split_fields(fields: list[dict[str, Any]], gates: list[dict[str, str]], deletions: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    verified = {field["field_id"]: field for field in fields if field["status"] == "verified"}
    basic = {key: value for key, value in verified.items() if key.startswith(BASIC_PREFIXES)}
    advanced = {key: value for key, value in verified.items() if key.startswith(ADVANCED_PREFIXES)}
    premium = {"fields": fields, "evidence_gates": gates, "deletions": deletions}
    return {"tier_basic": basic, "tier_advanced": advanced, "tier_premium": premium}
