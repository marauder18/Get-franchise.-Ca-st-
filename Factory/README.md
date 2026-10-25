# GetFranchise Offline Factory

This is a local, no-cost, no-API factory for moving an existing nine-section franchise report through extraction, cleanup, evidence gating, and publication into the JSON file used by the static GetFranchise website. It never browses, calls an AI model, sends HTTP requests, or requires credentials.

## Install

Python 3.11+ is sufficient. There are no third-party packages.

```powershell
cd Factory
pip install -r requirements.txt
```

Optional local path overrides belong in `.env`; copy `.env.example`. No API keys are supported or read.

## Run

Run the isolated three-process pipeline against an existing local report:

```powershell
python run_factory.py "Subway Canada"
```

## Use with your own local agent (Hermes)

The offline pipeline above remains intentionally offline. For a local Hermes agent that needs guarded, no-cost research tools, use [`AGENT_AID.md`](AGENT_AID.md). Its `agent_aid.py` command line stores public-source snapshots, claims, verification results, evidence gates, and exports in a separate local workspace. It does **not** create or run another AI agent, call Ollama, use an API key, or publish to the website automatically.

Run one station again without rerunning earlier stages:

```powershell
python run_station.py extract "Subway Canada"
python run_station.py clean workspace/raw/subway-canada.json
python run_station.py publish workspace/clean/subway-canada.json
```

Validate all existing reports locally, in parallel:

```powershell
python validate_existing.py
```

Run tests:

```powershell
python -m pytest tests/
```

## Stations and outputs

- `extract`: finds one local report and writes `workspace/raw/<slug>.json` from its source ledger.
- `clean`: deletes unsafe fields, records every deletion, and writes `workspace/clean/<slug>.json`.
- `publish`: requires source-backed verified values and all eight evidence gates to pass, then writes `workspace/published/<slug>.json` and upserts a **research-queue** row in the site JSON data file. The factory does not classify source URLs as official or automatically promote a record into the buyer-facing shortlist.

Each station is invoked in a separate Python process by `run_factory.py`; files are the only handoff. Logs are JSON Lines under `workspace/logs/`.

## Publication rule

The factory fails closed. Existing screening reports commonly have failed evidence gates, so they will extract and clean but will not publish. A factory record remains in the internal research queue even after publication: URL, date, and reliability metadata alone do not prove that a source is official, Canadian, or suitable for a buyer-facing shortlist. The separate public readiness gate requires five source links, at least one classified official source, four verified core fee fields, an evidence grade of `B-` or better, Canadian/cross-border checks, and a clear confirmation boundary. This system does not create or infer research.

## Layout

- `schemas/`: fixed raw, clean, and published record contracts.
- `integration/tier_splitter.py`: Basic, Advanced, and Premium tier split.
- `integration/website_writer.py`: idempotent JSON upsert into the static site data export.
- `validate_existing.py`: parallel audit for the current 484 report files.
