# HANDOFF CONTRACTS + WEBSITE INGESTION SCHEMA

## DELIVERABLE 3 — HANDOFF CONTRACTS

**S1→S2 (gap list)**
```json
{
  "franchise_name": {"type": "string", "required": true},
  "file": {"type": "string", "required": true},
  "template_ok": {"type": "boolean", "required": true},
  "source_count": {"type": "integer", "required": true},
  "existing_sources": {"type": "array<string>", "required": true},
  "gaps": {"type": "array<gap>", "required": true},
  "gap_count": {"type": "integer", "required": true}
}
// gap = {"field_id": string, "section": int 1-9, "current_value": string, "placeholder": string}
// Example: {"field_id": "financials.initial_investment", "section": 3, "current_value": "Estimated (industry benchmark)", "placeholder": "lower to mid six figures CAD buildout"}
```

**S2→S3 (candidates)**
```json
{
  "franchise_name": {"type": "string", "required": true},
  "low_source_alert": {"type": "boolean", "required": true},
  "candidates": {"type": "array<candidate>", "required": true},
  "unfilled_gaps": {"type": "array<string>", "required": true}
}
// candidate = {"field_id": string, "section": int, "candidate_value": string|null,
//   "source": {"name": string, "url": string, "access_date": "YYYY-MM-DD", "reliability": int 10-100},
//   "usable_for_scoring": boolean, "note": string}
```

**S3→S4 (verified)**
```json
{
  "franchise_name": {"type": "string", "required": true},
  "verified": {"type": "array<verified_field>", "required": true},
  "conflicts": {"type": "array<conflict>", "required": true},
  "critical_conflicts": {"type": "array<string>", "required": true},
  "still_unverified": {"type": "array<string>", "required": true},
  "counts": {"type": "object", "required": true}
}
// verified_field = {"field_id": string, "section": int, "value": string, "source_primary": source, "source_second": source}
// conflict = {"field_id": string, "value_a": string, "source_a": source, "value_b": string, "source_b": source}
// source = {"name": string, "url": string, "access_date": "YYYY-MM-DD", "reliability": int}
```

**S4→S5 (formatted report)**
```json
{
  "franchise_name": {"type": "string", "required": true},
  "report_markdown": {"type": "string", "required": true},
  "gate_results": {"type": "array<gate>", "required": true},
  "source_count": {"type": "integer", "required": true},
  "fields_rejected": {"type": "integer", "required": true}
}
// gate = {"name": string, "result": "PASS"|"FAIL"}
```

**S5→S6 (audit)**
```json
{
  "franchise_name": {"type": "string", "required": true},
  "violations": {"type": "array<violation>", "required": true},
  "fields_rejected": {"type": "integer", "required": true},
  "gates_checked": {"type": "integer", "required": true},
  "sources_checked": {"type": "integer", "required": true},
  "ready": {"type": "boolean", "required": true}
}
// violation = {"section": int, "field_id": string, "type": string, "detail": string}
```

## DELIVERABLE 4 — WEBSITE INGESTION SCHEMA

```json
{
  "record": {
    "franchise_id": "slug-from-name",
    "name": "Subway Canada",
    "last_updated": "YYYY-MM-DD",
    "audit_ready": true,

    "tier_basic": {
      "category": "food > subs and sandwiches",
      "cuisine_type": "Sandwiches, salads, bowls",
      "founded": {"value": "1965", "status": "screening_reference"},
      "hq": {"value": "Shelton, Connecticut", "status": "screening_reference"},
      "canadian_owned": {"value": false, "status": "screening_reference"},
      "franchise_available_canada": {"value": true, "status": "verified"},
      "units_canada": {"value": 3012, "as_of": "2026-07-15", "status": "verified"},
      "units_international": {"value": "35,000+", "status": "screening_reference"},
      "generic_score": 69,
      "risk_level": "Medium",
      "growth_outlook": "Neutral",
      "tags": ["Screening Only", "Investor Gates Incomplete"]
    },

    "tier_advanced": {
      "initial_investment_cad": {"value": null, "status": "not_verified", "reason": "no Canadian disclosure loaded"},
      "franchise_fee_cad": {"value": null, "status": "not_verified"},
      "royalty_pct": {"value": 8.0, "status": "conflicted", "values": [8.0, 6.0], "note": "unresolved — franchisor confirmation required"},
      "marketing_fee_pct": {"value": 4.5, "status": "estimated", "confidence_pct": 20},
      "auv_cad": {"value": null, "status": "not_verified"},
      "systemwide_revenue": {"value": "971.9M USD", "year": 2023, "status": "screening_reference"},
      "province_counts": {"ON": null, "QC": null, "BC": null},
      "factor_scores": {"risk": 67, "brand_strength": 65, "canadian_fit": 49, "franchise_availability": 10, "financial_terms_completeness": 52, "franchisee_satisfaction": 55, "customer_satisfaction": 60, "expansion": 52, "profit_potential": 65, "support_quality": 55, "resale_value": 62},
      "swot_flags": {"red": ["..."], "yellow": ["..."], "green": ["..."]}
    },

    "tier_premium": {
      "sources": [{"name": "...", "url": "...", "access_date": "...", "reliability": 90}],
      "conflicts": [{"field_id": "...", "value_a": "...", "source_a": "...", "value_b": "...", "source_b": "..."}],
      "evidence_gates": [{"name": "Direct franchisor confirmation received", "result": "FAIL"}],
      "document_checklist": ["..."],
      "fields_rejected": 12,
      "do_not_use_list": ["..."],
      "research_notes": ["..."]
    }
  }
}
```
Field-to-tier rule: identity/browse → basic; money and comparison numbers → advanced; raw source objects, lineage, and audit trail → premium. Every non-basic field carries `status`; estimated keeps `confidence_pct`; not_verified exports as `null` in tier_advanced with the reason preserved in tier_premium.
