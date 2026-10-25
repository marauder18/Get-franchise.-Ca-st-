# GetFranchise Research Plan

Goal: turn the current screening database into a source-backed Canadian franchise diligence database without overstating confidence.

## 1. Prioritize The Queue

Start with the existing database views and priority files:

- `v_deep_dive_candidates`: brands closest to usable diligence.
- `v_source_rebuild_queue`: brands missing primary sources, fees, or disclosure evidence.
- `GETFRANCHISE_NON_FOOD_RESEARCH_QUEUE_2026-07-18.*`: non-food queue.
- `GETFRANCHISE_RESEARCH_PRIORITY_2026-07-18.csv`: food and general priority queue.

Research order:

1. Brands with strong Canadian presence and more existing source depth.
2. Brands under or near the target investment filter of less than `$320,000 CAD`.
3. Brands with official Canadian franchise pages but missing fee/entity/economics fields.
4. Zero-source records, rebuilt from scratch.

## 2. Source Hierarchy

Use sources in this order:

1. Canadian disclosure package or legal franchise document.
2. Official Canadian franchisor/franchise-development page.
3. Canadian corporate registry, provincial registry, or government/legal record.
4. Canadian franchise association, FRANdata-style database, or credible franchise directory.
5. Established business/news source for dated expansions, closures, acquisitions, or disputes.
6. Google Places or location-store APIs for current footprint validation.
7. Aggregated employment/review platforms only for sentiment themes, never exact investment claims.

Reject for investor-grade scoring:

- U.S.-only FDD numbers unless explicitly marked as non-Canadian context.
- USD-only values that are not converted and verified against Canadian terms.
- Old location counts without a source date.
- Blog/review/forum claims from individuals.
- AI-generated summaries without linked primary evidence.

## 3. Field-Level Evidence To Capture

For each brand, capture evidence at the field level:

- `value`
- `source_url`
- `source_date`
- `retrieved_date`
- `source_reliability`
- `evidence_quote`
- `confidence`
- `investor_scoring_status`

Minimum high-value fields:

- Canadian franchise availability.
- Exact Canadian signing entity.
- Initial investment range in CAD.
- Franchise fee in CAD.
- Royalty.
- Marketing/advertising fee.
- Required liquid capital and net worth.
- Territory rights.
- Term, renewal, and transfer fees.
- Canadian unit count by province.
- Openings, closures, transfers, and renewals.
- Canadian AUV, EBITDA, gross sales, or comparable unit economics.
- Litigation, insolvency, or material dispute history.
- Training/support obligations.
- Franchisee interview notes.

## 4. Research Workflow

For each brand:

1. Open the current report and export row.
2. Check official Canadian brand/franchise pages first.
3. Save source-backed changes into `franchise-intel/data/research_overrides.json` or `franchise-intel/data/non_food_research_overrides.json`.
4. Mark fields as verified only when the source is Canadian and directly supports the value.
5. Add rejected-source notes when a source looked relevant but failed the Canadian/investor-grade test.
6. Regenerate reports with `python franchise-intel/generate_reports.py`.
7. Rebuild exports/database from `output/franchises` scripts.
8. Re-query the database to confirm source counts, rejected fields, evidence grade, and decision posture changed as expected.

## 5. Franchisor Confirmation

Public research is not enough for investor-grade scoring. For each serious candidate, contact the franchisor and request:

- Current Canadian franchise package.
- Current CAD investment and fee schedule.
- Canadian signing entity and disclosure document.
- Opening/closure/transfer/renewal counts for the last 3 years.
- Canadian unit economics or permissible financial performance representations.
- Territory policy.
- Franchisee validation contacts.

Until this is complete, reports should continue to show `Franchisor Confirmation: None confirmed` and `Investor-Grade Score: N/A`.

## 6. Quality Checks

Run these checks after each research batch:

```powershell
python franchise-intel/generate_reports.py
cd output/franchises
python build_getfranchise_database.py
python query_getfranchise_database.py summary
python query_getfranchise_database.py rebuild-queue --limit 25
```

Batch acceptance criteria:

- No fabricated exact values.
- Every new exact value has a source.
- Canadian and U.S. evidence are clearly separated.
- Source dates and retrieved dates are present where possible.
- Investor-grade score remains blocked unless all gates are complete.
- Generated reports and database row counts are consistent.

