# Hermes evidence-factory toolkit

`agent_aid.py` is a local toolbelt for an existing agent such as Hermes. It is **not an agent**: it never calls Ollama, selects a model, sends paid API requests, or invents research. Hermes supplies the judgement and calls this program to create durable, auditable evidence records.

## One-time setup

Install a real Python 3.11+ runtime. The current machine's `python` command resolves to the Microsoft Store placeholder, so Python must be installed before this script can run. No Python packages are required.

Run commands from `Factory`:

```powershell
python agent_aid.py create-job "Pizza Nova"
```

The program writes only to `Factory/workspace/agent_aid/`, which is gitignored.

## Tool sequence for Hermes

Give Hermes this instruction after it has shell access:

```text
You are the researcher. Use agent_aid.py as your evidence ledger.
Never state that a value is verified unless verify-claim succeeds.
Never mark a gate PASS without linked source IDs.
Use public sources only, honour failures/access restrictions, and never bypass a login, paywall, CAPTCHA, robots rule, or rate limit.
Treat search results as leads, not evidence. Quote the exact supporting passage for every candidate claim.
For Canadian investment, fee, royalty, marketing fee, and AUV fields, use a second independent domain before verification. If sources disagree, call mark-conflict. If evidence is unavailable, record unverified rather than guessing.
Run audit and export when research is complete. Exported screening profiles may be incomplete; only an audit-clean record with all eight gates passing is investor-ready.
```

Typical run:

```powershell
# 1. Create/reopen a job. The response supplies its job ID.
python agent_aid.py create-job "Pizza Nova"

# 2. Search the public web for leads. This stores nothing as evidence.
python agent_aid.py discover 'Pizza Nova Canada franchise investment'

# 3. Fetch a permitted public source and save an immutable text snapshot.
python agent_aid.py fetch-source --job 1 --url "https://example.com" --source-type official --canadian-scope yes

# 4. Attach an exact quotation to a candidate value. Source ID comes from step 3.
python agent_aid.py add-claim --job 1 --field financials.franchise_fee_cad --value "25000" --source 1 --quote "Exact quoted source text" --scoring-eligible

# 5. Fetch an independent source, then verify against its source ID.
python agent_aid.py verify-claim --claim 1 --source 2 --quote "Exact confirming source text"

# 6. Check policy failures and create a safe data export.
python agent_aid.py audit --job 1
python agent_aid.py export --job 1
```

## What this intentionally does not do

- It does not run or replace Hermes.
- It does not use a paid API, cloud model, or database.
- It does not automatically publish to the live website.
- It does not bypass source restrictions or treat a search snippet as proof.
- It cannot manufacture non-public disclosure packages, private franchisee interviews, or direct franchisor confirmation.

The export is an auditable handoff. Add a separate reviewed publish step only after the agent’s research quality is proven on real brands.
