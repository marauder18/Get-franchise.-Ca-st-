"""Station 2: remove unsafe values and record each deletion."""
from __future__ import annotations

import argparse
from pathlib import Path

from common import VALID_STATUSES, log, now, read_contract, read_json, require_valid, valid_source, write_json
from config import CLEAN_DIR, LOG_DIR, ensure_workspace


def clean(raw_path: Path, clean_dir: Path = CLEAN_DIR, log_dir: Path = LOG_DIR) -> Path:
    ensure_workspace()
    read_contract("cleanup_prompt.txt")
    raw = read_json(raw_path)
    require_valid(raw, "franchise_raw.schema.json")
    kept, deletions = [], []
    for field in raw["fields"]:
        reason = ""
        if field["status"] not in VALID_STATUSES:
            reason = "unsupported evidence status"
        elif field["status"] == "verified" and not valid_source(field.get("source")):
            reason = "verified value lacks valid local source metadata"
        elif field["status"] == "Not Verified" and field["value"] != "Not Verified":
            reason = "unverified value was not normalized"
        if reason:
            deletions.append({"field_id": field.get("field_id", ""), "reason": reason})
        else:
            kept.append(field)
    document = {
        "schema_version": "1.0",
        "franchise": raw["franchise"],
        "slug": raw["slug"],
        "raw_path": str(raw_path.resolve()),
        "cleaned_at": now(),
        "fields": kept,
        "evidence_gates": raw["evidence_gates"],
        "deletions": deletions,
    }
    require_valid(document, "franchise_clean.schema.json")
    output = clean_dir / f"{raw['slug']}.json"
    write_json(output, document)
    log_path = log_dir / f"{raw['slug']}.clean.log"
    for deletion in deletions:
        log(log_path, {"station": "clean", "action": "deleted", **deletion})
    log(log_path, {"station": "clean", "status": "done", "kept": len(kept), "deleted": len(deletions)})
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean one local raw factory record. No network access.")
    parser.add_argument("raw_path", type=Path)
    args = parser.parse_args()
    print(clean(args.raw_path))


if __name__ == "__main__":
    main()
