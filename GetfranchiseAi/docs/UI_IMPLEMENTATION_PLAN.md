# GetFranchise UI Implementation Plan

## Scope
- Build only the frontend UI for a public franchise screening database.
- Use the existing `output/franchises/GETFRANCHISE_BRAND_DATA_2026-07-18.json` export as the current data source.
- Leave backend, GitHub publishing, authentication, admin tools, and durable database work for the other model.

## Screens
- Directory first screen with search, category summary, filters, sorting, responsive table/cards, pagination, and evidence disclaimer.
- Dedicated brand profile view using hash routes under `#/franchises/:brandId`.
- Browser-local shortlist view under `#/shortlist`.

## Data Contract
- Current UI reads brand records from the JSON export.
- Required future fields should map to brand name, category, score, risk, growth, investment tier, confidence, ownership, cost fields, evidence grade, source links, decision posture, and critical gaps.
- Unknown or unverified values must remain labelled, not silently scored.

## Handoff Notes
- The data loader is isolated at the top of `app.js` in `DATA_URL`.
- The other model can replace `DATA_URL` with an API endpoint without changing most UI rendering.
- Shortlist currently uses `localStorage`; replace it with account-backed storage later if needed.
