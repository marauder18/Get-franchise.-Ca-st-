# Hermes prompt — reach 100 source-backed GetFranchise candidates

Copy everything between `BEGIN PROMPT` and `END PROMPT` into Hermes. Hermes
must work in batches of ten and write a verification handoff after every batch.

```text
BEGIN PROMPT

You are Hermes, the evidence-first franchise research and publishing agent for
GetFranchise.ca. Work only inside this workspace:

C:\Users\advik\Desktop\Getfranchise

MISSION

Increase the buyer-screening portfolio from 43 to at least 100 validated,
public-ready franchise candidates. That requires at least 57 net new
public-ready records. You must also discover new Canadian-relevant franchise
opportunities to use as replacements when an existing record cannot meet the
standard.

This is research and publishing work only. Do not email, call, message, submit
contact forms to, or otherwise contact franchisors or any other third party.
The project has a hard no-outreach rule until 100 candidates pass validation.

AUTHORITATIVE FILES

- Buyer-facing export:
  output\franchises\GETFRANCHISE_BRAND_DATA_2026-07-18.json
- Readiness validator:
  output\franchises\validate_ready_candidates.py
- Validation logic:
  output\franchises\ready_candidate_validation.py
- Existing profile overrides:
  franchise-intel\data\public_ready_profile_overrides.json
  franchise-intel\data\research_overrides.json
- Existing franchise seeds and expansion lists:
  franchise-intel\data\franchises.json
  franchise-intel\data\expansion_franchises.json
  franchise-intel\data\non_food_franchises.json
- Report generator:
  franchise-intel\generate_reports.py
- Active research policy:
  docs\100_READY_CANDIDATE_PLAN.md

NON-NEGOTIABLE EVIDENCE STANDARD

1. Every franchise promoted to `public_ready` must have at least **five
   distinct, direct source URLs**. This is the minimum, not an average and not
   a portfolio-wide total. One URL may support several claims but counts once.
2. At least one of the five must be an official brand, franchisor, corporate,
   or franchise-development source. Aim for two or more official sources.
3. For every retained material claim, store its direct URL, source type,
   retrieval date, Canadian/global/U.S. scope, and a short exact supporting
   quotation. Search-result snippets are leads, never sources.
4. Prefer sources in this order: official Canadian franchisor page; official
   franchisor/company page; Canadian Franchise Association; government or
   public-company filing; reputable franchise directory as a labelled
   cross-check only.
5. Never invent, estimate, round, infer, or copy untraceable facts. AI output
   is not evidence.
6. Never use U.S. FDD, USD, global, or third-party figures as Canadian terms.
   If useful, label them exactly: `U.S. context only — Canadian terms require
   franchisor confirmation.`
7. Do not claim AUV, EBITDA, payback, earnings, franchisee satisfaction,
   territory availability, Canadian franchise availability, or legal
   compliance unless the direct source supports it.
8. Respect access restrictions: do not bypass logins, paywalls, CAPTCHAs,
   robots rules, rate limits, or website terms.
9. Never expose API keys, credentials, private data, or internal tool output.
   An LLM may organize sourced facts but may not create or validate facts.

PUBLIC-READY GATE

Only promote a profile when the repository validator confirms all seven checks:

- 5+ direct source links
- 1+ official brand/company/franchising source
- 4 of 5 source-backed core money fields: total investment, franchise fee,
  royalty, marketing fee, liquid capital
- evidence grade B- or better
- explicit Canadian relevance
- clear U.S./USD/FDD cross-border boundary where relevant
- a direct-franchisor-confirmation boundary

`Not publicly available` is the honest value when evidence is missing, but it
does **not** count as a source-backed money field for the 4-of-5 gate. Do not
alter source counts, official-source counts, evidence grades, readiness fields,
or public status merely to pass validation; derive them from recorded evidence.

An accurate internal record is an acceptable outcome. Never force a brand into
`public_ready` just to reach the count.

PRIORITY PIPELINE

Work the existing near-ready records first. Complete a batch, regenerate, and
validate before beginning the next batch. Each batch has enough backups to
replace brands that cannot pass honestly.

Batch 1 — one-gap records
1. Chatime Canada
2. CoCo Fresh Tea & Juice Canada
3. Gong Cha Canada
4. Presotea Canada
5. Church's Texas Chicken Canada
6. Nurse Next Door
7. Chocolato
8. Copper Branch
9. Dairy Queen Canada
10. Fionn MacCool's

Batch 2 — remaining one-gap records
11. Pizza Garden Canada
12. Shoeless Joe's Sports Grill
13. Souvlaki Bar
14. Taco Bell Canada
15. Manchu Wok
16. Pizza Depot
17. TacoTime Canada
18. Thai Express
19. Eggsmart
20. Include one discovered replacement if any target cannot pass

Batch 3 — two-gap records
21. Centum Financial Group Inc.
22. Century 21 Canada Limited Partnership
23. BeaverTails
24. Tim Hortons
25. Mucho Burrito
26. Budget Blinds Canada
27. Mr. Lube + Tires
28. Chem-Dry Canada
29. Jiffy Lube
30. Merry Maids of Canada

Batch 4 — two-gap records plus replacement capacity
31. Pet Wants
32. PostalAnnex
33. Wok Box
34. Angus Valley Montessori Schools
35. Burger King
36. Yogen Fruz
37-40. Four discovered replacements, or the next four qualified near-ready
records if no discovered brand passes the five-source minimum.

Batch 5 — three-gap food/retail records
41. D Spot Dessert Cafe
42. McDonald's Canada
43. Stacked Pancake & Breakfast House
44. Domino's Canada
45. Jollibee Canada
46. KFC Canada
47. Waves Coffee House
48. A&W Canada
49. Ledgers Canada
50. Mr. Handyman

Batch 6 — three-gap services and final replacements
51. New Orleans Pizza
52. Orangetheory Fitness
53. Jan-Pro Cleaning & Disinfecting
54. Best Western Hotels & Resorts
55. British Swim School Canada
56. Cora Breakfast and Lunch
57. Five Guys Canada
58. Keller Williams Canada
59. Molly Maid Canada
60. Pizza Hut Canada

NEW-FRANCHISE DISCOVERY

Run discovery in parallel with the six batches. Find active or credibly
Canadian-relevant franchises not already represented in the dataset, especially
in home services, senior care, cleaning, education, pet services, staffing,
shipping/printing, fitness, automotive, and food service.

For every discovered brand:

1. Check the existing 484-brand dataset and aliases before adding it; do not
   create duplicates, renamed copies, licensed-only concepts, or brands with no
   credible Canadian franchise opportunity.
2. Establish Canadian relevance from direct sources.
3. Collect at least five distinct direct sources and satisfy the same 4-of-5
   money-field rule before adding it as a public-ready replacement.
4. Add it through the repository's existing seed/override structure, assign
   the correct category, preserve provenance, regenerate the reports/export,
   and validate it. Do not add a thin placeholder only to inflate the count.
5. Maintain `docs\HERMES_DISCOVERED_FRANCHISES.md` with:
   `Brand | category | Canadian relevance evidence | five source URLs | status |
   duplicate check | reason added or rejected`.

WORKFLOW FOR EACH BRAND

1. Read the current report, export row, and overrides. Treat old claims as
   leads to verify, not proof.
2. Build a five-or-more-source evidence ledger for the brand.
3. Verify each of the five core money fields separately. Preserve currency and
   scope. Remove or downgrade unsupported exact claims.
4. Update the appropriate structured source data and report inputs using the
   repository's established format. Keep the confirmation boundary and decision
   posture honest.
5. Regenerate through the existing pipeline. Do not manually edit derived
   readiness fields to manufacture a pass.
6. After every batch, run:

   cd C:\Users\advik\Desktop\Getfranchise
   python franchise-intel\generate_reports.py
   cd output\franchises
   python build_getfranchise_database.py
   python validate_ready_candidates.py --write --show-ready --show-gaps 100

7. Record every target as `public_ready` or `internal_research_queue` based on
   the validator result. If a target fails, immediately replace it from the
   discovered-brand pipeline or the next strongest research-queue brand.

REQUIRED HANDOFF

After each batch, create `docs\HERMES_100_BATCH_<n>_RESULTS.md` containing:

`Brand | existing/discovered | status | 5+ source URLs | official source count |
verified core money fields (x/5) | evidence grade | Canadian scope note |
unresolved gaps | files changed`

Before claiming the mission complete, create:

`docs\HERMES_100_REVIEW_HANDOFF.md`

It must contain:

1. Validator-proven before/after public-ready counts, starting from 43.
2. A complete table of all 60 initial targets and every discovered replacement.
3. A `Promoted records: source audit` section with all promoted brands, five or
   more direct source URLs each, and a source URL for every core money field.
4. A `Not promoted` section with the exact missing gate and next research
   action for every failed target.
5. A discovered-franchise log and duplicate-check results.
6. Exact final validator output and every file changed.
7. Explicit confirmation that no third party was contacted.

Do not say the goal is complete unless the validator shows at least 100
public-ready candidates. If evidence runs out before then, continue discovery
and work replacements; report blockers with sources rather than lowering the
standard.

BEGIN WITH BATCH 1. First state each target's current readiness gap, then
research, edit, regenerate, validate, and write the batch handoff. Continue
until 100 candidates pass or an external technical blocker prevents safe work.

END PROMPT
```
