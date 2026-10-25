from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "franchises.json"
EXPANSION_FILE = ROOT / "data" / "expansion_franchises.json"
FRANCHISE_200_FILE = ROOT / "data" / "franchise_targets_200.json"
NON_FOOD_FILE = ROOT / "data" / "non_food_franchises.json"
NON_FOOD_EXPANSION_FILE = ROOT / "data" / "non_food_expansion_franchises.json"
NON_FOOD_CATEGORY_TARGETS_FILE = ROOT / "data" / "non_food_category_targets.json"
RESEARCH_OVERRIDES_FILE = ROOT / "data" / "research_overrides.json"
NON_FOOD_RESEARCH_OVERRIDES_FILE = ROOT / "data" / "non_food_research_overrides.json"
OUTPUT_ROOT = ROOT.parent / "output" / "franchises"
DEFAULT_REPORT_FOLDER = "food franchises"

FOOD_CATEGORY_FOLDERS = {
    "asian": "food franchises/asian",
    "bakery": "food franchises/bakery",
    "beverage": "food franchises/beverages",
    "breakfast": "food franchises/breakfast",
    "burger": "food franchises/burgers",
    "chicken": "food franchises/chicken",
    "coffee": "food franchises/coffee",
    "dessert-qsr": "food franchises/desserts",
    "health": "food franchises/healthy fast casual",
    "indian": "food franchises/indian",
    "mediterranean": "food franchises/mediterranean",
    "mexican": "food franchises/mexican",
    "pizza": "food franchises/pizza",
    "qsr": "food franchises/general qsr",
    "sandwich": "food franchises/subs and sandwiches",
    "seafood": "food franchises/seafood",
    "snack": "food franchises/snacks",
    "casual": "food franchises/casual dining",
}

EVIDENCE_RETRIEVED_DATE = "2026-07-16"
TARGET_INVESTMENT_CAD = 320_000
TARGET_INVESTMENT_LABEL = "less than $320,000 CAD"

INVESTOR_GATES = [
    ("franchisor_confirmation", "Direct franchisor confirmation received"),
    ("canadian_disclosure_package", "Canadian disclosure package obtained"),
    ("canadian_signing_entity", "Exact Canadian signing entity confirmed"),
    ("cad_investment_fees", "CAD investment and recurring fees verified"),
    ("canadian_unit_economics", "Canadian AUV, EBITDA, or comparable P&L verified"),
    ("closure_transfer_renewal", "Closure, transfer, resale, and renewal data verified"),
    ("franchisee_interviews", "Current/former franchisee interviews completed"),
    ("local_market_review", "Target-market review, competition, lease, and demographic checks completed"),
]

INVESTOR_LABELS = [
    "Reject",
    "Watchlist",
    "Proceed to Disclosure Review",
    "Proceed to Franchisee Interviews",
    "Proceed to Legal/Accounting Review",
    "Investment-Ready Candidate",
]

WEIGHTS = {
    "Investment": 0.07,
    "Investment Goal Fit": 0.07,
    "Payback": 0.09,
    "Profit Margin": 0.09,
    "Scalability": 0.07,
    "Hours": 0.04,
    "Industry Strength": 0.07,
    "Recurring Revenue": 0.07,
    "Franchisor Support": 0.07,
    "Franchisee Satisfaction": 0.07,
    "Exit Value": 0.05,
    "Territory Protection": 0.04,
    "Training Quality": 0.06,
    "Brand Maturity": 0.05,
    "Canadian Market Fit": 0.04,
    "Franchise Availability": 0.03,
    "Financial Terms Completeness": 0.02,
}

GOALS = {
    "Investment": "Affordable entry cost",
    "Investment Goal Fit": f"Target investment {TARGET_INVESTMENT_LABEL}",
    "Payback": "3-5 years",
    "Profit Margin": "Strong unit economics",
    "Scalability": "Multi-unit ownership possible",
    "Hours": "Manager-run possible (not owner-dependent)",
    "Industry Strength": "Growing or stable category",
    "Recurring Revenue": "High repeat, membership, contract, or referral frequency",
    "Franchisor Support": "Strong training + operational support",
    "Franchisee Satisfaction": "High satisfaction",
    "Exit Value": "Strong resale value (2-4x cash flow benchmark)",
    "Territory Protection": "Protected territory or clear market rights",
    "Training Quality": "Documented, practical initial and ongoing training",
    "Brand Maturity": "Established operating history",
    "Canadian Market Fit": "Canadian HQ, ownership, or clear Canadian operating presence",
    "Franchise Availability": "Franchising available in Canada",
    "Financial Terms Completeness": "Investment, franchise fee, royalty, and marketing fee identified",
}

PROVINCES = ["BC", "Alberta", "SK", "MB", "Ontario", "Quebec", "NB", "NS", "PE", "NL"]

RELIABILITY_GUIDE = {
    "FDD / legal document": "95-100",
    "Official franchise/company website": "85-95",
    "CFA / FRANdata / franchise database": "80-90",
    "Franchise Genius / FranDB / GetFDD / ClearlyFDD": "80-90",
    "Government source": "90-95",
    "Established news outlet": "70-85",
    "Industry report": "75-85",
    "Google Maps / Places API": "80-90",
    "Glassdoor / Indeed aggregate": "50-70",
    "Forum / Reddit aggregate": "30-50",
    "Individual social post": "10-30",
}


@dataclass(frozen=True)
class FactorResult:
    name: str
    value: str
    goal: str
    score: int
    explanation: str


def clamp_score(value: int) -> int:
    return max(0, min(100, int(round(value))))


def contains_estimate(value: str) -> bool:
    return "Estimated" in value or "not verified" in value.lower() or "not available" in value.lower()


def value_of(field: Any, default: str = "Not Verified") -> str:
    if isinstance(field, dict):
        return str(field.get("value") or default)
    if field in (None, ""):
        return default
    return str(field)


def report_folder_name(franchise: dict[str, Any]) -> str:
    return str(franchise.get("report_folder") or DEFAULT_REPORT_FOLDER)


def output_dir_for_franchise(franchise: dict[str, Any]) -> Path:
    if is_food_franchise(franchise):
        return OUTPUT_ROOT / food_report_folder(franchise)
    return OUTPUT_ROOT / report_folder_name(franchise)


def is_food_report_folder(folder_name: str) -> bool:
    lowered = folder_name.lower()
    return lowered == DEFAULT_REPORT_FOLDER or "food" in lowered


def is_food_franchise(franchise: dict[str, Any]) -> bool:
    return is_food_report_folder(report_folder_name(franchise))


def franchise_category_key(franchise: dict[str, Any]) -> str:
    category = franchise.get("category")
    if isinstance(category, str) and category.strip():
        return category.strip().lower()

    cuisine_type = franchise.get("profile", {}).get("cuisine_type", franchise.get("cuisine_type", ""))
    cuisine_text = value_of(cuisine_type).lower()
    if any(term in cuisine_text for term in ["submarine", "sandwich", "subs"]):
        return "sandwich"
    if "coffee" in cuisine_text or "cafe" in cuisine_text:
        return "coffee"
    if "pizza" in cuisine_text:
        return "pizza"
    if any(term in cuisine_text for term in ["burger", "hamburger"]):
        return "burger"
    return ""


def food_report_folder(franchise: dict[str, Any]) -> str:
    category = franchise_category_key(franchise)
    return FOOD_CATEGORY_FOLDERS.get(category, "food franchises/other food")


def evidence_of(field: Any) -> dict[str, str]:
    if not isinstance(field, dict):
        return {
            "value": value_of(field),
            "confidence": "20" if contains_estimate(value_of(field)) else "",
            "source_url": "Not Verified",
            "source_date": "Not Verified",
            "reliability": "Not Verified",
            "quote": "Not Verified",
        }
    return {
        "value": value_of(field),
        "confidence": str(field.get("confidence", "20")),
        "source_url": str(field.get("source_url", "Not Verified")),
        "source_date": str(field.get("source_date", "Not Verified")),
        "reliability": str(field.get("source_reliability", "Not Verified")),
        "quote": str(field.get("evidence_quote", "Not Verified")),
    }


def source_name(url: str) -> str:
    if url == "Not Verified":
        return url
    host = urlparse(url).netloc.replace("www.", "")
    return host or url


def evidence_row(label: str, field: Any, include_confidence: bool = False) -> str:
    e = evidence_of(field)
    if include_confidence:
        return f"- {label}: {e['value']} ({e['confidence']}% confidence)"
    return f"- {label}: {e['value']}"


def get_nested(franchise: dict[str, Any], section: str, key: str, default: str = "Not Verified") -> Any:
    return franchise.get(section, {}).get(key, default)


def investment_numbers(franchise: dict[str, Any]) -> list[int]:
    text = value_of(franchise["financials"].get("initial_investment", ""))
    if contains_estimate(text):
        return []
    numbers = [int(n.replace(",", "")) for n in re.findall(r"\$?([0-9][0-9,]{4,})", text)]
    thousand_numbers = [
        int(float(n.replace(",", "")) * 1_000)
        for n in re.findall(r"\$?([0-9]+(?:\.[0-9]+)?)\s*k\b", text.lower())
    ]
    million_numbers = [
        int(float(n) * 1_000_000)
        for n in re.findall(r"\b([0-9]+(?:\.[0-9]+)?)\s*(?:million|m)\b", text.lower())
    ]
    return numbers + thousand_numbers + million_numbers


def infer_investment_score(franchise: dict[str, Any]) -> int:
    numbers = investment_numbers(franchise)
    if not numbers:
        return 55
    high = max(numbers)
    if high <= 400_000:
        return 90
    if high <= 750_000:
        return 75
    if high <= 1_250_000:
        return 60
    return 40


def infer_investment_goal_fit_score(franchise: dict[str, Any]) -> int:
    numbers = investment_numbers(franchise)
    if not numbers:
        return 45
    high = max(numbers)
    if high <= TARGET_INVESTMENT_CAD:
        return 95
    overage = high / TARGET_INVESTMENT_CAD
    if overage <= 1.10:
        return 80
    if overage <= 1.25:
        return 65
    if overage <= 1.50:
        return 45
    if overage <= 2.00:
        return 30
    return 25


def infer_payback_score(franchise: dict[str, Any]) -> int:
    text = value_of(franchise["financials"].get("payback_period", ""))
    nums = [int(n) for n in re.findall(r"\b([0-9])\b", text)]
    if not nums:
        return 55
    midpoint = sum(nums[:2]) / min(len(nums), 2) if len(nums) >= 2 else nums[0]
    if 3 <= midpoint <= 5:
        return 90
    if 2 <= midpoint < 3 or 5 < midpoint <= 7:
        return 70
    return 45


def infer_margin_score(franchise: dict[str, Any]) -> int:
    text = value_of(franchise["financials"].get("profit_margin", ""))
    percentages = [int(n) for n in re.findall(r"([0-9]{1,2})%", text)]
    if not percentages:
        return 55
    high = max(percentages)
    if high >= 20:
        return 88
    if high >= 15:
        return 78
    if high >= 10:
        return 65
    return 45


def infer_growth_score(franchise: dict[str, Any]) -> int:
    text = " ".join(value_of(v) for v in franchise.get("growth", {}).values())
    if "positive" in text.lower() or "growth" in text.lower():
        return 76
    if "stable" in text.lower():
        return 68
    if "declining" in text.lower():
        return 42
    return 60


def infer_recurring_score(franchise: dict[str, Any]) -> int:
    descriptor = (
        f"{value_of(franchise.get('profile', {}).get('industry', ''))} "
        f"{value_of(franchise.get('profile', {}).get('cuisine_type', ''))}"
    ).lower()
    category = franchise_category_key(franchise)

    if category in {"fitness", "education", "child-services", "senior-care", "staffing", "cleaning"}:
        return 84
    if category in {"shipping-printing", "pet-services", "coffee", "breakfast"}:
        return 78
    if category in {"finance", "home-services", "automotive", "hotel"}:
        return 70
    if category in {"real-estate"}:
        return 62
    if any(term in descriptor for term in ["membership", "tuition", "home care", "staffing", "cleaning", "janitorial"]):
        return 84
    if any(term in descriptor for term in ["coffee", "breakfast", "fitness", "shipping", "printing", "pet", "maintenance"]):
        return 78
    if any(term in descriptor for term in ["mortgage", "real estate", "hotel", "handyman", "brokerage"]):
        return 68
    if any(term in descriptor for term in ["coffee", "breakfast"]):
        return 88
    if any(term in descriptor for term in ["pizza", "burger", "burgers"]):
        return 78
    return 65


def infer_support_score(franchise: dict[str, Any]) -> int:
    support = value_of(franchise.get("franchisee", {}).get("support_quality", "")).lower()
    training = value_of(franchise.get("franchisee", {}).get("training_quality", "")).lower()
    combined = support + " " + training
    if "very strong" in combined:
        return 88
    if "strong" in combined:
        return 78
    if "moderate" in combined:
        return 65
    return 55


def infer_satisfaction_score(franchise: dict[str, Any]) -> int:
    value = value_of(franchise.get("franchisee", {}).get("satisfaction_score", ""))
    if contains_estimate(value):
        return 55
    nums = [int(n) for n in re.findall(r"\b([0-9]{1,3})\b", value)]
    return clamp_score(nums[0]) if nums else 55


def infer_scalability_score(franchise: dict[str, Any]) -> int:
    scale_text = value_of(franchise.get("growth", {}).get("total_locations_canada", "")).lower()
    difficulty = value_of(franchise.get("franchisee", {}).get("operational_difficulty", "")).lower()
    score = 75 if "large" in scale_text or "national" in scale_text else 60
    if "high" in difficulty:
        score -= 8
    return clamp_score(score)


def infer_hours_score(franchise: dict[str, Any]) -> int:
    difficulty = value_of(franchise.get("franchisee", {}).get("operational_difficulty", "")).lower()
    if "high volume" in difficulty or "labour-intensive" in difficulty:
        return 55
    if "moderate" in difficulty:
        return 68
    return 62


def infer_exit_value_score(franchise: dict[str, Any]) -> int:
    saturation = value_of(franchise.get("competitive", {}).get("market_saturation", "")).lower()
    brand_signal = value_of(franchise.get("growth", {}).get("total_locations_canada", "")).lower()
    score = 75 if "large" in brand_signal or "national" in brand_signal else 62
    if "high" in saturation:
        score -= 6
    return clamp_score(score)


def infer_territory_score(franchise: dict[str, Any]) -> int:
    text = value_of(franchise.get("financials", {}).get("territory_protection", "Not Verified")).lower()
    if "exclusive" in text or "protected" in text:
        return 82
    if contains_estimate(text) or "not verified" in text:
        return 50
    if "no" in text:
        return 35
    return 60


def infer_training_score(franchise: dict[str, Any]) -> int:
    text = value_of(franchise.get("franchisee", {}).get("training_quality", "Not Verified")).lower()
    if "very strong" in text:
        return 88
    if "strong" in text or "documented" in text:
        return 78
    if "moderate" in text or "standardized" in text:
        return 65
    if "not verified" in text:
        return 50
    return 58


def infer_brand_maturity_score(franchise: dict[str, Any]) -> int:
    founded = value_of(franchise.get("profile", {}).get("founded", "Not Verified"))
    years = [int(n) for n in re.findall(r"\b(18[0-9]{2}|19[0-9]{2}|20[0-2][0-9])\b", founded)]
    if not years:
        return 45
    age = 2026 - min(years)
    if age >= 50:
        return 90
    if age >= 25:
        return 78
    if age >= 10:
        return 65
    return 45


def infer_canadian_fit_score(franchise: dict[str, Any]) -> int:
    profile = franchise.get("profile", {})
    headquarters = value_of(profile.get("headquarters", "")).lower()
    owned = value_of(profile.get("canadian_owned", "")).lower()
    score = 45
    if "canada" in headquarters or "ontario" in headquarters or "alberta" in headquarters or "british columbia" in headquarters or "quebec" in headquarters:
        score += 25
    if "yes" in owned:
        score += 20
    elif "hybrid" in owned:
        score += 12
    elif "no" in owned:
        score += 4
    return clamp_score(score)


def infer_franchise_availability_score(franchise: dict[str, Any]) -> int:
    text = value_of(franchise.get("profile", {}).get("franchise_available", "Not Verified")).lower()
    if "yes" in text:
        return 90
    if "no" in text:
        return 10
    return 45


def infer_financial_terms_completeness_score(franchise: dict[str, Any]) -> int:
    financials = franchise.get("financials", {})
    fields = ["initial_investment", "franchise_fee", "royalty", "marketing_fee"]
    score = 0
    for key in fields:
        value = value_of(financials.get(key, "Not Verified"))
        if value.lower() in {"not verified", "not verified / not available"}:
            score += 0
        elif contains_estimate(value):
            score += 13
        else:
            score += 22
    return clamp_score(score)


def factor_results(franchise: dict[str, Any]) -> list[FactorResult]:
    financials = franchise["financials"]
    profile = franchise["profile"]
    return [
        FactorResult("Investment", financials.get("initial_investment", "Estimated (industry benchmark)"), GOALS["Investment"], infer_investment_score(franchise), "Investment score rewards lower entry cost. Estimated or unverified investment data is capped until official franchise terms are loaded."),
        FactorResult("Investment Goal Fit", financials.get("initial_investment", "Estimated (industry benchmark)"), GOALS["Investment Goal Fit"], infer_investment_goal_fit_score(franchise), f"Goal fit compares the required investment with the maximum target of {TARGET_INVESTMENT_LABEL}. Costs above the target lower the screening score; unverified costs are capped."),
        FactorResult("Payback", financials.get("payback_period", "Estimated (industry benchmark)"), GOALS["Payback"], infer_payback_score(franchise), "Payback aligns best when the expected range lands near the 3-5 year target."),
        FactorResult("Profit Margin", financials.get("profit_margin", "Estimated (industry benchmark)"), GOALS["Profit Margin"], infer_margin_score(franchise), "Margin score compares available or benchmarked unit-level profitability against the target return profile for this screening model."),
        FactorResult("Scalability", franchise["growth"].get("total_locations_canada", "Not verified / not available"), GOALS["Scalability"], infer_scalability_score(franchise), "Scalability is inferred from system maturity, national footprint, and operational complexity."),
        FactorResult("Hours", franchise["franchisee"].get("operational_difficulty", "Estimated (industry benchmark)"), GOALS["Hours"], infer_hours_score(franchise), "Manager-run potential declines when the model is highly labour-intensive, late-hour, or execution-heavy."),
        FactorResult("Industry Strength", franchise["growth"].get("net_growth_rate", "Estimated (industry benchmark)"), GOALS["Industry Strength"], infer_growth_score(franchise), "Category strength scores better when available signals indicate stable or positive demand and unit economics."),
        FactorResult("Recurring Revenue", franchise["profile"].get("cuisine_type", "Food service"), GOALS["Recurring Revenue"], infer_recurring_score(franchise), "Recurring revenue rewards categories with repeat visits, memberships, service contracts, refill behaviour, or strong referral frequency."),
        FactorResult("Franchisor Support", franchise["franchisee"].get("support_quality", "Estimated (industry benchmark)"), GOALS["Franchisor Support"], infer_support_score(franchise), "Support score reflects training maturity, operating systems, and the stated strength of franchisor support signals."),
        FactorResult("Franchisee Satisfaction", franchise["franchisee"].get("satisfaction_score", "Estimated (industry benchmark)"), GOALS["Franchisee Satisfaction"], infer_satisfaction_score(franchise), "Unverified franchisee satisfaction is conservatively capped until survey, disclosure, or verified interview data exists."),
        FactorResult("Exit Value", franchise["competitive"].get("market_saturation", "Estimated (industry benchmark)"), GOALS["Exit Value"], infer_exit_value_score(franchise), "Exit value favors strong resale demand, mature brand recognition, and cash-flow transferability; saturation lowers the score."),
        FactorResult("Territory Protection", financials.get("territory_protection", "Not Verified"), GOALS["Territory Protection"], infer_territory_score(franchise), "Territory score rewards verified protected areas, exclusivity, or clear market rights."),
        FactorResult("Training Quality", franchise["franchisee"].get("training_quality", "Not Verified"), GOALS["Training Quality"], infer_training_score(franchise), "Training score rewards verified duration, format, field support, and franchisee-rated quality."),
        FactorResult("Brand Maturity", profile.get("founded", "Not Verified"), GOALS["Brand Maturity"], infer_brand_maturity_score(franchise), "Brand maturity uses the founded year to reward longer operating history and proven consumer awareness."),
        FactorResult("Canadian Market Fit", f"{value_of(profile.get('headquarters'))}; Canadian owned: {value_of(profile.get('canadian_owned'))}", GOALS["Canadian Market Fit"], infer_canadian_fit_score(franchise), "Canadian fit scores headquarters, ownership, and local operating relevance because Canada-specific execution matters."),
        FactorResult("Franchise Availability", profile.get("franchise_available", "Not Verified"), GOALS["Franchise Availability"], infer_franchise_availability_score(franchise), "Franchise availability matters because unavailable or unclear franchise programs are not actionable opportunities."),
        FactorResult("Financial Terms Completeness", "Initial investment, franchise fee, royalty, and marketing fee", GOALS["Financial Terms Completeness"], infer_financial_terms_completeness_score(franchise), "Completeness rewards having the four core franchise-cost fields identified, while estimated terms are capped until confirmed."),
    ]


def weighted_score(factors: list[FactorResult]) -> int:
    return clamp_score(sum(f.score * WEIGHTS[f.name] for f in factors))


def risk_level(score: int) -> str:
    if score >= 75:
        return "Low"
    if score >= 60:
        return "Medium"
    return "High"


def growth_outlook(franchise: dict[str, Any], score: int) -> str:
    growth_text = value_of(franchise["growth"].get("net_growth_rate", "")).lower()
    if "positive" in growth_text or score >= 75:
        return "Positive"
    if "declining" in growth_text or score < 55:
        return "Negative"
    return "Neutral"


def investment_tier(franchise: dict[str, Any]) -> str:
    investment = value_of(franchise["financials"].get("initial_investment", ""))
    numbers = investment_numbers(franchise)
    if not numbers:
        return "Estimated / requires verification"
    high = max(numbers)
    if high <= 400_000:
        return "Low"
    if high <= 900_000:
        return "Medium"
    return "High"


def money(amount: int) -> str:
    return f"${amount:,.0f} CAD"


def bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- Not verified / not available"


def province_ranking(franchise: dict[str, Any]) -> list[tuple[str, str]]:
    levels = {"Very high": 4, "High": 3, "Medium": 2, "Low": 1, "Low to medium": 1.5}
    province_data = franchise["growth"].get("locations_by_province", {})
    ranked = sorted(PROVINCES, key=lambda p: levels.get(value_of(province_data.get(p, "")).replace("Not Verified", ""), 0), reverse=True)
    return [(province, value_of(province_data.get(province, "Not Verified"))) for province in ranked]


def ai_scores(franchise: dict[str, Any], factors: list[FactorResult], final_score: int) -> dict[str, int]:
    factor_map = {f.name: f.score for f in factors}
    return {
        "Investment Score": factor_map["Investment"],
        "Investment Goal Fit": factor_map["Investment Goal Fit"],
        "Growth Score": factor_map["Industry Strength"],
        "Risk Score": clamp_score(100 - (100 - final_score) * 0.8),
        "Brand Strength": clamp_score((factor_map["Recurring Revenue"] + factor_map["Exit Value"] + factor_map["Brand Maturity"]) / 3 + 8),
        "Canadian Fit": factor_map["Canadian Market Fit"],
        "Franchise Availability": factor_map["Franchise Availability"],
        "Financial Terms Completeness": factor_map["Financial Terms Completeness"],
        "Franchisee Satisfaction": factor_map["Franchisee Satisfaction"],
        "Customer Satisfaction": 60 if "requires Google" in value_of(franchise["customer"].get("google_rating", "")) else 72,
        "Expansion Score": factor_map["Scalability"],
        "Profit Potential": factor_map["Profit Margin"],
        "Support Quality": factor_map["Franchisor Support"],
        "Resale Value": factor_map["Exit Value"],
    }


def tags(franchise: dict[str, Any], score: int, investor: dict[str, Any]) -> list[str]:
    output = ["Screening Only"]
    owned = value_of(franchise["profile"].get("canadian_owned", "")).lower()
    saturation = value_of(franchise["competitive"].get("market_saturation", "")).lower()
    growth_signal = value_of(franchise["growth"].get("net_growth_rate", "")).lower()
    investment = franchise.get("financials", {}).get("initial_investment")
    goal_fit_score = infer_investment_goal_fit_score(franchise)

    if investor["score"] == "N/A":
        output.append("Investor Gates Incomplete")
    if contains_estimate(value_of(investment)) or evidence_of(investment)["source_url"] == "Not Verified":
        output.append("Estimated Economics")
    elif goal_fit_score >= 80:
        output.append("Within Budget Target")
    elif goal_fit_score <= 45:
        output.append("Above Budget Target")

    if "yes" in owned:
        output.append("Canadian Owned")
    elif "hybrid" in owned:
        output.append("Canadian Operating Presence")
    elif "no" in owned:
        output.append("Cross-Border Caution")

    if "high" in saturation:
        output.append("High Saturation")
    elif "low" in saturation:
        output.append("Whitespace Candidate")

    if "positive" in growth_signal:
        output.append("Positive Growth Signal")
    if score >= 75:
        output.append("Higher Screening Score")
    elif score < 60:
        output.append("Higher Screening Risk")
    if infer_scalability_score(franchise) >= 75:
        output.append("Multi-Unit Potential")
    return list(dict.fromkeys(output))


def score_explanation(name: str, value: int) -> str:
    if value >= 80:
        tier = "strong"
    elif value >= 65:
        tier = "moderate"
    else:
        tier = "conservative"
    return f"{value}/100 is a {tier} score based on available signals. Exact source-backed data would raise confidence and may change the score."


def numeric_confidence(field: Any) -> int:
    evidence = evidence_of(field)
    try:
        return int(float(evidence["confidence"]))
    except (TypeError, ValueError):
        return 0


def disallowed_source_for_investor_scoring(evidence: dict[str, str]) -> bool:
    source = evidence["source_url"].lower()
    value = evidence["value"].lower()
    if "usd" in value or "u.s." in value or "us fdd" in value:
        return True
    if "wikipedia.org" in source:
        return True
    if "/en-us/" in source or "subwayfranchise.com/en-us" in source:
        return True
    if any(domain in source for domain in ["businessinsider.com", "investopedia.com", "nypost.com"]):
        return True
    return False


def has_scoring_evidence(field: Any, min_confidence: int = 70) -> bool:
    evidence = evidence_of(field)
    if evidence["source_url"] == "Not Verified":
        return False
    if contains_estimate(evidence["value"]):
        return False
    if disallowed_source_for_investor_scoring(evidence):
        return False
    return numeric_confidence(field) >= min_confidence


def evidence_gate_results(franchise: dict[str, Any]) -> list[dict[str, str]]:
    evidence = franchise.get("investor_evidence", {})
    results = []
    for key, label in INVESTOR_GATES:
        gate = evidence.get(key, {})
        passed = bool(gate.get("verified")) if isinstance(gate, dict) else False
        results.append(
            {
                "key": key,
                "label": label,
                "status": "PASS" if passed else "FAIL",
                "detail": value_of(gate.get("detail") if isinstance(gate, dict) else gate, "Not Verified"),
            }
        )
    return results


def minimum_investor_gates_pass(gates: list[dict[str, str]]) -> bool:
    required = {
        "franchisor_confirmation",
        "canadian_disclosure_package",
        "canadian_signing_entity",
        "cad_investment_fees",
        "canadian_unit_economics",
        "closure_transfer_renewal",
        "franchisee_interviews",
        "local_market_review",
    }
    passed = {gate["key"] for gate in gates if gate["status"] == "PASS"}
    return required.issubset(passed)


def franchisor_confirmation_text(franchise: dict[str, Any]) -> str:
    gate = franchise.get("investor_evidence", {}).get("franchisor_confirmation", {})
    if isinstance(gate, dict):
        detail = value_of(gate.get("detail"), "")
        if gate.get("verified"):
            return detail or "Confirmed directly by the franchisor."
        if detail and detail != "Not Verified":
            return detail
    return "None confirmed. All figures must be confirmed directly by the franchisor before investment use."


def critical_evidence_fields(franchise: dict[str, Any]) -> dict[str, Any]:
    financials = franchise.get("financials", {})
    growth = franchise.get("growth", {})
    franchisee = franchise.get("franchisee", {})
    return {
        "Initial investment": financials.get("initial_investment"),
        "Franchise fee": financials.get("franchise_fee"),
        "Royalty": financials.get("royalty"),
        "Marketing fee": financials.get("marketing_fee"),
        "Average unit revenue": financials.get("average_unit_revenue"),
        "Profit margin / EBITDA": financials.get("profit_margin"),
        "Closure trend": growth.get("closures_last_12_months", growth.get("closures_this_year")),
        "Transfer / renewal terms": financials.get("renewal_terms"),
        "Franchisee satisfaction": franchisee.get("satisfaction_score"),
    }


def investor_status(franchise: dict[str, Any], generic_score: int) -> dict[str, Any]:
    gates = evidence_gate_results(franchise)
    missing_fields = [
        label for label, field in critical_evidence_fields(franchise).items()
        if not has_scoring_evidence(field)
    ]
    red_flags = franchise.get("red_flags", [])
    hard_blockers = [gate["label"] for gate in gates if gate["status"] == "FAIL"]
    passes_minimum_gates = minimum_investor_gates_pass(gates)

    if not passes_minimum_gates:
        label = "Not investment-ready / requires franchisor confirmation"
        score = "N/A"
        reason = f"Minimum investor gates failed: {'; '.join(hard_blockers)}."
    else:
        deductions = len(missing_fields) * 4 + len(red_flags) * 3
        score_value = clamp_score(generic_score - deductions)
        score = f"{score_value}/100"
        if score_value >= 85 and not red_flags:
            label = "Investment-Ready Candidate"
        elif score_value >= 75:
            label = "Proceed to Legal/Accounting Review"
        elif score_value >= 65:
            label = "Proceed to Franchisee Interviews"
        elif score_value >= 50:
            label = "Watchlist"
        else:
            label = "Reject"
        reason = (
            f"All minimum investor gates passed. Investor-grade score deducts for "
            f"{len(missing_fields)} unsupported critical fields and {len(red_flags)} red flags."
        )

    return {
        "label": label,
        "score": score,
        "reason": reason,
        "gates": gates,
        "passes_minimum_gates": passes_minimum_gates,
        "missing_fields": missing_fields,
        "hard_blockers": hard_blockers,
        "red_flags": red_flags,
    }


def capital_fit(franchise: dict[str, Any]) -> list[str]:
    financials = franchise.get("financials", {})
    liquid = value_of(financials.get("minimum_liquid_capital"))
    investment = value_of(financials.get("initial_investment"))
    tier = investment_tier(franchise)
    if "Estimated" in tier or "Not Verified" in investment:
        affordability = "Affordability tier cannot be trusted until CAD investment and liquidity requirements are verified."
    elif tier == "Low":
        affordability = "Lower capital barrier relative to larger franchise systems, subject to lease and working-capital buffer."
    elif tier == "Medium":
        affordability = "Moderate capital barrier; young operators likely need lender support and a conservative cash buffer."
    else:
        affordability = "High capital barrier; generally better suited to well-capitalized or multi-unit operators."
    return [
        f"Minimum liquid capital: {liquid}",
        f"Investment tier: {tier}",
        "Working-capital buffer: Not Verified; request franchisor guidance and lender stress test.",
        affordability,
    ]


def investment_goal_fit(franchise: dict[str, Any]) -> list[str]:
    financials = franchise.get("financials", {})
    investment = value_of(financials.get("initial_investment"))
    numbers = investment_numbers(franchise)
    score = infer_investment_goal_fit_score(franchise)
    lines = [
        f"Target investment goal: {TARGET_INVESTMENT_LABEL}",
        f"Reported investment range: {investment}",
        f"Goal Fit Score: {score}/100",
    ]
    if not numbers:
        lines.append("Fit decision: Cannot verify fit. The score is capped because the investment amount is estimated or missing.")
        lines.append("Score impact: Lowers the screening score until exact CAD investment and working-capital requirements are confirmed.")
        return lines

    low = min(numbers)
    high = max(numbers)
    if high <= TARGET_INVESTMENT_CAD:
        decision = "Fits budget. The full reported range is under the maximum target, but value still depends on verified sales, EBITDA, and resale data."
    elif low <= TARGET_INVESTMENT_CAD <= high:
        gap = high - TARGET_INVESTMENT_CAD
        decision = f"Partly above target. The low end may fit, but the high end is above target by up to {money(gap)}."
    else:
        gap = high - TARGET_INVESTMENT_CAD
        decision = f"Does not fit budget. The reported range is above target by at least {money(low - TARGET_INVESTMENT_CAD)} and up to {money(gap)}."
    lines.append(f"Range parsed for scoring: {money(low)} to {money(high)}")
    lines.append(f"Fit decision: {decision}")
    lines.append("Value test: Prefer franchises under the target unless verified EBITDA, payback, resale value, and financing terms justify paying more.")
    return lines


def operator_fit(franchise: dict[str, Any]) -> list[str]:
    difficulty = value_of(franchise.get("franchisee", {}).get("operational_difficulty"))
    return [
        f"Operational difficulty: {difficulty}",
        "Owner-operator requirement: Not Verified; confirm with disclosure package and franchise agreement.",
        "Semi-absentee possibility: Not Verified; do not assume manager-run operation until franchisee interviews confirm it.",
        "Multi-unit readiness: Screen only after the first-unit economics, staffing model, and territory rights are verified.",
        "Industry experience requirement: Not Verified; confirm franchisor approval criteria.",
    ]


def financial_model(franchise: dict[str, Any]) -> list[str]:
    financials = franchise.get("financials", {})
    operating_cost_stack = "rent, royalty, marketing, payroll, direct operating costs, debt service, and manager salary"
    sensitivity = "rent +10%, wage +10%, direct-cost ratio +300 bps, sales -10%, sales -20%"
    if is_food_franchise(franchise):
        operating_cost_stack = "rent, royalty, marketing, labour, food cost, debt service, and manager salary"
        sensitivity = "rent +10%, wage +10%, food cost +300 bps, sales -10%, sales -20%, delivery commission mix shift"
    return [
        "Conservative case: Not model-ready; uses no investment scoring until Canadian sales, occupancy, payroll, and direct-cost data are verified.",
        f"Base case: Generic screening assumes {value_of(financials.get('profit_margin'))}; this is excluded from investor-grade scoring unless sourced.",
        "Upside case: Requires verified AUV, site-specific occupancy cost, local wage assumptions, and mature-unit margin support.",
        f"Break-even sales: Not Verified; calculate after {operating_cost_stack} are known.",
        "EBITDA estimate: Not Verified for investor scoring.",
        f"Payback: {value_of(financials.get('realistic_payback_range', financials.get('payback_period')))}; excluded unless supported by Canadian disclosure or franchisee P&L.",
        f"Sensitivity tests required: {sensitivity}.",
    ]


def franchisee_diligence(franchise: dict[str, Any]) -> list[str]:
    interview_log = franchise.get("franchisee_interview_log", [])
    if interview_log:
        return [str(item) for item in interview_log]
    interview_questions = "actual launch cost, first-year sales, mature sales, payroll ratio, gross margin, occupancy cost, franchisor support, renewal pressure, and transfer experience"
    if is_food_franchise(franchise):
        interview_questions = "actual buildout cost, first-year sales, mature sales, labour ratio, food cost, rent occupancy, franchisor support, renewal pressure, and transfer experience"
    return [
        "Interview count: 0 verified interviews loaded.",
        "Required minimum: 3 current franchisees, 2 former franchisees, and 1 transfer/resale operator where available.",
        f"Questions: {interview_questions}.",
        "Contradiction flags: Not available until interviews are logged.",
    ]


def local_market_fit(franchise: dict[str, Any]) -> list[str]:
    return [
        "Target city score: N/A until a specific city or trade area is provided.",
        "Required checks: demographics, traffic generators, competition density, service radius or territory overlap, occupancy pressure, reviews, parking/access, and cannibalization.",
        f"Current saturation signal: {value_of(franchise.get('competitive', {}).get('market_saturation'))}",
    ]


def document_request_checklist() -> list[str]:
    return [
        "Canadian disclosure document and all exhibits",
        "Exact Canadian franchisor/signing entity and affiliates",
        "Franchise agreement, lease rider, personal guarantee, renewal and transfer terms",
        "Current CAD investment range and required working capital",
        "Royalty, ad fund, technology, training, renewal, transfer, supplier, audit, and local marketing fees",
        "Canadian AUV, store-level P&L support, closure/transfer/resale history, and litigation history",
        "Territory map, non-traditional venue rules, platform or channel rules, and encroachment protections",
    ]


def source_ledger(franchise: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    investor_scoring_paths = {
        "financials.initial_investment",
        "financials.franchise_fee",
        "financials.royalty",
        "financials.marketing_fee",
        "financials.technology_fee",
        "financials.training_fee",
        "financials.renewal_fee",
        "financials.transfer_fee",
        "financials.other_mandatory_fees",
        "financials.average_unit_revenue",
        "financials.item_19_avg_revenue",
        "financials.item_19_gross_profit",
        "financials.item_19_net_profit",
        "financials.realistic_payback_range",
        "financials.profit_margin",
        "financials.minimum_net_worth",
        "financials.minimum_liquid_capital",
        "financials.franchise_term",
        "financials.renewal_terms",
        "financials.territory_protection",
        "growth.openings_last_12_months",
        "growth.closures_last_12_months",
        "growth.three_year_unit_trend",
        "franchisee.satisfaction_score",
        "franchisee.average_tenure",
        "franchisee.turnover_percent",
        "franchisee.litigation_history_5yr",
    }

    def collect(path: str, value: Any) -> None:
        if isinstance(value, dict) and "value" in value:
            evidence = evidence_of(value)
            allowed = "Yes" if path in investor_scoring_paths and has_scoring_evidence(value) else "No"
            rows.append(
                {
                    "claim": f"{path}: {evidence['value']}",
                    "source": evidence["source_url"],
                    "source_date": evidence["source_date"],
                    "retrieved_date": EVIDENCE_RETRIEVED_DATE,
                    "reliability": evidence["reliability"],
                    "allowed": allowed,
                }
            )
        elif isinstance(value, dict):
            for key, child in value.items():
                collect(f"{path}.{key}" if path else str(key), child)
        elif isinstance(value, list):
            for index, child in enumerate(value, start=1):
                collect(f"{path}[{index}]", child)
        elif path and path.split(".")[-1] not in {"locations_by_province"}:
            rows.append(
                {
                    "claim": f"{path}: {value_of(value)}",
                    "source": "Not Verified",
                    "source_date": "Not Verified",
                    "retrieved_date": EVIDENCE_RETRIEVED_DATE,
                    "reliability": "Not Verified",
                    "allowed": "No",
                }
            )

    for section in ["profile", "financials", "growth", "customer", "franchisee", "competitive"]:
        collect(section, franchise.get(section, {}))
    return rows


def source_ledger_lines(franchise: dict[str, Any]) -> list[str]:
    rows = source_ledger(franchise)
    if not rows:
        return ["No source ledger entries loaded."]
    return [
        f"- Claim: {row['claim']} | Source: {row['source']} | Source date: {row['source_date']} | Retrieved: {row['retrieved_date']} | Reliability: {row['reliability']} | Allowed in investor scoring: {row['allowed']}"
        for row in rows
    ]


def confirmed_source_ledger_lines(franchise: dict[str, Any]) -> list[str]:
    rows = [row for row in source_ledger(franchise) if row["source"] != "Not Verified"]
    if not rows:
        return ["No source-backed evidence loaded yet."]
    return [
        f"- {row['claim']} | Source: {row['source']} | Date: {row['source_date']} | Reliability: {row['reliability']} | Investor scoring use: {row['allowed']}"
        for row in rows
    ]


def compact_evidence_gate_lines(status: dict[str, Any]) -> list[str]:
    lines = []
    for gate in status["gates"]:
        if gate["detail"] != "Not Verified":
            lines.append(f"{gate['label']}: {gate['status']} ({gate['detail']})")
        else:
            lines.append(f"{gate['label']}: {gate['status']}")
    return lines


def do_not_use_for_investment_scoring(franchise: dict[str, Any]) -> list[str]:
    blocked = [
        "U.S. FDD data unless independently reconciled to the Canadian franchise offer",
        "Generic category estimates and industry benchmarks",
        "Old or unsourced location counts",
        "Wikipedia/background facts",
        "Unsourced sentiment, review anecdotes, forum posts, and social media claims",
    ]
    ledger_blocked = [
        row["claim"] for row in source_ledger(franchise)
        if row["allowed"] == "No" and len(row["claim"]) < 180
    ][:10]
    return blocked + ledger_blocked


def next_research_queue(status: dict[str, Any]) -> list[str]:
    queue = [f"Resolve gate: {blocker}" for blocker in status["hard_blockers"]]
    queue.extend(f"Verify field: {field}" for field in status["missing_fields"])
    if not queue:
        queue.append("Run legal/accounting review and lender stress test before signing.")
    return queue


def evidence_sources(franchise: dict[str, Any]) -> list[str]:
    sources: dict[str, tuple[str, str]] = {}

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            url = value.get("source_url")
            if url and url != "Not Verified":
                sources[url] = (str(value.get("source_date", "Not Verified")), str(value.get("source_reliability", "Not Verified")))
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(franchise)
    return [f"{source_name(url)} | {date} | Reliability {reliability} | {url}" for url, (date, reliability) in sources.items()]


def total_source_count(franchise: dict[str, Any]) -> int:
    return len(evidence_sources(franchise))


def render_report(franchise: dict[str, Any]) -> str:
    factors = factor_results(franchise)
    generic_score = weighted_score(factors)
    investor = investor_status(franchise, generic_score)
    franchisor_confirmation = franchisor_confirmation_text(franchise)
    ai_score_map = ai_scores(franchise, factors, generic_score)
    goal_fit_score = infer_investment_goal_fit_score(franchise)
    profile = franchise["profile"]
    financials = franchise["financials"]
    growth = franchise["growth"]
    customer = franchise["customer"]
    franchisee = franchise["franchisee"]
    sentiment = franchise["sentiment"]
    competitive = franchise["competitive"]
    ranked_provinces = province_ranking(franchise)

    factor_block = [
        f"{factor.name}: {factor.score}/100\n"
        f"  Value: {value_of(factor.value)}\n"
        f"  Goal: {factor.goal}\n"
        f"  Note: {factor.explanation}"
        for factor in factors
    ]

    ai_block = [
        f"- {label}: {value}/100 - {score_explanation(label, value)}"
        for label, value in ai_score_map.items()
    ]

    profile_rows = [
        evidence_row("Founded", profile.get("founded")),
        evidence_row("HQ", profile.get("headquarters")),
        evidence_row("Canadian Owned", profile.get("canadian_owned")),
        evidence_row("Industry", profile.get("industry")),
        evidence_row("Category / Service", profile.get("cuisine_type")),
        evidence_row("Franchising in Canada", profile.get("franchise_available")),
        evidence_row("Franchising Internationally", profile.get("franchising_internationally")),
        evidence_row("Total Canadian Units", growth.get("total_locations_canada")),
        evidence_row("Total International Units", growth.get("total_locations_international")),
        evidence_row("Systemwide Revenue", financials.get("systemwide_revenue")),
        evidence_row("Average Unit Revenue", financials.get("average_unit_revenue")),
        evidence_row("Openings 12mo", growth.get("openings_last_12_months", growth.get("new_locations_this_year"))),
        evidence_row("Closures 12mo", growth.get("closures_last_12_months", growth.get("closures_this_year"))),
        evidence_row("Net Growth %", growth.get("net_growth_rate")),
        evidence_row("3-Year Unit Trend", growth.get("three_year_unit_trend")),
    ]

    money_rows = [
        evidence_row("Total Investment Range", financials.get("initial_investment"), True),
        evidence_row("Franchise Fee", financials.get("franchise_fee"), True),
        evidence_row("Royalty %", financials.get("royalty"), True),
        evidence_row("Marketing Fund %", financials.get("marketing_fee"), True),
        evidence_row("Technology Fee", financials.get("technology_fee"), True),
        evidence_row("Training Fee", financials.get("training_fee"), True),
        evidence_row("Renewal Fee", financials.get("renewal_fee"), True),
        evidence_row("Transfer Fee", financials.get("transfer_fee"), True),
        evidence_row("Other Mandatory Fees", financials.get("other_mandatory_fees"), True),
        evidence_row("Average Unit Revenue", financials.get("average_unit_revenue"), True),
        evidence_row("Item 19 Avg Revenue", financials.get("item_19_avg_revenue"), True),
        evidence_row("Item 19 Gross Profit", financials.get("item_19_gross_profit"), True),
        evidence_row("Item 19 Net Profit", financials.get("item_19_net_profit"), True),
        evidence_row("Payback", financials.get("realistic_payback_range", financials.get("payback_period")), True),
        evidence_row("Profit Margin", financials.get("profit_margin"), True),
        evidence_row("Min Net Worth", financials.get("minimum_net_worth"), True),
        evidence_row("Min Liquid Capital", financials.get("minimum_liquid_capital"), True),
        evidence_row("Term Length", financials.get("franchise_term"), True),
        evidence_row("Territory Protection", financials.get("territory_protection"), True),
        evidence_row("Franchisor Financing", financials.get("franchisor_financing"), True),
    ]

    province_block = [
        f"{index}. {province}: {level}"
        for index, (province, level) in enumerate(ranked_provinces, start=1)
    ]

    if is_food_franchise(franchise):
        strengths = [
            "Strong repeat-purchase potential from food-service demand patterns",
            "Recognizable brand signals reduce customer-discovery risk",
            "Standardized franchisor systems support multi-location execution when operators are capable",
        ]
        weaknesses = [
            "Several key figures still need direct franchisor confirmation",
            "Labour, rent, food cost, and local competition can materially change store-level returns",
            "Mature markets may limit whitespace and increase cannibalization risk",
        ]
        default_opportunity = "Verify official economics and identify underserved provinces before expansion decisions"
        default_threat = "Unverified economics, saturation, labour costs, rent, and local competition can materially reduce returns"
    else:
        strengths = [
            "Business and service models can diversify the portfolio beyond food-service demand cycles",
            "Recognizable brand signals reduce customer-acquisition risk",
            "Standardized franchisor systems can support local execution when operators are capable",
        ]
        weaknesses = [
            "Several key figures still need direct franchisor confirmation",
            "Staffing, occupancy cost, service delivery, and local competition can materially change returns",
            "Local licensing, territory quality, or referral flow can sharply affect performance",
        ]
        default_opportunity = "Verify official economics and identify underserved territories or business corridors before expansion decisions"
        default_threat = "Unverified economics, sales execution, hiring pressure, occupancy cost, and local competition can materially reduce returns"

    confidence = "Medium" if generic_score >= 65 else "Low"
    if any("Not verified" in value_of(v).lower() or "Estimated" in value_of(v) for section in [financials, growth, customer] for v in (section.values() if isinstance(section, dict) else [])):
        confidence = "Medium-Low"

    rejected_count = sum(
        1
        for section in [profile, financials, growth, customer, franchisee, competitive]
        for value in section.values()
        if evidence_of(value)["source_url"] == "Not Verified"
    )

    missing_evidence_lines = [
        f"{field}: not reliable for investment scoring until confirmed"
        for field in investor["missing_fields"]
    ] or ["No unsupported critical scoring fields remain."]

    return f"""{franchise['name'].upper()}

1. SUMMARY
Generic Screening Score: {generic_score}/100
Investor-Grade Score: {investor['score']}
Investor-Grade Status: {investor['label']}
Franchisor Confirmation: {franchisor_confirmation}
Risk Level: {risk_level(generic_score)}
Growth Outlook: {growth_outlook(franchise, generic_score)}
Investment Tier: {investment_tier(franchise)}
Investment Goal Fit: {goal_fit_score}/100 against {TARGET_INVESTMENT_LABEL}
Confidence Level: {confidence}

Important note: This is a clean screening report, not a final investment recommendation. Source-backed information has been added where available, but no record is marked franchisor-confirmed.

2. COMPANY PROFILE
{chr(10).join(profile_rows)}

3. MONEY AND UNIT ECONOMICS
{chr(10).join(money_rows)}

Financial Model Status
{bullet_lines(financial_model(franchise))}

Capital Fit for Young Entrepreneurs
{bullet_lines(capital_fit(franchise))}

Investment Goal Fit
{bullet_lines(investment_goal_fit(franchise))}

4. LOCATIONS AND MARKET
Locations by Province:
{bullet_lines([f"{p}: {value_of(growth.get('locations_by_province', {}).get(p, 'Not Verified'))}" for p in PROVINCES])}

Province Ranking:
{chr(10).join(province_block)}

Main competitors: {', '.join(competitive.get('main_competitors', ['Not Verified']))}
Market saturation: {value_of(competitive.get('market_saturation', 'Not Verified'))}
Differentiation: {value_of(competitive.get('differentiation', 'Not Verified'))}
Threat level: {value_of(competitive.get('threat_level', 'Not Verified'))}

Local Market Fit
{bullet_lines(local_market_fit(franchise))}

5. CUSTOMER AND FRANCHISEE SIGNALS
Google Rating: {value_of(customer.get('google_rating', 'Not Verified'))}
Review Volume: {value_of(customer.get('review_volume', 'Not Verified'))}
Customer Sentiment Trend: {value_of(customer.get('sentiment_trend', 'Not Verified'))}
Insight Summary: {value_of(customer.get('insight_summary', 'Not Verified'))}

Top Praises:
{bullet_lines(customer.get('top_praises', sentiment.get('positive_themes', [])))}

Top Complaints:
{bullet_lines(customer.get('top_complaints', sentiment.get('negative_themes', [])))}

Franchisee Satisfaction: {value_of(franchisee.get('satisfaction_score', 'Not Verified'))}
Training Quality: {value_of(franchisee.get('training_quality', 'Not Verified'))}
Support Quality: {value_of(franchisee.get('support_quality', 'Not Verified'))}
Operational Difficulty: {value_of(franchisee.get('operational_difficulty', 'Not Verified'))}
Litigation History 5yr: {value_of(franchisee.get('litigation_history_5yr', 'Not Verified'))}

6. SCREENING SCORE
Generic Screening Score: {generic_score}/100
This score is for comparison only. It is not franchisor-confirmed and is not an investment recommendation.
Important scoring inputs include founded year, headquarters, Canadian ownership, industry, category/service line, Canadian franchise availability, initial investment, franchise fee, royalty, and marketing fee.

Factor Breakdown
{chr(10).join(chr(10) + block for block in factor_block)}

AI Score Signals
{chr(10).join(ai_block)}

Tags
{bullet_lines(tags(franchise, generic_score, investor))}

7. RISKS AND FIT
Strengths:
{bullet_lines(strengths)}

Weaknesses:
{bullet_lines(weaknesses)}

Opportunities:
{bullet_lines(franchise.get('opportunities', [default_opportunity]))}

Threats:
{bullet_lines(franchise.get('threats', [default_threat]))}

Red Flags:
{bullet_lines(franchise.get('red_flags', ['No field-level source evidence loaded for several critical economics fields']))}

Yellow Flags:
{bullet_lines(franchise.get('yellow_flags', ['Estimated data should be replaced with official or legally disclosed data']))}

Green Flags:
{bullet_lines(franchise.get('green_flags', strengths[:2]))}

8. EVIDENCE STATUS
Franchisor Confirmation: {franchisor_confirmation}
Investor-Grade Score: {investor['score']}
Reason: {investor['reason']}

Evidence Gates
{bullet_lines(compact_evidence_gate_lines(investor))}

Missing Evidence Impact
{bullet_lines(missing_evidence_lines)}

Document Request Checklist
{bullet_lines(document_request_checklist())}

9. SOURCES
Total Source Count: {total_source_count(franchise)}

Source Reliability Guide
{bullet_lines([f"{source}: {score}" for source, score in RELIABILITY_GUIDE.items()])}

Source-Backed Evidence Loaded
{chr(10).join(confirmed_source_ledger_lines(franchise))}

Evidence Source URLs:
{bullet_lines(evidence_sources(franchise))}

Research Notes:
{bullet_lines(franchise.get('source_notes', []))}

Critical Gaps:
{bullet_lines(franchise.get('critical_gaps', ['Field-level source URL, date, reliability, and quote for most seed data', 'Official unit economics', 'Verified franchisee satisfaction and turnover', 'Current review, field-call, and job-posting data']))}

Do Not Use For Investment Scoring:
{bullet_lines(do_not_use_for_investment_scoring(franchise))}

Fields Rejected Due To Evidence Rules: {rejected_count}
"""


def safe_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "", name).strip() + ".txt"


def estimated_financials(category: str) -> dict[str, str]:
    category_ranges = {
        "burger": ("Estimated (industry benchmark): high six figures to multi-million CAD buildout", "Estimated (industry benchmark): 5-8 years", "Estimated (industry benchmark): 8-16% store-level EBITDA range for mature burger QSR units"),
        "chicken": ("Estimated (industry benchmark): high six figures to multi-million CAD buildout", "Estimated (industry benchmark): 4-7 years", "Estimated (industry benchmark): 8-16% store-level EBITDA range for mature chicken QSR units"),
        "pizza": ("Estimated (industry benchmark): mid six figures to low seven figures CAD buildout", "Estimated (industry benchmark): 3-6 years", "Estimated (industry benchmark): 8-15% store-level EBITDA range for mature pizza QSR units"),
        "sandwich": ("Estimated (industry benchmark): lower to mid six figures CAD buildout", "Estimated (industry benchmark): 3-6 years", "Estimated (industry benchmark): 7-14% store-level EBITDA range for mature sandwich QSR units"),
        "mexican": ("Estimated (industry benchmark): mid six figures CAD buildout", "Estimated (industry benchmark): 3-6 years", "Estimated (industry benchmark): 8-15% store-level EBITDA range for mature Mexican QSR units"),
        "beverage": ("Estimated (industry benchmark): lower to mid six figures CAD buildout", "Estimated (industry benchmark): 3-6 years", "Estimated (industry benchmark): 8-16% store-level EBITDA range for mature beverage QSR units"),
        "dessert-qsr": ("Estimated (industry benchmark): mid six figures to low seven figures CAD buildout", "Estimated (industry benchmark): 4-7 years", "Estimated (industry benchmark): 8-16% store-level EBITDA range for mature treat/QSR units"),
        "coffee": ("Estimated (industry benchmark): mid six figures to low seven figures CAD cafe buildout", "Estimated (industry benchmark): 4-7 years", "Estimated (industry benchmark): 8-16% store-level EBITDA range for mature cafe units"),
        "bakery": ("Estimated (industry benchmark): mid six figures CAD bakery/cafe buildout", "Estimated (industry benchmark): 3-6 years", "Estimated (industry benchmark): 8-15% store-level EBITDA range for mature bakery/cafe units"),
        "health": ("Estimated (industry benchmark): lower to mid six figures CAD fast-casual buildout", "Estimated (industry benchmark): 3-6 years", "Estimated (industry benchmark): 7-14% store-level EBITDA range for mature health-focused QSR units"),
        "asian": ("Estimated (industry benchmark): mid six figures CAD QSR/fast-casual buildout", "Estimated (industry benchmark): 3-6 years", "Estimated (industry benchmark): 8-15% store-level EBITDA range for mature Asian QSR units"),
        "mediterranean": ("Estimated (industry benchmark): mid six figures CAD QSR/fast-casual buildout", "Estimated (industry benchmark): 3-6 years", "Estimated (industry benchmark): 8-15% store-level EBITDA range for mature Mediterranean QSR units"),
        "breakfast": ("Estimated (industry benchmark): mid six figures to low seven figures CAD restaurant buildout", "Estimated (industry benchmark): 4-7 years", "Estimated (industry benchmark): 8-15% store-level EBITDA range for mature breakfast restaurant units"),
        "snack": ("Estimated (industry benchmark): lower to mid six figures CAD kiosk/QSR buildout", "Estimated (industry benchmark): 3-6 years", "Estimated (industry benchmark): 8-16% store-level EBITDA range for mature snack/kiosk units"),
        "casual": ("Estimated (industry benchmark): high six figures to multi-million CAD casual dining buildout", "Estimated (industry benchmark): 5-8 years", "Estimated (industry benchmark): 6-14% store-level EBITDA range for mature casual dining units"),
        "seafood": ("Estimated (industry benchmark): high six figures to low seven figures CAD restaurant buildout", "Estimated (industry benchmark): 4-7 years", "Estimated (industry benchmark): 6-14% store-level EBITDA range for mature seafood restaurant units"),
        "indian": ("Estimated (industry benchmark): mid six figures CAD QSR/fast-casual buildout", "Estimated (industry benchmark): 3-6 years", "Estimated (industry benchmark): 8-15% store-level EBITDA range for mature Indian QSR units"),
        "qsr": ("Estimated (industry benchmark): mid six figures CAD food-service buildout", "Estimated (industry benchmark): 3-6 years", "Estimated (industry benchmark): 7-15% store-level EBITDA range for mature food-service franchise units"),
        "real-estate": ("Estimated (industry benchmark): low five figures to low six figures CAD brokerage-office launch", "Estimated (industry benchmark): 2-5 years", "Estimated (industry benchmark): 15-30% office-level EBITDA range for mature brokerage operations"),
        "hotel": ("Estimated (industry benchmark): multi-million CAD hotel acquisition, conversion, or development capital", "Estimated (industry benchmark): 6-10 years", "Estimated (industry benchmark): 12-28% property-level EBITDA range depending on market and flag"),
        "fitness": ("Estimated (industry benchmark): mid six figures to low seven figures CAD studio buildout", "Estimated (industry benchmark): 3-6 years", "Estimated (industry benchmark): 15-25% studio-level EBITDA range for mature membership models"),
        "education": ("Estimated (industry benchmark): low to mid six figures CAD education-centre launch", "Estimated (industry benchmark): 2-5 years", "Estimated (industry benchmark): 15-30% centre-level EBITDA range for mature tutoring models"),
        "cleaning": ("Estimated (industry benchmark): low six figures CAD service-business launch", "Estimated (industry benchmark): 2-4 years", "Estimated (industry benchmark): 12-25% operating margin range for mature cleaning franchises"),
        "automotive": ("Estimated (industry benchmark): high six figures to multi-million CAD service-centre buildout", "Estimated (industry benchmark): 4-8 years", "Estimated (industry benchmark): 10-20% service-centre EBITDA range for mature automotive operations"),
        "home-services": ("Estimated (industry benchmark): low to mid six figures CAD service-territory launch", "Estimated (industry benchmark): 2-5 years", "Estimated (industry benchmark): 12-25% local operating margin range for mature home-service franchises"),
        "child-services": ("Estimated (industry benchmark): high six figures to multi-million CAD childcare or youth-facility buildout", "Estimated (industry benchmark): 4-8 years", "Estimated (industry benchmark): 12-24% centre-level EBITDA range for mature child-service operations"),
        "senior-care": ("Estimated (industry benchmark): low to mid six figures CAD service-office launch", "Estimated (industry benchmark): 2-5 years", "Estimated (industry benchmark): 10-20% local operating margin range for mature home-care franchises"),
        "shipping-printing": ("Estimated (industry benchmark): low to mid six figures CAD business-service centre buildout", "Estimated (industry benchmark): 3-6 years", "Estimated (industry benchmark): 12-22% store-level EBITDA range for mature shipping and printing centres"),
        "staffing": ("Estimated (industry benchmark): low to mid six figures CAD professional-office launch", "Estimated (industry benchmark): 2-5 years", "Estimated (industry benchmark): 12-20% office-level EBITDA range for mature staffing franchises"),
        "pet-services": ("Estimated (industry benchmark): mid six figures CAD specialty retail buildout", "Estimated (industry benchmark): 3-6 years", "Estimated (industry benchmark): 8-18% store-level EBITDA range for mature pet retail or service concepts"),
        "finance": ("Estimated (industry benchmark): low five figures to low six figures CAD office launch", "Estimated (industry benchmark): 2-4 years", "Estimated (industry benchmark): 20-40% office-level EBITDA range for mature brokerage, accounting, or advisory models"),
    }
    investment, payback, margin = category_ranges.get(category, category_ranges["qsr"])
    return {
        "initial_investment": investment,
        "franchise_fee": "Estimated (industry benchmark)",
        "royalty": "Estimated (industry benchmark)",
        "marketing_fee": "Estimated (industry benchmark)",
        "technology_fee": "Not Verified",
        "training_fee": "Not Verified",
        "renewal_fee": "Not Verified",
        "transfer_fee": "Not Verified",
        "other_mandatory_fees": "Not Verified",
        "average_unit_revenue": "Not Verified",
        "item_19_avg_revenue": "Not Verified",
        "item_19_gross_profit": "Not Verified",
        "item_19_net_profit": "Not Verified",
        "payback_period": payback,
        "realistic_payback_range": "Not Verified",
        "profit_margin": margin,
        "minimum_net_worth": "Not Verified",
        "minimum_liquid_capital": "Not Verified",
        "franchise_term": "Not Verified",
        "renewal_terms": "Not Verified",
        "territory_protection": "Not Verified",
        "franchisor_financing": "Not Verified",
    }


def expansion_record(seed: dict[str, Any]) -> dict[str, Any]:
    category = seed.get("category", "qsr")
    name = seed["name"]
    report_folder = str(seed.get("report_folder") or DEFAULT_REPORT_FOLDER)
    is_food = is_food_report_folder(report_folder)
    industry = seed.get("industry", "Quick-service restaurant" if is_food else "Business or consumer service")
    descriptor = seed.get("cuisine_type", "Food service" if is_food else "Service category")
    operational_difficulty = (
        "Moderate to high; labour scheduling, throughput, food cost, and local management quality matter"
        if is_food
        else "Moderate; local sales execution, staffing, compliance, and service quality drive results"
    )
    positive_themes = (
        [
            "Recognizable QSR category with repeat-purchase potential",
            "Standardized menu and operating model can support multi-unit execution",
            "Canadian market comparability supports side-by-side screening",
        ]
        if is_food
        else [
            "Recognizable service category with repeat-use, membership, or referral potential",
            "Standardized operating systems can support local execution and multi-unit ownership",
            "Canadian market comparability supports side-by-side screening",
        ]
    )
    negative_themes = (
        [
            "Official Canadian economics not loaded",
            "Store-level returns depend heavily on site selection, labour, rent, food cost, and local competition",
            "Franchisee satisfaction and closure data remain unverified",
        ]
        if is_food
        else [
            "Official Canadian economics not loaded",
            "Local demand, staffing, occupancy cost, and sales execution can materially change returns",
            "Franchisee satisfaction and closure data remain unverified",
        ]
    )
    risks_mentioned = (
        ["Unverified Canadian economics", "Category competition", "Labour, rent, and food-cost pressure"]
        if is_food
        else ["Unverified Canadian economics", "Category competition", "Staffing, occupancy, and local execution pressure"]
    )
    source_note_prefix = (
        f"{name} was added as an expansion target for Canadian food/QSR comparison."
        if is_food
        else f"{name} was added as a non-food comparison target for Canadian franchise screening."
    )
    consensus_summary = (
        "Comparable QSR opportunity for screening, but not investor-grade until source-backed Canadian data is loaded."
        if is_food
        else "Comparable non-food opportunity for screening, but not investor-grade until source-backed Canadian data is loaded."
    )
    record = {
        "name": name,
        "category": category,
        "report_folder": report_folder,
        "profile": {
            "founded": seed.get("founded", "Not Verified"),
            "headquarters": seed.get("headquarters", "Not Verified"),
            "canadian_owned": seed.get("canadian_owned", "Not Verified"),
            "industry": industry,
            "cuisine_type": descriptor,
            "franchise_available": seed.get("franchise_available", "Yes"),
            "franchising_internationally": "Not Verified",
        },
        "financials": estimated_financials(category),
        "growth": {
            "total_locations_canada": "Canadian footprint present; exact current count not verified in this seed file",
            "total_locations_international": "Not Verified",
            "locations_by_province": seed.get("province_strength", {}),
            "new_locations_this_year": "Not verified / not available",
            "closures_this_year": "Not verified / not available",
            "openings_last_12_months": "Not Verified",
            "closures_last_12_months": "Not Verified",
            "net_growth_rate": "Estimated (industry benchmark): stable to selective growth",
            "three_year_unit_trend": "Not Verified",
            "active_job_postings": "Not Verified",
            "hiring_trend": "Not Verified",
            "average_unit_age": "Not Verified",
        },
        "customer": {
            "google_rating": "Not verified / requires Google Places API",
            "review_volume": "Not verified / requires Google Places API",
            "sentiment_trend": "Not Verified",
            "insight_summary": "Current customer and operator truth requires review analysis, local field calls, and market-level research.",
        },
        "franchisee": {
            "satisfaction_score": "Not Verified",
            "training_quality": "Standardized system expected; exact training duration and franchisee-rated quality not verified",
            "operational_difficulty": operational_difficulty,
            "support_quality": "Not Verified",
            "marketing_support_quality": "Not Verified",
            "average_tenure": "Not Verified",
            "turnover_percent": "Not Verified",
            "association": "Not Verified",
            "litigation_history_5yr": "Not Verified",
        },
        "sentiment": {
            "positive_themes": positive_themes,
            "negative_themes": negative_themes,
            "profit_reality": "This profile is useful for early screening only. It cannot support investment scoring until Canadian disclosure, P&L, closure, fee, and franchisee-interview evidence is obtained.",
            "risks_mentioned": risks_mentioned,
            "consensus_summary": consensus_summary,
        },
        "competitive": {
            "main_competitors": seed.get("competitors", ["Local and regional category competitors"]),
            "market_saturation": seed.get("saturation", "Medium"),
            "differentiation": "Brand/category positioning requires verification against local competitors, trade-area conditions, and channel dynamics.",
            "threat_level": "Medium",
            "market_share_estimate": "Not Verified",
            "category_growth_rate": "Not Verified",
            "international_competitive_pressure": "Not Verified",
        },
        "investor_evidence": {},
        "source_notes": [
            source_note_prefix,
            "All economics are placeholders or industry-screening estimates until official Canadian franchise documents and verified field evidence are loaded.",
        ],
        "critical_gaps": [
            "Canadian disclosure package",
            "Exact Canadian signing entity",
            "CAD investment and recurring fees",
            "Canadian AUV, EBITDA, or comparable P&L",
            "Closure, transfer, resale, renewal, and litigation data",
            "Current/former franchisee interviews",
            "Target-market lease, competition, demographic, and delivery-radius checks",
        ],
        "red_flags": [
            "No Canadian disclosure document loaded",
            "No verified Canadian unit economics loaded",
            "No franchisee interview log loaded",
        ],
        "yellow_flags": [
            "Generic estimates are present for screening only",
            "Province footprint is directional and not a verified live count",
        ],
        "green_flags": [
            "Category expands the comparison set beyond the original food-only folder",
            "Brand/category has repeat-use, membership, contract, or referral potential",
        ],
    }
    for section, values in seed.get("field_evidence", {}).items():
        if section in record and isinstance(record[section], dict):
            record[section].update(values)
    if seed.get("investor_evidence"):
        record["investor_evidence"] = seed["investor_evidence"]
    return record


def apply_research_overrides(franchises: list[dict[str, Any]]) -> list[dict[str, Any]]:
    override_items: list[dict[str, Any]] = []
    for override_file in [RESEARCH_OVERRIDES_FILE, NON_FOOD_RESEARCH_OVERRIDES_FILE]:
        if override_file.exists():
            override_items.extend(json.loads(override_file.read_text(encoding="utf-8")))

    if not override_items:
        return franchises

    override_map = {item["name"].lower(): item for item in override_items}

    for franchise in franchises:
        override = override_map.get(franchise["name"].lower())
        if not override:
            continue

        for section in ["profile", "financials", "growth", "customer", "franchisee", "competitive", "sentiment"]:
            values = override.get(section)
            if values:
                franchise.setdefault(section, {})
                franchise[section].update(values)

        for top_level in ["investor_evidence"]:
            values = override.get(top_level)
            if values:
                franchise.setdefault(top_level, {})
                franchise[top_level].update(values)

        for list_field in ["source_notes", "critical_gaps", "red_flags", "yellow_flags", "green_flags", "opportunities", "threats"]:
            values = override.get(list_field)
            if values:
                existing = franchise.setdefault(list_field, [])
                for value in values:
                    if value not in existing:
                        existing.append(value)

    return franchises


def category_target_records() -> list[dict[str, Any]]:
    if not NON_FOOD_CATEGORY_TARGETS_FILE.exists():
        return []

    target_data = json.loads(NON_FOOD_CATEGORY_TARGETS_FILE.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []
    default_province_strength = {
        "Ontario": "Not Verified",
        "Alberta": "Not Verified",
        "BC": "Not Verified",
        "Quebec": "Not Verified",
    }

    for category_group in target_data.get("categories", []):
        defaults = {
            "category": category_group["category"],
            "report_folder": category_group["report_folder"],
            "industry": category_group["industry"],
            "cuisine_type": category_group["service_line"],
            "province_strength": category_group.get("province_strength", default_province_strength),
            "competitors": category_group.get("competitors", ["Local and regional category competitors"]),
            "saturation": category_group.get("saturation", "Not Verified"),
            "franchise_available": category_group.get("franchise_available", "Not Verified"),
            "source_notes": [
                f"Added from the 15-per-category non-food database target list for {category_group['report_folder']}.",
                "This is a screening target only until franchisor-confirmed Canadian disclosure and economics are loaded.",
            ],
            "critical_gaps": [
                "Franchisor confirmation of Canadian franchise availability",
                "Canadian disclosure package or legal franchise document",
                "Exact Canadian signing entity",
                "Current CAD investment, franchise fee, royalty, and marketing fee",
                "Canadian AUV, EBITDA, closure, transfer, renewal, and litigation data",
                "Current/former franchisee interviews",
                "Current Canadian location count and target-market checks",
            ],
            "red_flags": [
                "No franchisor-confirmed evidence loaded",
                "No verified Canadian investment economics loaded",
            ],
            "yellow_flags": [
                "Added for structured category coverage",
                "Category and competitor assumptions need verification",
            ],
        }
        for target in category_group["targets"]:
            record = dict(defaults)
            if isinstance(target, str):
                record["name"] = target
            else:
                record.update(target)
            records.append(record)
    return records


def load_franchises() -> list[dict[str, Any]]:
    franchises = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    existing_names = {franchise["name"].lower() for franchise in franchises}
    for seed_file in [EXPANSION_FILE, FRANCHISE_200_FILE, NON_FOOD_FILE, NON_FOOD_EXPANSION_FILE]:
        if not seed_file.exists():
            continue
        expansion_seeds = json.loads(seed_file.read_text(encoding="utf-8"))
        for seed in expansion_seeds:
            if seed["name"].lower() not in existing_names:
                franchises.append(expansion_record(seed))
                existing_names.add(seed["name"].lower())
    for seed in category_target_records():
        if seed["name"].lower() not in existing_names:
            franchises.append(expansion_record(seed))
            existing_names.add(seed["name"].lower())
    return apply_research_overrides(franchises)


def main() -> None:
    franchises = load_franchises()
    output_dirs: set[Path] = set()
    for franchise in franchises:
        output_dir = output_dir_for_franchise(franchise)
        output_dir.mkdir(parents=True, exist_ok=True)
        report = render_report(franchise)
        (output_dir / safe_filename(franchise["name"])).write_text(report, encoding="utf-8")
        output_dirs.add(output_dir)
    print(f"Generated {len(franchises)} reports across {len(output_dirs)} folders in {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
