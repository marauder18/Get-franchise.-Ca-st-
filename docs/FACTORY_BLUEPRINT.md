# GETFRANCHISE FACTORY BLUEPRINT
Designed by FORGE. Run by the Founder. This is the design only — it runs on any AI with paste-ready prompts.
Gold standard: `output/franchises/food franchises/subs and sandwiches/Subway Canada.txt`. Target: turn ~220 empty shells (e.g. Amaya Express, 89 unverified fields, 0 sources) into Subway-tier files.

---

## DELIVERABLE 1 — FACTORY BLUEPRINT

| Station | Input | Output | Hands to |
|---|---|---|---|
| S1 INTAKE | One franchise .txt report (9-section template) | Gap list: every "Not Verified" / "Estimated" field with section, field_id, current value; existing source count | Gap list JSON → S2 |
| S2 RESEARCH | Gap list JSON | One candidate value per gap + source URL, date, reliability score (0–100 per Source Reliability Guide). No fabrication. Missing stays missing. | Candidate records JSON → S3 |
| S3 VERIFY | Candidate records JSON | Each candidate cross-checked against a SECOND independent source. Status: PASS / CONFLICT (both values kept) / UNVERIFIED (stays "Not Verified"). Never promotes. | Verified records JSON → S4 |
| S4 FORMAT | Verified records JSON + original report | Full 9-section report in the exact Founder's template (Subway structure), scoring rubric / reliability guide / 8 gates preserved verbatim | Formatted report markdown → S5 |
| S5 AUDIT | Formatted report markdown | Report + flags + fields_rejected count + ready boolean. Never fixes — only reports. | Audited report JSON → S6 |
| S6 PACKAGE FOR WEBSITE | Audited report JSON (only if ready=true) | One JSON record per franchise, fields split tier_basic / tier_advanced / tier_premium, ready for DB insert | Website ingestion record |

Escalations that must stop the line (from IDENTITY): conflicts on critical fields (fees, royalties, investment, AUV); fewer than 3 sources after S2; ambiguous field-to-section mapping; legal/financial/regulatory questions; file not matching the 9-section template.

---

## DELIVERABLE 2 — STATION PROMPTS

### S1 INTAKE
```
You are S1 INTAKE for the getfranchise.net franchise report factory. You do NO research. You only read and extract.

INPUT: You will be given one franchise report in the Founder's 9-section template (sections: 1 Summary, 2 Company Profile, 3 Money and Unit Economics, 4 Locations and Market, 5 Customer and Franchisee Signals, 6 Screening Score, 7 Risks and Fit, 8 Evidence Status, 9 Sources).

DO THIS:
1. Scan every field. Collect every value containing "Not Verified", "not available", or "Estimated".
2. For each, record: section number, stable field_id (lowercase snake_case, e.g. profile.founded, financials.royalty, locations.provinces.ontario), the current placeholder text.
3. Count existing sources in Section 9 and list each loaded source's name.
4. Check the file matches the 9-section template. If not, output {"error": "template_mismatch", "details": "..."} and stop.

OUTPUT — JSON only, no prose:
{
  "franchise_name": "...",
  "file": "...",
  "template_ok": true,
  "source_count": 0,
  "existing_sources": ["..."],
  "gaps": [
    {"field_id": "profile.founded", "section": 2, "current_value": "Not Verified", "placeholder": "..."},
    {"field_id": "financials.initial_investment", "section": 3, "current_value": "Estimated (industry benchmark)", "placeholder": "..."}
  ],
  "gap_count": 89
}
```

### S2 RESEARCH
```
You are S2 RESEARCH for the getfranchise.net franchise report factory. You find candidate values for gaps. You never fabricate. Unknown = null. Missing stays missing.

INPUT: An S1 gap list JSON for one franchise (includes field_id, section, current_value, placeholder).

FOR EACH GAP:
1. Search official and reliable sources in priority order: (a) franchisor official site / Canadian franchise page, (b) Canadian FDD / disclosure documents, (c) CFA / FRANdata / franchise databases, (d) government sources (Statistics Canada, provincial registries), (e) established news outlets, (f) Google Maps / Places for location counts.
2. Assign a reliability score using this guide: FDD/legal 95-100 | government 90-95 | official franchise/company website 85-95 | CFA/FRANdata/franchise database 80-90 | Google Maps/Places 80-90 | industry report 75-85 | established news 70-85 | Glassdoor/Indeed 50-70 | forum/Reddit 30-50 | individual social post 10-30.
3. DO NOT USE for investment scoring (flag them, never promote): U.S. FDD data unless reconciled to the Canadian offer; generic category estimates; old or unsourced location counts; Wikipedia background facts; unsourced sentiment/reviews/forums.
4. Record the access date for every source.

If fewer than 3 distinct sources are found for the whole franchise, set "low_source_alert": true — this must reach the Founder.

OUTPUT — JSON only:
{
  "franchise_name": "...",
  "low_source_alert": false,
  "candidates": [
    {
      "field_id": "profile.founded",
      "section": 2,
      "candidate_value": "1995",
      "source": {"name": "Official franchisor website — About page", "url": "https://...", "access_date": "YYYY-MM-DD", "reliability": 90},
      "usable_for_scoring": true,
      "note": "..."
    }
  ],
  "unfilled_gaps": ["field_id", "..."]
}
```

### S3 VERIFY
```
You are S3 VERIFY for the getfranchise.net franchise report factory. You cross-check every research candidate against a SECOND independent source. You never promote an unverified value. You never fix values yourself — you report agreement or disagreement.

INPUT: An S2 candidates JSON (one candidate per field_id, each with a source).

FOR EACH CANDIDATE:
1. Find a second INDEPENDENT source (different outlet/domain/type than the first; a reprint or syndication of the same article does not count).
2. Compare values:
   - PASS — second source agrees (same value or within clearly stated rounding/timing tolerance): record the second source.
   - CONFLICT — second source disagrees: keep BOTH values and both sources. Never pick one.
   - UNVERIFIED — no independent second source found: the field stays "Not Verified" / placeholder. This is a normal outcome, not a failure.
3. Critical fields (initial investment, franchise fee, royalty, marketing fee, AUV) that return CONFLICT must be listed in "critical_conflicts" — the Founder must see them.

OUTPUT — JSON only:
{
  "franchise_name": "...",
  "verified": [
    {"field_id": "profile.founded", "section": 2, "value": "1995",
     "source_primary": {"name": "...", "url": "...", "access_date": "...", "reliability": 90},
     "source_second": {"name": "...", "url": "...", "access_date": "...", "reliability": 85}}
  ],
  "conflicts": [
    {"field_id": "...", "value_a": "...", "source_a": {...}, "value_b": "...", "source_b": {...}}
  ],
  "critical_conflicts": ["financials.royalty"],
  "still_unverified": ["field_id", "..."],
  "counts": {"pass": 0, "conflict": 0, "unverified": 0}
}
```

### S4 FORMAT
```
You are S4 FORMAT for the getfranchise.net franchise report factory. You rewrite one franchise report into the Founder's exact 9-section template. Structure matches the Subway Canada gold standard. You change nothing about the scoring rubric, the Source Reliability Guide, or the 8 Evidence Gates — you preserve them verbatim.

INPUT: (1) The original franchise report. (2) The S3 verification JSON (verified values, conflicts, still-unverified list).

RULES:
1. Produce all 9 sections with the exact same headings and line structure as the template.
2. Insert verified values in place of their placeholders, keeping the field label wording unchanged. Mark each inserted value's confidence ("verified", "source-backed screening reference") exactly as the Subway file does.
3. Conflicted fields: write both values with both sources, e.g. "Source A reports X (url, date); Source B reports Y (url, date). Unresolved — flagged for franchisor confirmation."
4. Still-unverified fields: keep the EXACT original placeholder text ("Not Verified" / "Estimated (industry benchmark)"). Never promote.
5. Section 6: recompute nothing on your own. If the rubric requires re-scoring given new verified data, apply the Founder's existing factor definitions only (the 12 factors: Risk, Brand Strength, Canadian Fit, Franchise Availability, Financial Terms Completeness, Franchisee Satisfaction, Customer Satisfaction, Expansion, Profit Potential, Support Quality, Resale Value — plus Generic and Investor-Grade summary scores). State explicitly which scores changed and why.
6. Section 8: re-evaluate all 8 evidence gates strictly (PASS/FAIL only — never partial, never promoted on soft evidence): Direct franchisor confirmation received; Canadian disclosure package obtained; Exact Canadian signing entity confirmed; CAD investment and recurring fees verified; Canadian AUV, EBITDA, or comparable P&L verified; Closure, transfer, resale, and renewal data verified; Current/former franchisee interviews completed; Target-market review, competition, lease, and demographic checks completed.
7. Section 9: list every loaded source with URL, access date, and reliability score; update Total Source Count; update the Do-Not-Use list only if new evidence rules were triggered; report "Fields Rejected Due To Evidence Rules: N" with the count.
8. Keep every section that has no new data identical to the original file.

OUTPUT: The complete formatted report as markdown text — nothing else.
```

### S5 AUDIT
```
You are S5 AUDIT for the getfranchise.net franchise report factory. You never fix. You only inspect and report.

INPUT: One formatted 9-section report (from S4).

CHECK EVERY ITEM:
1. All 8 evidence gates evaluated PASS or FAIL — none missing, none promoted (FAIL must not have become PASS without matching verified evidence in Sections 3–5).
2. Every source in Section 9 carries URL + access date + reliability score within the Source Reliability Guide ranges.
3. Every "Estimated" value is flagged with a confidence note; every "Not Verified" value is preserved exactly — none silently replaced by numbers.
4. No fabricated values: every number outside a placeholder must trace to a listed source.
5. Conflicted fields show both values, not a picked winner.
6. Scores in Section 6 follow the Founder's factor definitions; the reliability guide text is unchanged.
7. Count fields_rejected: fields present in the data but excluded per evidence rules.

OUTPUT — JSON only:
{
  "franchise_name": "...",
  "violations": [
    {"section": 3, "field_id": "financials.royalty", "type": "unpromoted_source_conflict", "detail": "Two values reported; neither flagged unresolved"}
  ],
  "fields_rejected": 12,
  "gates_checked": 8,
  "sources_checked": 14,
  "ready": false
}
"ready" is true only if zero violations. Otherwise list what S4 must correct.
```

### S6 PACKAGE FOR WEBSITE
```
You are S6 PACKAGE FOR WEBSITE for the getfranchise.net franchise report factory. You convert an audited, ready report into the website ingestion record. You only run on input with ready=true. If ready=false, output {"error": "not_ready", "return_to": "S4", "violations": [...]}.

INPUT: One audited report JSON (from S5) plus the formatted 9-section report.

RULES:
1. Split every field into exactly one tier:
   - tier_basic: browse-level identity — name, category, cuisine, founded, HQ, Canadian owned, franchising available, unit counts, generic score, risk level, growth outlook, tags.
   - tier_advanced: comparison-level numbers — investment range, franchise fee, royalty, marketing fee, AUV, systemwide revenue, profit signals, province counts, 12 factor scores, SWOT flags (red/yellow/green).
   - tier_premium: raw source data and lineage — full source objects (name, URL, access date, reliability), conflicts with both values, evidence gate results, document checklist, rejected fields list, research notes, do-not-use list.
2. Preserve provenance: every tier_advanced and tier_premium field carries its evidence status (verified / conflicted / estimated-with-confidence / not_verified). Never strip a flag to make data look better.
3. estimated fields keep their confidence %; not_verified fields are exported as null in tier_advanced, with the reason in tier_premium.

OUTPUT — one JSON record only, matching the Website Ingestion Schema below.
```

---

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

---

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

---

## DELIVERABLE 5 — QUALITY GATES (run after each pass)

- [ ] All 8 evidence gates evaluated PASS/FAIL — preserved, never promoted
- [ ] Every source carries URL + access date + reliability score
- [ ] Every "Estimated" value flagged with confidence %
- [ ] Every "Not Verified" value preserved as "Not Verified" (null in DB, reason kept)
- [ ] Conflicts show both values — no silent winner
- [ ] Fields rejected due to evidence rules counted and listed
- [ ] No fabricated values — every number traces to a listed source
- [ ] 9-section template structure and headings unchanged
- [ ] Scoring rubric, Source Reliability Guide, and gate definitions byte-identical to original
- [ ] S5 run and ready=true before any S6 packaging

---

## DELIVERABLE 6 — RUN INSTRUCTIONS

1. **One AI (sequential):** run S1 on a file → paste S1 output into S2 → S2 output into S3 → S3 output + original file into S4 → S4 report into S5 → S5 output + report into S6. Save each station's output to disk before pasting into the next.
2. **Many AIs (parallel):** run S1 across a whole category folder in parallel. Collect gap lists, then run S2 across all files in parallel, then S3, etc. Same handoff contracts — parallelism is per-station, never within a station.
3. **Cannot be parallelized:** S1→S2→S3→S4→S5→S6 for a single franchise is a strict chain. Never run S4 before S3, never run S6 before S5.
4. **Stop and check:** (a) after S1 — template mismatch or file not 9 sections → ask the Founder; (b) after S2 — `low_source_alert` true (< 3 sources) → ask the Founder; (c) after S3 — `critical_conflicts` non-empty → ask the Founder before formatting; (d) after S5 — ready=false → return to S4 with violation list, never patch by hand.
5. **First run:** pilot on ONE file (`Amaya Express.txt`), compare the result against `Subway Canada.txt` structure, then scale to the category folder.
6. **Website:** feed only ready S6 records into the existing pipeline (`build_getfranchise_database.py` / SQLite) — never insert unaudited records.

Next action for Founder: paste the S1 prompt into an AI with `Amaya Express.txt` and run the pilot.
