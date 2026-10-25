from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parent
DEFAULT_REPORT_FOLDER = "food franchises"
REPORTS_DIR = ROOT / DEFAULT_REPORT_FOLDER
REPORT_GLOB = "*.txt"
MASTER_FILE = ROOT / "MASTER_DUE_DILIGENCE.md"
AUDIT_FILE = ROOT / "PORTFOLIO_STRUCTURE_AND_RESEARCH_AUDIT_2026-07-24.md"
APPENDIX_MARKER = "10. PROFESSIONAL RESEARCH LAYER (2026-07-24)"
LEGACY_APPENDIX_MARKERS = ("10. PROFESSIONAL RESEARCH LAYER (2026-07-18)",)
PASS_DATE = "July 24, 2026"


FOOD_CONTEXT_SOURCES = [
    (
        "Statistics Canada: food services and drinking places, April 2026",
        "https://www150.statcan.gc.ca/n1/daily-quotidien/260629/dq260629c-eng.htm",
    ),
    (
        "Statistics Canada: food services and drinking places, December 2025 / annual 2025 section",
        "https://www150.statcan.gc.ca/n1/daily-quotidien/260225/dq260225d-eng.htm",
    ),
    (
        "Statistics Canada: food services and drinking places, annual 2024",
        "https://www150.statcan.gc.ca/n1/daily-quotidien/260309/dq260309a-eng.htm",
    ),
    (
        "Statistics Canada: payroll employment, earnings and job vacancies, March 2026",
        "https://www150.statcan.gc.ca/n1/daily-quotidien/260528/dq260528b-eng.htm",
    ),
    (
        "Statistics Canada: Labour Force Survey, May 2026",
        "https://www150.statcan.gc.ca/n1/daily-quotidien/260605/dq260605a-eng.htm",
    ),
]


COMMON_CONTEXT_SOURCES = [
    (
        "Ontario: franchising information for buyers and owners",
        "https://www.ontario.ca/page/franchising-information-buyers-and-owners",
    ),
    (
        "British Columbia: Franchises Act",
        "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/15035",
    ),
    (
        "Manitoba: The Franchises Act",
        "https://web2.gov.mb.ca/laws/statutes/ccsm/f156.php?lang=en",
    ),
    (
        "New Brunswick: Franchises Act",
        "https://laws.gnb.ca/en/document/cs/2014%2C%20c.111",
    ),
    (
        "Prince Edward Island: Franchises Act",
        "https://www.princeedwardisland.ca/en/legislation/franchises-act",
    ),
    (
        "Canadian Franchise Association: franchise disclosure legislation across Canada",
        "https://cfa.ca/advocacy/franchise-disclosure-leg/",
    ),
    (
        "Canadian Franchise Association: Saskatchewan effective June 30, 2026",
        "https://cfa.ca/saskatchewan-enacts-franchise-disclosure-legislation-effective-june-30-2026/",
    ),
]


@dataclass
class ReportData:
    path: Path
    report_folder: str
    name: str
    title: str
    generic_score: int | None
    risk_level: str
    growth_outlook: str
    investment_tier: str
    confidence_level: str
    investment_goal_fit: str
    source_count: int
    rejected_fields: int | None
    founded: str
    headquarters: str
    canadian_owned: str
    industry: str
    cuisine: str
    investment_range: str
    franchise_fee: str
    royalty: str
    marketing_fee: str
    min_liquid_capital: str
    market_saturation: str
    threat_level: str
    operational_difficulty: str
    franchisor_confirmation: str
    critical_gaps: list[str]
    source_rank: int = 0


def report_directories() -> list[Path]:
    directories: list[Path] = []
    for child in sorted(ROOT.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith(".") or child.name == "__pycache__":
            continue
        if child.name.endswith("franchises"):
            directories.append(child)
    return directories


def iter_report_paths() -> list[Path]:
    paths: list[Path] = []
    for directory in report_directories():
        paths.extend(sorted(directory.rglob(REPORT_GLOB)))
    return paths


def first_nonblank_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def strip_professional_appendix(text: str) -> str:
    for marker in (APPENDIX_MARKER, *LEGACY_APPENDIX_MARKERS):
        if marker in text:
            return text.split(marker)[0].rstrip() + "\n"
    return text.rstrip() + "\n"


def extract_line_value(text: str, label: str) -> str:
    pattern = re.compile(rf"^{re.escape(label)}:\s*(.+)$", re.MULTILINE)
    match = pattern.search(text)
    if match:
        return match.group(1).strip()

    pattern = re.compile(rf"^- {re.escape(label)}:\s*(.+)$", re.MULTILINE)
    match = pattern.search(text)
    if match:
        return match.group(1).strip()

    return "Not stated"


def extract_line_value_any(text: str, labels: list[str]) -> str:
    for label in labels:
        value = extract_line_value(text, label)
        if value != "Not stated":
            return value
    return "Not stated"


def extract_int_value(text: str, label: str) -> int | None:
    value = extract_line_value(text, label)
    match = re.search(r"(\d+)", value)
    return int(match.group(1)) if match else None


def extract_critical_gaps(text: str) -> list[str]:
    match = re.search(
        r"Critical Gaps:\n(?P<body>.*?)(?:\nDo Not Use For Investment Scoring:|\nFields Rejected Due To Evidence Rules:|\Z)",
        text,
        re.DOTALL,
    )
    if not match:
        return []

    gaps = []
    for raw_line in match.group("body").splitlines():
        line = raw_line.strip()
        if line.startswith("- "):
            gaps.append(line[2:].strip())
    return gaps


def load_report(path: Path) -> ReportData:
    text = path.read_text(encoding="utf-8")
    text = strip_professional_appendix(text)
    return ReportData(
        path=path,
        report_folder=path.parent.name,
        name=path.name,
        title=first_nonblank_line(text),
        generic_score=extract_int_value(text, "Generic Screening Score"),
        risk_level=extract_line_value(text, "Risk Level"),
        growth_outlook=extract_line_value(text, "Growth Outlook"),
        investment_tier=extract_line_value(text, "Investment Tier"),
        confidence_level=extract_line_value(text, "Confidence Level"),
        investment_goal_fit=extract_line_value(text, "Investment Goal Fit"),
        source_count=extract_int_value(text, "Total Source Count") or 0,
        rejected_fields=extract_int_value(text, "Fields Rejected Due To Evidence Rules"),
        founded=extract_line_value(text, "Founded"),
        headquarters=extract_line_value(text, "HQ"),
        canadian_owned=extract_line_value(text, "Canadian Owned"),
        industry=extract_line_value(text, "Industry"),
        cuisine=extract_line_value_any(text, ["Category / Service", "Cuisine"]),
        investment_range=extract_line_value(text, "Total Investment Range"),
        franchise_fee=extract_line_value(text, "Franchise Fee"),
        royalty=extract_line_value(text, "Royalty %"),
        marketing_fee=extract_line_value(text, "Marketing Fund %"),
        min_liquid_capital=extract_line_value(text, "Min Liquid Capital"),
        market_saturation=extract_line_value(text, "Market saturation"),
        threat_level=extract_line_value(text, "Threat level"),
        operational_difficulty=extract_line_value(text, "Operational Difficulty"),
        franchisor_confirmation=extract_line_value(text, "Franchisor Confirmation"),
        critical_gaps=extract_critical_gaps(text),
    )


def is_verified(value: str) -> bool:
    lowered = value.lower()
    blocked_tokens = (
        "not verified",
        "estimated",
        "requires verification",
        "n/a",
        "not stated",
    )
    return not any(token in lowered for token in blocked_tokens)


def is_non_canadian_offer(data: ReportData) -> bool:
    owned = data.canadian_owned.lower()
    investment = data.investment_range.lower()
    explicitly_non_canadian = (
        owned == "no"
        or owned.startswith("no -")
        or owned.startswith("no,")
        or "united states" in owned
        or "u.s." in owned
        or "us-based" in owned
    )
    return explicitly_non_canadian or "usd" in investment


def infer_category(data: ReportData) -> str:
    folder = data.report_folder.lower()
    folder_map = {
        "real estate franchises": "real_estate",
        "hotels franchises": "hotel",
        "fitness franchises": "fitness",
        "education franchises": "education",
        "cleaning franchises": "cleaning",
        "automotive franchises": "automotive",
        "home services franchises": "home_services",
        "child services franchises": "child_services",
        "senior care franchises": "senior_care",
        "shipping and printing franchises": "shipping_printing",
        "staffing franchises": "staffing",
        "pet services franchises": "pet_services",
        "finance franchises": "finance",
    }
    if folder in folder_map:
        return folder_map[folder]

    combined = f"{data.title} {data.industry} {data.cuisine}".lower()

    if any(
        token in combined
        for token in ("dessert", "ice cream", "frozen yogurt", "donut", "bakery", "bubble tea", "tea", "juice", "smoothie", "coffee")
    ):
        return "beverage_dessert"

    if any(token in combined for token in ("quick-service", "qsr")):
        return "limited_service"

    if any(token in combined for token in ("casual dining", "sports bar", "full-service")):
        return "full_service"

    if any(
        token in combined
        for token in (
            "pizza",
            "burger",
            "shawarma",
            "burrito",
            "sandwich",
            "subs",
            "submarine",
            "ramen",
            "noodle",
            "poke",
            "pretzel",
            "fries",
            "wings",
            "chicken",
            "taco",
            "sushi",
        )
    ):
        return "limited_service"

    if any(
        token in combined
        for token in ("breakfast", "bar", "grill", "roadhouse", "bbq", "rotisserie", "restaurant", "lunch")
    ):
        return "full_service"

    return "general_foodservice"


def category_context(category: str) -> str:
    if category == "limited_service":
        return (
            "Canadian limited-service eating place sales reached $47.3 billion in 2025, up 5.9% from 2024. "
            "That supports demand resilience, but store-level returns still depend heavily on throughput, rent and labour discipline."
        )
    if category == "full_service":
        return (
            "Canadian full-service restaurant sales reached $43.6 billion in 2025, up 5.8% from 2024. "
            "That supports the category, but table turns, manager depth and labour scheduling remain decisive underwriting variables."
        )
    if category == "beverage_dessert":
        return (
            "Canada's foodservice market remained positive in 2025 and into April 2026, but beverage and dessert concepts are more exposed to weather, "
            "mall traffic, impulse demand and daypart concentration than staple meal categories."
        )
    if category == "real_estate":
        return "Real-estate franchise underwriting depends more on agent recruiting, retention, commission splits, and office-level operating leverage than on walk-in demand."
    if category == "hotel":
        return "Hotel economics turn on occupancy, ADR, RevPAR, property age, renovation reserves, and whether the local demand mix is business, highway, or destination-led."
    if category == "fitness":
        return "Fitness studios are driven by membership acquisition, retention, coach payroll, site visibility, and the brand's ability to control churn."
    if category == "education":
        return "Education and tutoring centres live or die on enrolment density, retention, scheduling utilization, and household demographics in the catchment."
    if category == "cleaning":
        return "Cleaning concepts depend on route density, labour recruitment, client retention, and quality control more than on broad category awareness alone."
    if category == "automotive":
        return "Automotive service units are controlled by bay utilization, technician availability, car-count trends, and the mix of maintenance versus higher-margin work."
    if category == "home_services":
        return "Home-service franchises depend on lead flow, contractor or technician supply, local reputation, and how strong the exclusive territory really is in practice."
    if category == "child_services":
        return "Child-service and childcare concepts are constrained by licensing, staffing ratios, occupancy utilization, and local household demand."
    if category == "senior_care":
        return "Senior-care models are driven by caregiver recruitment, referral relationships, compliance discipline, and how consistently billable hours can be filled."
    if category == "shipping_printing":
        return "Shipping and printing centres rely on small-business account retention, parcel volume, print mix, and business-district trade area quality."
    if category == "staffing":
        return "Staffing franchises are fundamentally sales and recruiting businesses, so returns depend on client mix, recruiter productivity, and payroll-funding discipline."
    if category == "pet_services":
        return "Pet retail and service concepts are helped by repeat nutrition purchases, but economics still depend on basket size, margin mix, and local competition."
    if category == "finance":
        return "Finance and accounting franchises are office economics businesses where lead flow, advisor productivity, compliance, and referral quality matter more than storefront traffic."
    return (
        "Canadian food services sales totalled $101.4 billion in 2025, and April 2026 sales were $8.8 billion, up 0.8% month over month. "
        "That is supportive at a portfolio level, but concept economics still rise or fall on location and execution."
    )


def pricing_and_labour_context(category: str) -> str:
    if category in {"limited_service", "full_service", "beverage_dessert", "general_foodservice"}:
        return (
            "Statistics Canada reported food purchased from restaurants was up 3.0% year over year in April 2026, while accommodation and food services "
            "payroll employment fell in March 2026 before broader sector employment rose by 17,000 in May 2026. In practice, that means pricing power and staffing conditions are still uneven."
        )
    return (
        "Current market conditions still need to be tested at the local level. Lease cost, hiring depth, territory quality, compliance burden, and lead flow should be treated as primary underwriting variables."
    )


def context_sources(category: str) -> list[tuple[str, str]]:
    if category in {"limited_service", "full_service", "beverage_dessert", "general_foodservice"}:
        return FOOD_CONTEXT_SOURCES + COMMON_CONTEXT_SOURCES
    return COMMON_CONTEXT_SOURCES


def evidence_grade(data: ReportData) -> str:
    core_fields = [
        data.investment_range,
        data.franchise_fee,
        data.royalty,
        data.marketing_fee,
    ]
    verified_core = sum(1 for field in core_fields if is_verified(field))

    if data.source_count >= 10 and verified_core >= 3:
        grade = "B"
    elif data.source_count >= 5 and verified_core >= 2:
        grade = "C+"
    elif data.source_count >= 3 and verified_core >= 1:
        grade = "C"
    elif data.source_count >= 1:
        grade = "D"
    else:
        grade = "F"

    if data.rejected_fields is not None and data.rejected_fields >= 50 and grade != "F":
        downgrade_order = {"B": "C+", "C+": "C", "C": "D", "D": "D"}
        grade = downgrade_order.get(grade, grade)

    return grade


def source_depth_comment(data: ReportData) -> str:
    if data.source_count >= 10:
        return "This is one of the strongest evidence packs in the folder by source depth, but it still stops short of investment-grade because store-level economics and legal package reconciliation remain incomplete."
    if data.source_count >= 4:
        return "This file has a better-than-average evidence base for the current folder, but it is still a preliminary memo rather than a fully underwritable franchise brief."
    if data.source_count >= 1:
        return "The current evidence pack is thin. It is usable for comparison screening, but not for investment committee use."
    return "This file had no brand-specific source pack before this pass. Treat every economic conclusion as unproven until the franchisor package and direct operating evidence are loaded."


def decision_posture(data: ReportData, grade: str) -> str:
    core_missing = not any(is_verified(field) for field in (data.investment_range, data.franchise_fee, data.royalty, data.marketing_fee))
    if grade == "F" or core_missing:
        return "Screening only; do not underwrite until a current Canadian disclosure package and direct franchisor economics are obtained."
    if grade in {"D", "C"}:
        return "Advance only to targeted diligence. The file can support shortlisting, but not commitment or formal return modeling."
    return "Candidate for manual deep dive. This is stronger than most files in the folder, but it still requires legal-document and unit-level validation before any recommendation."


def committee_action(data: ReportData, grade: str) -> str:
    core_missing = not any(is_verified(field) for field in (data.investment_range, data.franchise_fee, data.royalty, data.marketing_fee))
    if grade == "F" or core_missing:
        return "Hold as screening inventory. Do not model returns, contact lenders, or compare against buy decisions until primary Canadian evidence is loaded."
    if grade in {"D", "C"}:
        return "Move to source rebuild or franchisor outreach only if the category is strategically attractive for the target operator."
    return "Eligible for a focused diligence sprint, limited to evidence collection and operator interviews before any financial recommendation."


def use_case_boundary(data: ReportData, grade: str) -> str:
    if grade in {"B", "C+"}:
        return "Appropriate for shortlist discussion and diligence planning; not appropriate for final investment approval."
    if grade in {"C", "D"}:
        return "Appropriate for market mapping and early comparison; not appropriate for financial underwriting."
    return "Appropriate only as a placeholder target in the database until brand-specific primary sources are added."


def category_diligence_questions(category: str) -> list[str]:
    questions = {
        "real_estate": [
            "What are the current broker-owner fees, split economics, desk-fee assumptions, and recruiting minimums?",
            "How many productive agents are required to cover fixed overhead after royalties, technology, rent, and administration?",
            "What retention, transfer, renewal, and territory provisions apply to Canadian brokerages?",
        ],
        "hotel": [
            "What property-improvement-plan, renovation reserve, brand-standard, and key-money obligations apply to the specific asset?",
            "What are the local ADR, occupancy, RevPAR, labour, insurance, and management-fee assumptions for the trade area?",
            "How do franchise, reservation, loyalty, technology, marketing, and purchasing fees flow through the property P&L?",
        ],
        "fitness": [
            "What membership count, churn rate, coach payroll, lease cost, and presale volume are needed to hit break-even?",
            "What territory protection or studio-spacing rule prevents cannibalization?",
            "What capital is required for equipment refresh, technology, music/licensing, and brand-standard updates?",
        ],
        "education": [
            "What enrolment level, instructor utilization, parent-retention rate, and local tuition price are needed for break-even?",
            "Does the model require owner-operator involvement, education credentials, or mandated instructional hours?",
            "What seasonal enrolment, tutoring competition, and school-calendar risks affect the target trade area?",
        ],
        "cleaning": [
            "What route density, cleaner retention, customer churn, insurance, supplies, and dispatch capacity are assumed?",
            "How much revenue is recurring contract work versus one-time residential or restoration work?",
            "What local wage, vehicle, training, and quality-control costs must be stress-tested?",
        ],
        "automotive": [
            "What bay count, technician capacity, parts margin, tire mix, warranty exposure, and utilization are required?",
            "What capex is needed for buildout, equipment, environmental compliance, signage, and future refreshes?",
            "How sensitive is the model to traffic counts, fleet accounts, EV adoption, and local repair competition?",
        ],
        "home_services": [
            "What lead sources, close rates, technician or contractor availability, gross margin, and callback rates are assumed?",
            "Is the territory exclusive, and does it contain enough qualified households at target ticket sizes?",
            "What seasonality, licensing, insurance, vehicle, and dispatch constraints apply locally?",
        ],
        "child_services": [
            "What licensing, child-to-staff ratio, insurance, facility, and safety requirements apply in the target province?",
            "What enrolment ramp, tuition price, staff cost, and occupancy utilization support break-even?",
            "How exposed is the model to subsidies, school calendars, parent retention, and local program competition?",
        ],
        "senior_care": [
            "What caregiver recruitment, retention, billable-hour utilization, referral-channel, and compliance assumptions drive margin?",
            "How are background checks, training, insurance, scheduling, overtime, and supervision costs handled?",
            "What proportion of revenue comes from private pay, referral partners, healthcare programs, or institutional accounts?",
        ],
        "shipping_printing": [
            "What parcel volume, print-margin mix, mailbox occupancy, business-account retention, and staffing level are required?",
            "What carrier, royalty, technology, equipment, lease, and local marketing fees apply?",
            "Does the trade area contain enough small-business density, daytime traffic, parking, and repeat commercial demand?",
        ],
        "staffing": [
            "What client acquisition rate, recruiter productivity, gross margin, bad-debt risk, and payroll-funding structure are assumed?",
            "Which industries dominate the local territory, and how cyclical are their hiring needs?",
            "What legal, workers-compensation, insurance, and compliance obligations sit with the franchisee?",
        ],
        "pet_services": [
            "What revenue mix comes from retail, grooming, daycare, boarding, training, subscription, or delivery channels?",
            "What labour, lease, animal-care, insurance, zoning, and facility-cleaning costs are required?",
            "How strong is local competition from national pet retailers, independents, veterinarians, and online channels?",
        ],
        "finance": [
            "What licensing, compliance, referral, advisor productivity, commission-split, and recurring-fee terms apply?",
            "How does the franchisee acquire clients, and what production level is needed before owner compensation?",
            "What technology, brand, training, territory, renewal, and transfer obligations affect long-term economics?",
        ],
    }
    return questions.get(
        category,
        [
            "What exact Canadian investment range, working capital, royalty, marketing, technology, transfer, and renewal terms apply?",
            "What local unit economics, staffing, occupancy, and customer-acquisition assumptions support break-even?",
            "What current franchisee evidence confirms support quality, satisfaction, closures, transfers, renewals, and resale outcomes?",
        ],
    )


def whitespace_context(data: ReportData) -> str:
    saturation = data.market_saturation.lower()
    if "high" in saturation:
        return "Whitespace is likely narrower in the brand's core markets. Expansion only works if the trade area is protected, non-cannibalizing and still supports acceptable four-wall economics after rent and labour."
    if "low" in saturation:
        return "Whitespace may exist, but a lighter footprint can also mean less mature field support, weaker brand awareness or more volatile local marketing efficiency."
    if "medium" in saturation:
        return "Whitespace may still exist, but the economics will be highly trade-area specific. Site selection matters more than headline brand familiarity."
    return "Current whitespace cannot be trusted from this file alone; province count, non-traditional formats and territory protection all need direct confirmation."


def ownership_context(data: ReportData) -> str:
    if is_non_canadian_offer(data):
        return "Cross-border caution applies here. Reconcile U.S. disclosures, USD figures, entity structure and any Canadian master-franchise arrangement before using the numbers in a Canadian model."
    return "Canadian operating relevance is a positive, but local ownership alone does not replace the need for current disclosure, unit economics, litigation checks and franchisee interviews."


def confidence_comment(data: ReportData) -> str:
    return (
        f"Current file confidence is {data.confidence_level}. That is directionally appropriate given the source depth, the number of rejected fields and the absence of direct franchisee interview evidence."
    )


def brand_positioning_line(data: ReportData) -> str:
    parts = [data.title]
    if is_verified(data.founded):
        parts.append(f"is presented as a {data.founded}-founded brand")
    else:
        parts.append("is presented as an established franchise brand")

    if data.cuisine != "Not stated":
        parts.append(f"with a current category/service line of {data.cuisine.lower()}")

    if data.growth_outlook != "Not stated":
        parts.append(f"with a current report growth outlook of {data.growth_outlook.lower()}")

    return " ".join(parts) + "."


def material_unknowns(data: ReportData) -> list[str]:
    gaps = data.critical_gaps[:5]
    if gaps:
        return gaps

    fallbacks = [
        "Current Canadian disclosure package or FDD-equivalent",
        "Exact Canadian signing entity and governing documents",
        "Verified current investment range and recurring fees",
        "Store-level unit economics, transfers, renewals and closures",
        "Current and former franchisee interviews",
    ]
    return fallbacks


def build_appendix(data: ReportData, total_reports: int) -> str:
    grade = evidence_grade(data)
    category = infer_category(data)
    lines = [
        "",
        APPENDIX_MARKER,
        f"Research Pass Date: {PASS_DATE}",
        f"Portfolio Source-Depth Rank: {data.source_rank}/{total_reports}",
        f"Brand-Specific Source Count Before This Pass: {data.source_count}",
        f"Evidence Grade: {grade}",
        f"Current Decision Posture: {decision_posture(data, grade)}",
        f"Investment Committee Action: {committee_action(data, grade)}",
        f"Approved Use Case: {use_case_boundary(data, grade)}",
        "",
        "Professional Assessment",
        f"- Positioning: {brand_positioning_line(data)}",
        f"- Evidence view: {source_depth_comment(data)}",
        f"- Category context: {category_context(category)}",
        f"- Market conditions: {pricing_and_labour_context(category)}",
        f"- Saturation / whitespace: {whitespace_context(data)}",
        f"- Ownership / entity view: {ownership_context(data)}",
        f"- Confidence discipline: {confidence_comment(data)}",
        "",
        "Canadian Franchise-Law Context",
        "- As of June 30, 2026, Saskatchewan became the seventh Canadian province with franchise disclosure legislation, joining British Columbia, Alberta, Manitoba, Ontario, New Brunswick and Prince Edward Island.",
        "- Ontario guidance and the British Columbia Franchises Act both reinforce the 14-day disclosure review principle before signing or payment; use that timing discipline across this portfolio even when a brand sells through a cross-border structure.",
        "- This file should not be promoted beyond screening until the exact province-specific legal package and signing entity are identified.",
        "",
        "Most Material Unknowns",
    ]

    for gap in material_unknowns(data):
        lines.append(f"- {gap}")

    lines.extend(
        [
            "",
            "Category-Specific Diligence Questions",
        ]
    )

    for question in category_diligence_questions(category):
        lines.append(f"- {question}")

    lines.extend(
        [
            "",
            "Advancement Requirements",
            "- Obtain the current Canadian disclosure package or equivalent, including all schedules and amendments.",
            "- Confirm the exact signing entity, province coverage, governing law and whether any Canadian master-franchise or area-development structure sits between the brand and the operator.",
            "- Verify current initial investment, working capital, royalties, ad fund, technology, transfer, renewal and refurbishment obligations.",
            "- Get at least three comparable unit P&Ls or a Canadian earnings-support package before modeling payback.",
            "- Validate the trade area with lease terms, competitor density, parking/access, delivery radius, review signals and local labour assumptions.",
            "",
            "Professional Quality Standard",
            "- Any exact number in this file should trace to a named source, source date, retrieval date, and reliability rating before it is used in a decision memo.",
            "- Any estimated field should remain excluded from investor-grade scoring, even when the estimate is useful for rough screening.",
            "- Any cross-border figure should be reconciled to Canadian currency, Canadian entity structure, and Canadian disclosure before comparison.",
            "",
            "11. PORTFOLIO CONTEXT SOURCES (2026-07-24)",
            "These sources were used to raise the professional context level of this file. They do not replace brand-specific franchisor documents.",
        ]
    )

    for label, url in context_sources(category):
        lines.append(f"- {label} | {url}")

    return "\n".join(lines).rstrip() + "\n"


def report_sort_key(data: ReportData) -> tuple[int, int]:
    rejected = data.rejected_fields if data.rejected_fields is not None else -1
    return (-data.source_count, rejected)


def write_audit_file(reports: list[ReportData]) -> None:
    sorted_reports = sorted(reports, key=report_sort_key)
    source_counts = [r.source_count for r in reports]
    zero_source_count = sum(1 for r in reports if r.source_count == 0)
    one_source_count = sum(1 for r in reports if r.source_count == 1)
    weak_count = sum(1 for r in reports if r.source_count <= 2)
    stronger_count = sum(1 for r in reports if r.source_count >= 4)
    median = sorted(source_counts)[len(source_counts) // 2]

    lines = [
        "# Portfolio Structure And Research Audit - July 24, 2026",
        "",
        "## Structure",
        f"- Franchise reports: {len(reports)} text files",
        f"- Master diligence file: `{MASTER_FILE.name}`",
        "- Directory shape: category folders under `output/franchises`, one brand per file, common 9-section screening template before this pass",
        "",
        "## Evidence Quality Snapshot",
        f"- Average brand-specific source count before this pass: {mean(source_counts):.2f}",
        f"- Median brand-specific source count before this pass: {median}",
        f"- Files with zero brand-specific sources: {zero_source_count}",
        f"- Files with one brand-specific source: {one_source_count}",
        f"- Files with two sources or fewer: {weak_count}",
        f"- Files with four sources or more: {stronger_count}",
        "",
        "## What This Professionalization Pass Added",
        "- Appended a dated professional research layer to every franchise report.",
        "- Added category-aware market context so non-food brands do not inherit restaurant-only commentary.",
        "- Added current Canadian franchise-law context, including Saskatchewan's June 30, 2026 implementation date.",
        "- Added evidence grading, decision posture and advancement requirements to force clearer investment discipline.",
        "- Added investment committee action language and approved-use boundaries to reduce overinterpretation of screening files.",
        "- Added category-specific diligence questions for every major non-food folder and foodservice category.",
        "",
        "## Highest Source-Depth Files Before This Pass",
        "",
        "| Rank | File | Sources | Rejected Fields |",
        "| --- | --- | ---: | ---: |",
    ]

    for idx, report in enumerate(sorted_reports[:25], start=1):
        rejected = report.rejected_fields if report.rejected_fields is not None else "-"
        lines.append(f"| {idx} | {report.name} | {report.source_count} | {rejected} |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "- The folder was not primarily a formatting problem; it was an evidence problem.",
            "- Most reports were still screening-grade because the majority had little or no brand-specific sourcing, even when the narrative sounded confident.",
            "- The portfolio is now easier to triage, but it is still not a substitute for current franchisor packages, current legal review and real unit-level economics.",
            "",
            "## Recommended Next Work",
            "- Deep-dive first into the highest source-depth files because they have the best chance of becoming investment-grade with incremental effort.",
            "- Rebuild zero-source files from official franchisor pages, disclosure documents and corporate/entity checks rather than trying to patch them with generic benchmarks.",
            "- If this portfolio will drive real capital allocation, convert the top shortlist into a tracked diligence workbook with entity, fee, lease, unit-economics and interview fields.",
        ]
    )

    AUDIT_FILE.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def update_master_file() -> None:
    original = MASTER_FILE.read_text(encoding="utf-8")
    marker = "## 2026 Canadian Context Upgrade"
    if marker in original:
        base = original.split(marker)[0].rstrip() + "\n"
    else:
        base = original.rstrip() + "\n"

    appendix = f"""

## 2026 Canadian Context Upgrade
- As of June 30, 2026, Saskatchewan joined British Columbia, Alberta, Manitoba, Ontario, New Brunswick and Prince Edward Island as a province with franchise disclosure legislation.
- Ontario buyer guidance and the British Columbia Franchises Act reinforce a 14-day disclosure review period before signing or payment; use that timing discipline as a minimum standard even when a brand uses a U.S. package or cross-border entity.
- This portfolio now spans food and non-food categories in separate subfolders under `output/franchises`.
- Do not apply food-service assumptions to gyms, staffing, finance, hotels, real estate, or other office/service concepts without category-specific evidence.

## Portfolio Triage Rule
- Do not treat low-source files as lower risk just because they have clean narrative formatting.
- Prioritize brands that already have multiple official sources, verified fee structures and a clear Canadian legal offer.
- Rebuild zero-source files from primary material instead of trying to improve them with benchmarks.

## Current Context Sources
- Ontario, franchising information for buyers and owners: https://www.ontario.ca/page/franchising-information-buyers-and-owners
- British Columbia, Franchises Act: https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/15035
- Manitoba, The Franchises Act: https://web2.gov.mb.ca/laws/statutes/ccsm/f156.php?lang=en
- New Brunswick, Franchises Act: https://laws.gnb.ca/en/document/cs/2014%2C%20c.111
- Prince Edward Island, Franchises Act: https://www.princeedwardisland.ca/en/legislation/franchises-act
- Canadian Franchise Association, franchise disclosure legislation across Canada: https://cfa.ca/advocacy/franchise-disclosure-leg/
- Canadian Franchise Association, Saskatchewan effective June 30, 2026: https://cfa.ca/saskatchewan-enacts-franchise-disclosure-legislation-effective-june-30-2026/
""".rstrip()

    MASTER_FILE.write_text(base + appendix + "\n", encoding="utf-8")


def main() -> None:
    reports = [load_report(path) for path in iter_report_paths()]
    ordered = sorted(reports, key=report_sort_key)
    for idx, report in enumerate(ordered, start=1):
        report.source_rank = idx

    report_count = len(reports)
    for report in reports:
        base_text = report.path.read_text(encoding="utf-8")
        base_text = strip_professional_appendix(base_text)
        appendix = build_appendix(report, report_count)
        report.path.write_text(base_text + appendix, encoding="utf-8")

    write_audit_file(reports)
    update_master_file()


if __name__ == "__main__":
    main()
