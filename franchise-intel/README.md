# Canadian Franchise AI Intelligence Notepad System

Python engine for generating structured `.txt` intelligence reports for Canadian franchise categories, with food and non-food reports separated into category folders.

This project intentionally does not create a website, dashboard, database UI, or HTML output. It writes one Notepad-compatible report per franchise:

`output/franchises/{category folder}/{Franchise_Name}.txt`

Food reports are split into subcategory folders, for example:

`output/franchises/food franchises/asian/{Franchise_Name}.txt`

`output/franchises/food franchises/coffee/{Franchise_Name}.txt`

`output/franchises/food franchises/subs and sandwiches/{Franchise_Name}.txt`

## Run

```powershell
python generate_reports.py
```

## Inputs

Seed and normalized franchise records live in:

`data/franchises.json`

Expansion targets live in:

`data/expansion_franchises.json`

Non-food category expansion targets live in:

`data/non_food_franchises.json`

The structured 15-per-category non-food target list lives in:

`data/non_food_category_targets.json`

Source-backed override records live in:

`data/research_overrides.json`

Every sourced field should include field-level provenance when possible: source URL/document, source date, retrieved date, reliability, and investor-scoring status. If a value is missing or not independently verified, the report labels it as `Estimated (industry benchmark)` or `Not verified / not available`.

## Data Rules

- Do not quote Reddit users, bloggers, reviewers, or individuals.
- Do not fabricate exact numbers.
- Use exact figures only when backed by named source notes.
- Use synthesized themes only for public sentiment.
- If uncertain, mark the field as `Estimated (industry benchmark)`.
- Do not use U.S. FDD data, USD values, generic estimates, old counts, Wikipedia/background facts, or unsourced sentiment for investor-grade scoring.
- Treat Canadian disclosure, Canadian signing entity, CAD fees, Canadian unit economics, closure/transfer/renewal data, franchisee interviews, and local-market checks as required investor gates.
- Current reports must state `Franchisor Confirmation: None confirmed` until the franchisor directly confirms the record. Source-backed data can appear in reports, but investor scoring remains blocked until franchisor confirmation and required evidence are complete.

## Scoring

The legacy core score is now the `Generic Screening Score`. It is goal-driven factor alignment and should be used only for early comparison:

- Investment: 7%
- Investment Goal Fit: 7%
- Payback: 9%
- Profit Margin: 9%
- Scalability: 7%
- Hours: 4%
- Industry Strength: 7%
- Recurring Revenue: 7%
- Franchisor Support: 7%
- Franchisee Satisfaction: 7%
- Exit Value: 5%
- Territory Protection: 4%
- Training Quality: 6%
- Brand Maturity: 5%
- Canadian Market Fit: 4%
- Franchise Availability: 3%
- Financial Terms Completeness: 2%

The default investor goal is `TARGET_INVESTMENT_CAD = 320,000`. The `Investment Goal Fit` factor compares each franchise's reported investment range against a maximum target of less than `$320,000 CAD`. Franchises above the target receive a lower screening score unless verified EBITDA, payback, resale, and financing evidence later justify the extra capital. Estimated or missing investment data is capped and clearly marked as not reliable for investment scoring.

Important profile and financial fields used directly in generic scoring include founded year, headquarters, Canadian ownership, industry, category/service line, Canadian franchise availability, initial investment, franchise fee, royalty, and marketing fee.

The `Investor-Grade Score` returns `N/A` unless minimum gates pass and the franchisor has directly confirmed the record. Until then, reports show `Not investment-ready / requires franchisor confirmation`.

## Daily Pipeline Shape

1. Ingest data into `data/franchises.json`.
2. Add screening-only food expansion targets to `data/expansion_franchises.json` and non-food category targets to `data/non_food_franchises.json` when full field-level evidence is not yet available.
3. Normalize values and source notes.
4. Recompute generic goal-alignment scores and investor evidence gates.
5. Regenerate tags, source ledgers, missing-evidence impact, financial model placeholders, and research queues.
6. Write `.txt` reports into category folders under `output/franchises`.
