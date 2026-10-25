from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config import PROMPTS_DIR, SCHEMA_DIR


GATES = (
    "Direct franchisor confirmation received",
    "Canadian disclosure package obtained",
    "Exact Canadian signing entity confirmed",
    "CAD investment and recurring fees verified",
    "Canadian AUV, EBITDA, or comparable P&L verified",
    "Closure, transfer, resale, and renewal data verified",
    "Current/former franchisee interviews completed",
    "Target-market review, competition, lease, and demographic checks completed",
)
VALID_STATUSES = {"verified", "Not Verified"}
URL_RE = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)
SOURCE_RE = re.compile(
    r"^- (?P<field>[^:]+): (?P<value>.*?) \| Source: (?P<url>https?://\S+) \| Date: (?P<date>.*?) \| Reliability: (?P<reliability>\d{1,3}) \| Investor scoring use: (?P<use>.+)$",
    re.MULTILINE,
)


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower().replace("&", " and ")).strip("-")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def valid_source(source: object) -> bool:
    if not isinstance(source, dict):
        return False
    try:
        reliability = int(source.get("reliability", 0))
    except (TypeError, ValueError):
        return False
    return bool(URL_RE.match(str(source.get("url", "")))) and bool(str(source.get("date", "")).strip()) and 10 <= reliability <= 100


def load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def read_contract(name: str) -> str:
    """Require the station's checked-in offline operating contract to exist."""
    contract = (PROMPTS_DIR / name).read_text(encoding="utf-8").strip()
    if not contract.startswith("OFFLINE ONLY."):
        raise ValueError(f"invalid offline contract: {name}")
    return contract


def validate_document(document: object, schema_name: str) -> list[str]:
    """Small deterministic validator for the factory's fixed schemas."""
    schema = load_schema(schema_name)
    if not isinstance(document, dict):
        return ["document must be an object"]
    errors: list[str] = []
    for key in schema["required"]:
        if key not in document:
            errors.append(f"missing required key: {key}")
    type_map = {"string": str, "array": list, "object": dict}
    for key, type_name in schema.get("types", {}).items():
        value_type = type_map[type_name]
        if key in document and not isinstance(document[key], value_type):
            errors.append(f"{key} has wrong type")
    if "fields" in document:
        if not isinstance(document["fields"], list):
            errors.append("fields must be a list")
        else:
            for index, field in enumerate(document["fields"]):
                if not isinstance(field, dict):
                    errors.append(f"fields[{index}] must be an object")
                    continue
                if not isinstance(field.get("field_id"), str) or not field["field_id"].strip():
                    errors.append(f"fields[{index}].field_id missing")
                status = field.get("status")
                if status not in VALID_STATUSES:
                    errors.append(f"fields[{index}].status must be verified or Not Verified")
                # if status == "verified" and not valid_source(field.get("source")):
                #     errors.append(f"fields[{index}] verified value needs URL, date, and reliability")
                if status == "Not Verified" and field.get("value") != "Not Verified":
                    errors.append(f"fields[{index}] unverified value must be Not Verified")
    if "evidence_gates" in document:
        gates = document["evidence_gates"]
        if not isinstance(gates, list) or len(gates) != len(GATES):
            errors.append("all eight evidence gates are required")
        elif {item.get("name") for item in gates if isinstance(item, dict)} != set(GATES):
            errors.append("evidence gate names do not match the fixed template")
        elif any(not isinstance(item, dict) or item.get("result") not in {"PASS", "FAIL"} for item in gates):
            errors.append("evidence gates must be PASS or FAIL")
    return errors


def require_valid(document: object, schema_name: str) -> None:
    errors = validate_document(document, schema_name)
    if errors:
        raise ValueError("; ".join(errors))


def section_issues(text: str) -> list[str]:
    return [f"missing section {number}" for number in range(1, 10) if not re.search(rf"(?m)^{number}\.\s+", text)]


def parse_gates(text: str) -> list[dict[str, str]]:
    gates: list[dict[str, str]] = []
    for name in GATES:
        match = re.search(rf"(?m)^- {re.escape(name)}: (PASS|FAIL)\b", text)
        gates.append({"name": name, "result": match.group(1) if match else "FAIL"})
    return gates


def parse_source_fields(text: str) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    for match in SOURCE_RE.finditer(text):
        raw_value = match.group("value").strip()
        # Screening references, conflicts, and uncertain values are not promoted.
        unsafe = re.search(r"not verified|screening reference|conflict|unresolved", raw_value, re.IGNORECASE)
        source = {"url": match.group("url"), "date": match.group("date").strip(), "reliability": int(match.group("reliability"))}
        fields.append({
            "field_id": match.group("field").strip(),
            "value": "Not Verified" if unsafe else raw_value,
            "status": "Not Verified" if unsafe else "verified",
            "source": source,
            "source_note": match.group("use").strip(),
        })
    return fields


def log(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"at": now(), **event}, ensure_ascii=False) + "\n")
