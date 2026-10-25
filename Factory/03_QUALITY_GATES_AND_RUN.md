# QUALITY GATES + RUN INSTRUCTIONS

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
