from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from professionalize_reports import (
    APPENDIX_MARKER,
    ROOT,
    decision_posture,
    evidence_grade,
    extract_line_value,
    infer_category,
    iter_report_paths,
    is_non_canadian_offer,
    is_verified,
    load_report,
    report_sort_key,
)


REPORT_GLOB = "*.txt"
EXPORT_DATE = "2026-07-18"
PRIMARY_OVERRIDE_FILE = ROOT / f"PRIMARY_SOURCE_OVERRIDES_{EXPORT_DATE}.json"
NON_FOOD_SOURCE_UPDATE_FILES = sorted(ROOT.glob("NON_FOOD_SOURCE_UPDATES_*.json"))
NON_FOOD_OVERRIDE_FILES = [
    ROOT.parent.parent / "franchise-intel" / "data" / "non_food_franchises.json",
    ROOT.parent.parent / "franchise-intel" / "data" / "non_food_expansion_franchises.json",
    ROOT.parent.parent / "franchise-intel" / "data" / "non_food_research_overrides.json",
]
BRAND_CSV = ROOT / f"GETFRANCHISE_BRAND_DATA_{EXPORT_DATE}.csv"
BRAND_JSON = ROOT / f"GETFRANCHISE_BRAND_DATA_{EXPORT_DATE}.json"
EVIDENCE_CSV = ROOT / f"GETFRANCHISE_SOURCE_EVIDENCE_{EXPORT_DATE}.csv"
PRIORITY_CSV = ROOT / f"GETFRANCHISE_RESEARCH_PRIORITY_{EXPORT_DATE}.csv"
SUMMARY_MD = ROOT / f"GETFRANCHISE_DATA_EXPORT_SUMMARY_{EXPORT_DATE}.md"
PRIMARY_BATCH_MD = ROOT / f"GETFRANCHISE_PRIMARY_SOURCE_BATCH_{EXPORT_DATE}.md"


KNOWN_NEWS_DOMAINS = {
    "apnews.com",
    "businessinsider.com",
    "investopedia.com",
    "nypost.com",
    "cbc.ca",
    "ctvnews.ca",
    "bnnbloomberg.ca",
    "globalnews.ca",
    "theglobeandmail.com",
    "financialpost.com",
}

KNOWN_REFERENCE_DOMAINS = {
    "wikipedia.org",
    "wikidata.org",
}

KNOWN_FRANCHISE_DIRECTORY_DOMAINS = {
    "cfa.ca",
    "franchisebusinessreview.com",
    "franchisedirect.com",
    "franchiseknowhow.com",
    "franchising.com",
    "franchisegator.com",
    "franchiseclique.com",
    "franchisedictionarymagazine.com",
    "franchisegenius.com",
    "frandata.com",
    "getfdd.com",
    "clearlyfdd.com",
    "frandb.com",
}

KNOWN_SOCIAL_DOMAINS = {
    "reddit.com",
    "youtube.com",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "x.com",
    "twitter.com",
    "tiktok.com",
}


def report_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return text.split(APPENDIX_MARKER)[0].rstrip() + "\n"


def parse_source_evidence(text: str) -> list[dict[str, str]]:
    match = re.search(
        r"Source-Backed Evidence Loaded\n(?P<body>.*?)(?:\nEvidence Source URLs:|\nResearch Notes:|\nCritical Gaps:|\Z)",
        text,
        re.DOTALL,
    )
    if not match:
        return []

    rows: list[dict[str, str]] = []
    line_re = re.compile(
        r"^- (?P<field>[^:]+): (?P<value>.*?) \| Source: (?P<source>.*?) \| Date: (?P<date>.*?) \| Reliability: (?P<reliability>.*?) \| Investor scoring use: (?P<investor_use>.+)$"
    )
    for raw_line in match.group("body").splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        parsed = line_re.match(line)
        if not parsed:
            continue
        row = parsed.groupdict()
        rows.append(row)
    return rows


def parse_source_urls(text: str) -> list[dict[str, str]]:
    match = re.search(
        r"Evidence Source URLs:\n(?P<body>.*?)(?:\nResearch Notes:|\nCritical Gaps:|\Z)",
        text,
        re.DOTALL,
    )
    if not match:
        return []

    rows: list[dict[str, str]] = []
    line_re = re.compile(
        r"^- (?P<domain>.*?) \| (?P<date>.*?) \| Reliability (?P<reliability>.*?) \| (?P<url>https?://.+)$"
    )
    for raw_line in match.group("body").splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        parsed = line_re.match(line)
        if not parsed:
            continue
        rows.append(parsed.groupdict())
    return rows


def source_type(url: str) -> str:
    parsed = urlparse(url)
    hostname = parsed.netloc.lower()
    hostname = hostname.removeprefix("www.")

    if (
        hostname.endswith(".gov")
        or hostname.endswith(".gc.ca")
        or hostname.endswith(".gov.mb.ca")
        or hostname.endswith(".gnb.ca")
        or hostname.endswith(".ontario.ca")
        or hostname.endswith(".princeedwardisland.ca")
        or hostname.endswith(".bclaws.gov.bc.ca")
        or "statcan.gc.ca" in hostname
        or "canlii.org" in hostname
    ):
        return "government_or_law"

    if any(hostname == domain or hostname.endswith(f".{domain}") for domain in KNOWN_NEWS_DOMAINS):
        return "news_or_business_media"

    if any(hostname == domain or hostname.endswith(f".{domain}") for domain in KNOWN_REFERENCE_DOMAINS):
        return "reference_or_wiki"

    if any(hostname == domain or hostname.endswith(f".{domain}") for domain in KNOWN_FRANCHISE_DIRECTORY_DOMAINS):
        return "franchise_directory"

    if any(hostname == domain or hostname.endswith(f".{domain}") for domain in KNOWN_SOCIAL_DOMAINS):
        return "social_or_forum"

    return "official_brand_or_company"


def cleaned_domain(url: str) -> str:
    hostname = urlparse(url).netloc.lower().removeprefix("www.")
    return hostname


def safe_join(values: list[str]) -> str:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(normalized)
    return " | ".join(output)


def extract_bullet_line_value(text: str, label: str) -> str:
    pattern = re.compile(rf"^- {re.escape(label)}:\s*(.+)$", re.MULTILINE)
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    return extract_line_value(text, label)


def extract_plain_line_value(text: str, label: str) -> str:
    pattern = re.compile(rf"^{re.escape(label)}:\s*(.+)$", re.MULTILINE)
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    return extract_line_value(text, label)


def extract_section_lines(text: str, heading: str, next_heading_pattern: str = r"\n(?:[A-Z][A-Za-z /%-]+:?|\d+\. [A-Z])") -> list[str]:
    pattern = re.compile(
        rf"^{re.escape(heading)}:?\n(?P<body>.*?)(?={next_heading_pattern}|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return []
    lines: list[str] = []
    for raw_line in match.group("body").splitlines():
        line = raw_line.strip()
        if line.startswith("- "):
            lines.append(line[2:].strip())
    return lines


def section_summary(text: str, heading: str, limit: int = 4) -> str:
    return safe_join(extract_section_lines(text, heading)[:limit]) or "Not stated"


def compact_values(*values: str) -> str:
    return safe_join([value for value in values if value and value != "Not stated"]) or "Not stated"


def useful_value(value: str) -> bool:
    lowered = value.strip().lower()
    return bool(lowered) and lowered not in {"not stated", "not verified", "n/a"}


def first_useful(*values: str) -> str:
    for value in values:
        if useful_value(value):
            return value
    return "Not stated"


BENCHMARK_REJECT_RE = re.compile(r"Estimated \(industry benchmark\)", re.IGNORECASE)
US_UNIT_ECONOMICS_RE = re.compile(
    r"\b(U\.S\.|US|USD)\b.*\b(AUV|Item 19|average|annual sales|gross revenue|sales)\b",
    re.IGNORECASE,
)


def reject_weak_screening_value(value: object) -> object:
    """Remove values banned by the investor-grade source firewall from website exports."""
    if not isinstance(value, str):
        return value
    if not value.strip():
        return value

    parts = [part.strip() for part in value.split("|")]
    kept: list[str] = []
    changed = False
    for part in parts:
        if BENCHMARK_REJECT_RE.search(part) or US_UNIT_ECONOMICS_RE.search(part):
            changed = True
            continue
        kept.append(part)

    if changed:
        return safe_join(kept) or "Not Verified"
    return value


def enforce_website_source_firewall(row: dict[str, object]) -> None:
    for key in (
        "total_investment_range",
        "franchise_fee",
        "royalty_percent",
        "marketing_fund_percent",
        "min_liquid_capital",
        "profitability_indicators",
        "growth_trends",
        "owner_reviews",
    ):
        row[key] = reject_weak_screening_value(row.get(key, ""))

    source_count = int(row.get("source_count") or 0)
    official_source_count = int(row.get("official_brand_source_count") or 0)
    if source_count == 0:
        row["generic_screening_score"] = None
        row["confidence_level"] = "Low"
        row["evidence_grade"] = "F"
        row["decision_posture"] = (
            "Rebuild from primary sources before screening. This file has no website-grade source links."
        )
        row["research_track"] = "rebuild_from_primary_sources"
    elif official_source_count == 0:
        row["confidence_level"] = "Low"


def evidence_field_value(evidence_items: list[dict[str, object]], *field_keys: str) -> str:
    normalized = [field.lower() for field in field_keys]
    for target in normalized:
        for item in evidence_items:
            key = str(item.get("field_key") or item.get("field") or "").lower()
            if key == target:
                value = str(item.get("field_value") or item.get("value") or "").strip()
                if useful_value(value):
                    return value
    for target in normalized:
        for item in evidence_items:
            key = str(item.get("field_key") or item.get("field") or "").lower()
            if key.endswith(target) or target in key:
                value = str(item.get("field_value") or item.get("value") or "").strip()
                if useful_value(value):
                    return value
    return "Not stated"


def preferred_contact_source(official_sources: list[str]) -> str:
    preferred_terms = ("franchise", "franchising", "opportunity", "opportunities", "own", "join", "inquiry")
    for source in official_sources:
        lowered = source.lower()
        if any(term in lowered for term in preferred_terms):
            return source
    return official_sources[0] if official_sources else "Not stated"


def report_enrichment_fields(text: str, official_sources: list[str], field_evidence: list[dict[str, object]]) -> dict[str, str]:
    location_checks = extract_bullet_line_value(text, "Required checks")
    territory_protection = extract_bullet_line_value(text, "Territory Protection")
    current_saturation = extract_bullet_line_value(text, "Current saturation signal")
    total_canadian_units = extract_bullet_line_value(text, "Total Canadian Units")
    total_international_units = extract_bullet_line_value(text, "Total International Units")
    source_canadian_units = evidence_field_value(field_evidence, "growth.total_locations_canada")
    source_international_units = evidence_field_value(field_evidence, "growth.total_locations_international")

    training_quality = extract_plain_line_value(text, "Training Quality")
    training_fee = extract_bullet_line_value(text, "Training Fee")
    support_quality = extract_plain_line_value(text, "Support Quality")
    source_training = evidence_field_value(field_evidence, "franchisee.training_quality", "financials.training_fee")
    source_support = evidence_field_value(field_evidence, "franchisee.support_quality")

    average_unit_revenue = extract_bullet_line_value(text, "Average Unit Revenue")
    item_19_revenue = extract_bullet_line_value(text, "Item 19 Avg Revenue")
    item_19_gross_profit = extract_bullet_line_value(text, "Item 19 Gross Profit")
    item_19_net_profit = extract_bullet_line_value(text, "Item 19 Net Profit")
    profit_margin = extract_bullet_line_value(text, "Profit Margin")
    payback = extract_bullet_line_value(text, "Payback")
    source_revenue = evidence_field_value(field_evidence, "financials.average_unit_revenue")
    source_margin = evidence_field_value(field_evidence, "financials.profit_margin")
    source_payback = evidence_field_value(field_evidence, "financials.payback")
    source_opening = evidence_field_value(field_evidence, "operations.opening_timeline", "financials.opening_timeline", "opening_timeline")

    openings = extract_bullet_line_value(text, "Openings 12mo")
    closures = extract_bullet_line_value(text, "Closures 12mo")
    net_growth = extract_bullet_line_value(text, "Net Growth %")
    three_year_trend = extract_bullet_line_value(text, "3-Year Unit Trend")

    google_rating = extract_plain_line_value(text, "Google Rating")
    review_volume = extract_plain_line_value(text, "Review Volume")
    sentiment = extract_plain_line_value(text, "Customer Sentiment Trend")
    insight = extract_plain_line_value(text, "Insight Summary")
    franchisee_satisfaction = extract_plain_line_value(text, "Franchisee Satisfaction")

    official_contact = preferred_contact_source(official_sources)
    source_contact = first_useful(official_contact, extract_line_value(text, "Franchisor Confirmation"))

    document_checklist = section_summary(text, "Document Request Checklist", 8)
    missing_evidence = section_summary(text, "Missing Evidence Impact", 8)
    fdd_status = "Canadian disclosure package not loaded or not verified"
    if "Canadian disclosure package obtained: PASS" in text:
        fdd_status = "Canadian disclosure package marked obtained"
    elif "Canadian disclosure package obtained: FAIL" in text:
        fdd_status = "Canadian disclosure package missing"

    return {
        "location_requirements": compact_values(location_checks, territory_protection, current_saturation),
        "average_time_to_open": compact_values(source_opening, extract_line_value(text, "Opening Timeline"), extract_line_value(text, "Time to Open")),
        "training_provided": compact_values(source_training, training_quality, training_fee, source_support, support_quality),
        "profitability_indicators": compact_values(source_revenue, average_unit_revenue, item_19_revenue, item_19_gross_profit, item_19_net_profit, source_margin, profit_margin, source_payback, payback),
        "number_of_locations": compact_values(source_canadian_units, total_canadian_units, source_international_units, total_international_units),
        "growth_trends": compact_values(openings, closures, net_growth, three_year_trend),
        "owner_reviews": compact_values(google_rating, review_volume, sentiment, insight, franchisee_satisfaction),
        "pros": section_summary(text, "Strengths"),
        "cons": section_summary(text, "Weaknesses"),
        "top_praises": section_summary(text, "Top Praises"),
        "top_complaints": section_summary(text, "Top Complaints"),
        "contact_information": source_contact,
        "fdd_summary": compact_values(fdd_status, document_checklist, missing_evidence),
    }


def research_track(source_count: int, official_brand_sources: int, grade: str, verified_core_fields: int) -> str:
    if source_count == 0:
        return "rebuild_from_primary_sources"
    if official_brand_sources == 0:
        return "find_official_brand_sources"
    if verified_core_fields < 3:
        return "verify_core_franchise_fees"
    if grade in {"B", "C+"}:
        return "deep_dive_candidate"
    return "complete_brand_diligence"


def load_primary_overrides() -> dict[str, dict[str, object]]:
    overrides: dict[str, dict[str, object]] = {}
    if PRIMARY_OVERRIDE_FILE.exists():
        overrides.update(json.loads(PRIMARY_OVERRIDE_FILE.read_text(encoding="utf-8")))
    for update_file in NON_FOOD_SOURCE_UPDATE_FILES:
        for report_file, override in json.loads(update_file.read_text(encoding="utf-8")).items():
            existing = overrides.get(report_file, {"brand_fields": {}, "evidence": [], "note": ""})
            existing_fields = dict(existing.get("brand_fields", {}))
            existing_fields.update(override.get("brand_fields", {}))
            existing_evidence = list(existing.get("evidence", []))
            existing_evidence.extend(override.get("evidence", []))
            overrides[report_file] = {
                "brand_fields": existing_fields,
                "evidence": existing_evidence,
                "note": safe_join([str(existing.get("note", "")), str(override.get("note", ""))]),
            }
    return overrides


def load_non_food_research_overrides() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in NON_FOOD_OVERRIDE_FILES:
        if path.exists():
            rows.extend(json.loads(path.read_text(encoding="utf-8")))
    return rows


def flatten_non_food_override(item: dict[str, object]) -> dict[str, object]:
    field_map = {
        "profile.founded": "founded",
        "profile.headquarters": "headquarters",
        "profile.canadian_owned": "canadian_owned",
        "profile.industry": "industry",
        "profile.cuisine_type": "cuisine",
        "financials.initial_investment": "total_investment_range",
        "financials.franchise_fee": "franchise_fee",
        "financials.royalty": "royalty_percent",
        "financials.marketing_fee": "marketing_fund_percent",
        "financials.minimum_liquid_capital": "min_liquid_capital",
    }
    brand_fields: dict[str, str] = {}
    evidence: list[dict[str, str]] = []
    top_level_map = {
        "founded": "founded",
        "headquarters": "headquarters",
        "canadian_owned": "canadian_owned",
        "industry": "industry",
        "cuisine_type": "cuisine",
    }
    for source_key, target_key in top_level_map.items():
        value = str(item.get(source_key, "")).strip()
        if useful_value(value):
            brand_fields[target_key] = value

    source_sections = item.get("field_evidence", item)
    if not isinstance(source_sections, dict):
        source_sections = {}

    for section_name, section_value in source_sections.items():
        if not isinstance(section_value, dict):
            continue
        for field_name, payload in section_value.items():
            if not isinstance(payload, dict):
                continue
            value = str(payload.get("value", "")).strip()
            source_url = str(payload.get("source_url", "")).strip()
            if not value or not source_url:
                continue
            field_key = f"{section_name}.{field_name}"
            mapped = field_map.get(field_key)
            if mapped:
                brand_fields[mapped] = value
            evidence.append(
                {
                    "field_key": field_key,
                    "field_value": value,
                    "source_url": source_url,
                    "source_date": str(payload.get("source_date", "2026 source")).strip(),
                    "source_reliability": str(payload.get("source_reliability", payload.get("confidence", "85"))).strip(),
                    "investor_scoring_use": "Yes" if field_key.startswith("financials.") else "No",
                }
            )

    notes = []
    notes.extend(str(note) for note in item.get("source_notes", []) if str(note).strip())
    notes.extend(str(gap) for gap in item.get("critical_gaps", []) if str(gap).strip())

    return {
        "brand_fields": brand_fields,
        "evidence": evidence,
        "note": safe_join(notes),
    }


def merge_non_food_overrides(primary: dict[str, dict[str, object]], reports: list[object]) -> dict[str, dict[str, object]]:
    merged = dict(primary)
    report_by_title = {str(report.title).casefold(): str(report.name) for report in reports}
    report_by_stem = {Path(str(report.name)).stem.casefold(): str(report.name) for report in reports}
    for item in load_non_food_research_overrides():
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        report_file = report_by_title.get(name.casefold()) or report_by_stem.get(name.casefold()) or f"{name}.txt"
        flattened = flatten_non_food_override(item)
        existing = merged.get(report_file, {"brand_fields": {}, "evidence": [], "note": ""})
        existing_fields = dict(existing.get("brand_fields", {}))
        existing_fields.update(flattened.get("brand_fields", {}))
        existing_evidence = list(existing.get("evidence", []))
        existing_evidence.extend(flattened.get("evidence", []))
        existing_note = safe_join([str(existing.get("note", "")), str(flattened.get("note", ""))])
        merged[report_file] = {
            "brand_fields": existing_fields,
            "evidence": existing_evidence,
            "note": existing_note,
        }
    return merged


def row_is_non_canadian_offer(canadian_owned: str, investment_range: str) -> bool:
    owned = (canadian_owned or "").strip().lower()
    investment = (investment_range or "").strip().lower()
    explicitly_non_canadian = (
        owned == "no"
        or owned.startswith("no -")
        or owned.startswith("no,")
        or "united states" in owned
        or "u.s." in owned
        or "us-based" in owned
    )
    return explicitly_non_canadian or "usd" in investment


def grade_from_values(
    source_count: int,
    official_source_count: int,
    government_source_count: int,
    official_evidence_count: int,
    rejected_fields: int | None,
    core_fields: list[str],
) -> str:
    verified_core = sum(1 for field in core_fields if is_verified(field))
    rejected = rejected_fields or 0

    if (
        source_count >= 10
        and official_source_count >= 5
        and verified_core >= 4
        and official_evidence_count >= 10
        and rejected < 35
    ):
        grade = "A"
    elif (
        source_count >= 8
        and official_source_count >= 4
        and verified_core >= 4
        and official_evidence_count >= 8
        and rejected < 50
    ):
        grade = "A-"
    elif (
        source_count >= 6
        and official_source_count >= 3
        and verified_core >= 3
        and official_evidence_count >= 6
        and rejected < 55
    ):
        grade = "B+"
    elif (
        verified_core >= 3
        and (
            (source_count >= 4 and official_source_count >= 2)
            or (official_evidence_count >= 6 and official_source_count >= 1)
        )
    ):
        grade = "B"
    elif source_count >= 3 and official_source_count >= 1 and verified_core >= 2:
        grade = "C+"
    elif source_count >= 3 and verified_core >= 1:
        grade = "C"
    elif source_count >= 1:
        grade = "D"
    else:
        grade = "F"

    if rejected_fields is not None and rejected_fields >= 50 and grade != "F":
        downgrade_order = {"A": "A-", "A-": "B+", "B+": "B", "B": "B", "C+": "C", "C": "D", "D": "D"}
        if official_source_count == 0 or verified_core < 3:
            downgrade_order.update({"A": "B", "A-": "B", "B+": "C+"})
        grade = downgrade_order.get(grade, grade)

    return grade


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    reports = [load_report(path) for path in iter_report_paths()]
    ordered = sorted(reports, key=report_sort_key)
    rank_map = {report.name: idx for idx, report in enumerate(ordered, start=1)}
    primary_overrides = merge_non_food_overrides(load_primary_overrides(), reports)

    brand_rows: list[dict[str, object]] = []
    evidence_rows: list[dict[str, object]] = []
    priority_rows: list[dict[str, object]] = []
    primary_batch_rows: list[dict[str, str]] = []

    total_official_brand_sources = 0
    total_evidence_rows = 0

    for report in reports:
        body = report_body(report.path)
        evidence_items = parse_source_evidence(body)
        source_urls = parse_source_urls(body)
        override = primary_overrides.get(report.name, {})
        override_brand_fields = override.get("brand_fields", {})
        override_evidence_items = override.get("evidence", [])
        override_note = override.get("note", "")

        source_type_counts: dict[str, int] = {}
        unique_official_brand_urls: set[str] = set()
        unique_government_or_law_urls: set[str] = set()
        unique_all_urls: set[str] = set()

        for item in evidence_items:
            url = item["source"]
            kind = source_type(url)
            unique_all_urls.add(url)
            source_type_counts[kind] = source_type_counts.get(kind, 0) + 1
            if kind == "official_brand_or_company":
                unique_official_brand_urls.add(url)
            if kind == "government_or_law":
                unique_government_or_law_urls.add(url)

            evidence_rows.append(
                {
                    "brand": report.title,
                    "report_file": report.name,
                    "report_path": report.path.relative_to(ROOT).as_posix(),
                    "field_key": item["field"],
                    "field_value": item["value"],
                    "source_url": url,
                    "source_domain": cleaned_domain(url),
                    "source_type": kind,
                    "source_date": item["date"],
                    "source_reliability": item["reliability"],
                    "investor_scoring_use": item["investor_use"],
                }
            )

        for item in override_evidence_items:
            url = item["source_url"]
            kind = source_type(url)
            unique_all_urls.add(url)
            source_type_counts[kind] = source_type_counts.get(kind, 0) + 1
            if kind == "official_brand_or_company":
                unique_official_brand_urls.add(url)
            if kind == "government_or_law":
                unique_government_or_law_urls.add(url)

            evidence_rows.append(
                {
                    "brand": report.title,
                    "report_file": report.name,
                    "report_path": report.path.relative_to(ROOT).as_posix(),
                    "field_key": item["field_key"],
                    "field_value": item["field_value"],
                    "source_url": url,
                    "source_domain": cleaned_domain(url),
                    "source_type": kind,
                    "source_date": item["source_date"],
                    "source_reliability": item["source_reliability"],
                    "investor_scoring_use": item["investor_scoring_use"],
                }
            )

        total_evidence_rows += len(evidence_items)
        total_official_brand_sources += len(unique_official_brand_urls)

        all_known_urls = source_urls if source_urls else [
            {
                "domain": cleaned_domain(item["source"]),
                "date": item["date"],
                "reliability": item["reliability"],
                "url": item["source"],
            }
            for item in evidence_items
        ]
        all_known_urls.extend(
            {
                "domain": cleaned_domain(item["source_url"]),
                "date": item["source_date"],
                "reliability": item["source_reliability"],
                "url": item["source_url"],
            }
            for item in override_evidence_items
        )

        official_url_list = [
            entry["url"]
            for entry in all_known_urls
            if source_type(entry["url"]) == "official_brand_or_company"
        ]

        government_url_list = [
            entry["url"]
            for entry in all_known_urls
            if source_type(entry["url"]) == "government_or_law"
        ]
        field_evidence: list[dict[str, object]] = [
            {
                "field_key": item["field"],
                "field_value": item["value"],
            }
            for item in evidence_items
        ]
        field_evidence.extend(override_evidence_items)
        enrichment = report_enrichment_fields(body, official_url_list[:5], field_evidence)

        core_fields = [
            report.investment_range,
            report.franchise_fee,
            report.royalty,
            report.marketing_fee,
            report.min_liquid_capital,
        ]
        verified_core_fields = sum(1 for value in core_fields if is_verified(value))
        grade = evidence_grade(report)
        posture = decision_posture(report, grade)
        category = infer_category(report)
        track = research_track(report.source_count, len(unique_official_brand_urls), grade, verified_core_fields)

        brand_row = {
            "brand": report.title,
            "report_file": report.name,
            "report_path": report.path.relative_to(ROOT).as_posix(),
            "source_depth_rank": rank_map[report.name],
            "category": category,
            "generic_screening_score": report.generic_score,
            "risk_level": report.risk_level,
            "growth_outlook": report.growth_outlook,
            "investment_tier": report.investment_tier,
            "confidence_level": report.confidence_level,
            "investment_goal_fit": report.investment_goal_fit,
            "founded": report.founded,
            "headquarters": report.headquarters,
            "canadian_owned": report.canadian_owned,
            "industry": report.industry,
            "cuisine": report.cuisine,
            "total_investment_range": report.investment_range,
            "franchise_fee": report.franchise_fee,
            "royalty_percent": report.royalty,
            "marketing_fund_percent": report.marketing_fee,
            "min_liquid_capital": report.min_liquid_capital,
            "location_requirements": enrichment["location_requirements"],
            "average_time_to_open": enrichment["average_time_to_open"],
            "training_provided": enrichment["training_provided"],
            "profitability_indicators": enrichment["profitability_indicators"],
            "number_of_locations": enrichment["number_of_locations"],
            "growth_trends": enrichment["growth_trends"],
            "owner_reviews": enrichment["owner_reviews"],
            "pros": enrichment["pros"],
            "cons": enrichment["cons"],
            "top_praises": enrichment["top_praises"],
            "top_complaints": enrichment["top_complaints"],
            "contact_information": enrichment["contact_information"],
            "fdd_summary": enrichment["fdd_summary"],
            "market_saturation": report.market_saturation,
            "threat_level": report.threat_level,
            "operational_difficulty": report.operational_difficulty,
            "franchisor_confirmation": report.franchisor_confirmation,
            "source_count": report.source_count,
            "evidence_grade": grade,
            "decision_posture": posture,
            "rejected_fields": report.rejected_fields,
            "verified_core_fee_fields": verified_core_fields,
            "official_brand_source_count": len(unique_official_brand_urls),
            "government_or_law_source_count": len(unique_government_or_law_urls),
            "cross_border_caution": "Yes" if is_non_canadian_offer(report) else "No",
            "research_track": track,
            "top_critical_gaps": safe_join(report.critical_gaps[:5]),
            "official_brand_sources": safe_join(official_url_list[:5]),
            "government_or_law_sources": safe_join(government_url_list[:5]),
        }

        if override_brand_fields:
            brand_row.update(override_brand_fields)

        core_fields = [
            str(brand_row["total_investment_range"]),
            str(brand_row["franchise_fee"]),
            str(brand_row["royalty_percent"]),
            str(brand_row["marketing_fund_percent"]),
            str(brand_row["min_liquid_capital"]),
        ]
        verified_core_fields = sum(1 for value in core_fields if is_verified(value))
        source_count = len(unique_all_urls)
        official_evidence_count = source_type_counts.get("official_brand_or_company", 0)
        total_evidence_count = sum(source_type_counts.values())
        grade = grade_from_values(
            source_count,
            len(unique_official_brand_urls),
            len(unique_government_or_law_urls),
            official_evidence_count,
            report.rejected_fields,
            core_fields,
        )
        track = research_track(source_count, len(unique_official_brand_urls), grade, verified_core_fields)
        posture = (
            "Primary-source batch loaded; advance to targeted diligence, but do not underwrite until disclosure, entity confirmation, and unit-level economics are verified."
            if override_brand_fields
            else decision_posture(report, grade)
        )

        brand_row["source_count"] = source_count
        brand_row["evidence_grade"] = grade
        brand_row["decision_posture"] = posture
        brand_row["verified_core_fee_fields"] = verified_core_fields
        brand_row["official_brand_source_count"] = len(unique_official_brand_urls)
        brand_row["government_or_law_source_count"] = len(unique_government_or_law_urls)
        brand_row["source_evidence_item_count"] = total_evidence_count
        brand_row["official_brand_evidence_item_count"] = official_evidence_count
        brand_row["cross_border_caution"] = "Yes" if row_is_non_canadian_offer(str(brand_row["canadian_owned"]), str(brand_row["total_investment_range"])) else "No"
        brand_row["research_track"] = track
        if override_note:
            existing_gaps = str(brand_row["top_critical_gaps"])
            brand_row["top_critical_gaps"] = safe_join([existing_gaps, override_note])

        enforce_website_source_firewall(brand_row)
        track = str(brand_row["research_track"])
        grade = str(brand_row["evidence_grade"])
        posture = str(brand_row["decision_posture"])
        verified_core_fields = int(brand_row["verified_core_fee_fields"] or 0)

        brand_rows.append(brand_row)

        priority_rows.append(
            {
                "brand": report.title,
                "report_file": report.name,
                "report_path": report.path.relative_to(ROOT).as_posix(),
                "research_track": track,
                "evidence_grade": grade,
                "source_depth_rank": rank_map[report.name],
                "source_count": source_count,
                "official_brand_source_count": len(unique_official_brand_urls),
                "official_brand_evidence_item_count": official_evidence_count,
                "verified_core_fee_fields": verified_core_fields,
                "cross_border_caution": "Yes" if row_is_non_canadian_offer(str(brand_row["canadian_owned"]), str(brand_row["total_investment_range"])) else "No",
                "decision_posture": posture,
                "priority_reason": safe_join(report.critical_gaps[:3] + ([override_note] if override_note else [])),
            }
        )

        if override_brand_fields or override_evidence_items:
            primary_batch_rows.append(
                {
                    "brand": report.title,
                    "report_file": report.name,
                    "report_path": report.path.relative_to(ROOT).as_posix(),
                    "official_sources_added": str(len({item["source_url"] for item in override_evidence_items})),
                    "updated_source_count": str(source_count),
                    "updated_evidence_grade": grade,
                    "updated_research_track": track,
                    "note": override_note,
                }
            )

    brand_rows.sort(
        key=lambda row: (
            row["source_depth_rank"],
            row["brand"],
        )
    )
    evidence_rows.sort(key=lambda row: (row["brand"], row["field_key"], row["source_url"]))
    priority_rows.sort(
        key=lambda row: (
            row["research_track"],
            row["source_depth_rank"],
            row["brand"],
        )
    )

    write_csv(
        BRAND_CSV,
        [
            "brand",
            "report_file",
            "report_path",
            "source_depth_rank",
            "category",
            "generic_screening_score",
            "risk_level",
            "growth_outlook",
            "investment_tier",
            "confidence_level",
            "investment_goal_fit",
            "founded",
            "headquarters",
            "canadian_owned",
            "industry",
            "cuisine",
            "total_investment_range",
            "franchise_fee",
            "royalty_percent",
            "marketing_fund_percent",
            "min_liquid_capital",
            "location_requirements",
            "average_time_to_open",
            "training_provided",
            "profitability_indicators",
            "number_of_locations",
            "growth_trends",
            "owner_reviews",
            "pros",
            "cons",
            "top_praises",
            "top_complaints",
            "contact_information",
            "fdd_summary",
            "market_saturation",
            "threat_level",
            "operational_difficulty",
            "franchisor_confirmation",
            "source_count",
            "evidence_grade",
            "decision_posture",
            "rejected_fields",
            "verified_core_fee_fields",
            "official_brand_source_count",
            "government_or_law_source_count",
            "source_evidence_item_count",
            "official_brand_evidence_item_count",
            "cross_border_caution",
            "research_track",
            "top_critical_gaps",
            "official_brand_sources",
            "government_or_law_sources",
        ],
        brand_rows,
    )
    BRAND_JSON.write_text(json.dumps(brand_rows, indent=2), encoding="utf-8")

    write_csv(
        EVIDENCE_CSV,
        [
            "brand",
            "report_file",
            "report_path",
            "field_key",
            "field_value",
            "source_url",
            "source_domain",
            "source_type",
            "source_date",
            "source_reliability",
            "investor_scoring_use",
        ],
        evidence_rows,
    )

    write_csv(
        PRIORITY_CSV,
        [
            "brand",
            "report_file",
            "report_path",
            "research_track",
            "evidence_grade",
            "source_depth_rank",
            "source_count",
            "official_brand_source_count",
            "official_brand_evidence_item_count",
            "verified_core_fee_fields",
            "cross_border_caution",
            "decision_posture",
            "priority_reason",
        ],
        priority_rows,
    )

    deep_dive_count = sum(1 for row in priority_rows if row["research_track"] == "deep_dive_candidate")
    rebuild_count = sum(1 for row in priority_rows if row["research_track"] == "rebuild_from_primary_sources")
    official_gap_count = sum(1 for row in priority_rows if row["research_track"] == "find_official_brand_sources")
    verify_fee_count = sum(1 for row in priority_rows if row["research_track"] == "verify_core_franchise_fees")

    summary_lines = [
        f"# GetFranchise Data Export Summary - {EXPORT_DATE}",
        "",
        "## Files Created",
        f"- `{BRAND_CSV.name}`: one row per franchise brand",
        f"- `{BRAND_JSON.name}`: JSON version of the brand dataset",
        f"- `{EVIDENCE_CSV.name}`: one row per source-backed evidence item",
        f"- `{PRIORITY_CSV.name}`: research work queue by brand",
        f"- `{PRIMARY_BATCH_MD.name}`: brands upgraded in the current primary-source batch",
        "",
        "## Coverage",
        f"- Brand rows: {len(brand_rows)}",
        f"- Evidence rows: {len(evidence_rows)}",
        f"- Official brand/company evidence rows: {total_official_brand_sources}",
        f"- Brands with primary-source overrides loaded in this batch: {len(primary_batch_rows)}",
        "",
        "## Research Queue Snapshot",
        f"- `deep_dive_candidate`: {deep_dive_count}",
        f"- `rebuild_from_primary_sources`: {rebuild_count}",
        f"- `find_official_brand_sources`: {official_gap_count}",
        f"- `verify_core_franchise_fees`: {verify_fee_count}",
        "",
        "## Notes",
        "- These exports structure the current franchise research already present in the folder.",
        "- They do not fabricate missing unit economics or disclosure data.",
        "- Use the priority CSV to decide whether a brand should be rebuilt, source-mapped, or taken into deep diligence.",
    ]
    SUMMARY_MD.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    primary_lines = [
        f"# GetFranchise Primary Source Batch - {EXPORT_DATE}",
        "",
        f"- Brands upgraded in this batch: {len(primary_batch_rows)}",
        "- These upgrades rely on official brand/company pages or official franchise pages identified during the current pass.",
        "- They improve the structured datasets first; narrative text files still require separate line-by-line rewrite if you want full report harmonization.",
        "",
        "| Brand | Sources Added | New Source Count | Grade | Research Track |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for row in sorted(primary_batch_rows, key=lambda item: item["brand"]):
        primary_lines.append(
            f"| {row['brand']} | {row['official_sources_added']} | {row['updated_source_count']} | {row['updated_evidence_grade']} | {row['updated_research_track']} |"
        )
    PRIMARY_BATCH_MD.write_text("\n".join(primary_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
