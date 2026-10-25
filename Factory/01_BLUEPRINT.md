# GETFRANCHISE FACTORY BLUEPRINT
Designed by FORGE. Run by the Founder. This is the design only — it runs on any AI with paste-ready prompts.
Gold standard: `output/franchises/food franchises/subs and sandwiches/Subway Canada.txt`. Target: turn ~220 empty shells (e.g. Amaya Express, 89 unverified fields, 0 sources) into Subway-tier files.

---

## DELIVERABLE 1 — FACTORY BLUEPRINT

| Station | Input | Output | Hands to |
|---|---|---|---|
| S1 INTAKE | One franchise .txt report (9-section template) | Gap list: every "Not Verified" / "Estimated" field with section, field_id, current value; existing source count | Gap list JSON → S2 |
| S2 RESEARCH | Gap list JSON | One candidate value per gap + source URL, date, reliability score (0–100 per Source Reliability Guide). No fabrication. Missing stays missing. | Candidate records JSON → S3 |
| S3 VERIFY | Candidate records JSON | Each candidate cross-checked against a SECOND independent source. Status: PASS / CONFLICT (both values kept) / UNVERIFIED (stays "Not Verified"). Never promotes. | Verified records JSON → S4 |
| S4 FORMAT | Verified records JSON + original report | Full 9-section report in the exact Founder's template (Subway structure), scoring rubric / reliability guide / 8 gates preserved verbatim | Formatted report markdown → S5 |
| S5 AUDIT | Formatted report markdown | Report + flags + fields_rejected count + ready boolean. Never fixes — only reports. | Audited report JSON → S6 |
| S6 PACKAGE FOR WEBSITE | Audited report JSON (only if ready=true) | One JSON record per franchise, fields split tier_basic / tier_advanced / tier_premium, ready for DB insert | Website ingestion record |

Escalations that must stop the line (from IDENTITY): conflicts on critical fields (fees, royalties, investment, AUV); fewer than 3 sources after S2; ambiguous field-to-section mapping; legal/financial/regulatory questions; file not matching the 9-section template.

