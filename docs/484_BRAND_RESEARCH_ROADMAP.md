# GetFranchise 484-Brand Research Roadmap

Date: 2026-10-04

## Outreach Gate

Do not draft, send, or log franchisor outreach until at least 100 brands pass
the ready-candidate validation. The current portfolio has 43 ready candidates,
so the immediate target is 57 additional source-backed candidates. This
supersedes the earlier 30-candidate outreach sequence.

## Principle

Quality over speed. The public site should only show records that are useful for buyer screening and honest about what is not confirmed. The full 484-brand portfolio stays as a private research backlog until each brand reaches the launch standard.

## Current Public Standard

A brand can be public when it has:

- At least one official brand, franchisor, company, or reliable franchise-development source.
- Current Canadian availability stated or clearly marked as not verified.
- Core money fields captured when publicly available: total investment, franchise fee, royalty, marketing fee, and liquid capital.
- Source links attached to exact values.
- Missing values marked as not publicly available, not estimated as fact.
- Franchisor confirmation status shown clearly.
- Investor-grade score blocked unless direct confirmation, Canadian disclosure, unit economics, legal/entity review, and franchisee validation are complete.

## Launch Site Scope

The public site is capped at 25 profiles across three categories:

- Beverage and dessert
- Limited-service food
- Full-service food

This keeps the user experience clean while the rest of the portfolio is rebuilt.

## Upgrade Tracks

### Track 1: Source Rebuild

Use for zero-source or weak-source brands.

Done means:

- Official Canadian or brand-level franchise source found.
- Canadian availability checked.
- Non-Canadian or outdated numbers rejected or labelled as context only.
- Report regenerated with source notes.

### Track 2: Fee Verification

Use for brands with sources but incomplete money fields.

Done means:

- Total investment, franchise fee, royalty, marketing fee, and liquid capital each marked source-backed or not publicly available.
- CAD versus USD is explicit.
- Any third-party values are treated as lower-confidence until franchisor-confirmed.

### Track 3: Legal And Entity Check

Use after a brand has credible public franchise data.

Done means:

- Canadian signing entity researched where available.
- Disclosure-package status noted.
- Litigation, insolvency, registry, or government/legal source checks added where available.

### Track 4: Franchisor Confirmation

Use only after the 100-ready-candidate gate is met, and then only for brands
that remain on the prioritized shortlist.

Done means:

- Outreach drafted from the approved template.
- Human approval before sending.
- Response logged.
- Confirmed corrections applied.
- `last_verified` and confirmation status updated only after a direct response.

## Batch Rhythm

Work in small batches:

- 10 brands per research batch.
- 1 category focus at a time.
- Regenerate reports and database after each batch.
- Promote only the strongest finished records into the public 25 when they beat an existing profile.

## Suggested Category Order

1. Finish the three launch categories first: beverage and dessert, limited-service food, full-service food.
2. Move to high-intent service categories: home services, senior care, cleaning, education.
3. Then expand to operational categories: automotive, pet services, shipping and printing, staffing, fitness.
4. Leave lower-source or lower-fit categories for later unless a buyer request justifies them.

## Acceptance Checks

After every batch, run:

```powershell
python franchise-intel/generate_reports.py
cd output/franchises
python build_getfranchise_database.py
python query_getfranchise_database.py summary
python query_getfranchise_database.py rebuild-queue --limit 25
```

No batch is accepted if it adds exact money claims without a source.
