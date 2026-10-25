# Boris Extraction Workflow

## Purpose

`output/franchises/` contains the finished franchise reports used as Factory
inputs. It also contains exports and a database. A finished report is **not**
automatically approved for the public buyer directory.

The current website data contains a larger research portfolio, while only
records that pass the separate public-ready validation are shown to buyers.

## Agent responsibilities

```text
Finished report in output/franchises/
        ↓
Boris: Extract + Clean
        ↓
Verification Station: PASS / HOLD / REJECT
        ↓
Main Hermes: Publish decision
        ↓
Public-ready validator: buyer-directory eligibility
```

### Boris — extraction and evidence intake

Boris works only on brands assigned by Main Hermes.

For each assigned brand:

1. Find its existing report under `output/franchises/`.
2. Run Factory **Extract** only.
3. Run Factory **Clean** only.
4. Keep the raw and clean records with their full source trail.
5. Hand the clean record to the Verification Station.
6. Wait for `PASS_TO_PUBLISH` before Main Hermes runs Factory Publish.

Use the stations individually so the verifier remains in the workflow:

```powershell
python Factory/run_station.py extract "BRAND NAME"
python Factory/run_station.py clean Factory/workspace/raw/BRAND-SLUG.json
```

Do **not** use `run_factory.py` for this workflow: it runs Extract, Clean, and
Publish together and would bypass the verifier handoff.

### Verification Station — evidence gate

The verifier receives the matching raw and clean records. It checks each
retained factual claim against the source trail, including currency/country
context, Canadian relevance, and U.S./USD/FDD labelling.

It returns exactly one verdict to Main Hermes:

- `PASS_TO_PUBLISH`
- `HOLD_FOR_BORIS_FIX`
- `REJECT_UNSAFE_DATA`

For a hold or rejection, it must name the exact field, missing or conflicting
source, and the fix required. It does not publish, alter website data, change
scores, or contact franchisors.

### Main Hermes — Factory owner

Main Hermes assigns the brands, receives Boris's cleaned records and the
verifier verdict, then decides whether to run Factory Publish. Publishing a
Factory record does not automatically place it in the public buyer directory;
the separate public-ready gate remains required.

## Rules

- Do not delete, rename, or move files in `output/franchises/`.
- Ignore `output/legacy-flat-food-reports/`; it contains older/duplicate
  material.
- Do not overwrite website exports or research overrides during extraction.
- Do not invent values or infer missing fees, profit, AUV, EBITDA, payback, or
  franchisee-sentiment claims.
- Treat U.S./USD/FDD data as clearly labelled context only, never Canadian
  evidence without direct Canadian confirmation.
- Do not conduct outreach, submit forms, or email franchisors.

## Required Boris handoff

```text
[BRAND] | Boris | Extracted / Cleaned / Sent to Verifier
| Original report: [path]
| Raw: [path]
| Clean: [path]
| Source URLs: [list]
| Not Verified: [short list]
| U.S./USD/FDD context: [short list or none]
```
