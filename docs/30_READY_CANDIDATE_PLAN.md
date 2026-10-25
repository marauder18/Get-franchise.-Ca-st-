# GetFranchise 30 Ready-Candidate Plan

Date: 2026-09-01

> **Superseded for outreach purposes on 2026-10-04.** The 30-candidate target
> was achieved, but franchisor outreach is now held until 100 candidates pass
> the same ready-candidate validation. See `100_READY_CANDIDATE_PLAN.md` for
> the active research and outreach rule.

Status: implemented as a non-destructive app-level research upgrade in `GetfranchiseAi/app.js`.

## Non-Destructive Rule

Do not delete any brand, report, source row, or generated export. Weak records stay in the research queue until upgraded. The public directory can stay limited, but the underlying 484-brand portfolio remains intact.

## Ready-Candidate Standard

A brand is a ready candidate when it has:

- At least 5 total source links.
- At least 1 official brand, franchisor, company, or reliable franchise-development source.
- At least 4 of 5 core money fields checked: total investment, franchise fee, royalty, marketing fee, liquid capital.
- Evidence grade of B- or better, or a clear explanation for why the profile is still useful.
- Canadian relevance stated clearly.
- U.S. FDD or non-Canadian figures labelled as context only.
- Direct franchisor confirmation still marked as required unless the franchisor has replied.

This means "ready for buyer screening," not investor-grade.

## Current 15 Ready Candidates

Keep these as the starting base:

1. Subway Canada
2. Good Earth Coffeehouse
3. COBS Bread
4. Boston Pizza
5. Booster Juice
6. Kumon Math and Reading Centres
7. The UPS Store
8. Handyman Connection
9. Mary Brown's Chicken
10. Panago Pizza
11. Mathnasium
12. Eggsmart
13. Global Pet Foods
14. Freshslice Pizza
15. Right at Home Canada

## Next 15 To Upgrade First

These are close enough that they should be faster and cleaner than rebuilding zero-source records:

1. Coffee Time
2. Quesada Burritos & Tacos
3. Robin's Donuts
4. Snap Fitness
5. Days Inns - Canada
6. Express Employment Professionals
7. Home Instead
8. The Grounds Guys
9. Pizza Pizza
10. Spherion
11. Stratus Building Solutions Canada
12. The Little Gym
13. Anytime Fitness
14. Chopped Leaf
15. Noodlebox

## Batch Plan

### Batch 1: Food And Beverage Fill-Ins

Target:

- Coffee Time
- Quesada Burritos & Tacos
- Robin's Donuts
- Pizza Pizza
- Chopped Leaf
- Noodlebox

Goal:

- Bring each to 5-8 good sources.
- Confirm all available fee fields.
- Separate Canadian, U.S., and franchisor/global data.

### Batch 2: Services With Strong Buyer Intent

Target:

- Snap Fitness
- Home Instead
- The Grounds Guys
- Stratus Building Solutions Canada
- The Little Gym

Goal:

- Add official franchise pages.
- Add territory/support/training detail.
- Verify liquidity and recurring fees where available.

### Batch 3: Operational And B2B Profiles

Target:

- Days Inns - Canada
- Express Employment Professionals
- Spherion
- Anytime Fitness

Goal:

- Confirm official franchising requirements.
- Add legal/entity/disclosure notes if available.
- Decide if each is public-candidate quality or stays internal.

## Per-Brand Research Steps

For each brand:

1. Open the current profile/report.
2. Find the official Canadian or brand franchising page first.
3. Add 5-8 total sources, preferring official sources.
4. Check total investment, franchise fee, royalty, marketing fee, and liquid capital.
5. Mark unknown fields as not publicly available.
6. Add source notes and rejected-source notes.
7. Regenerate reports and database.
8. Compare against the current public 25 before promoting.

## Acceptance Check

After each batch, run:

```powershell
python franchise-intel/generate_reports.py
cd output/franchises
python build_getfranchise_database.py
python query_getfranchise_database.py summary
python query_getfranchise_database.py rebuild-queue --limit 25
```

Do not accept a batch if exact fee or investment claims were added without source links.

## Implemented Result

The app-level validation now returns 33 ready candidates, including all 15 upgrade targets in this plan. The result is above the original 30-candidate goal because several drink-profile upgrades also meet the same ready-candidate threshold.

Implemented upgrade targets:

1. Coffee Time
2. Quesada Burritos & Tacos
3. Robin's Donuts
4. Snap Fitness
5. Days Inns - Canada
6. Express Employment Professionals
7. Home Instead
8. The Grounds Guys
9. Pizza Pizza
10. Spherion
11. Stratus Building Solutions Canada
12. The Little Gym
13. Anytime Fitness
14. Chopped Leaf
15. Noodlebox

## Goal

Reach 30 ready candidates by adding 15 upgraded candidates to the current 15, while keeping the full 484-brand database intact and clearly separating public screening from investor-grade diligence.
