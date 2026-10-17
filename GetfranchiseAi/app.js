const DATA_URL = "../output/franchises/GETFRANCHISE_BRAND_DATA_2026-07-18.json";
const FOOD_SERVICE_CATEGORIES = new Set(["beverage_dessert", "limited_service", "full_service"]);
const DRINK_PROFILE_IDS = new Set([
  "booster-juice",
  "chatime-canada",
  "gong-cha-canada",
  "presotea-canada",
  "coco-fresh-tea-juice-canada",
  "jugo-juice",
  "second-cup-cafe",
  "yogen-fruz",
]);
const SECTION_TABS = [
  ["all", "Source-backed"],
  ["drinks", "Drinks"],
  ["limited_service", "Quick Service"],
  ["full_service", "Full Service"],
  ["services", "Services"],
];
const PAGE_SIZE = 25;
const STORAGE_KEY = "getfranchise-shortlist";
const PLAN_STORAGE_KEY = "getfranchise-plan";
const MATCH_STORAGE_KEY = "getfranchise-match-v1";
const COMPARE_FIELDS_STORAGE_KEY = "getfranchise-comparison-fields-v1";
const BETA_ACCESS_STORAGE_KEY = "getfranchise-founder-beta-access";
const PLANS = {
  basic: {
    name: "Basic",
    price: "$0",
    cadence: "Free forever",
    summary: "A clear place to start your franchise search.",
    features: ["Browse the source-backed directory", "Compare up to 2 franchises at a time", "No exports or original-file access"],
  },
  advanced: {
    name: "Advanced",
    price: "$5",
    cadence: "per month",
    summary: "For buyers narrowing down a serious shortlist.",
    features: ["Full side-by-side comparison engine", "Deep analysis views and saved comparisons", "No raw source-file access"],
  },
  premium: {
    name: "Premium",
    price: "$15",
    cadence: "per month",
    summary: "Reserved for the account-backed research workflow.",
    features: ["Original internal records are not served by this preview", "Bulk comparisons and CSV exports are preview-only", "Everything in Advanced once accounts are live"],
  },
};
const TIER_LIMITS = { basic: 5, advanced: 10, premium: Infinity };
const TIER_QUESTION_COUNTS = { basic: 15, advanced: 60, premium: 100 };
const QUESTIONNAIRE_VERSION = "2.0";
const Q = (id, text, type, options, weight, mapsTo) => ({ id, text, type, options, weight, mapsTo });
// Versioned, export-schema-aware questionnaire. Questions can be shown even
// where the current export cannot assess every mapped signal; those cases are
// labelled unavailable instead of being inferred.
const CORE_QUESTIONNAIRE = [
  Q("investment_budget", "What total initial investment range are you comfortable considering?", "single-select", ["Under $150k", "$150k–$300k", "$300k–$500k", "$500k–$1m", "Over $1m", "Unsure"], 10, "Financials: total investment"),
  Q("preferred_category", "Which franchise categories are you most interested in?", "multi-select", ["Food service", "Home services", "Senior care", "Child services", "Pet services", "Automotive", "Fitness", "Education", "Finance", "Real estate", "Shipping & printing", "Other"], 10, "Company profile: category"),
  Q("operating_role", "How involved do you want to be in day-to-day operations?", "single-select", ["Owner-operator", "Manage a manager", "Semi-absentee", "Unsure"], 8, "Signals: operational difficulty, training, support"),
  Q("target_location", "Where do you plan to operate?", "text", [], 8, "Locations: footprint, saturation, competitors"),
  Q("liquid_capital", "How much liquid capital can you commit without borrowing?", "single-select", ["Under $75k", "$75k–$150k", "$150k–$300k", "$300k–$500k", "Over $500k", "Prefer not to say"], 9, "Financials: liquid capital"),
  Q("category_experience", "Which areas match your professional or operating experience?", "multi-select", ["Food service", "Sales", "Retail", "Home services", "Caregiving", "Children’s programs", "Automotive", "Finance", "Management", "None of these"], 6, "Signals: training, support"),
  Q("growth_goal", "What is your ownership goal over the next five years?", "single-select", ["One stable unit", "Build multiple units", "Replace my income", "Add to an existing business", "Explore options"], 7, "Company profile: units; Signals: support"),
  Q("risk_preference", "How much uncertainty are you comfortable with?", "slider", ["1 Conservative", "2", "3 Balanced", "4", "5 Opportunity-seeking"], 7, "Scores: screening score; Evidence: confidence"),
  Q("launch_timeline", "When would you like to open?", "single-select", ["Within 6 months", "6–12 months", "12–24 months", "More than 24 months", "Unsure"], 5, "Financials: time to open; Signals: training"),
  Q("ownership_preference", "Do you prefer Canadian-owned, international, or either ownership?", "single-select", ["Canadian-owned", "International", "Either"], 3, "Company profile: ownership"),
  Q("customer_model", "Which customer model appeals most?", "multi-select", ["Repeat consumer visits", "Business-to-business", "Essential service", "Family services", "Appointment-based", "Walk-in retail", "Online-supported"], 4, "Company profile: industry, cuisine"),
  Q("territory_priority", "How important is clear territory or lower local saturation?", "slider", ["1 Not important", "2", "3", "4", "5 Essential"], 7, "Locations: saturation, competitors"),
  Q("local_competition", "How much local competition are you willing to accept?", "single-select", ["Low only", "Moderate is fine", "High if the brand is strong", "Unsure"], 5, "Locations: competitors, saturation"),
  Q("staffing_tolerance", "What staffing level can you realistically manage?", "single-select", ["Mostly self-run", "Small team", "Medium team", "Large team", "Unsure"], 6, "Signals: operational difficulty"),
  Q("hours_preference", "What operating schedule fits you best?", "multi-select", ["Weekdays", "Evenings", "Weekends", "Early mornings", "Flexible", "I can manage any schedule"], 5, "Signals: operational difficulty"),
  Q("food_operations_tolerance", "Are you comfortable with food preparation, inventory, and health-compliance work?", "single-select", ["Yes", "Somewhat", "No", "Not applicable"], 5, "Company profile: category; Signals: operational difficulty"),
  Q("sales_comfort", "How comfortable are you with local sales and business development?", "slider", ["1 Not comfortable", "2", "3", "4", "5 Very comfortable"], 5, "Signals: support"),
  Q("training_need", "How much structured training do you need before opening?", "single-select", ["Extensive", "Moderate", "Minimal", "Unsure"], 6, "Signals: training"),
  Q("support_priority", "Which franchisor support matters most to you?", "multi-select", ["Site selection", "Initial training", "Opening support", "Marketing", "Ongoing operations", "Technology", "Recruiting", "None is decisive"], 6, "Signals: support"),
  Q("location_format", "Which location format would you consider?", "multi-select", ["Storefront", "Mobile", "Home-based", "Office-based", "Commercial service territory", "Kiosk or non-traditional site", "Unsure"], 5, "Company profile; Locations"),
  Q("site_control", "How much site-selection responsibility do you want?", "single-select", ["Franchisor-led", "Shared", "I want control", "Unsure"], 3, "Signals: support; Locations"),
  Q("financing_readiness", "How ready are you to arrange financing?", "single-select", ["Funding secured", "Pre-qualified", "Researching options", "Not ready", "Prefer not to say"], 4, "Financials: investment, fee"),
  Q("fee_sensitivity", "Which ongoing cost matters most when comparing opportunities?", "single-select", ["Royalty", "Marketing fund", "Upfront fee", "Total investment", "All matter equally"], 6, "Financials: fee, royalty, marketing fee"),
  Q("revenue_evidence_priority", "How important is independently supported financial evidence to your decision?", "slider", ["1 Helpful", "2", "3", "4", "5 Required"], 8, "Evidence: verification gates, confidence; Financials: AUV, payback"),
  Q("evidence_tolerance", "Would you consider a franchise with material information still unverified?", "single-select", ["No", "Only with strong official sources", "Yes, if I can investigate", "Unsure"], 8, "Evidence: source count, confidence"),
  Q("brand_maturity", "What stage of franchise system do you prefer?", "single-select", ["Established network", "Growing network", "Emerging concept", "No preference"], 4, "Company profile: units, founded"),
  Q("unit_count_preference", "What network size feels right to you?", "single-select", ["Under 25 units", "25–100", "100–500", "Over 500", "No preference"], 3, "Company profile: units"),
  Q("expansion_appetite", "Would you consider developing multiple locations?", "single-select", ["Yes now", "Maybe later", "No", "Unsure"], 4, "Company profile: units; Signals: support"),
  Q("customer_reputation_priority", "How important is customer reputation?", "slider", ["1 Low", "2", "3", "4", "5 Essential"], 4, "Signals: customer rating"),
  Q("franchisee_validation_priority", "How important is franchisee satisfaction evidence?", "slider", ["1 Low", "2", "3", "4", "5 Essential"], 6, "Signals: franchisee satisfaction"),
  Q("payback_expectation", "What payback period would you consider acceptable?", "single-select", ["Under 3 years", "3–5 years", "Over 5 years", "I will assess later"], 6, "Financials: payback"),
  Q("income_goal", "What annual owner-income outcome are you targeting after stabilization?", "number", ["CAD amount"], 4, "Financials: AUV, payback"),
  Q("deal_breakers", "What should immediately remove a franchise from consideration?", "multi-select", ["Above-budget investment", "High recurring fees", "Low evidence", "High saturation", "Complex operations", "Long launch timeline", "International ownership", "None"], 9, "Financials; Locations; Signals; Evidence"),
  Q("additional_context", "Is there anything else a suitable franchise must fit?", "text", [], 2, "No direct score; displayed as user context only"),
  Q("review_priority", "What should the final recommendation prioritize if trade-offs remain?", "single-select", ["Affordability", "Evidence quality", "Growth potential", "Operational simplicity", "Market opportunity", "Support"], 8, "Scoring weights across applicable categories"),
];
// These questions create a fuller ownership-style profile. They are intentionally
// context-only until the source data contains fields that can assess them fairly.
const P = (id, text, options, mapsTo) => ({ ...Q(id, text, "single-select", options, 0, mapsTo), contextOnly: true });
const PERSONALITY_QUESTIONS = [
  P("decision_pace", "When a major decision is needed, what pace feels right?", ["Decide quickly", "Compare options first", "Take time to validate", "Ask trusted advisors"], "Decision style"),
  P("decision_process", "How do you prefer to make operating decisions?", ["Data first", "Customer feedback first", "Team input first", "A mix of all three"], "Decision style"),
  P("ambiguity_comfort", "How comfortable are you acting before every detail is known?", ["Very comfortable", "Somewhat comfortable", "Prefer clarity", "Need a clear process"], "Risk and decision style"),
  P("detail_preference", "How much detail do you want before committing?", ["High-level only", "Key facts", "Full model", "Full model plus independent review"], "Diligence style"),
  P("communication_style", "What leadership communication style suits you best?", ["Direct and concise", "Collaborative", "Coaching-oriented", "Highly structured"], "Leadership style"),
  P("negotiation_comfort", "How comfortable are you negotiating with landlords, vendors, and lenders?", ["Very comfortable", "Comfortable with support", "Prefer an advisor", "Avoid it where possible"], "Negotiation support"),
  P("feedback_style", "How do you prefer to receive performance feedback?", ["Live dashboard", "Weekly review", "Monthly review", "Only major exceptions"], "Management cadence"),
  P("routine_preference", "What kind of work rhythm energizes you?", ["Predictable routine", "Some variety", "Fast-changing", "Project-based"], "Operating rhythm"),
  P("system_adherence", "How closely do you want to follow a franchisor playbook?", ["Very closely", "Mostly closely", "Room for local judgment", "Maximum flexibility"], "Brand-system fit"),
  P("local_marketing", "How involved do you want to be in local marketing?", ["Lead it myself", "Share it with the franchisor", "Use franchisor programs", "Minimal involvement"], "Marketing involvement"),
  P("community_presence", "How important is being visible in your local community?", ["Essential", "Important", "Nice to have", "Not a priority"], "Local-market fit"),
  P("customer_interaction", "How much direct customer interaction do you want?", ["Daily and hands-on", "Regularly", "Occasionally", "Very little"], "Owner-operator fit"),
  P("employee_coaching", "How interested are you in coaching and developing staff?", ["A core strength", "Comfortable", "Can learn it", "Prefer a manager to lead it"], "People leadership"),
  P("hiring_confidence", "How confident are you hiring frontline staff?", ["Very confident", "Somewhat confident", "Need a playbook", "Need substantial support"], "Staffing readiness"),
  P("retention_priority", "How much effort can you put into staff retention?", ["A major priority", "Regular effort", "Some effort", "Limited capacity"], "People leadership"),
  P("conflict_style", "When team conflict appears, what is your usual approach?", ["Address it immediately", "Coach through it", "Use a manager or HR process", "Prefer to avoid conflict"], "People leadership"),
  P("sales_appetite", "How energized are you by selling and building relationships?", ["Very energized", "Comfortable", "Can do it when needed", "Prefer not to"], "Business development"),
  P("digital_comfort", "How comfortable are you with apps, dashboards, and digital marketing tools?", ["Very comfortable", "Comfortable", "Need training", "Prefer support"], "Technology readiness"),
  P("bookkeeping_comfort", "How involved do you want to be in bookkeeping and reconciliations?", ["Hands-on", "Review weekly", "Review monthly", "Outsource with oversight"], "Financial management"),
  P("compliance_style", "How do you approach compliance checklists and audits?", ["I enjoy systems", "I follow them carefully", "I need reminders", "I want strong support"], "Compliance readiness"),
  P("supplier_management", "How comfortable are you managing vendors and supply issues?", ["Very comfortable", "Comfortable", "Need guidance", "Prefer centralized support"], "Operations support"),
  P("inventory_tolerance", "How willing are you to manage inventory and waste?", ["Very willing", "Somewhat willing", "Only with good systems", "Prefer to avoid it"], "Operations fit"),
  P("equipment_tolerance", "How comfortable are you handling equipment or facility problems?", ["Very comfortable", "Can coordinate vendors", "Need franchisor support", "Prefer minimal exposure"], "Operations fit"),
  P("facility_involvement", "How hands-on do you want to be with site upkeep?", ["Very hands-on", "Regular oversight", "Manager-led", "Third-party managed"], "Operations fit"),
  P("emergency_response", "How available can you be for an unexpected operating issue?", ["Any time", "Most times", "Business hours", "Only through a manager"], "Owner availability"),
  P("personal_hours", "What weekly owner commitment is realistic at launch?", ["50+ hours", "40-50 hours", "25-40 hours", "Under 25 hours"], "Owner availability"),
  P("travel_tolerance", "How much travel can you make for training or site visits?", ["Frequent travel is fine", "Some travel", "Limited travel", "Very little travel"], "Launch readiness"),
  P("partner_structure", "Who will share ownership or decision-making?", ["Just me", "Operating partner", "Financial partner", "Family partnership"], "Ownership structure"),
  P("leadership_preference", "Which leadership role fits you best?", ["Coach the team", "Run operations", "Drive sales", "Review strategy and finance"], "Leadership style"),
  P("decision_authority", "How much decision authority do you want to retain?", ["Most decisions", "Shared with franchisor", "Shared with a manager", "Mostly delegated"], "Ownership structure"),
  P("change_tolerance", "How do you respond to frequent menu, system, or brand changes?", ["I enjoy adapting", "I can adapt", "I prefer stability", "I need advance planning"], "Change readiness"),
  P("technology_adoption", "How quickly do you adopt new operating technology?", ["Early adopter", "When proven", "With training", "Only when required"], "Technology readiness"),
  P("reporting_cadence", "How often would you like to review business performance?", ["Daily", "Weekly", "Monthly", "Quarterly"], "Management cadence"),
  P("metrics_priority", "Which metric matters most to you at launch?", ["Cash flow", "Customer loyalty", "Team stability", "Growth"], "Management priorities"),
  P("cash_flow_style", "How cautiously do you manage cash flow?", ["Very conservatively", "Conservatively", "Balanced", "Comfortable taking measured risk"], "Financial readiness"),
  P("debt_comfort", "How comfortable are you using debt to fund growth?", ["Avoid debt", "Use limited debt", "Use prudent leverage", "Comfortable with leverage"], "Financial readiness"),
  P("reinvestment_appetite", "How willing are you to reinvest profits into a second unit?", ["Very willing", "Possibly later", "Prefer distributions", "Not interested"], "Growth strategy"),
  P("emergency_reserve", "How much operating reserve do you want before opening?", ["More than expected need", "A solid reserve", "Minimum required", "Still building it"], "Financial readiness"),
  P("lease_comfort", "How comfortable are you reviewing a commercial lease?", ["Very comfortable", "With a lawyer", "Need strong support", "New to this"], "Real-estate readiness"),
  P("real_estate_role", "What role do you want in selecting a site?", ["Lead selection", "Jointly assess", "Approve franchisor options", "Rely on franchisor"], "Real-estate readiness"),
  P("territory_need", "How important is territorial protection?", ["Non-negotiable", "Very important", "Helpful", "Not decisive"], "Territory preference"),
  P("competition_response", "How do you view a competitive market?", ["Avoid it", "Enter with clear demand", "Compete with a strong brand", "I enjoy competition"], "Market style"),
  P("multiunit_timing", "When would you realistically consider a second unit?", ["Within 2 years", "Within 3-5 years", "After one unit is stable", "Never"], "Growth strategy"),
  P("exit_horizon", "What is your likely ownership horizon?", ["Under 5 years", "5-10 years", "10+ years", "Build a family asset"], "Exit planning"),
  P("succession_plan", "How important is a succession or resale path?", ["Essential", "Important", "Helpful", "Not a priority yet"], "Exit planning"),
  P("mission_priority", "How important is alignment with the brand’s mission and values?", ["Essential", "Important", "Helpful", "Not decisive"], "Brand fit"),
  P("customer_quality", "What customer experience standard do you want to protect?", ["Premium and personal", "Fast and consistent", "Value-led", "Convenience-led"], "Customer model"),
  P("brand_control", "How much creative control do you want over local offers and service?", ["Very little needed", "Some local flexibility", "Meaningful flexibility", "A lot of freedom"], "Brand-system fit"),
  P("product_complexity", "What product or service complexity suits you?", ["Simple and repeatable", "Moderate complexity", "Specialized work", "Complex is fine"], "Operations fit"),
  P("seasonality_comfort", "How comfortable are you with seasonal sales swings?", ["Avoid them", "Manage moderate swings", "Comfortable with swings", "They do not concern me"], "Financial readiness"),
  P("local_causes", "Would you like the business to participate in local causes?", ["Actively", "Occasionally", "Only franchisor programs", "Not a focus"], "Community presence"),
  P("sustainability_priority", "How important are sustainability and local sourcing to you?", ["Essential", "Important", "Helpful", "Not decisive"], "Brand fit"),
  P("location_preference", "What market feels most natural for your first unit?", ["Downtown urban", "Suburban", "Small city", "Rural or regional"], "Location preference"),
  P("bilingual_readiness", "Could you operate in a bilingual market if the opportunity fit?", ["Yes", "With support", "Possibly later", "No"], "Market readiness"),
  P("team_culture", "What team culture do you want to build?", ["High-performance", "Warm and family-like", "Professional and structured", "Flexible and entrepreneurial"], "People leadership"),
  P("social_media_role", "How involved do you want to be in local social media?", ["Create content myself", "Approve content", "Use agency/franchisor", "Minimal involvement"], "Marketing involvement"),
  P("networking_appetite", "How much local networking can you do?", ["Weekly", "Monthly", "Occasionally", "Very little"], "Business development"),
  P("goal_orientation", "Which outcome matters most in year one?", ["Learning operations", "Reliable cash flow", "Building a team", "Preparing to expand"], "Ownership goals"),
  P("patience_for_payoff", "How patient can you be before the business stabilizes?", ["More than 3 years", "2-3 years", "1-2 years", "Need quick stability"], "Financial readiness"),
  P("independence_preference", "How independent do you want to be from the franchisor day to day?", ["Very guided", "Balanced", "Mostly independent", "Highly independent"], "Brand-system fit"),
  P("franchisor_contact", "How often do you want contact with the franchisor after launch?", ["Weekly", "Monthly", "As needed", "Minimal"], "Support preference"),
  P("disclosure_review", "How will you review franchise disclosure documents?", ["With a franchise lawyer", "With lawyer and accountant", "Independently then advisors", "I need guidance"], "Diligence readiness"),
  P("legal_advisor", "Do you have access to a franchise lawyer?", ["Yes", "Finding one", "Not yet", "Need a referral"], "Diligence readiness"),
  P("accountant_advisor", "Do you have an accountant who can review the opportunity?", ["Yes", "Finding one", "Not yet", "Need a referral"], "Diligence readiness"),
  P("franchisee_interviews", "How many current or former franchisees will you aim to interview?", ["10 or more", "5-9", "1-4", "I need help planning this"], "Diligence readiness"),
];
const QUESTIONNAIRE = [...CORE_QUESTIONNAIRE, ...PERSONALITY_QUESTIONS];
const COMPARISON_FIELDS = [
  ["category", "Category", (b) => labelize(b.category)], ["company", "Founded / ownership / HQ", (b) => `${simpleValue(b.founded)} · ${simpleValue(b.canadianOwned)} · ${simpleValue(b.headquarters)}`],
  ["network", "Network size", (b) => simpleValue(b.numberOfLocations)], ["investment", "Total investment", (b) => simpleValue(b.totalInvestment)], ["fee", "Franchise fee", (b) => simpleValue(b.franchiseFee)],
  ["royalty", "Royalty", (b) => simpleValue(b.royalty)], ["marketing", "Marketing fee", (b) => simpleValue(b.marketing)], ["liquid", "Liquid-capital requirement", (b) => simpleValue(b.liquidCapital)],
  ["saturation", "Saturation", (b) => simpleValue(b.saturation)], ["operations", "Operational difficulty", (b) => simpleValue(b.operations)], ["training", "Training", (b) => simpleValue(b.trainingProvided)],
  ["sources", "Source count", (b) => String(b.sourceCount)], ["evidence", "Evidence grade", (b) => b.evidenceGrade], ["confirmation", "Confirmation", (b) => verificationStatusLabel(b)],
  ["screening", "Screening score", (b) => b.score === null ? "Unavailable" : `${b.score}/100`], ["risk", "Risk", (b) => b.risk], ["gaps", "Critical gaps", (b) => b.gaps.length ? b.gaps.join("; ") : "None stated"],
  ["sources_links", "Source links", (b) => [...b.officialSources, ...b.governmentSources].length ? [...b.officialSources, ...b.governmentSources].map((url) => `<a href="${escapeAttr(url)}" target="_blank" rel="noreferrer">Source</a>`).join(" · ") : "Unavailable"],
];
const BASIC_FIELDS = ["category", "investment", "fee", "royalty", "evidence", "screening", "risk", "confirmation"];
const OUTREACH_STORAGE_KEY = "getfranchise-outreach-status";
const RESEARCH_STORAGE_KEY = "getfranchise-research-status";
const RESEARCH_QUEUE_LIMIT = 80;
// Outreach is deliberately held until the research portfolio is broad enough
// to support a fair first-pass comparison. This is a hard UI gate, not merely
// a status label: it prevents franchise-development email drafts before then.
const OUTREACH_MINIMUM_READY_CANDIDATES = 100;
const CORRECTION_EMAIL = "corrections@getfranchise.ca";
const BUYER_EMAIL = "hello@getfranchise.ca";
const CONTACT_EMAIL_OVERRIDES = {
  "dominos-canada": "development@dominos.ca",
  "molly-maid-canada": "franchiseopportunities@mollymaid.ca",
  "postalannex": "info@postalannex.com",
};
const BUYER_RESEARCH_TOPICS = [
  ["Total capital", "Initial investment, liquid capital, net worth, working capital, buildout, inventory, lease deposits, insurance, and opening marketing."],
  ["Recurring fees", "Royalty, brand fund, local marketing, technology, transfer, renewal, audit, supplier, training, and required purchasing fees."],
  ["Financial proof", "FDD or disclosure status, Item 19 or equivalent earnings claims, AUV, margin, payback, closure, transfer, and resale history."],
  ["Territory", "Protected territory, site approval, exclusivity, online sales rules, cannibalization risk, relocation rules, and local market saturation."],
  ["Operations", "Training, opening support, staffing load, owner-operator expectations, supplier restrictions, equipment, hours, licensing, and compliance."],
  ["Franchisee validation", "Current and former franchisee calls, satisfaction, support quality, disputes, litigation, renewal terms, and whether operators would buy again."],
];
const LOGO_DOMAINS = {
  "booster-juice": "boosterjuice.com",
  "boston-pizza": "bostonpizza.com",
  "budget-blinds-canada": "budgetblinds.com",
  "carls-jr-canada": "carlsjr.com",
  "certapro-painters-canada": "certapro.ca",
  "chem-dry-canada": "chemdryfranchise.com",
  "chocolato": "chocolato.ca",
  "chatime-canada": "chatime.com",
  "church-s-texas-chicken-canada": "churchstexaschicken.com",
  "cobs-bread": "cobsbread.com",
  "coco-fresh-tea-juice-canada": "cocobubbletea.ca",
  "coffee-time": "coffeetime.com",
  "comfort-keepers-canada": "comfortkeepers.ca",
  "copper-branch": "eatcopperbranch.com",
  "dairy-queen-canada": "dairyqueen.com",
  "days-inns-canada": "wyndhamhotels.com",
  "eggsmart": "eggsmart.com",
  "express-employment-professionals": "expresspros.com",
  "fionn-maccool-s": "fionnmaccools.com",
  "freshslice-pizza": "freshslice.com",
  "freshii": "freshii.com",
  "global-pet-foods": "globalpetfoods.com",
  "gong-cha-canada": "gongchacanada.ca",
  "good-earth-coffeehouse": "goodearthcoffeehouse.com",
  "handyman-connection": "handymanconnection.com",
  "home-instead": "homeinstead.com",
  "jiffy-lube": "jiffylube.com",
  "jugo-juice": "jugojuice.com",
  "kumon-math-and-reading-centres": "kumonfranchise.com",
  "little-caesars-canada": "littlecaesars.ca",
  "manchu-wok": "manchuwok.com",
  "mary-brown-s-chicken": "marybrowns.com",
  "mcdonalds-canada": "mcdonalds.com",
  "mathnasium": "mathnasium.com",
  "merry-maids-of-canada": "merrymaids.ca",
  "mr-sub": "mrsub.ca",
  "mucho-burrito": "muchoburrito.com",
  "panago-pizza": "panago.com",
  "presotea-canada": "presotea.ca",
  "pet-wants": "petwants.com",
  "pizza-pizza": "pizzapizza.ca",
  "pita-pit-canada": "pitapit.ca",
  "pizza-depot": "pizzadepot.ca",
  "pizza-garden-canada": "pizzagarden.ca",
  "pizza-hotline": "pizzahotline.ca",
  "postalannex": "postalannex.com",
  "quesada-burritos-and-tacos": "quesada.ca",
  "right-at-home-canada": "rightathomecanada.com",
  "real-fruit-bubble-tea": "realfruitbubbletea.com",
  "robin-s-donuts": "robinsdonuts.com",
  "school-of-rock-canada": "schoolofrock.com",
  "second-cup-cafe": "mysecondcup.com",
  "shoeless-joe-s-sports-grill": "shoelessjoes.ca",
  "snap-fitness": "snapfitness.com",
  "souvlaki-bar": "souvlakibar.ca",
  "subway-canada": "subway.com",
  "blenz-coffee": "blenz.com",
  "club-pilates-canada": "clubpilates.com",
  "sunset-grill": "sunsetgrill.ca",
  "tacotime-canada": "tacotimecanada.com",
  "thai-express": "thaiexpress.ca",
  "the-grounds-guys": "groundsguys.ca",
  "the-ups-store": "theupsstore.ca",
  "tim-hortons": "timhortons.ca",
  "yogen-fruz": "yogenfruz.com",
  "nurse-next-door": "nursenextdoorfranchise.com",
};

const app = document.querySelector("#app");
const navShortlistCount = document.querySelector("#navShortlistCount");
const primaryNavLinks = [...document.querySelectorAll(".top-nav a")];

const state = {
  allBrands: [],
  brands: [],
  filtered: [],
  query: "",
  category: "all",
  section: "all",
  investment: "all",
  evidence: "all",
  risk: "all",
  ownership: "all",
  sort: "score_desc",
  researchQuery: "",
  researchCategory: "all",
  researchNeed: "priority",
  researchStage: "all",
  page: 1,
  plan: readPlan(),
  shortlist: new Set(readShortlist()),
  match: readMatch(),
  matchStep: 0,
  comparisonSort: "rank",
  comparisonFilters: { category: "all", investment: "all", risk: "all", evidence: "all", availability: "all" },
  comparisonFields: readComparisonFields(),
};

bindInteractionFeedback();
init();

function bindInteractionFeedback() {
  document.addEventListener("pointerdown", (event) => {
    if (!(event.target instanceof Element)) return;
    const control = event.target.closest(
      "button:not(:disabled), a.primary-button, a.secondary-button, a.chip-button, a.table-action, .top-nav a"
    );
    if (!control || control.classList.contains("is-disabled")) return;

    const bounds = control.getBoundingClientRect();
    const ripple = document.createElement("span");
    ripple.className = "press-ripple";
    ripple.style.left = `${event.clientX - bounds.left}px`;
    ripple.style.top = `${event.clientY - bounds.top}px`;
    control.append(ripple);
    ripple.addEventListener("animationend", () => ripple.remove(), { once: true });
  });
}

async function init() {
  try {
    const response = await fetch(DATA_URL);
    if (!response.ok) {
      throw new Error(`Database export returned ${response.status}`);
    }
    const rows = await response.json();
    state.allBrands = rows.map(normalizeBrand);
    state.brands = getPublicBrands(state.allBrands);
    pruneShortlistToPublishedProfiles();
    state.filtered = applyFilters();
    window.addEventListener("hashchange", renderRoute);
    renderRoute();
  } catch (error) {
    renderError(error);
  }
}

function normalizeBrand(row, index) {
  const name = clean(row.brand || `Brand ${index + 1}`);
  const id = slugify(name);
  const brand = {
    id,
    name: toTitle(name),
    rawName: name,
    category: clean(row.category || "uncategorized"),
    score: numberOrNull(row.generic_screening_score),
    risk: clean(row.risk_level || "Not Verified"),
    growth: clean(row.growth_outlook || "Not Verified"),
    investment: clean(row.investment_tier || "Not Verified"),
    confidence: clean(row.confidence_level || "Not Verified"),
    goalFit: clean(row.investment_goal_fit || "Not Verified"),
    founded: clean(row.founded || "Not Verified"),
    headquarters: clean(row.headquarters || "Not Verified"),
    canadianOwned: clean(row.canadian_owned || "Not Verified"),
    industry: clean(row.industry || "Not Verified"),
    cuisine: clean(row.cuisine || "Not Verified"),
    totalInvestment: clean(row.total_investment_range || "Not publicly available"),
    franchiseFee: clean(row.franchise_fee || "Not publicly available"),
    royalty: clean(row.royalty_percent || "Not publicly available"),
    marketing: clean(row.marketing_fund_percent || "Not publicly available"),
    liquidCapital: clean(row.min_liquid_capital || "Not publicly available"),
    locationRequirements: clean(row.location_requirements || "Not stated"),
    averageTimeToOpen: clean(row.average_time_to_open || "Not stated"),
    trainingProvided: clean(row.training_provided || "Not stated"),
    profitabilityIndicators: clean(row.profitability_indicators || "Not stated"),
    numberOfLocations: clean(row.number_of_locations || "Not stated"),
    growthTrends: clean(row.growth_trends || "Not stated"),
    ownerReviews: clean(row.owner_reviews || "Not stated"),
    pros: splitPipes(row.pros),
    cons: splitPipes(row.cons),
    topPraises: splitPipes(row.top_praises),
    topComplaints: splitPipes(row.top_complaints),
    contactInformation: clean(row.contact_information || "Not stated"),
    fddSummary: clean(row.fdd_summary || "Not stated"),
    saturation: clean(row.market_saturation || "Not Verified"),
    threat: clean(row.threat_level || "Not Verified"),
    operations: clean(row.operational_difficulty || "Not Verified"),
    confirmation: clean(row.franchisor_confirmation || "Not confirmed"),
    sourceCount: numberOrNull(row.source_count) || 0,
    evidenceGrade: clean(row.evidence_grade || "Not Graded"),
    posture: clean(row.decision_posture || "Needs manual review"),
    gaps: splitPipes(row.top_critical_gaps),
    officialSources: splitSources(row.official_brand_sources),
    governmentSources: splitSources(row.government_or_law_sources),
    officialCount: numberOrNull(row.official_brand_source_count) || 0,
    governmentCount: numberOrNull(row.government_or_law_source_count) || 0,
    sourceDepthRank: numberOrNull(row.source_depth_rank),
    rejectedFields: numberOrNull(row.rejected_fields) || 0,
    verifiedCoreFeeFields: numberOrNull(row.verified_core_fee_fields) || 0,
    crossBorderCaution: clean(row.cross_border_caution || "Not Verified"),
    researchTrack: clean(row.research_track || "standard_review"),
    readyCandidate: clean(row.ready_candidate || ""),
    readyChecksPassed: numberOrNull(row.ready_candidate_checks_passed),
    readyChecksTotal: numberOrNull(row.ready_candidate_checks_total),
    readyGaps: splitPipes(row.ready_candidate_gaps),
    publicProfileStatus: clean(row.public_profile_status || ""),
    reportFile: clean(row.report_file || ""),
    reportPath: clean(row.report_path || ""),
    subcategory: deriveSubcategory(clean(row.report_path || "")),
  };
  return brand;
}

function deriveSubcategory(reportPath) {
  if (!reportPath) return "";
  const parts = reportPath.split(/[\\/]/).filter(Boolean);
  const idx = parts.findIndex((part) => part.toLowerCase().endsWith("franchises"));
  if (idx === -1) return "";
  const next = parts[idx + 1];
  if (!next || idx + 2 >= parts.length) return "";
  return next;
}

function renderRoute() {
  updateShortlistCount();
  const hash = window.location.hash || "#/";
  updateActiveNavigation(hash);
  if (hash.startsWith("#/franchises/")) {
    renderProfile(hash.replace("#/franchises/", ""));
    return;
  }
  if (hash === "#/shortlist") {
    renderShortlist();
    return;
  }
  if (hash === "#/match") {
    renderMatch();
    return;
  }
  if (hash === "#/beta-tier") {
    renderBetaTier();
    return;
  }
  if (hash === "#/pricing") {
    renderPricing();
    return;
  }
  if (hash === "#/research-queue") {
    renderResearchQueue();
    return;
  }
  if (hash === "#/franchisor-review") {
    renderFranchisorReview();
    return;
  }
  if (hash === "#/" || hash === "#/directory") {
    renderDirectory();
    return;
  }
  renderHome(hash === "#/how-it-works");
}

function updateActiveNavigation(hash) {
  const activePath = hash.startsWith("#/franchises/") ? "#/directory" : hash;
  primaryNavLinks.forEach((link) => {
    const isActive = link.getAttribute("href") === activePath;
    link.classList.toggle("is-active", isActive);
    if (isActive) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
}

function renderHome(scrollToHowItWorks = false) {
  const publicStats = getStats(state.brands);
  const portfolioStats = getStats(state.allBrands);
  const reviewedSources = publicStats.sources || "Growing";
  const categories = publicStats.categories || "Multiple";

  app.innerHTML = `
    <section class="home-hero">
      <div class="home-hero-inner">
        <div class="home-hero-copy">
          <p class="pill-label">Franchise research, made personal</p>
          <h1>Find the franchise that fits <em>your</em> life.</h1>
          <p class="home-lead">Buying a franchise is a big decision. GetFranchise turns an overwhelming search into a clear path—so you can understand your options, compare the facts, and focus on opportunities that make sense for you.</p>
          <div class="hero-actions home-hero-actions">
            <a class="primary-button home-primary-button" href="#/match">Find my franchise match</a>
            <a class="secondary-button home-secondary-button" href="#/how-it-works">See how it works</a>
          </div>
          <p class="home-reassurance"><span aria-hidden="true">✓</span> No franchise knowledge needed. Start with a few simple questions.</p>
        </div>
        <aside class="fit-preview" aria-label="Example franchise fit preview">
          <div class="fit-preview-top"><span>YOUR FIT PREVIEW</span><strong>Built around you</strong></div>
          <div class="fit-profile">
            <div class="fit-avatar" aria-hidden="true">✦</div>
            <div><strong>Starting your search</strong><p>We help turn your priorities into a practical shortlist.</p></div>
          </div>
          <div class="fit-meter"><div><span>Budget fit</span><b>Matched to your range</b></div><i><span></span></i></div>
          <div class="fit-meter"><div><span>Day-to-day fit</span><b>Based on your preferences</b></div><i><span></span></i></div>
          <div class="fit-meter"><div><span>Evidence confidence</span><b>Sources shown clearly</b></div><i><span></span></i></div>
          <a href="#/match" class="fit-preview-cta">Start your fit profile <span aria-hidden="true">→</span></a>
        </aside>
      </div>
    </section>

    <section class="home-proof" aria-label="GetFranchise research overview">
      <div><strong>${publicStats.total}</strong><span>published franchise profiles</span></div>
      <div><strong>${categories}</strong><span>categories to explore</span></div>
      <div><strong>${reviewedSources}</strong><span>reviewed source links</span></div>
      <div><strong>${portfolioStats.total}</strong><span>brands in our research universe</span></div>
    </section>

    <section class="home-section home-problem-section">
      <div class="section-kicker">A clearer way to start</div>
      <div class="home-section-heading">
        <h2>Franchise research shouldn’t feel like a second full-time job.</h2>
        <p>Most sites give you a long list of logos. We help you make sense of the decision before you spend weeks chasing the wrong opportunities.</p>
      </div>
      <div class="difference-grid">
        <article><span class="difference-number">01</span><h3>Start with yourself</h3><p>Your budget, interests, lifestyle and comfort with risk all shape what “right” looks like. Our match questionnaire makes those priorities your starting point.</p></article>
        <article><span class="difference-number">02</span><h3>See the facts, not just the pitch</h3><p>Review investment ranges, fees, categories and source links in one place. Where information is missing or estimated, we say so plainly.</p></article>
        <article><span class="difference-number">03</span><h3>Compare with confidence</h3><p>Save the opportunities worth your time, compare them side by side, and know what to ask a franchisor next.</p></article>
      </div>
    </section>

    <section id="how-it-works" class="home-section home-steps-section">
      <div class="steps-copy"><p class="eyebrow">How GetFranchise works</p><h2>From “I have no idea where to start” to a shortlist you can act on.</h2><p>Our tools are designed for first-time franchise buyers. You stay in control; we give you a smarter framework for doing the homework.</p><a class="primary-button" href="#/match">Build my fit profile</a></div>
      <ol class="steps-list">
        <li><span>1</span><div><h3>Tell us what matters</h3><p>Share your investment range, the kind of work you want to do, and what you want your future to look like.</p></div></li>
        <li><span>2</span><div><h3>Explore suitable opportunities</h3><p>Get a focused starting point, then browse franchise profiles with the details that matter to a buyer.</p></div></li>
        <li><span>3</span><div><h3>Research and compare</h3><p>Keep your shortlist organized, compare key facts, and use source links to take the next conversation further.</p></div></li>
      </ol>
    </section>

    <section class="home-section home-feature-section">
      <div class="home-section-heading feature-heading"><div><p class="eyebrow">Built for better decisions</p><h2>Everything you need to research with more clarity.</h2></div><p>We don’t promise a magic answer. We give you a transparent, practical way to narrow the field and ask better questions.</p></div>
      <div class="feature-showcase-grid">
        <article class="showcase-card showcase-card-wide"><span class="showcase-icon">⌁</span><h3>Personal fit questionnaire</h3><p>Move beyond generic “top franchise” lists. Start with signals about your capital, category interests, ownership style and risk tolerance.</p><a href="#/match">Find my match <span>→</span></a></article>
        <article class="showcase-card"><span class="showcase-icon">◫</span><h3>Side-by-side comparisons</h3><p>See opportunities next to each other instead of jumping between browser tabs and spreadsheets.</p><a href="#/shortlist">Compare my shortlist <span>→</span></a></article>
        <article class="showcase-card"><span class="showcase-icon">✓</span><h3>Source-aware profiles</h3><p>Know when a detail is supported, estimated, or still needs direct confirmation.</p><a href="#/directory">Browse profiles <span>→</span></a></article>
      </div>
    </section>

    <section class="home-section trust-section">
      <div><p class="eyebrow">Our goal</p><h2>Help every visitor leave with a better next step.</h2><p>Whether you are ready to invest or only beginning to explore, GetFranchise exists to help you identify opportunities worth a closer look—and the questions worth asking before you commit.</p></div>
      <div class="trust-points"><p><span>✓</span><strong>Transparent about what we know</strong><small>Evidence and gaps are clearly labeled.</small></p><p><span>✓</span><strong>Focused on the buyer’s fit</strong><small>Not simply the biggest or most advertised brand.</small></p><p><span>✓</span><strong>Built for Canadian research</strong><small>Profiles and next steps designed around Canadian buyers.</small></p></div>
    </section>

    <section class="home-final-cta">
      <p class="eyebrow">Your search can start here</p><h2>Find a franchise that makes sense for you.</h2><p>Take a few minutes to tell us what matters. We’ll help you turn the possibilities into a starting point you can trust.</p><div class="hero-actions"><a class="primary-button home-primary-button" href="#/match">Find my franchise match</a><a class="secondary-button home-secondary-button" href="#/directory">Explore the directory</a></div>
    </section>
  `;
  app.focus({ preventScroll: true });
  if (scrollToHowItWorks) document.querySelector("#how-it-works")?.scrollIntoView({ behavior: "smooth" });
}

function renderPricing() {
  const currentPlan = PLANS[state.plan];
  app.innerHTML = `
    <section class="pricing-hero">
      <div>
        <p class="pill-label">Straightforward access</p>
        <h1>Choose the research depth that fits your decision.</h1>
        <p>Start free, then move up only when your shortlist needs more evidence, comparison power, or source-file access.</p>
      </div>
      <aside class="pricing-trust-card">
        <span class="pricing-trust-icon" aria-hidden="true">✓</span>
        <div><strong>Clear boundaries</strong><p>Every plan spells out exactly what you can view, compare, and take with you.</p></div>
      </aside>
    </section>
    <section class="pricing-layout">
      <div class="pricing-heading">
        <div><p class="eyebrow">Plans</p><h2>Built around how you research.</h2></div>
        <p>Beta access is manually assigned to this browser profile. This preview has no accounts, billing, payment provider, or checkout.</p>
      </div>
      <div class="pricing-grid">
        ${Object.entries(PLANS).map(([key, plan]) => `
          <article class="price-card ${key === "advanced" ? "is-featured" : ""} ${state.plan === key ? "is-current" : ""}">
            ${key === "advanced" ? '<span class="popular-pill">Most popular</span>' : ""}
            <p class="eyebrow">${escapeHtml(plan.name)}</p>
            <div class="price-line"><strong>${plan.price}</strong><span>${escapeHtml(plan.cadence)}</span></div>
            <p class="price-summary">${escapeHtml(plan.summary)}</p>
            <ul class="plan-features">${plan.features.map((feature) => `<li><span aria-hidden="true">✓</span>${escapeHtml(feature)}</li>`).join("")}</ul>
            <div class="plan-card-actions">
              <span class="${state.plan === key ? "badge good" : "badge"}">${state.plan === key ? "BETA — manually assigned" : "Preview access"}</span>
              ${key === "basic" ? '<a class="secondary-button" href="#/match">Start the questionnaire</a>' : `<a class="secondary-button" href="mailto:${BUYER_EMAIL}?subject=${encodeURIComponent(`GetFranchise ${plan.name} access`)}">Request ${escapeHtml(plan.name)} access</a>`}
            </div>
          </article>
        `).join("")}
      </div>
      <section class="plan-clarity-card">
        <div><p class="eyebrow">Currently exploring</p><h3>${escapeHtml(currentPlan.name)} <span class="badge good">BETA</span></h3><p>${state.plan === "basic" ? "You can compare two brands and answer four matching questions." : state.plan === "advanced" ? "You can compare ten brands and answer nine matching questions." : "You have the complete suitability questionnaire, unlimited comparison, source trail, and CSV export."}</p></div>
        <a class="table-action" href="#/match">Find my match</a>
      </section>
    </section>
  `;
  app.focus({ preventScroll: true });
}

function renderDirectory() {
  state.filtered = applyFilters();
  const publicStats = getStats(state.brands);
  const portfolioStats = getStats(state.allBrands);
  const readyStats = getReadyValidationStats(state.allBrands);
  const backlogCount = Math.max(0, portfolioStats.total - publicStats.total);
  const categories = getCategorySummary(state.brands).slice(0, 8);
  const pageCount = Math.max(1, Math.ceil(state.filtered.length / PAGE_SIZE));
  state.page = Math.min(state.page, pageCount);
  const pageRows = state.filtered.slice((state.page - 1) * PAGE_SIZE, state.page * PAGE_SIZE);

  app.innerHTML = `
    <section class="hero-band launch-hero">
      <div class="hero-inner">
        <div>
          <p class="pill-label">Canadian franchise research</p>
          <h1>Compare ${publicStats.total} franchise profiles.</h1>
          <p class="hero-copy">
            The directory includes fully validated profiles and franchises published by the Factory. Every profile retains its source and verification boundary, while the remaining ${backlogCount}-brand portfolio stays in the research queue.
          </p>
          <div class="hero-form">
            <input id="heroSearch" type="search" value="${escapeAttr(state.query)}" placeholder="Search Subway, coffee, senior care..." aria-label="Search franchises" />
            <button class="primary-button" id="heroSearchButton">Search database</button>
          </div>
          <div class="hero-actions">
            <a class="primary-button" href="#/match">Find your franchise match</a>
            <a class="secondary-button hero-secondary" href="#/pricing">View plans &amp; pricing</a>
          </div>
          <p class="microcopy">Use the verification details on every profile before relying on a cost, fee, or availability claim.</p>
        </div>
        <aside class="at-glance-panel hero-card">
          <p class="eyebrow">Franchise directory</p>
          <dl>
            <div><dt>Directory profiles</dt><dd>${publicStats.total}</dd></div>
            <div><dt>Categories shown</dt><dd>${publicStats.categories}</dd></div>
            <div><dt>Reviewed source links</dt><dd>${publicStats.sources}</dd></div>
            <div><dt>Research backlog</dt><dd>${backlogCount}</dd></div>
          </dl>
        </aside>
      </div>
    </section>

    <section class="content-band">
      <section class="match-promo">
        <div><p class="eyebrow">Personalized starting point</p><h2>Not sure where to begin?</h2><p>Answer a short suitability questionnaire. We rank only against supported fields and clearly flag information the current records cannot assess.</p></div>
        <div class="inline-actions"><a class="primary-button" href="#/match">Take the questionnaire</a><a class="secondary-button" href="#/pricing">Compare plans</a></div>
      </section>
      <div class="intro-row">
        <div>
          <p class="eyebrow">Browse</p>
          <h2>Explore the published directory, then compare the evidence.</h2>
        </div>
        <p>Every card shows the core money fields, contact path, and proof level. Profiles that still need franchisor confirmation say so directly.</p>
      </div>

      <div class="quality-roadmap">
        <div>
          <p class="eyebrow">Data posture</p>
          <strong>Directory: ${publicStats.total} profiles. Fully validated: ${readyStats.ready}. Research backlog: ${backlogCount} records.</strong>
        </div>
        <span>Fully validated profiles pass the complete readiness check. Factory-published profiles stay clearly marked so you can see where direct confirmation is still needed.</span>
      </div>

      <div class="section-switcher" aria-label="Directory sections">
        ${SECTION_TABS.map(([value, label]) => `
          <button class="section-tab${state.section === value ? " is-active" : ""}" data-section="${escapeAttr(value)}" type="button">
            ${escapeHtml(label)}
          </button>
        `).join("")}
      </div>

      <div class="buyer-topics" aria-label="Franchise research checklist">
        ${BUYER_RESEARCH_TOPICS.map(([title, body]) => `
          <article>
            <strong>${escapeHtml(title)}</strong>
            <span>${escapeHtml(body)}</span>
          </article>
        `).join("")}
      </div>

      <div class="review-strip">
        <div>
          <p class="eyebrow">Verification loop</p>
          <h2>Email the franchisor, confirm the costs, and mark what changed.</h2>
        </div>
        <a class="primary-button" href="#/franchisor-review">Open verification queue</a>
      </div>

      <div class="filter-panel">
        <div class="filter-panel-head">
          <div>
            <p class="eyebrow">Filters</p>
            <h2>Find the right opportunity faster</h2>
          </div>
          <button class="secondary-button" id="clearFilters">Reset filters</button>
        </div>

        <div class="filter-grid">
          <div class="field search-field">
            <label for="queryInput">Search</label>
            <input id="queryInput" type="search" value="${escapeAttr(state.query)}" placeholder="Search brand, category, fee, city, email, or link" />
          </div>
          ${selectField("categorySelect", "Category", state.category, [["all", "All categories"], ...getFilterOptions("category")])}
          ${selectField("investmentSelect", "Investment", state.investment, [["all", "All investment tiers"], ...getFilterOptions("investment")])}
          ${selectField("riskSelect", "Risk", state.risk, [["all", "All risk levels"], ...getFilterOptions("risk")])}
          <div class="field">
            <label for="evidenceSelect">Evidence</label>
            <select id="evidenceSelect">${optionsHtml([["all", "All evidence grades"], ...getFilterOptions("evidenceGrade")], state.evidence)}</select>
          </div>
          <div class="field">
            <label for="ownershipSelect">Ownership</label>
            <select id="ownershipSelect">${optionsHtml([["all", "Any ownership"], ["canadian", "Canadian owned"], ["non_canadian", "Not Canadian owned"]], state.ownership)}</select>
          </div>
          <div class="field sort-field">
            <label for="sortSelect">Sort by</label>
            <select id="sortSelect">${optionsHtml([
              ["score_desc", "Best screening fit"],
              ["sources_desc", "Most source-backed"],
              ["evidence_desc", "Best evidence grade"],
              ["brand_asc", "Brand A to Z"],
              ["sources_asc", "Needs cleanup first"],
            ], state.sort)}</select>
          </div>
        </div>
      </div>

      <div class="category-rail" aria-label="Top categories">
        ${categories.map(renderCategoryCard).join("")}
      </div>

      <div class="results-header">
        <div>
          <h2>${state.filtered.length} source-backed profiles</h2>
          <p>Showing ${pageRows.length} on page ${state.page} of ${pageCount}. Click a profile for contacts, source links, and ready-candidate checks.</p>
        </div>
        <a class="clear-link" href="#/shortlist">Compare shortlist</a>
      </div>

      ${pageRows.length ? renderResults(pageRows) : renderEmpty()}
      ${renderPagination(pageCount)}
      <section class="waitlist-band">
        <div class="waitlist-heading">
          <p class="eyebrow">Early access</p>
          <h2>Get the next release.</h2>
          <p>Separate updates for buyers and franchisor teams keep launch notes relevant.</p>
        </div>
        <div class="waitlist-grid">
          <article class="waitlist-card">
            <p class="eyebrow">For buyers</p>
            <h3>I am exploring franchises to buy</h3>
            <p>Get early access to research tools, opportunity comparisons, and buyer-focused launch notes.</p>
            <a class="primary-button" href="mailto:${BUYER_EMAIL}?subject=Buyer%20early%20access%20request">Join buyer list</a>
          </article>
          <article class="waitlist-card">
            <p class="eyebrow">For brands</p>
            <h3>I am a franchisor / brand</h3>
            <p>Confirm or correct your Canadian costs, royalty, fees, territory details, and official franchise contact links.</p>
            <a class="primary-button" href="#/franchisor-review">Join brand list</a>
          </article>
        </div>
      </section>
      <p class="disclaimer">
        Public data must be confirmed directly with the franchisor and reviewed against Canadian disclosure documents, signing entities,
        franchisee interviews, unit economics, closure history, and legal records before investment use.
      </p>
    </section>
  `;

  bindDirectoryEvents();
  app.focus({ preventScroll: true });
}

function featureTile(title, body) {
  return `
    <article class="feature-tile">
      <span class="feature-icon" aria-hidden="true">${escapeHtml(title.slice(0, 1))}</span>
      <h3>${escapeHtml(title)}</h3>
      <p>${escapeHtml(body)}</p>
    </article>
  `;
}

function renderCategorySpotlight(category, title, brands) {
  const rows = brands.slice(0, 3);
  return `
    <section class="category-section">
      <div class="category-section-head">
        <h3>${escapeHtml(title)}</h3>
        <span>${rows.length ? `${rows.reduce((sum, brand) => sum + brand.sourceCount, 0)} reviewed sources` : "Coming soon"}</span>
      </div>
      <div class="category-preview-grid">
        ${rows.map((brand, index) => renderSpotlightCard(brand, category, index)).join("")}
      </div>
    </section>
  `;
}

function getSpotlightBrands(category) {
  return state.brands
    .filter((brand) => brand.category === category)
    .sort((a, b) =>
      gradeRank(b.evidenceGrade) - gradeRank(a.evidenceGrade) ||
      b.sourceCount - a.sourceCount ||
      b.verifiedCoreFeeFields - a.verifiedCoreFeeFields ||
      (b.score ?? -1) - (a.score ?? -1) ||
      a.name.localeCompare(b.name)
    )
    .slice(0, 3);
}

function renderSpotlightCard(brand, category, index) {
  return `
    <article class="spotlight-card ${index === 0 ? "is-leading" : ""}">
      <div class="brand-art">
        ${brandMark(brand)}
      </div>
      <div class="spotlight-body">
        <strong>${escapeHtml(brand.name)}</strong>
        <span>${escapeHtml(brand.cuisine || labelize(category))}</span>
        <p>${escapeHtml(brand.evidenceGrade)} evidence - ${brand.sourceCount} sources - ${brand.verifiedCoreFeeFields} fees</p>
        <a href="#/franchises/${brand.id}">View profile</a>
      </div>
    </article>
  `;
}

function renderResults(rows) {
  return `
    <div class="opportunity-grid">
      ${rows.map(renderBrandCard).join("")}
    </div>
    <details class="table-shell data-detail">
      <summary>Open compact data table</summary>
      <table class="brand-table">
        <thead>
          <tr>
            <th>Brand</th>
            <th>Investment</th>
            <th>Fee</th>
            <th>Royalty</th>
            <th>Liquid capital</th>
            <th>Contact</th>
            <th>Proof</th>
            <th><span class="visually-hidden">Shortlist</span></th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(renderBrandRow).join("")}
        </tbody>
      </table>
    </details>
  `;
}

function renderBrandRow(brand) {
  return `
    <tr>
      <td>
        <div class="brand-cell">
          ${brandMark(brand)}
          <span>
            <a class="brand-title" href="#/franchises/${brand.id}">${escapeHtml(brand.name)}</a>
            <span class="brand-meta">${escapeHtml(labelize(brand.category))} - ${escapeHtml(brand.industry)}</span>
          </span>
        </div>
      </td>
      <td>${escapeHtml(preferredInvestmentLabel(brand))}</td>
      <td>${escapeHtml(simpleValue(brand.franchiseFee))}</td>
      <td>${escapeHtml(simpleValue(brand.royalty))}</td>
      <td>${escapeHtml(simpleValue(brand.liquidCapital))}</td>
      <td>${contactActionHtml(brand, "table-action")}</td>
      <td>${badge(verificationStatusLabel(brand), verificationBadgeClass(brand))}</td>
      <td><button class="icon-button shortlist-toggle" data-id="${brand.id}" title="${shortlistTitle(brand)}" aria-label="${shortlistTitle(brand)}">${state.shortlist.has(brand.id) ? "*" : "+"}</button></td>
    </tr>
  `;
}

function renderBrandCard(brand) {
  const proofLabel = dataQualityLabel(brand);
  const coreFees = `${brand.verifiedCoreFeeFields}/5 fees`;
  return `
    <article class="brand-card">
      <div class="card-top">
        ${brandMark(brand)}
        <div>
          <a class="brand-title" href="#/franchises/${brand.id}">${escapeHtml(brand.name)}</a>
          <div class="card-meta-row">
            <span class="brand-meta">${escapeHtml(labelize(brand.category))}</span>
            ${badge(proofLabel, dataQualityClass(brand))}
          </div>
        </div>
        <button class="icon-button shortlist-toggle" data-id="${brand.id}" title="${shortlistTitle(brand)}" aria-label="${shortlistTitle(brand)}">${state.shortlist.has(brand.id) ? "*" : "+"}</button>
      </div>

      <div class="investment-callout">
        <span>Starting investment</span>
        <strong>${escapeHtml(preferredInvestmentLabel(brand))}</strong>
      </div>

      <div class="card-actions">
        <span>${escapeHtml(coreFees)} verified</span>
        <a class="table-action" href="#/franchises/${brand.id}">View profile</a>
      </div>
    </article>
  `;
}

function renderProfile(id) {
  const brand = state.brands.find((item) => item.id === id);
  if (!brand) {
    app.innerHTML = `<section class="empty-state"><h1>Profile not found</h1><p class="note">This brand is not in the current research export.</p><p><a class="primary-button" href="#/directory">Back to directory</a></p></section>`;
    return;
  }

  const sources = [...brand.officialSources, ...brand.governmentSources];
  const contactLinks = getContactLinks(brand);
  const contactEmail = getContactEmail(brand);
  const readyValidation = getReadyCandidateValidation(brand);
  const canViewDeepAnalysis = state.plan !== "basic";
  app.innerHTML = `
    <section class="profile-hero">
      <div class="profile-hero-inner">
        <div>
          <a class="clear-link" href="#/directory">Back to directory</a>
          <div class="profile-heading">
            ${brandMark(brand)}
            <div>
              <p class="eyebrow">${escapeHtml(labelize(brand.category))}</p>
              <h1>${escapeHtml(brand.name)}</h1>
            </div>
          </div>
          <div class="profile-meta">
            ${badge(brand.investment)}
            ${badge(verificationStatusLabel(brand), verificationBadgeClass(brand))}
            ${badge(`${brand.verifiedCoreFeeFields}/5 money fields`)}
            ${badge(`${brand.sourceCount} sources`)}
                      ${badge(readyValidation.passed ? "Source-backed" : "Readiness gaps", readyValidation.passed ? "good" : "warn")}
          </div>
        </div>
        <div class="profile-actions">
          <button class="primary-button shortlist-toggle" data-id="${brand.id}">${state.shortlist.has(brand.id) ? "Remove from shortlist" : "Add to shortlist"}</button>
          ${contactActionHtml(brand, "secondary-button")}
          ${draftActionHtml(brand, "secondary-button")}
        </div>
      </div>
    </section>

    <section class="profile-grid">
      <div class="profile-card profile-verdict">
        <h2>Buyer Snapshot</h2>
        <div class="snapshot-grid snapshot-grid-wide">
          ${miniField("Screening fit", brand.score === null ? "n/a" : `${brand.score}/100`)}
          ${miniField("Risk", brand.risk)}
          ${miniField("Confidence", brand.confidence)}
          ${miniField("Growth outlook", brand.growth)}
          ${miniField("Investment tier", brand.investment)}
          ${miniField("Research status", verificationStatusLabel(brand))}
        </div>
        <p class="note">${escapeHtml(brand.goalFit)}</p>
      </div>

      <div class="profile-card">
        <h2>Core Cost & Fee Facts</h2>
        <div class="essentials-grid">
          ${detailItem("Total investment", brand.totalInvestment)}
          ${detailItem("Franchise fee", brand.franchiseFee)}
          ${detailItem("Royalty", brand.royalty)}
          ${detailItem("Marketing fund", brand.marketing)}
          ${detailItem("Liquid capital", brand.liquidCapital)}
          ${detailItem("Investment fit", brand.investment)}
        </div>
      </div>

      <aside class="profile-card calm-summary-card">
        <h2>Quick Read</h2>
        <div class="quick-read-list">
          ${quickReadItem("Money clarity", `${brand.verifiedCoreFeeFields}/5 core fee fields verified`)}
          ${quickReadItem("Source depth", `${brand.sourceCount} total sources, ${brand.officialCount} official`)}
          ${quickReadItem("Contact path", contactSummary(brand))}
          ${quickReadItem("Buyer posture", brand.posture)}
          ${quickReadItem("Ready validation", `${readyValidation.passedCount}/${readyValidation.total} checks passed`)}
        </div>
      </aside>

      ${canViewDeepAnalysis ? `
      <div class="profile-card">
        <h2>Operating Requirements</h2>
        <div class="essentials-grid">
          ${detailItem("Number of locations", brand.numberOfLocations)}
          ${detailItem("Time to open", brand.averageTimeToOpen)}
          ${detailItem("Training provided", brand.trainingProvided)}
          ${detailItem("Location / territory", brand.locationRequirements)}
          ${detailItem("Founded", brand.founded)}
          ${detailItem("Headquarters", brand.headquarters)}
          ${detailItem("Canadian owned", brand.canadianOwned)}
          ${detailItem("Cuisine / service", brand.cuisine)}
        </div>
      </div>

      <aside class="profile-card">
        <h2>Contact & Links</h2>
        <div class="status-panel ${verificationStatusClass(brand)}">
          <strong>${escapeHtml(verificationStatusLabel(brand))}</strong>
          <span>${escapeHtml(verificationStatusDetail(brand))}</span>
        </div>
        <div class="contact-list">
          ${contactEmail ? `<a href="mailto:${escapeAttr(contactEmail)}">${escapeHtml(contactEmail)}</a>` : `<span>Franchisor email needed: no public direct email found in current research.</span>`}
          ${contactLinks.length ? contactLinks.map((link) => `<a href="${escapeAttr(link)}" target="_blank" rel="noreferrer">${escapeHtml(link)}</a>`).join("") : `<span>No official contact link in current research data.</span>`}
          ${draftActionHtml(brand, "contact-link")}
        </div>
      </aside>

      <aside class="profile-card">
        <h2>Proof Level</h2>
        <div class="snapshot-grid">
          ${miniField("Evidence grade", brand.evidenceGrade)}
          ${miniField("Total sources", brand.sourceCount)}
          ${miniField("Official links", brand.officialCount)}
          ${miniField("Legal sources", brand.governmentCount)}
          ${miniField("Ready checks", `${readyValidation.passedCount}/${readyValidation.total}`)}
        </div>
      </aside>

      <div class="profile-card">
        <h2>Ready Candidate Validation</h2>
        ${renderValidationChecklist(brand)}
      </div>

      <div class="profile-card correction-card">
        <h2>Verification Needed</h2>
        <p class="note">Before a buyer relies on this profile, GetFranchise needs the franchisor to confirm the current Canadian franchise package, fee schedule, territory rules, training, support, and disclosure status.</p>
        <div class="correction-actions">
          ${draftActionHtml(brand, "primary-button")}
          <a class="secondary-button" href="#/franchisor-review">Open verification queue</a>
        </div>
      </div>

      <div class="profile-card">
        <h2>What To Confirm</h2>
        ${renderNeedsImprovement(brand)}
      </div>

      <aside class="profile-card">
        <h2>Pros and Cons</h2>
        <div class="split-list">
          <div>
            <h3>Pros</h3>
            <ul class="gap-list">
              ${(brand.pros.length ? brand.pros : brand.topPraises.length ? brand.topPraises : ["Not stated"]).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
            </ul>
          </div>
          <div>
            <h3>Cons</h3>
            <ul class="gap-list con-list">
              ${(brand.cons.length ? brand.cons : brand.topComplaints.length ? brand.topComplaints : ["Not stated"]).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
            </ul>
          </div>
        </div>
      </aside>

      <div class="profile-card">
        <h2>Financial Performance</h2>
        <p class="note">${escapeHtml(simpleValue(brand.profitabilityIndicators))}</p>
      </div>

      <div class="profile-card">
        <h2>Disclosure & Cross-Border Notes</h2>
        <div class="detail-grid">
          ${detailItem("FDD / disclosure", brand.fddSummary)}
          ${detailItem("Cross-border caution", brand.crossBorderCaution)}
          ${detailItem("Research track", labelize(brand.researchTrack))}
          ${detailItem("Rejected fields", brand.rejectedFields)}
        </div>
      </div>

      <aside class="profile-card">
        <h2>Market & Growth</h2>
        <div class="split-list">
          ${detailItem("Growth trends", brand.growthTrends)}
          ${detailItem("Market saturation", brand.saturation)}
          ${detailItem("Threat level", brand.threat)}
          ${detailItem("Operations difficulty", brand.operations)}
        </div>
      </aside>

      <div class="profile-card">
        <h2>Franchisee Validation</h2>
        <p class="note">${escapeHtml(simpleValue(brand.ownerReviews))}</p>
      </div>

      <div class="profile-card">
        <h2>Buyer Notes</h2>
        <p class="note">${escapeHtml(brand.posture)}</p>
      </div>
      ` : `
      <div class="profile-card profile-verdict deep-analysis-preview">
        <div class="feature-lock"><span aria-hidden="true">⌁</span><div><strong>Advanced deep analysis</strong><p>Compare operational requirements, validation gaps, performance context, market risk, and buyer notes side-by-side with Advanced.</p><a class="table-action" href="#/pricing">Unlock Advanced · $10/mo</a></div></div>
      </div>
      `}

      <aside class="profile-card">
        <h2>Public Source Links</h2>
        ${
          sources.length
            ? `<ul class="source-list">${sources.map((source) => `<li><a href="${escapeAttr(source)}" target="_blank" rel="noreferrer">${escapeHtml(source)}</a></li>`).join("")}</ul><p class="note">These links support the public screening record. Confirm current Canadian terms directly with the franchisor.</p>`
            : `<p class="note">No public source links were included in this export. This profile should remain in the research queue.</p>`
        }
      </aside>

      <div class="profile-card report-card">
        <div class="card-heading-row">
          <h2>Research Record Boundary</h2>
        </div>
        <p class="note">Original research workpapers are kept out of the public preview. Buyer-facing claims must be supported by the linked public sources above; they are not replaced by a paid-access lock.</p>
      </div>
    </section>
  `;
  bindShortlistButtons();
  app.focus({ preventScroll: true });
}

function renderFranchisorReview() {
  const publicStats = getStats(state.brands);
  const outreachOpen = publicStats.readyCandidates >= OUTREACH_MINIMUM_READY_CANDIDATES;
  const outreachRows = getOutreachRows();
  app.innerHTML = `
    <section class="review-hero">
      <div class="review-hero-inner">
        <a class="clear-link" href="#/directory">Back to directory</a>
        <p class="eyebrow">${outreachOpen ? "Verification queue" : "Outreach held"}</p>
        <h1>${outreachOpen ? "Turn public research into confirmed franchise data." : "Build 100 ready candidates before contacting franchisors."}</h1>
        <p class="hero-copy">${outreachOpen ? "Use each brand's own franchise email when available. If no public email is in the dataset, open the official franchise link and add the correct development contact before drafting outreach." : `This workspace currently has ${publicStats.readyCandidates} ready candidates. Research and source verification remain the priority; franchisor contact opens only after ${OUTREACH_MINIMUM_READY_CANDIDATES} candidates meet the hard readiness gate.`}</p>
      </div>
    </section>

    <section class="review-layout">
      <div class="review-summary">
        <div>${miniField("Research profiles", publicStats.total)}</div>
        <div>${miniField("Ready candidates", `${publicStats.readyCandidates}/${OUTREACH_MINIMUM_READY_CANDIDATES}`)}</div>
        <div>${miniField("Still required", Math.max(0, OUTREACH_MINIMUM_READY_CANDIDATES - publicStats.readyCandidates))}</div>
        <div>${miniField("Direct emails", publicStats.emails)}</div>
        <div>${miniField("Email needed", outreachRows.filter((row) => !row.email).length)}</div>
      </div>

      <div class="review-panel">
        <h2>Buyer Research Checklist</h2>
        <div class="buyer-topics compact">
          ${BUYER_RESEARCH_TOPICS.map(([title, body]) => `
            <article>
              <strong>${escapeHtml(title)}</strong>
              <span>${escapeHtml(body)}</span>
            </article>
          `).join("")}
        </div>
      </div>

      ${outreachOpen ? `
        <div class="review-panel">
          <h2>Outreach Queue</h2>
          <div class="table-shell outreach-shell">
            <table class="brand-table outreach-table">
              <thead>
                <tr>
                  <th>Brand</th>
                  <th>Email</th>
                  <th>Link</th>
                  <th>Status</th>
                  <th>Draft</th>
                </tr>
              </thead>
              <tbody>
                ${outreachRows.map(renderOutreachRow).join("")}
              </tbody>
            </table>
          </div>
        </div>

        <div class="review-panel">
          <h2>Email Submission</h2>
          <p class="note">Send the draft to the brand's franchise-development email only. Ask them to confirm the current Canadian costs, ongoing fees, territory rules, support, disclosure package, and the best official contact link.</p>
          <div class="correction-actions">
            <a class="primary-button" href="${escapeAttr(generalCorrectionMailto())}">Submit correction to GetFranchise</a>
            <a class="secondary-button" href="#/directory">Browse profiles</a>
          </div>
        </div>` : `
        <div class="review-panel">
          <h2>Outreach gate</h2>
          <p class="note">Do not draft, send, or log franchisor outreach until 100 candidates pass the readiness checks. Use the internal research queue to add official sources and complete the five core money fields first.</p>
          <div class="correction-actions"><a class="secondary-button" href="#/research-queue">Open research queue</a></div>
        </div>`}
    </section>
  `;
  if (outreachOpen) bindOutreachControls();
  app.focus({ preventScroll: true });
}

function renderResearchQueue() {
  const rows = getResearchQueueRows();
  const stats = getResearchQueueStats();
  const visibleRows = rows.slice(0, RESEARCH_QUEUE_LIMIT);

  app.innerHTML = `
    <section class="review-hero">
      <div class="review-hero-inner">
        <a class="clear-link" href="#/directory">Back to directory</a>
        <p class="eyebrow">Internal research queue</p>
        <h1>Upgrade the 484-brand portfolio carefully.</h1>
        <p class="hero-copy">Use this workspace to rebuild weak records, verify fee fields, add legal/entity checks, and decide which profiles are ready for the public directory.</p>
      </div>
    </section>

    <section class="review-layout research-layout">
      <div class="review-summary snapshot-grid-wide">
        <div>${miniField("Total records", stats.total)}</div>
        <div>${miniField("Public now", stats.publicNow)}</div>
        <div>${miniField("Zero-source", stats.zeroSource)}</div>
        <div>${miniField("Thin evidence", stats.thinEvidence)}</div>
        <div>${miniField("Fee gaps", stats.feeGaps)}</div>
        <div>${miniField("Ready candidates", stats.readyCandidates)}</div>
      </div>

      <div class="review-panel">
        <div class="card-heading-row">
          <div>
            <p class="eyebrow">Filters</p>
            <h2>Pick the next careful batch</h2>
          </div>
          <button class="secondary-button" id="clearResearchFilters">Reset queue</button>
        </div>
        <div class="research-filter-grid">
          <div class="field search-field">
            <label for="researchQueryInput">Search</label>
            <input id="researchQueryInput" type="search" value="${escapeAttr(state.researchQuery)}" placeholder="Search brand, category, fees, source links, or gaps" />
          </div>
          ${selectField("researchCategorySelect", "Category", state.researchCategory, [["all", "All categories"], ...getAllCategoryOptions()])}
          ${selectField("researchNeedSelect", "Need", state.researchNeed, [
            ["priority", "Priority work"],
            ["source_rebuild", "Source rebuild"],
            ["fee_verification", "Fee verification"],
            ["legal_entity", "Legal/entity check"],
            ["outreach", "Franchisor outreach"],
            ["public_candidates", "Public candidates"],
            ["all", "Everything"],
          ])}
          ${selectField("researchStageSelect", "Stage", state.researchStage, [["all", "Any stage"], ...researchStageOptions()])}
        </div>
      </div>

      <div class="review-panel research-method">
        <h2>Batch Rules</h2>
        <div class="buyer-topics compact">
          <article><strong>10 at a time</strong><span>Keep every batch small enough to review by hand before regenerating exports.</span></article>
          <article><strong>5-8 sources</strong><span>Prefer official Canadian pages, CFA, legal/entity records, and current franchisor materials.</span></article>
          <article><strong>No guesses</strong><span>Exact costs need a source. Missing Canadian terms stay marked as not publicly available.</span></article>
          <article><strong>Promote slowly</strong><span>A record enters the public set only when it beats an existing public profile on source quality.</span></article>
        </div>
      </div>

      <div class="review-panel">
        <div class="card-heading-row">
          <div>
            <h2>${rows.length} matching records</h2>
            <p class="note">Showing the first ${visibleRows.length}. Stage changes are saved in this browser only.</p>
          </div>
          <a class="secondary-button" href="../docs/484_BRAND_RESEARCH_ROADMAP.md" target="_blank" rel="noreferrer">Open roadmap</a>
        </div>
        <div class="table-shell research-table-shell">
          <table class="brand-table research-table">
            <thead>
              <tr>
                <th>Brand</th>
                <th>Need</th>
                <th>Evidence</th>
                <th>Money</th>
                <th>Sources</th>
                <th>Stage</th>
                <th>Next action</th>
              </tr>
            </thead>
            <tbody>
              ${visibleRows.map(renderResearchQueueRow).join("")}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  `;

  bindResearchQueueEvents();
  app.focus({ preventScroll: true });
}

function renderResearchQueueRow(item) {
  const brand = item.brand;
  const validation = getReadyCandidateValidation(brand);
  const profileHref = state.brands.some((row) => row.id === brand.id) ? `#/franchises/${brand.id}` : "";
  return `
    <tr>
      <td>
        <div class="brand-cell">
          ${brandMark(brand)}
          <span>
            ${profileHref ? `<a class="brand-title" href="${profileHref}">${escapeHtml(brand.name)}</a>` : `<strong class="brand-title">${escapeHtml(brand.name)}</strong>`}
            <span class="brand-meta">${escapeHtml(labelize(brand.category))}</span>
          </span>
        </div>
      </td>
      <td>${badge(item.needLabel, researchNeedBadgeClass(item.need))}</td>
      <td>${escapeHtml(brand.evidenceGrade)} / ${brand.sourceCount} sources<br><span class="muted">${validation.passedCount}/${validation.total} ready checks</span></td>
      <td>${brand.verifiedCoreFeeFields}/5 fees</td>
      <td>${brand.officialCount} official / ${brand.governmentCount} legal</td>
      <td>
        <select class="status-select research-stage-select" data-id="${escapeAttr(brand.id)}" aria-label="Research stage for ${escapeAttr(brand.name)}">
          ${optionsHtml(researchStageOptions(), item.stage)}
        </select>
      </td>
      <td>
        <div class="research-actions">
          <span>${escapeHtml(item.nextAction)}</span>
        </div>
      </td>
    </tr>
  `;
}

function bindResearchQueueEvents() {
  const ids = ["researchQueryInput", "researchCategorySelect", "researchNeedSelect", "researchStageSelect"];
  ids.forEach((id) => {
    const element = document.querySelector(`#${id}`);
    if (!element) return;
    element.addEventListener("input", syncResearchFilters);
    element.addEventListener("change", syncResearchFilters);
  });
  const clear = document.querySelector("#clearResearchFilters");
  if (clear) {
    clear.addEventListener("click", () => {
      Object.assign(state, {
        researchQuery: "",
        researchCategory: "all",
        researchNeed: "priority",
        researchStage: "all",
      });
      renderResearchQueue();
    });
  }
  document.querySelectorAll(".research-stage-select").forEach((select) => {
    select.addEventListener("change", () => {
      const saved = readResearchStatuses();
      saved[select.dataset.id] = select.value;
      localStorage.setItem(RESEARCH_STORAGE_KEY, JSON.stringify(saved));
      renderResearchQueue();
    });
  });
}

function syncResearchFilters(event) {
  const target = event.target;
  const activeId = target.id;
  const cursor = typeof target.selectionStart === "number" ? target.selectionStart : null;
  if (target.id === "researchQueryInput") state.researchQuery = target.value;
  if (target.id === "researchCategorySelect") state.researchCategory = target.value;
  if (target.id === "researchNeedSelect") state.researchNeed = target.value;
  if (target.id === "researchStageSelect") state.researchStage = target.value;
  renderResearchQueue();
  const nextActive = document.querySelector(`#${activeId}`);
  if (nextActive) {
    nextActive.focus({ preventScroll: true });
    if (cursor !== null && "setSelectionRange" in nextActive) {
      nextActive.setSelectionRange(cursor, cursor);
    }
  }
}

function getShortlistStats(rows) {
  const scores = rows.map((brand) => brand.score).filter((score) => Number.isFinite(score));
  return {
    selected: rows.length,
    ready: rows.filter(isPublicCandidate).length,
    sources: rows.reduce((sum, brand) => sum + brand.sourceCount, 0),
    emails: rows.filter((brand) => getContactEmail(brand)).length,
    averageScore: scores.length ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length) : "n/a",
  };
}

/* Matching and tier-aware comparison ------------------------------------------------ */
function tierQuestionnaire() {
  return QUESTIONNAIRE.slice(0, TIER_QUESTION_COUNTS[state.plan]);
}

function renderMatch() {
  const questions = tierQuestionnaire();
  state.matchStep = Math.max(0, Math.min(state.matchStep, questions.length - 1));
  const question = questions[state.matchStep];
  const answered = questions.filter((item) => hasAnswer(state.match.answers[item.id])).length;
  const complete = answered === questions.length;
  app.innerHTML = `
    <section class="shortlist-layout match-layout">
      <p class="eyebrow">Suitability profile <span class="badge good">BETA — ${escapeHtml(PLANS[state.plan].name)}</span></p>
      <h1>Find your franchise match</h1>
      <p class="note">Questionnaire v${QUESTIONNAIRE_VERSION}. Answers stay in this browser. Your ownership-style answers shape the profile; only fields supported by the current export affect a franchise score.</p>
      <div class="match-progress"><span>Question ${state.matchStep + 1} of ${questions.length}</span><progress value="${answered}" max="${questions.length}"></progress><strong>${Math.round((answered / questions.length) * 100)}%</strong></div>
      <article class="question-card">
        <p class="eyebrow">${question.contextOnly ? "Ownership style" : "Maps to"}: ${escapeHtml(question.mapsTo)}</p>
        <h2>${escapeHtml(question.text)}</h2>
        ${renderQuestionControl(question, state.match.answers[question.id])}
        <div class="shortlist-actions">
          <button class="secondary-button" id="matchBack" ${state.matchStep === 0 ? "disabled" : ""}>Back</button>
          <div class="inline-actions"><button class="secondary-button" id="matchSave">Save answer</button><button class="primary-button" id="matchNext">${state.matchStep === questions.length - 1 ? "See matches" : "Next"}</button></div>
        </div>
      </article>
      ${complete ? renderMatchResults() : `<p class="note">Complete all ${questions.length} available questions to see a ranked starting point.</p>`}
    </section>`;
  bindMatchControls(questions, question);
  if (complete) document.querySelector(".match-results")?.insertAdjacentHTML("afterbegin", renderOwnershipStyle());
}

function renderOwnershipStyle() {
  const dimensions = [
    ["Decision style", state.match.answers.decision_pace || state.match.answers.decision_process],
    ["Operating rhythm", state.match.answers.routine_preference],
    ["Leadership role", state.match.answers.leadership_preference],
    ["Customer involvement", state.match.answers.customer_interaction],
    ["Growth horizon", state.match.answers.multiunit_timing || state.match.answers.exit_horizon],
    ["Diligence readiness", state.match.answers.disclosure_review || state.match.answers.franchisee_interviews],
  ].filter(([, value]) => hasAnswer(value));
  if (!dimensions.length) return "";
  return `<section class="ownership-style-card"><p class="eyebrow">Your ownership style</p><h2>Use this as a decision brief</h2><p class="note">These are your stated preferences, not a personality score or a recommendation.</p><div class="decision-lens-grid">${dimensions.map(([label, value]) => `<article><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`).join("")}</div></section>`;
}

function renderQuestionControl(question, answer) {
  if (question.type === "text") return `<textarea id="matchAnswer" rows="4" placeholder="Optional context">${escapeHtml(answer || "")}</textarea>`;
  if (question.type === "number") return `<input id="matchAnswer" type="number" min="0" step="1000" inputmode="numeric" value="${escapeAttr(answer || "")}" placeholder="CAD amount" />`;
  if (question.type === "slider") {
    const value = String(answer || "3").match(/\d/)?.[0] || "3";
    return `<div class="slider-control"><input id="matchAnswer" type="range" min="1" max="5" value="${value}" /><output id="sliderOutput">${escapeHtml(question.options[Number(value) - 1])}</output></div>`;
  }
  if (question.type === "multi-select") {
    const selected = Array.isArray(answer) ? answer : [];
    return `<div class="option-grid">${question.options.map((option) => `<label><input type="checkbox" name="matchAnswer" value="${escapeAttr(option)}" ${selected.includes(option) ? "checked" : ""} /> <span>${escapeHtml(option)}</span></label>`).join("")}</div>`;
  }
  return `<div class="option-grid">${question.options.map((option) => `<label><input type="radio" name="matchAnswer" value="${escapeAttr(option)}" ${answer === option ? "checked" : ""} /> <span>${escapeHtml(option)}</span></label>`).join("")}</div>`;
}

function readRenderedAnswer(question) {
  if (["text", "number", "slider"].includes(question.type)) return document.querySelector("#matchAnswer")?.value?.trim() || "";
  const selected = [...document.querySelectorAll('input[name="matchAnswer"]:checked')].map((input) => input.value);
  return question.type === "multi-select" ? selected : (selected[0] || "");
}

function bindMatchControls(questions, question) {
  const save = () => { state.match.answers[question.id] = readRenderedAnswer(question); saveMatch(); };
  document.querySelector("#matchSave")?.addEventListener("click", () => { save(); showToast("Answer saved locally.", "View plans"); });
  document.querySelector("#matchBack")?.addEventListener("click", () => { save(); state.matchStep -= 1; renderMatch(); });
  document.querySelector("#matchNext")?.addEventListener("click", () => { save(); if (state.matchStep < questions.length - 1) { state.matchStep += 1; renderMatch(); } else renderMatch(); });
  document.querySelector("#matchAnswer[type=range]")?.addEventListener("input", (event) => { document.querySelector("#sliderOutput").textContent = question.options[Number(event.target.value) - 1]; });
}

function renderMatchResults() {
  const categories = state.match.answers.preferred_category;
  const candidates = Array.isArray(categories) && categories.length ? state.brands.filter((brand) => categoryFit(categories, brand.category) > 0) : state.brands;
  const rows = candidates.map((brand) => ({ brand, result: questionnaireMatch(brand) }))
    .sort((a, b) => b.result.score - a.result.score || gradeRank(b.brand.evidenceGrade) - gradeRank(a.brand.evidenceGrade) || b.brand.sourceCount - a.brand.sourceCount || a.brand.name.localeCompare(b.brand.name))
    .slice(0, 10);
  const upgrade = state.plan === "basic" ? "You’ve found a focused starting point. Upgrade to Advanced to answer five more questions about capital, experience, growth, risk, and timing." : state.plan === "advanced" ? "Unlock Premium for the complete suitability profile, including operating style, territory, evidence, and decision-priority questions." : "Your complete suitability profile is applied to these results.";
  return `<section class="match-results"><h2>Your ranked starting point</h2><p class="note">${escapeHtml(upgrade)}</p>${rows.length ? rows.map(({ brand, result }) => `<article class="match-result"><div><strong>${escapeHtml(brand.name)}</strong><span>${escapeHtml(labelize(brand.category))}</span></div><b>${result.score}/100 match</b><p>${escapeHtml(matchExplanation(result))}</p><a class="table-action" href="#/franchises/${brand.id}">Profile</a></article>`).join("") : `<p class="note">No current public profiles match the categories you selected.</p>`}</section>`;
}

function matchExplanation(result) {
  const unavailable = result.details.filter((detail) => detail.status === "unavailable").length;
  const matched = result.details.filter((detail) => detail.fit > 0).slice(0, 2).map((detail) => detail.label);
  return matched.length ? `Supported fit: ${matched.join("; ")}.${unavailable ? ` ${unavailable} answered item${unavailable === 1 ? " is" : "s are"} unavailable to assess.` : ""}` : "No supported positive fit could be established from the currently mapped fields.";
}

function questionnaireMatch(brand) {
  const details = tierQuestionnaire().filter((question) => hasAnswer(state.match.answers[question.id])).map((question) => assessQuestion(question, state.match.answers[question.id], brand));
  const denominator = details.filter((detail) => !detail.contextOnly).reduce((sum, detail) => sum + detail.weight, 0);
  const numerator = details.reduce((sum, detail) => sum + detail.weight * detail.fit * detail.confidence, 0);
  return { score: denominator ? Math.round((numerator / denominator) * 100) : 0, details, denominator };
}

function assessQuestion(question, answer, brand) {
  const unavailable = (label = question.text) => ({ label, weight: question.weight, fit: 0, confidence: 0, status: "unavailable" });
  const assessed = (fit, value, label = question.text) => {
    if (!isPubliclyUseful(value)) return unavailable(label);
    const status = /estimate|estimated|approx/i.test(String(value)) ? "estimated" : "supported";
    const confidence = status === "estimated" ? 0.6 : recordConfidenceMultiplier(brand);
    return { label, weight: question.weight, fit, confidence, status };
  };
  if (question.contextOnly) return { label: question.text, weight: 0, fit: 0, confidence: 0, status: "context", contextOnly: true };
  const text = (value) => String(value || "").toLowerCase();
  const selected = Array.isArray(answer) ? answer : [answer];
  switch (question.id) {
    case "investment_budget": return assessed(budgetFit(answer, brand.totalInvestment), brand.totalInvestment, "initial investment");
    case "preferred_category": return assessed(categoryFit(selected, brand.category), brand.category, "preferred category");
    case "liquid_capital": return assessed(budgetFit(answer, brand.liquidCapital, true), brand.liquidCapital, "liquid capital");
    case "ownership_preference": return answer === "Either" ? assessed(1, brand.canadianOwned, "ownership") : assessed(answer === "Canadian-owned" ? (/^yes/i.test(brand.canadianOwned) ? 1 : 0) : (/^yes/i.test(brand.canadianOwned) ? 0 : 1), brand.canadianOwned, "ownership");
    case "risk_preference": return assessed(riskFit(Number(String(answer)[0]), brand.risk), brand.risk, "risk tolerance");
    case "growth_goal": case "brand_maturity": case "unit_count_preference": case "expansion_appetite": return assessed(networkFit(question.id, answer, brand.numberOfLocations), brand.numberOfLocations, "network size");
    case "launch_timeline": return assessed(timelineFit(answer, brand.averageTimeToOpen), brand.averageTimeToOpen, "launch timeline");
    case "territory_priority": case "local_competition": return assessed(saturationFit(question, answer, brand.saturation), brand.saturation, "market saturation");
    case "staffing_tolerance": case "hours_preference": case "food_operations_tolerance": case "operating_role": return assessed(operationFit(question, answer, brand), brand.operations, "operational difficulty");
    case "training_need": return assessed(trainingFit(answer, brand.trainingProvided), brand.trainingProvided, "training");
    case "fee_sensitivity": return assessed(feeFit(answer, brand), feeValueForQuestion(answer, brand), "ongoing cost");
    case "revenue_evidence_priority": case "evidence_tolerance": case "customer_reputation_priority": case "franchisee_validation_priority": return assessed(evidenceFit(question, answer, brand), brand.evidenceGrade, "evidence quality");
    case "deal_breakers": return assessed(dealBreakerFit(selected, brand), dealBreakerValue(selected, brand), "deal breakers");
    case "review_priority": return assessed(reviewPriorityFit(answer, brand), reviewPriorityValue(answer, brand), "review priority");
    case "additional_context": return { label: question.text, weight: question.weight, fit: 0, confidence: 0, status: "context", contextOnly: true };
    // The checked-in export has no field that can responsibly map these prompts.
    default: return unavailable();
  }
}

function recordConfidenceMultiplier(brand) { return brand.sourceCount > 0 && brand.officialCount > 0 ? 1 : brand.sourceCount > 0 ? 0.6 : 0; }
function hasAnswer(value) { return Array.isArray(value) ? value.length > 0 : String(value || "").trim() !== ""; }
function categoryFit(values, category) { const map = { "Food service": ["beverage_dessert", "limited_service", "full_service"], "Home services": ["home_services"], "Senior care": ["senior_care"], "Child services": ["child_services"], "Pet services": ["pet_services"], "Automotive": ["automotive"], "Fitness": ["fitness"], "Education": ["education"], "Finance": ["finance"], "Real estate": ["real_estate"], "Shipping & printing": ["shipping_printing"] }; return values.some((value) => (map[value] || []).includes(category)) ? 1 : 0; }
function budgetFit(answer, value, liquid = false) { const cap = { "Under $150k": 150000, "$150k–$300k": 300000, "$300k–$500k": 500000, "$500k–$1m": 1000000, "Over $1m": Infinity, "Under $75k": 75000, "$75k–$150k": 150000, "$150k–$300k": 300000, "$300k–$500k": 500000, "Over $500k": Infinity }[answer]; if (!cap || !isPubliclyUseful(value)) return 0; const money = firstMoney(value); return Number.isFinite(money) ? (liquid ? (money <= cap ? 1 : 0) : (money <= cap ? 1 : 0)) : 0; }
function firstMoney(value) { const match = String(value).replace(/,/g, "").match(/\$?\s*(\d+(?:\.\d+)?)\s*([mk])?/i); if (!match) return null; return Number(match[1]) * (match[2]?.toLowerCase() === "m" ? 1000000 : match[2]?.toLowerCase() === "k" ? 1000 : 1); }
function riskFit(preference, risk) { if (!preference || !isPubliclyUseful(risk)) return 0; const level = /low/i.test(risk) ? 1 : /medium/i.test(risk) ? 3 : /high/i.test(risk) ? 5 : 0; return level && Math.abs(level - preference) <= 2 ? 1 : 0; }
function networkFit(id, answer, value) { const n = firstMoney(value); if (!Number.isFinite(n)) return 0; if (id === "unit_count_preference") return (answer === "Under 25 units" && n < 25) || (answer === "25–100" && n >= 25 && n <= 100) || (answer === "100–500" && n > 100 && n <= 500) || (answer === "Over 500" && n > 500) || answer === "No preference" ? 1 : 0; if (id === "brand_maturity") return answer === "No preference" ? 1 : (answer === "Established network" ? n >= 100 : answer === "Growing network" ? n >= 25 && n < 500 : n < 100 ? 1 : 0); return answer === "One stable unit" || answer === "No" ? 1 : n >= 25 ? 1 : 0; }
function timelineFit(answer, value) { const months = String(value).match(/(\d+)\s*(?:month|mo)/i); if (!months) return 0; const n = Number(months[1]); if (answer === "Within 6 months") return n <= 6 ? 1 : 0; if (answer === "6–12 months") return n >= 6 && n <= 12 ? 1 : 0; if (answer === "12–24 months") return n >= 12 && n <= 24 ? 1 : 0; return answer === "More than 24 months" ? (n > 24 ? 1 : 0) : 0; }
function saturationFit(question, answer, value) { if (!isPubliclyUseful(value)) return 0; const low = /low/i.test(value); if (question.id === "territory_priority") return Number(String(answer)[0]) >= 4 ? (low ? 1 : 0) : 1; return answer === "Low only" ? (low ? 1 : 0) : 1; }
function operationFit(question, answer, brand) { if (!isPubliclyUseful(brand.operations)) return 0; const hard = /high|complex/i.test(brand.operations); if (question.id === "food_operations_tolerance" && categoryFit(["Food service"], brand.category)) return answer === "No" ? 0 : answer === "Yes" ? 1 : 0.5; if (question.id === "staffing_tolerance") return answer === "Mostly self-run" ? (hard ? 0 : 1) : 1; if (question.id === "operating_role") return answer === "Semi-absentee" ? (hard ? 0 : 1) : 1; return 1; }
function trainingFit(answer, value) { if (!isPubliclyUseful(value)) return 0; const extensive = /extensive|week|comprehensive/i.test(value); return answer === "Extensive" ? (extensive ? 1 : 0) : answer === "Minimal" ? (extensive ? 0 : 1) : 1; }
function feeValueForQuestion(answer, b) { return answer === "Royalty" ? b.royalty : answer === "Marketing fund" ? b.marketing : answer === "Upfront fee" ? b.franchiseFee : b.totalInvestment; }
function feeFit(answer, b) { const value = feeValueForQuestion(answer, b); return isPubliclyUseful(value) ? 1 : 0; }
function evidenceFit(question, answer, b) { const score = Math.min(1, gradeRank(b.evidenceGrade) / gradeRank("A")); if (question.id === "evidence_tolerance") return answer === "No" || answer === "Only with strong official sources" ? score : 1; return score; }
function dealBreakerValue(values, b) { if (values.includes("Above-budget investment")) return b.totalInvestment; if (values.includes("High recurring fees")) return `${b.royalty} ${b.marketing}`; if (values.includes("Low evidence")) return b.evidenceGrade; if (values.includes("High saturation")) return b.saturation; if (values.includes("Complex operations")) return b.operations; if (values.includes("International ownership")) return b.canadianOwned; return "No direct score"; }
function dealBreakerFit(values, b) { if (values.includes("None")) return 1; if (values.includes("Above-budget investment") && budgetFit(state.match.answers.investment_budget, b.totalInvestment) === 0) return 0; if (values.includes("Low evidence") && gradeRank(b.evidenceGrade) < gradeRank("B-")) return 0; if (values.includes("High saturation") && /high/i.test(b.saturation)) return 0; if (values.includes("Complex operations") && /high|complex/i.test(b.operations)) return 0; if (values.includes("International ownership") && !/^yes/i.test(b.canadianOwned)) return 0; return 1; }
function reviewPriorityValue(answer, b) { return ({ Affordability: b.totalInvestment, "Evidence quality": b.evidenceGrade, "Growth potential": b.growth, "Operational simplicity": b.operations, "Market opportunity": b.saturation, Support: b.trainingProvided })[answer] || ""; }
function reviewPriorityFit(answer, b) { const value = reviewPriorityValue(answer, b); if (!isPubliclyUseful(value)) return 0; if (answer === "Evidence quality") return evidenceFit({ id: "" }, "", b); if (answer === "Operational simplicity") return /high|complex/i.test(value) ? 0 : 1; if (answer === "Market opportunity") return /high/i.test(value) ? 0 : 1; return 1; }

function availableComparisonFields() { return COMPARISON_FIELDS.filter(([key]) => state.plan === "premium" || (state.plan === "advanced" ? key !== "sources_links" : BASIC_FIELDS.includes(key))); }
function getComparisonRows() {
  const max = TIER_LIMITS[state.plan];
  const selected = state.brands.filter((brand) => state.shortlist.has(brand.id)).map((brand) => ({ brand, match: questionnaireMatch(brand) }));
  const filtered = selected.filter(({ brand }) => {
    const f = state.comparisonFilters;
    return (f.category === "all" || brand.category === f.category) && (f.investment === "all" || brand.investment === f.investment) && (f.risk === "all" || brand.risk === f.risk) && (f.evidence === "all" || brand.evidenceGrade === f.evidence) && (f.availability === "all" || availabilityFilterMatch(brand, f.availability));
  }).map((item) => ({ ...item, rank: comparisonRank(item.brand, item.match) }));
  return filtered.sort(comparisonRowSorter).slice(0, max);
}
function availabilityFilterMatch(b, value) { const statuses = [b.totalInvestment, b.franchiseFee, b.royalty, b.marketing, b.liquidCapital].map((field) => fieldAvailability(field, b)); return value === "estimated" ? statuses.includes("estimated") : value === "verified" ? statuses.includes("supported") : value === "unavailable" ? statuses.includes("unavailable") : true; }
function fieldAvailability(value, brand) { if (!isPubliclyUseful(value) || recordConfidenceMultiplier(brand) === 0) return "unavailable"; return /estimate|estimated|approx/i.test(value) ? "estimated" : "supported"; }
function comparisonRank(b, match) { const components = [{ key: "questionnaire match", weight: 45, value: match.denominator ? match.score : null }, { key: "generic screening score", weight: 20, value: b.score }, { key: "evidence quality", weight: 15, value: gradeRank(b.evidenceGrade) ? Math.round((gradeRank(b.evidenceGrade) / gradeRank("A")) * 100) : null }, { key: "financial fit", weight: 10, value: financialFit(b) }, { key: "risk and operational fit", weight: 10, value: operationalRiskFit(b) }]; const usable = components.filter((item) => Number.isFinite(item.value)); const totalWeight = usable.reduce((sum, item) => sum + item.weight, 0); const score = totalWeight ? Math.round(usable.reduce((sum, item) => sum + item.value * item.weight, 0) / totalWeight) : 0; return { score, usable: usable.map((item) => item.key), missing: components.filter((item) => !Number.isFinite(item.value)).map((item) => item.key) }; }
function financialFit(b) { const checks = [state.match.answers.investment_budget ? assessQuestion(QUESTIONNAIRE[0], state.match.answers.investment_budget, b) : null, state.match.answers.liquid_capital ? assessQuestion(QUESTIONNAIRE[4], state.match.answers.liquid_capital, b) : null].filter(Boolean); return checks.length ? Math.round((checks.reduce((sum, item) => sum + item.fit * item.confidence, 0) / checks.length) * 100) : null; }
function operationalRiskFit(b) { const values = [isPubliclyUseful(b.risk) ? riskFit(Number(String(state.match.answers.risk_preference || "3")[0]), b.risk) : null, isPubliclyUseful(b.operations) ? (/high|complex/i.test(b.operations) ? 40 : 80) : null].filter((value) => value !== null); return values.length ? Math.round((values.reduce((a, b) => a + b, 0) / values.length) * 100) : null; }
function comparisonRowSorter(a, b) { const sort = state.comparisonSort; if (sort === "match") return b.match.score - a.match.score || b.rank.score - a.rank.score; if (sort === "screening") return (b.brand.score ?? -1) - (a.brand.score ?? -1); if (sort === "investment") return (firstMoney(a.brand.totalInvestment) ?? Infinity) - (firstMoney(b.brand.totalInvestment) ?? Infinity); if (sort === "evidence") return gradeRank(b.brand.evidenceGrade) - gradeRank(a.brand.evidenceGrade); if (sort === "sources") return b.brand.sourceCount - a.brand.sourceCount; if (sort === "name") return a.brand.name.localeCompare(b.brand.name); return b.rank.score - a.rank.score || b.match.score - a.match.score || gradeRank(b.brand.evidenceGrade) - gradeRank(a.brand.evidenceGrade) || b.brand.sourceCount - a.brand.sourceCount || a.brand.name.localeCompare(b.brand.name); }

function renderComparisonDecisionLens(items) {
  const withInvestment = items.filter(({ brand }) => Number.isFinite(firstMoney(brand.totalInvestment)));
  const withRisk = items.filter(({ brand }) => /low|medium|high/i.test(brand.risk));
  const lowestInvestment = withInvestment.sort((a, b) => firstMoney(a.brand.totalInvestment) - firstMoney(b.brand.totalInvestment))[0];
  const strongestEvidence = [...items].sort((a, b) => gradeRank(b.brand.evidenceGrade) - gradeRank(a.brand.evidenceGrade) || b.brand.sourceCount - a.brand.sourceCount)[0];
  const lowestRisk = withRisk.sort((a, b) => (/low/i.test(a.brand.risk) ? 1 : /medium/i.test(a.brand.risk) ? 2 : 3) - (/low/i.test(b.brand.risk) ? 1 : /medium/i.test(b.brand.risk) ? 2 : 3))[0];
  const cards = [
    lowestInvestment && ["Lowest disclosed entry point", lowestInvestment.brand.name, lowestInvestment.brand.totalInvestment],
    strongestEvidence && ["Strongest evidence trail", strongestEvidence.brand.name, `${strongestEvidence.brand.evidenceGrade} grade · ${strongestEvidence.brand.sourceCount} sources`],
    lowestRisk && ["Lower reported risk", lowestRisk.brand.name, lowestRisk.brand.risk],
  ].filter(Boolean);
  return `<section class="comparison-decision-lens"><div><p class="eyebrow">Decision lens</p><h2>What separates this shortlist</h2><p class="note">These are comparison signals, not a recommendation. Open each profile and verify current terms before acting.</p></div><div class="decision-lens-grid">${cards.map(([label, name, value]) => `<article><span>${escapeHtml(label)}</span><strong>${escapeHtml(name)}</strong><p>${escapeHtml(simpleValue(value))}</p></article>`).join("")}</div></section>`;
}

function renderComparisonMatrix(items) {
  const fields = availableComparisonFields().filter(([key]) => state.comparisonFields.includes(key));
  return `<div class="compare-shell table-shell"><table class="compare-table"><thead><tr><th>Field</th>${items.map(({ brand, match, rank }) => `<th><div class="compare-brand-head">${brandMark(brand)}<a class="brand-title" href="#/franchises/${brand.id}">${escapeHtml(brand.name)}</a><button class="icon-button shortlist-toggle" data-id="${brand.id}" title="Remove ${escapeAttr(brand.name)}" aria-label="Remove ${escapeAttr(brand.name)} from shortlist">x</button></div><span class="compare-note">Rank ${rank.score}/100 · Match ${match.score}/100</span></th>`).join("")}</tr></thead><tbody>${fields.map(([key, label, render]) => `<tr><th scope="row">${escapeHtml(label)}</th>${items.map(({ brand }) => `<td class="${bestFieldClass(key, brand, items)}">${renderComparisonValue(key, render, brand)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}
function renderComparisonValue(key, render, brand) { const output = render(brand); const raw = { investment: brand.totalInvestment, fee: brand.franchiseFee, royalty: brand.royalty, marketing: brand.marketing, liquid: brand.liquidCapital }[key]; const status = raw ? fieldAvailability(raw, brand) : null; return `${output}${status ? `<span class="compare-note">${status === "supported" ? "Source-supported" : status === "estimated" ? "Estimated" : "Unavailable to assess"}</span>` : ""}`; }
function bestFieldClass(key, brand, items) { if (!["investment", "screening", "evidence", "sources"].includes(key)) return ""; const value = key === "investment" ? firstMoney(brand.totalInvestment) : key === "screening" ? brand.score : key === "evidence" ? gradeRank(brand.evidenceGrade) : brand.sourceCount; const all = items.map(({ brand: item }) => key === "investment" ? firstMoney(item.totalInvestment) : key === "screening" ? item.score : key === "evidence" ? gradeRank(item.evidenceGrade) : item.sourceCount).filter(Number.isFinite); if (!Number.isFinite(value) || !all.length) return "is-unavailable"; const best = key === "investment" ? Math.min(...all) : Math.max(...all); return value === best ? "best-value" : ""; }

function renderShortlist() {
  const savedCount = [...state.shortlist].filter((id) => state.brands.some((brand) => brand.id === id)).length;
  const rows = getComparisonRows(); const stats = getShortlistStats(rows.map((item) => item.brand)); const fields = availableComparisonFields();
  const categories = [["all", "All categories"], ...getFilterOptions("category")];
  app.innerHTML = `<section class="shortlist-layout comparison-layout"><p class="eyebrow">Saved locally <span class="badge good">BETA — ${escapeHtml(PLANS[state.plan].name)}</span></p><h1>Compare shortlist</h1><p class="note">${state.plan === "basic" ? "Basic compares up to 2 brands." : state.plan === "advanced" ? "Advanced compares up to 10 brands." : "Premium comparison is unlimited and includes source/evidence trails."} ${savedCount > rows.length ? `${savedCount - rows.length} saved brand${savedCount - rows.length === 1 ? " is" : "s are"} retained locally but outside this tier’s current comparison limit or filters.` : ""}</p><div class="comparison-controls"><label>Sort <select id="comparisonSort">${optionsHtml([["rank", "Comparison rank"], ["match", "Questionnaire match"], ["screening", "Screening score"], ["investment", "Investment"], ["evidence", "Evidence"], ["sources", "Source count"], ["name", "Name"]], state.comparisonSort)}</select></label><label>Category <select id="compareCategory">${optionsHtml(categories, state.comparisonFilters.category)}</select></label><label>Investment tier <select id="compareInvestment">${optionsHtml([["all", "All investment tiers"], ...getFilterOptions("investment")], state.comparisonFilters.investment)}</select></label><label>Risk <select id="compareRisk">${optionsHtml([["all", "All risks"], ...getFilterOptions("risk")], state.comparisonFilters.risk)}</select></label><label>Evidence <select id="compareEvidence">${optionsHtml([["all", "All evidence grades"], ...getFilterOptions("evidenceGrade")], state.comparisonFilters.evidence)}</select></label><label>Availability <select id="compareAvailability">${optionsHtml([["all", "All availability"], ["verified", "Source-supported"], ["estimated", "Estimated"], ["unavailable", "Unavailable"]], state.comparisonFilters.availability)}</select></label></div><details class="field-picker"><summary>Choose comparison fields (${state.comparisonFields.filter((key) => fields.some(([id]) => id === key)).length}/${fields.length})</summary><div class="option-grid">${fields.map(([key, label]) => `<label><input type="checkbox" class="comparison-field" value="${key}" ${state.comparisonFields.includes(key) ? "checked" : ""}> <span>${escapeHtml(label)}</span></label>`).join("")}</div></details><div class="shortlist-actions"><a class="secondary-button" href="#/match">Update suitability profile</a><div class="inline-actions">${state.plan === "premium" && rows.length ? '<button class="primary-button" id="exportComparison">Export comparison CSV</button>' : ""}<button class="secondary-button" id="clearShortlist" ${savedCount ? "" : "disabled"}>Clear shortlist</button></div></div>${rows.length ? `<div class="review-summary snapshot-grid-wide shortlist-summary"><div>${miniField("Compared", rows.length)}</div><div>${miniField("Saved", savedCount)}</div><div>${miniField("Avg screening", stats.averageScore === "n/a" ? "n/a" : `${stats.averageScore}/100`)}</div><div>${miniField("Sources", stats.sources)}</div><div>${miniField("Tier limit", TIER_LIMITS[state.plan] === Infinity ? "Unlimited" : TIER_LIMITS[state.plan])}</div><div>${miniField("Questionnaire", `${tierQuestionnaire().filter((q) => hasAnswer(state.match.answers[q.id])).length}/${tierQuestionnaire().length}`)}</div></div>${renderComparisonMatrix(rows)}${renderVerdict(rows)}` : renderEmpty("No shortlisted brands fit these comparison filters.", "Save brands from the directory or adjust the filters.")}</section>`;
  const comparisonNote = document.querySelector(".comparison-layout > .note");
  if (state.plan === "basic" && comparisonNote) comparisonNote.textContent = comparisonNote.textContent.replace("Basic compares up to 2 brands.", "Basic compares up to 5 brands.");
  document.querySelector(".shortlist-summary")?.insertAdjacentHTML("afterend", renderComparisonDecisionLens(rows));
  bindShortlistButtons(); bindComparisonControls();
  document.querySelector("#clearShortlist")?.addEventListener("click", () => { state.shortlist.clear(); saveShortlist(); renderShortlist(); });
  document.querySelector("#exportComparison")?.addEventListener("click", () => downloadComparisonCsv(rows.map((item) => item.brand)));
}

function bindComparisonControls() { [["comparisonSort", "comparisonSort"], ["compareCategory", "category"], ["compareInvestment", "investment"], ["compareRisk", "risk"], ["compareEvidence", "evidence"], ["compareAvailability", "availability"]].forEach(([id, key]) => document.querySelector(`#${id}`)?.addEventListener("change", (event) => { if (key === "comparisonSort") state.comparisonSort = event.target.value; else state.comparisonFilters[key] = event.target.value; renderShortlist(); })); document.querySelectorAll(".comparison-field").forEach((input) => input.addEventListener("change", () => { state.comparisonFields = [...document.querySelectorAll(".comparison-field:checked")].map((item) => item.value); if (!state.comparisonFields.length) state.comparisonFields = [availableComparisonFields()[0][0]]; saveComparisonFields(); renderShortlist(); })); }

function renderVerdict(items) { const best = items[0]; if (!best) return ""; const tier = state.plan; const reasons = supportedVerdictReasons(best.brand, best.match).slice(0, tier === "basic" ? 1 : 3); const watch = best.brand.gaps[0] || (!isPubliclyUseful(best.brand.totalInvestment) ? "Total investment is unavailable to assess" : "Confirm current disclosure, territory, and unit economics directly."); const confidence = verdictConfidence(best.brand, best.match); const because = reasons.length ? reasons.join("; ") : "Evidence is insufficient to support a recommendation."; const trail = tier === "premium" ? `<details class="evidence-trail"><summary>Source and evidence trail</summary><p>${escapeHtml(best.brand.evidenceGrade)} evidence grade · ${best.brand.sourceCount} sources · ${best.brand.officialCount} official sources · ${escapeHtml(verificationStatusLabel(best.brand))}</p>${[...best.brand.officialSources, ...best.brand.governmentSources].map((url) => `<a href="${escapeAttr(url)}" target="_blank" rel="noreferrer">${escapeHtml(url)}</a>`).join("<br>") || "No source links are available."}</details>` : ""; return `<section class="verdict-card"><p class="eyebrow">${tier === "basic" ? "Focused verdict" : "Comparison verdict"}</p><h2>Recommended: ${escapeHtml(best.brand.name)}</h2><p><strong>Because:</strong> ${escapeHtml(because)}</p><p><strong>Watch out for:</strong> ${escapeHtml(watch)}</p><p><strong>Confidence:</strong> ${confidence}</p>${trail}</section>`; }
function supportedVerdictReasons(b, match) { const reasons = []; if (match.score > 0) reasons.push(`questionnaire match is ${match.score}/100 based on available supported fields`); if (isPubliclyUseful(b.totalInvestment) && assessQuestion(QUESTIONNAIRE[0], state.match.answers.investment_budget, b).fit > 0) reasons.push(`initial investment fits the stated budget`); if (gradeRank(b.evidenceGrade) >= gradeRank("B-") && b.sourceCount >= 5) reasons.push(`${b.evidenceGrade} evidence grade is supported by ${b.sourceCount} sources`); if (b.score !== null) reasons.push(`generic screening score is ${b.score}/100`); if (isPubliclyUseful(b.risk) && !/high/i.test(b.risk)) reasons.push(`recorded risk is ${b.risk}`); return reasons; }
function verdictConfidence(b, match) { const decisiveMissing = match.details.some((item) => item.status === "unavailable" && ["initial investment", "preferred category", "evidence quality"].includes(item.label)); if (gradeRank(b.evidenceGrade) >= gradeRank("B-") && b.sourceCount >= 5 && b.officialCount && !decisiveMissing) return "high"; if (b.sourceCount > 0 && gradeRank(b.evidenceGrade) >= gradeRank("C")) return "medium"; return "low"; }

async function renderBetaTier() { const configured = String(window.__GETFRANCHISE_BETA_CONFIG__?.founderPassphraseHash || ""); const authorized = readBetaAccess(); app.innerHTML = `<section class="shortlist-layout beta-tier"><p class="eyebrow">Founder-only route</p><h1>Beta tier assignment</h1>${!configured ? "<p class=\"note\">Founder access is not configured for this build.</p>" : !authorized ? `<p class="note">Enter the founder passphrase to assign a browser-local beta tier. This is not account-backed administration.</p><label class="field">Passphrase<input id="founderPassphrase" type="password" autocomplete="current-password"></label><button class="primary-button" id="unlockBeta">Continue</button><p class="note" id="betaMessage"></p>` : `<p class="note">BETA — manually assigned. This affects only this browser profile; no payment or account functionality is present.</p><div class="option-grid">${Object.entries(PLANS).map(([key, plan]) => `<label><input type="radio" name="betaPlan" value="${key}" ${state.plan === key ? "checked" : ""}> <span>${escapeHtml(plan.name)}</span></label>`).join("")}</div><button class="primary-button" id="assignBeta">Assign tier</button>`}</section>`; if (configured && !authorized) document.querySelector("#unlockBeta")?.addEventListener("click", async () => { const passphrase = document.querySelector("#founderPassphrase").value; const digest = await sha256(passphrase); if (digest === configured.toLowerCase()) { writeBetaAccess(); renderBetaTier(); } else document.querySelector("#betaMessage").textContent = "Access was not granted."; }); if (authorized) document.querySelector("#assignBeta")?.addEventListener("click", () => { state.plan = document.querySelector('input[name="betaPlan"]:checked').value; savePlan(); renderBetaTier(); }); }
async function sha256(value) { const bytes = new TextEncoder().encode(value); const digest = await crypto.subtle.digest("SHA-256", bytes); return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join(""); }
function bindDirectoryEvents() {
  const ids = [
    "queryInput",
    "heroSearch",
    "categorySelect",
    "investmentSelect",
    "evidenceSelect",
    "riskSelect",
    "ownershipSelect",
    "sortSelect",
  ];
  ids.forEach((id) => {
    const element = document.querySelector(`#${id}`);
    if (!element) return;
    element.addEventListener("input", syncFilters);
    element.addEventListener("change", syncFilters);
  });
  const heroButton = document.querySelector("#heroSearchButton");
  if (heroButton) heroButton.addEventListener("click", syncFilters);
  const clear = document.querySelector("#clearFilters");
  if (clear) {
    clear.addEventListener("click", () => {
      Object.assign(state, {
        query: "",
        category: "all",
        section: "all",
        investment: "all",
        evidence: "all",
        risk: "all",
        ownership: "all",
        sort: "score_desc",
        page: 1,
      });
      renderDirectory();
    });
  }
  document.querySelectorAll(".category-card").forEach((button) => {
    button.addEventListener("click", () => {
      state.category = button.dataset.category || "all";
      state.section = "all";
      state.page = 1;
      renderDirectory();
    });
  });
  document.querySelectorAll(".section-tab").forEach((button) => {
    button.addEventListener("click", () => {
      state.section = button.dataset.section || "all";
      state.category = "all";
      state.page = 1;
      renderDirectory();
    });
  });
  document.querySelectorAll("[data-page]").forEach((button) => {
    button.addEventListener("click", () => {
      state.page = Number(button.dataset.page);
      renderDirectory();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });
  bindShortlistButtons();
}

function getContactEmail(brand) {
  if (CONTACT_EMAIL_OVERRIDES[brand.id]) return CONTACT_EMAIL_OVERRIDES[brand.id];
  const match = String(brand.contactInformation || "").match(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/);
  return match ? match[0] : "";
}

function getContactLinks(brand) {
  const links = [
    ...splitSources(brand.contactInformation),
    ...brand.officialSources,
  ].filter((link) => /^https?:\/\//i.test(link));
  return [...new Set(links)].slice(0, 4);
}

function hasUsefulContact(brand) {
  return getContactEmail(brand) || getContactLinks(brand).length ? 1 : 0;
}

function contactSummary(brand) {
  const email = getContactEmail(brand);
  if (email) return email;
  const links = getContactLinks(brand);
  if (links.length) return new URL(links[0]).hostname.replace(/^www\./, "");
  return "Email needed";
}

function contactActionHtml(brand, className) {
  if (!outreachIsOpen()) return `<span class="${className} is-disabled">Outreach opens at 100</span>`;
  const email = getContactEmail(brand);
  if (email) return `<a class="${className}" href="mailto:${escapeAttr(email)}">Email</a>`;
  const links = getContactLinks(brand);
  if (links.length) return `<a class="${className}" href="${escapeAttr(links[0])}" target="_blank" rel="noreferrer">Official link</a>`;
  return `<span class="${className} is-disabled">Email needed</span>`;
}

function franchisorOutreachMailto(brand) {
  if (!outreachIsOpen()) return "";
  const email = getContactEmail(brand);
  if (!email) return "";
  const subject = `Verification request for ${brand.name} franchise listing`;
  const body = [
    `Hello ${brand.name} team,`,
    "",
    "I'm building GetFranchise.ca, a Canadian franchise research directory. We have a free public profile for your franchise based on publicly available information, and I want to make sure the basic buyer information is accurate.",
    "",
    "Could you please confirm or correct these fields?",
    `- Total investment: ${simpleValue(brand.totalInvestment)}`,
    `- Franchise fee: ${simpleValue(brand.franchiseFee)}`,
    `- Royalty: ${simpleValue(brand.royalty)}`,
    `- Marketing fee: ${simpleValue(brand.marketing)}`,
    `- Liquid capital requirement: ${simpleValue(brand.liquidCapital)}`,
    "- Current Canadian franchise availability",
    "- Best official franchise contact email or link",
    "",
    "If you would prefer that we remove the listing or not contact you again, please reply and we will do that.",
    "",
    "Thank you,",
    "GetFranchise.ca",
  ].join("\n");
  return `mailto:${email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

function draftActionHtml(brand, className = "table-action") {
  const href = franchisorOutreachMailto(brand);
  if (!href) return `<span class="${className} is-disabled">Email needed</span>`;
  return `<a class="${className}" href="${escapeAttr(href)}">Draft email</a>`;
}

function readyCandidateCount() {
  return state.brands.filter(isPublicCandidate).length;
}

function outreachIsOpen() {
  return readyCandidateCount() >= OUTREACH_MINIMUM_READY_CANDIDATES;
}

function getOutreachRows() {
  const saved = readOutreachStatuses();
  return state.brands
    .map((brand) => ({
      brand,
      email: getContactEmail(brand),
      link: getContactLinks(brand)[0] || "",
      status: saved[brand.id] || "not_contacted",
    }))
    .sort((a, b) =>
      statusRank(a.status) - statusRank(b.status) ||
      Boolean(b.email) - Boolean(a.email) ||
      gradeRank(b.brand.evidenceGrade) - gradeRank(a.brand.evidenceGrade) ||
      b.brand.verifiedCoreFeeFields - a.brand.verifiedCoreFeeFields ||
      a.brand.name.localeCompare(b.brand.name)
    );
}

function renderOutreachRow(row) {
  return `
    <tr>
      <td>
        <div class="brand-cell">
          ${brandMark(row.brand)}
          <span>
            <a class="brand-title" href="#/franchises/${row.brand.id}">${escapeHtml(row.brand.name)}</a>
            <span class="brand-meta">${escapeHtml(simpleValue(row.brand.totalInvestment))}</span>
          </span>
        </div>
      </td>
      <td>${row.email ? `<a href="mailto:${escapeAttr(row.email)}">${escapeHtml(row.email)}</a>` : `<span class="muted">No public email found</span>`}</td>
      <td>${row.link ? `<a class="table-action" href="${escapeAttr(row.link)}" target="_blank" rel="noreferrer">Open</a>` : `<span class="muted">No link</span>`}</td>
      <td>
        <select class="status-select" data-id="${escapeAttr(row.brand.id)}" aria-label="Outreach status for ${escapeAttr(row.brand.name)}">
          ${optionsHtml([
            ["not_contacted", "Not contacted"],
            ["drafted", "Drafted"],
            ["sent", "Email sent"],
            ["follow_up", "Follow-up due"],
            ["response_received", "Response received"],
            ["confirmed", "Costs confirmed"],
            ["declined", "Declined / remove"],
          ], row.status)}
        </select>
      </td>
      <td>${draftActionHtml(row.brand)}</td>
    </tr>
  `;
}

function bindOutreachControls() {
  document.querySelectorAll(".status-select").forEach((select) => {
    select.addEventListener("change", () => {
      const saved = readOutreachStatuses();
      saved[select.dataset.id] = select.value;
      localStorage.setItem(OUTREACH_STORAGE_KEY, JSON.stringify(saved));
      renderFranchisorReview();
    });
  });
}

function readOutreachStatuses() {
  try {
    return JSON.parse(localStorage.getItem(OUTREACH_STORAGE_KEY) || "{}");
  } catch {
    return {};
  }
}

function statusRank(status) {
  return {
    not_contacted: 0,
    drafted: 1,
    sent: 2,
    follow_up: 3,
    response_received: 4,
    confirmed: 5,
    declined: 6,
  }[status] ?? 0;
}

function getReadyCandidateValidation(brand) {
  const checks = [
    {
      key: "source_depth",
      label: "5+ source links",
      passed: brand.sourceCount >= 5,
      detail: `${brand.sourceCount} source links in the current public record.`,
    },
    {
      key: "official_source",
      label: "Official source present",
      passed: brand.officialCount >= 1,
      detail: `${brand.officialCount} official brand, company, or franchising links.`,
    },
    {
      key: "money_fields",
      label: "4/5 money fields checked",
      passed: brand.verifiedCoreFeeFields >= 4,
      detail: `${brand.verifiedCoreFeeFields}/5 core fields checked: investment, fee, royalty, marketing, and liquid capital.`,
    },
    {
      key: "evidence_grade",
      label: "Evidence grade B- or better",
      passed: gradeRank(brand.evidenceGrade) >= gradeRank("B-"),
      detail: `${brand.evidenceGrade || "Not Graded"} current evidence grade.`,
    },
    {
      key: "canadian_relevance",
      label: "Canadian relevance stated",
      passed: hasCanadianRelevance(brand),
      detail: "Canada, Canadian, CAD, CFA, or a Canadian web/source signal appears in the profile.",
    },
    {
      key: "cross_border_boundary",
      label: "Cross-border figures labelled",
      passed: hasClearCrossBorderBoundary(brand),
      detail: "U.S., USD, and FDD-context figures must be labelled as context or marked for Canadian confirmation.",
    },
    {
      key: "confirmation_boundary",
      label: "Franchisor confirmation boundary",
      passed: hasConfirmationBoundary(brand),
      detail: "The record must say whether direct franchisor confirmation is still required or already received.",
    },
  ];
  const passedCount = checks.filter((check) => check.passed).length;
  return {
    passed: passedCount === checks.length,
    passedCount,
    total: checks.length,
    checks,
  };
}

function getReadyValidationStats(brands) {
  const validations = brands.map(getReadyCandidateValidation);
  const ready = brands.filter(isPublicCandidate).length;
  return {
    ready,
    notReady: brands.length - ready,
    averagePassed: validations.length
      ? Math.round((validations.reduce((sum, validation) => sum + validation.passedCount, 0) / validations.length) * 10) / 10
      : 0,
  };
}

function hasCanadianRelevance(brand) {
  const text = [
    brand.name,
    brand.rawName,
    brand.category,
    brand.industry,
    brand.canadianOwned,
    brand.headquarters,
    brand.totalInvestment,
    brand.franchiseFee,
    brand.liquidCapital,
    brand.numberOfLocations,
    brand.growthTrends,
    brand.contactInformation,
    brand.officialSources.join(" "),
  ]
    .join(" ")
    .toLowerCase();
  return /\b(canada|canadian|cad|cfa\.ca|\.ca\b|en-ca|\/ca\/)/i.test(text);
}

function hasClearCrossBorderBoundary(brand) {
  const moneyText = [brand.totalInvestment, brand.franchiseFee, brand.royalty, brand.marketing, brand.liquidCapital].join(" ");
  if (!/\b(u\.s\.|us|usa|usd|fdd|item 7|item 19|american)\b/i.test(moneyText)) return true;
  const boundaryText = [moneyText, brand.crossBorderCaution, brand.confirmation, brand.posture, brand.fddSummary].join(" ");
  return /confirm|context|canadian|canada-specific|reconcile|not verified|requires?/i.test(boundaryText);
}

function hasConfirmationBoundary(brand) {
  const text = [brand.confirmation, brand.posture, brand.fddSummary].join(" ").toLowerCase();
  return /direct|franchisor|confirm|confirmation|required|requires|not confirmed|none confirmed|reviewed|verified/.test(text);
}

function renderValidationChecklist(brand, compact = false) {
  const validation = getReadyCandidateValidation(brand);
  return `
    <ul class="validation-checklist${compact ? " compact" : ""}">
      ${validation.checks.map((check) => `
        <li class="${check.passed ? "is-pass" : "is-gap"}">
          <strong>${check.passed ? "Pass" : "Gap"}: ${escapeHtml(check.label)}</strong>
          ${compact ? "" : `<span>${escapeHtml(check.detail)}</span>`}
        </li>
      `).join("")}
    </ul>
  `;
}

function validationSummaryHtml(brand) {
  const validation = getReadyCandidateValidation(brand);
  return `
    ${badge(validation.passed ? "Source-backed" : "Readiness gaps", validation.passed ? "good" : "warn")}
    <span class="compare-note">${validation.passedCount}/${validation.total} checks passed</span>
  `;
}

function firstValidationGap(brand) {
  const gap = getReadyCandidateValidation(brand).checks.find((check) => !check.passed);
  return gap ? gap.label : "Ready for buyer screening";
}

function getResearchQueueRows() {
  const saved = readResearchStatuses();
  const query = state.researchQuery.trim().toLowerCase();
  return state.allBrands
    .map((brand) => {
      const need = researchNeed(brand);
      return {
        brand,
        need,
        needLabel: researchNeedLabel(need),
        nextAction: researchNextAction(brand, need),
        stage: saved[brand.id] || defaultResearchStage(brand, need),
      };
    })
    .filter((item) => {
      const brand = item.brand;
      const queryText = [
        brand.name,
        brand.category,
        brand.industry,
        brand.evidenceGrade,
        brand.totalInvestment,
        brand.franchiseFee,
        brand.royalty,
        brand.marketing,
        brand.liquidCapital,
        brand.contactInformation,
        brand.posture,
        brand.gaps.join(" "),
        brand.officialSources.join(" "),
        item.needLabel,
        item.stage,
      ]
        .join(" ")
        .toLowerCase();
      return (
        (!query || queryText.includes(query)) &&
        (state.researchCategory === "all" || brand.category === state.researchCategory) &&
        (state.researchNeed === "all" || researchNeedMatches(item, state.researchNeed)) &&
        (state.researchStage === "all" || item.stage === state.researchStage)
      );
    })
    .sort(researchSorter);
}

function researchSorter(a, b) {
  return (
    researchNeedRank(a.need) - researchNeedRank(b.need) ||
    a.brand.sourceCount - b.brand.sourceCount ||
    a.brand.officialCount - b.brand.officialCount ||
    a.brand.verifiedCoreFeeFields - b.brand.verifiedCoreFeeFields ||
    gradeRank(b.brand.evidenceGrade) - gradeRank(a.brand.evidenceGrade) ||
    a.brand.name.localeCompare(b.brand.name)
  );
}

function getResearchQueueStats() {
  const all = state.allBrands;
  return {
    total: all.length,
    publicNow: state.brands.length,
    zeroSource: all.filter((brand) => brand.sourceCount === 0).length,
    thinEvidence: all.filter((brand) => brand.sourceCount > 0 && brand.sourceCount < 5).length,
    feeGaps: all.filter((brand) => brand.verifiedCoreFeeFields < 4).length,
    readyCandidates: all.filter(isPublicCandidate).length,
  };
}

function researchNeed(brand) {
  const validation = getReadyCandidateValidation(brand);
  const failedKeys = new Set(validation.checks.filter((check) => !check.passed).map((check) => check.key));
  if (validation.passed) return "public_candidates";
  if (failedKeys.has("source_depth") || failedKeys.has("official_source")) return "source_rebuild";
  if (failedKeys.has("money_fields") || failedKeys.has("evidence_grade")) return "fee_verification";
  if (failedKeys.has("canadian_relevance") || failedKeys.has("cross_border_boundary") || brand.governmentCount === 0) return "legal_entity";
  if (failedKeys.has("confirmation_boundary") || /none confirmed|not confirmed|no direct|not verified/i.test(brand.confirmation)) return "outreach";
  return "maintenance";
}

function researchNeedMatches(item, filter) {
  if (filter === "priority") return item.need !== "maintenance" && item.stage !== "published";
  return item.need === filter;
}

function researchNeedLabel(need) {
  return {
    source_rebuild: "Source rebuild",
    fee_verification: "Fee verification",
    legal_entity: "Legal/entity",
    outreach: "Outreach",
    public_candidates: "Public candidate",
    maintenance: "Maintain",
  }[need] || "Review";
}

function researchNeedRank(need) {
  return {
    source_rebuild: 1,
    fee_verification: 2,
    legal_entity: 3,
    outreach: 4,
    public_candidates: 5,
    maintenance: 6,
  }[need] || 9;
}

function researchNextAction(brand, need) {
  if (need === "source_rebuild") return "Find official Canadian/brand franchise page and reject weak exact numbers.";
  if (need === "fee_verification") return "Verify total investment, franchise fee, royalty, marketing, and liquid capital.";
  if (need === "legal_entity") return "Add signing entity, disclosure status, registry, litigation, or insolvency checks.";
  if (need === "outreach") return "Draft franchisor confirmation email and log response before marking verified.";
  if (need === "public_candidates") {
    const validation = getReadyCandidateValidation(brand);
    return `Passed ${validation.passedCount}/${validation.total} ready checks. Compare shortlist options, then confirm legal/entity and franchisor details.`;
  }
  return "Recheck sources on the next scheduled refresh.";
}

function defaultResearchStage(brand, need) {
  if (state.brands.some((item) => item.id === brand.id)) return "published";
  if (need === "source_rebuild") return "needs_sources";
  if (need === "fee_verification") return "needs_fee_check";
  if (need === "legal_entity") return "needs_legal_check";
  if (need === "outreach") return "needs_outreach";
  if (need === "public_candidates") return "ready_for_review";
  return "monitor";
}

function isPublicCandidate(brand) {
  // Factory publication is an explicit directory authorization. Keep the
  // validation gate for every other record so the research queue remains
  // private by default.
  return isFactoryPublished(brand) || (
    brand.publicProfileStatus.toLowerCase() === "public_ready" &&
    getReadyCandidateValidation(brand).passed
  );
}

function isFactoryPublished(brand) {
  const reportPath = brand.reportPath.replace(/\\/g, "/").toLowerCase();
  return brand.researchTrack.toLowerCase() === "factory_evidence_review" ||
    reportPath.includes("factory/workspace/published/");
}

function readResearchStatuses() {
  try {
    return JSON.parse(localStorage.getItem(RESEARCH_STORAGE_KEY) || "{}");
  } catch {
    return {};
  }
}

function researchStageOptions() {
  return [
    ["needs_sources", "Needs sources"],
    ["needs_fee_check", "Needs fee check"],
    ["needs_legal_check", "Needs legal check"],
    ["needs_outreach", "Needs outreach"],
    ["researching", "Researching"],
    ["ready_for_review", "Ready for review"],
    ["published", "Published"],
    ["monitor", "Monitor"],
  ];
}

function getAllCategoryOptions() {
  return [...new Set(state.allBrands.map((brand) => brand.category).filter(Boolean))]
    .sort((a, b) => labelize(a).localeCompare(labelize(b)))
    .map((category) => [category, labelize(category)]);
}

function researchNeedBadgeClass(need) {
  if (need === "source_rebuild" || need === "fee_verification") return "risk";
  if (need === "legal_entity" || need === "outreach") return "warn";
  if (need === "public_candidates") return "good";
  return "";
}

function getPublicBrands(brands) {
  const sorted = brands
    .filter(isPublicCandidate)
    .sort((a, b) => {
      return (
        hasUsefulContact(b) - hasUsefulContact(a) ||
        b.sourceCount - a.sourceCount ||
        b.verifiedCoreFeeFields - a.verifiedCoreFeeFields ||
        gradeRank(b.evidenceGrade) - gradeRank(a.evidenceGrade) ||
        (b.score ?? -1) - (a.score ?? -1) ||
        a.name.localeCompare(b.name)
      );
    });
  const pinned = sorted.filter((brand) => DRINK_PROFILE_IDS.has(brand.id));
  const rest = sorted.filter((brand) => !DRINK_PROFILE_IDS.has(brand.id));
  return [...pinned, ...rest];
}

function syncFilters(event) {
  const target = event.target;
  const activeId = target.id;
  const cursor = typeof target.selectionStart === "number" ? target.selectionStart : null;
  if (target.id === "queryInput" || target.id === "heroSearch") state.query = target.value;
  if (target.id === "categorySelect") state.category = target.value;
  if (target.id === "investmentSelect") state.investment = target.value;
  if (target.id === "evidenceSelect") state.evidence = target.value;
  if (target.id === "riskSelect") state.risk = target.value;
  if (target.id === "ownershipSelect") state.ownership = target.value;
  if (target.id === "sortSelect") state.sort = target.value;
  state.page = 1;
  renderDirectory();
  const nextActive = document.querySelector(`#${activeId}`);
  if (nextActive) {
    nextActive.focus({ preventScroll: true });
    if (cursor !== null && "setSelectionRange" in nextActive) {
      nextActive.setSelectionRange(cursor, cursor);
    }
  }
}

function bindShortlistButtons() {
  document.querySelectorAll(".shortlist-toggle").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      const id = button.dataset.id;
      if (state.shortlist.has(id)) {
        state.shortlist.delete(id);
      } else if (state.shortlist.size >= TIER_LIMITS[state.plan]) {
        showToast(`${PLANS[state.plan].name} includes comparisons of up to ${TIER_LIMITS[state.plan]} franchises. A founder can assign a higher beta tier for this browser.`, "View plans");
        return;
      } else {
        state.shortlist.add(id);
      }
      saveShortlist();
      renderRoute();
    });
  });
}

function applyFilters() {
  const query = state.query.trim().toLowerCase();
  const filtered = state.brands.filter((brand) => {
    const queryText = [
      brand.name,
      brand.category,
      brand.industry,
      brand.evidenceGrade,
      brand.cuisine,
      brand.totalInvestment,
      brand.franchiseFee,
      brand.royalty,
      brand.marketing,
      brand.liquidCapital,
      brand.headquarters,
      brand.contactInformation,
      getContactEmail(brand),
      brand.evidenceGrade,
      brand.posture,
      brand.gaps.join(" "),
      brand.officialSources.join(" "),
    ]
      .join(" ")
      .toLowerCase();

    const ownershipMatch =
      state.ownership === "all" ||
      (state.ownership === "canadian" && brand.canadianOwned.toLowerCase().startsWith("yes")) ||
      (state.ownership === "non_canadian" && !brand.canadianOwned.toLowerCase().startsWith("yes"));
    const sectionMatch =
      state.section === "all" ||
      (state.section === "drinks" && DRINK_PROFILE_IDS.has(brand.id)) ||
      (state.section === "services" && !FOOD_SERVICE_CATEGORIES.has(brand.category)) ||
      brand.category === state.section;

    return (
      (!query || queryText.includes(query)) &&
      sectionMatch &&
      (state.category === "all" || brand.category === state.category) &&
      (state.investment === "all" || brand.investment === state.investment) &&
      (state.evidence === "all" || brand.evidenceGrade === state.evidence) &&
      (state.risk === "all" || brand.risk === state.risk) &&
      ownershipMatch
    );
  });

  return filtered.sort(sorter(state.sort));
}

function sorter(sort) {
  return (a, b) => {
    if (sort === "brand_asc") return a.name.localeCompare(b.name);
    if (sort === "sources_desc") return b.sourceCount - a.sourceCount || a.name.localeCompare(b.name);
    if (sort === "sources_asc") {
      return a.sourceCount - b.sourceCount || a.officialCount - b.officialCount || (a.score ?? -1) - (b.score ?? -1) || a.name.localeCompare(b.name);
    }
    if (sort === "evidence_desc") return gradeRank(b.evidenceGrade) - gradeRank(a.evidenceGrade) || a.name.localeCompare(b.name);
    return (b.score || -1) - (a.score || -1) || a.name.localeCompare(b.name);
  };
}

function gradeRank(grade) {
  const ranks = { A: 8, "A-": 7.5, "B+": 7, B: 6.5, "B-": 6, "C+": 5.5, C: 5, "C-": 4.5, D: 3, F: 1 };
  return ranks[grade] || 0;
}

function getStats(brands) {
  return {
    total: brands.length,
    sources: brands.reduce((sum, brand) => sum + brand.sourceCount, 0),
    emails: brands.filter((brand) => getContactEmail(brand)).length,
    sourceGaps: brands.filter((brand) => brand.sourceCount === 0).length,
    categories: new Set(brands.map((brand) => brand.category)).size,
    ready: brands.filter(isPublicCandidate).length,
  };
}

function getCategorySummary(brands) {
  const map = new Map();
  brands.forEach((brand) => {
    const existing = map.get(brand.category) || { category: brand.category, count: 0, scores: [], sources: 0 };
    existing.count += 1;
    if (brand.score !== null) existing.scores.push(brand.score);
    existing.sources += brand.sourceCount;
    map.set(brand.category, existing);
  });
  return [...map.values()]
    .map((item) => ({
      ...item,
      average: item.scores.length ? Math.round(item.scores.reduce((sum, score) => sum + score, 0) / item.scores.length) : null,
    }))
    .sort((a, b) => b.count - a.count);
}

function renderCategoryCard(item) {
  const active = state.category === item.category ? " is-active" : "";
  return `
    <button class="category-card${active}" data-category="${escapeAttr(item.category)}">
      <strong>${escapeHtml(labelize(item.category))}</strong>
      <span>${item.count} profiles - avg fit ${item.average ?? "n/a"} - ${item.sources} sources</span>
    </button>
  `;
}

function dataQualityLabel(brand) {
  if (isFactoryPublished(brand)) return "Factory published - verify details";
  if (isPublicCandidate(brand)) return "Source-backed";
  if (brand.sourceCount === 0) return "Rebuild required";
  if (brand.officialCount === 0) return "No official source";
  if (brand.sourceCount < 5) return "Thin evidence";
  return "Source-backed";
}

function dataQualityClass(brand) {
  if (isFactoryPublished(brand)) return "warn";
  if (isPublicCandidate(brand)) return "good";
  if (brand.sourceCount === 0 || brand.officialCount === 0) return "risk";
  if (brand.sourceCount < 5) return "warn";
  return "good";
}

function preferredInvestmentLabel(brand) {
  if (isPubliclyUseful(brand.totalInvestment)) return brand.totalInvestment;
  if (isPubliclyUseful(brand.investment)) return brand.investment;
  return "Request current Canadian disclosure";
}

function isPubliclyUseful(value) {
  return value && !/not publicly|not stated|not verified|unavailable|unknown/i.test(String(value));
}

function cardActionNote(brand) {
  if (brand.officialCount > 0 && brand.verifiedCoreFeeFields >= 3) {
    return "Ready for buyer review";
  }
  if (brand.officialCount > 0) return "Verify fees before outreach";
  return "Needs source check";
}

function franchisorReviewStatus(brand) {
  return /none confirmed|not confirmed|no direct|not verified/i.test(brand.confirmation)
    ? "Review requested / not confirmed"
    : brand.confirmation;
}

function verificationStatusLabel(brand) {
  if (/none confirmed|not confirmed|no direct|not verified/i.test(brand.confirmation)) {
    return "Needs Direct Confirmation";
  }
  if (/direct franchisor|franchisor confirmed|brand confirmed|confirmed by/i.test(brand.confirmation)) {
    return "Franchisor Confirmed";
  }
  return "Source-Backed Research";
}

function verificationStatusDetail(brand) {
  if (/none confirmed|not confirmed|no direct|not verified/i.test(brand.confirmation)) {
    return "This profile has not been confirmed by the franchisor. Buyers should request current Canadian disclosure and fee documents.";
  }
  return "Public sources support parts of this profile. Still confirm current Canadian disclosure, fees, territory, and unit economics directly with the brand.";
}

function verificationStatusClass(brand) {
  return /none confirmed|not confirmed|no direct|not verified/i.test(brand.confirmation) ? "is-public" : "is-reviewed";
}

function verificationBadgeClass(brand) {
  if (/none confirmed|not confirmed|no direct|not verified/i.test(brand.confirmation)) return "warn";
  if (/direct franchisor|franchisor confirmed|brand confirmed|confirmed by/i.test(brand.confirmation)) return "good";
  return "warn";
}

function simpleValue(value) {
  return isPubliclyUseful(value) ? String(value) : "Verify directly";
}

function correctionMailto(brand) {
  const subject = `Correction request for ${brand.name} franchise profile`;
  const body = [
    `Brand: ${brand.name}`,
    `Profile ID: ${brand.id}`,
    `Current evidence grade: ${brand.evidenceGrade}`,
    `Current source count: ${brand.sourceCount}`,
    "",
    "Correction or confirmation requested:",
    "",
    "Supporting source URL or document:",
    "",
    "May GetFranchise display this updated information publicly? Yes/No",
    "",
    "Submitted by:",
    "Name:",
    "Title:",
    "Company:",
    "Corporate email:",
  ].join("\n");
  return `mailto:${CORRECTION_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

function generalCorrectionMailto() {
  const subject = "Canadian franchise profile correction";
  const body = [
    "Brand:",
    "Correction or confirmation requested:",
    "",
    "Supporting source URL or document:",
    "",
    "May GetFranchise display this updated information publicly? Yes/No",
    "",
    "Submitted by:",
    "Name:",
    "Title:",
    "Company:",
    "Corporate email:",
  ].join("\n");
  return `mailto:${CORRECTION_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

function renderPagination(pageCount) {
  if (pageCount <= 1) return "";
  const prev = Math.max(1, state.page - 1);
  const next = Math.min(pageCount, state.page + 1);
  return `
    <div class="pagination" aria-label="Pagination">
      <button class="secondary-button" data-page="${prev}" ${state.page === 1 ? "disabled" : ""}>Previous</button>
      <button class="secondary-button" data-page="${next}" ${state.page === pageCount ? "disabled" : ""}>Next</button>
    </div>
  `;
}

function renderEmpty(title = "No franchises match these filters.", body = "Clear filters or search for a broader term.") {
  return `<div class="empty-state"><h2>${escapeHtml(title)}</h2><p class="note">${escapeHtml(body)}</p></div>`;
}

function renderError(error) {
  app.innerHTML = `
    <section class="error-panel">
      <h1>Database export could not load</h1>
      <p class="note">Start the local preview with <strong>GetfranchiseAi/run-local.bat</strong>, then open <strong>http://localhost:5174/GetfranchiseAi/</strong>. The UI expects the export at <strong>${DATA_URL}</strong>.</p>
      <p class="disclaimer">${escapeHtml(error.message)}</p>
    </section>
  `;
}

function selectField(id, label, selected, options) {
  return `<div class="field"><label for="${id}">${label}</label><select id="${id}">${optionsHtml(options, selected)}</select></div>`;
}

function optionsHtml(options, selected) {
  return options.map(([value, label]) => `<option value="${escapeAttr(value)}" ${value === selected ? "selected" : ""}>${escapeHtml(label)}</option>`).join("");
}

function getFilterOptions(key) {
  return [...new Set(state.brands.map((brand) => brand[key]).filter(Boolean))]
    .sort((a, b) => String(a).localeCompare(String(b)))
    .map((value) => [value, key === "category" ? labelize(value) : value]);
}

function badge(text, className = "") {
  return `<span class="badge ${className}">${escapeHtml(text || "Not Verified")}</span>`;
}

function scoreHtml(score) {
  const value = score ?? 0;
  return `<span class="score-meter"><strong>${score ?? "n/a"}</strong><span class="meter-track"><span class="meter-fill" style="width:${Math.max(0, Math.min(100, value))}%"></span></span></span>`;
}

function trustStack(brand) {
  return `
    <span class="trust-stack">
      <strong>${brand.sourceCount} sources</strong>
      <span>${brand.verifiedCoreFeeFields} core fees verified</span>
    </span>
  `;
}

function renderNeedsImprovement(brand) {
  const items = getNeedsImprovementItems(brand);
  if (!items.length) {
    return `<p class="note">No obvious launch-profile gaps were detected. Keep this profile in the outreach queue for date refreshes and franchisor reconfirmation.</p>`;
  }
  return `
    <ul class="gap-list">
      ${items.map((item) => `<li><strong>${escapeHtml(item.label)}</strong><span>${escapeHtml(item.detail)}</span></li>`).join("")}
    </ul>
  `;
}

function getNeedsImprovementItems(brand) {
  const items = [];
  const confirmation = brand.confirmation.toLowerCase();
  const disclosure = brand.fddSummary.toLowerCase();
  const profitability = brand.profitabilityIndicators.toLowerCase();
  const ownerReviews = brand.ownerReviews.toLowerCase();
  const growthText = `${brand.growthTrends} ${brand.posture} ${brand.gaps.join(" ")}`.toLowerCase();
  const moneyFields = [brand.totalInvestment, brand.franchiseFee, brand.royalty, brand.marketing, brand.liquidCapital];

  if (/^(not confirmed|none confirmed|no direct|not verified)/i.test(brand.confirmation) || !/confirmed|verified/.test(confirmation)) {
    items.push({
      label: "Franchisor confirmation",
      detail: "Contact the franchisor and record which fields they confirm, correct, decline to disclose, or ask to remove.",
    });
  }

  if (/not|none|unavailable|no public|not stated|not verified/.test(disclosure)) {
    items.push({
      label: "Canadian disclosure package",
      detail: "Record whether a current Canadian disclosure package was requested, received, or unavailable for the buyer's province.",
    });
  }

  if (moneyFields.some((value) => /not publicly|not stated|not verified|unavailable/i.test(value))) {
    items.push({
      label: "Core money fields",
      detail: "Tighten CAD investment range, franchise fee, royalty, marketing fund, liquid capital, and net-worth requirements.",
    });
  }

  if (/not stated|not verified|not publicly|unavailable|no specific/i.test(profitability)) {
    items.push({
      label: "Canadian unit economics",
      detail: "Mark AUV, gross sales, EBITDA, payback, and financial-performance data as disclosed, not disclosed, or source-backed.",
    });
  }

  if (!/closure|closed|transfer|resale|renewal/.test(growthText)) {
    items.push({
      label: "Closures, transfers, and resales",
      detail: "Add current Canadian unit count plus openings, closures, transfers, resales, and renewals where source-backed.",
    });
  }

  if (!/interview|franchisee|former operator|current operator/.test(ownerReviews)) {
    items.push({
      label: "Franchisee validation",
      detail: "Track current and former franchisee interviews separately from customer reviews or generic owner sentiment.",
    });
  }

  if (brand.governmentCount === 0) {
    items.push({
      label: "Legal and entity check",
      detail: "Add Canadian signing entity, registry, litigation, insolvency, or government/legal source coverage where available.",
    });
  }

  return items;
}

function miniField(label, value) {
  return `<div class="mini-field"><span>${escapeHtml(label)}</span><strong>${escapeHtml(String(value))}</strong></div>`;
}

function compactMoneyRow(label, value) {
  const display = isPubliclyUseful(value) ? value : "Verify";
  return `
    <div class="money-row">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(String(display))}</strong>
    </div>
  `;
}

function quickReadItem(label, value) {
  return `
    <div class="quick-read-item">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(String(value || "Not Verified"))}</strong>
    </div>
  `;
}

function metricField(label, value) {
  const display = isPubliclyUseful(value) ? value : "Verify";
  return `<div class="metric-field"><span>${escapeHtml(label)}</span><strong>${escapeHtml(String(display))}</strong></div>`;
}

function detailItem(label, value) {
  return `<div class="detail-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(simpleValue(value))}</strong></div>`;
}

function exportField(label, value) {
  return `<div class="export-field"><span>${escapeHtml(label)}</span><strong>${escapeHtml(String(value || "Not Verified"))}</strong></div>`;
}

function brandMark(brand) {
  const initials = brand.name
    .replace(/\b(canada|candidate|franchise|inc|ltd)\b/gi, "")
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
    .slice(0, 3);
  const logoUrl = brandLogoUrl(brand);
  if (!logoUrl) {
    return `<span class="logo-tile" aria-hidden="true"><span class="logo-initials">${escapeHtml(initials || "GF")}</span></span>`;
  }
  return `
    <span class="logo-tile logo-online" aria-hidden="true">
      <img src="${escapeAttr(logoUrl)}" alt="" loading="lazy" referrerpolicy="no-referrer" onload="this.closest('.logo-tile').classList.add('has-logo');" onerror="this.remove();" />
      <span class="logo-initials">${escapeHtml(initials || "GF")}</span>
    </span>
  `;
}

function brandLogoUrl(brand) {
  const domain = LOGO_DOMAINS[brand.id];
  const fallbackDomain = domain || logoDomainFromSources(brand);
  if (!fallbackDomain) return "";
  return `https://www.google.com/s2/favicons?sz=128&domain_url=https://${fallbackDomain}`;
}

function logoDomainFromSources(brand) {
  const firstSource = [...brand.officialSources, ...getContactLinks(brand)].find(Boolean);
  if (!firstSource) return "";
  try {
    const hostname = new URL(firstSource).hostname.replace(/^www\./, "");
    return hostname;
  } catch {
    return "";
  }
}

function gradeClass(grade) {
  if (/^A|^B/.test(grade)) return "good";
  if (/^C/.test(grade)) return "warn";
  return "";
}

function riskClass(risk) {
  return /high/i.test(risk) ? "risk" : /medium/i.test(risk) ? "warn" : "good";
}

function shortlistTitle(brand) {
  return state.shortlist.has(brand.id) ? `Remove ${brand.name} from shortlist` : `Add ${brand.name} to shortlist`;
}

function readShortlist() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveShortlist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...state.shortlist]));
  updateShortlistCount();
}

function readPlan() {
  try {
    const savedPlan = localStorage.getItem(PLAN_STORAGE_KEY);
    return Object.hasOwn(PLANS, savedPlan) ? savedPlan : "basic";
  } catch {
    return "basic";
  }
}

function savePlan() {
  localStorage.setItem(PLAN_STORAGE_KEY, state.plan);
}

function readMatch() {
  try {
    const saved = JSON.parse(localStorage.getItem(MATCH_STORAGE_KEY) || "{}");
    return saved.version === QUESTIONNAIRE_VERSION && saved.answers ? saved : { version: QUESTIONNAIRE_VERSION, answers: {} };
  } catch {
    return { version: QUESTIONNAIRE_VERSION, answers: {} };
  }
}

function saveMatch() {
  localStorage.setItem(MATCH_STORAGE_KEY, JSON.stringify({ version: QUESTIONNAIRE_VERSION, answers: state.match.answers }));
}

function readComparisonFields() {
  try {
    const saved = JSON.parse(localStorage.getItem(COMPARE_FIELDS_STORAGE_KEY) || "[]");
    return Array.isArray(saved) && saved.length ? saved : [...BASIC_FIELDS];
  } catch {
    return [...BASIC_FIELDS];
  }
}

function saveComparisonFields() {
  localStorage.setItem(COMPARE_FIELDS_STORAGE_KEY, JSON.stringify(state.comparisonFields));
}

function readBetaAccess() {
  try { return sessionStorage.getItem(BETA_ACCESS_STORAGE_KEY) === "1"; } catch { return false; }
}

function writeBetaAccess() {
  try { sessionStorage.setItem(BETA_ACCESS_STORAGE_KEY, "1"); } catch { /* browser storage unavailable */ }
}

function showToast(message, actionLabel) {
  document.querySelector(".app-toast")?.remove();
  const toast = document.createElement("div");
  toast.className = "app-toast";
  toast.setAttribute("role", "status");
  toast.innerHTML = `<span>${escapeHtml(message)}</span><a href="#/pricing">${escapeHtml(actionLabel)}</a>`;
  document.body.append(toast);
  window.setTimeout(() => toast.remove(), 6500);
}

function downloadComparisonCsv(rows) {
  const headers = ["Franchise", "Screening fit", "Evidence grade", "Total investment", "Franchise fee", "Royalty", "Marketing fund", "Liquid capital", "Risk", "Sources"];
  const values = rows.map((brand) => [
    brand.name,
    brand.score === null ? "n/a" : `${brand.score}/100`,
    brand.evidenceGrade,
    simpleValue(brand.totalInvestment),
    simpleValue(brand.franchiseFee),
    simpleValue(brand.royalty),
    simpleValue(brand.marketing),
    simpleValue(brand.liquidCapital),
    brand.risk,
    brand.sourceCount,
  ]);
  const csv = [headers, ...values]
    .map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(","))
    .join("\n");
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  link.download = "getfranchise-comparison.csv";
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(link.href), 0);
}

function pruneShortlistToPublishedProfiles() {
  const publishedIds = new Set(state.brands.map((brand) => brand.id));
  state.shortlist = new Set([...state.shortlist].filter((id) => publishedIds.has(id)));
  saveShortlist();
}

function updateShortlistCount() {
  navShortlistCount.textContent = String(state.shortlist.size);
}

function splitPipes(value) {
  return clean(value)
    .split("|")
    .map((item) => item.trim())
    .filter(Boolean);
}

function splitSources(value) {
  return clean(value)
    .split("|")
    .map((item) => item.trim())
    .filter((item) => /^https?:\/\//i.test(item));
}

function labelize(value) {
  const raw = clean(value);
  const categoryLabels = {
    beverage_dessert: "Beverages & Desserts",
    limited_service: "Limited-Service Food",
    full_service: "Full-Service Restaurants",
    senior_care: "Senior Care",
    home_services: "Home Services",
    shipping_printing: "Shipping & Printing",
    pet_services: "Pet Services",
    child_services: "Child Services",
    real_estate: "Real Estate",
  };
  if (categoryLabels[raw]) return categoryLabels[raw];
  return raw
    .replace(/_/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function toTitle(value) {
  const preservedAcronyms = new Set(["A&W", "KFC", "UPS", "OPA", "COBS", "RBI", "FDD", "CAD", "USA", "U.S."]);
  return clean(value).replace(/\w\S*/g, (word) => {
    const normalized = word.toUpperCase();
    if (preservedAcronyms.has(normalized)) return normalized;
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
  });
}

function slugify(value) {
  return clean(value)
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function numberOrNull(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function clean(value) {
  return String(value ?? "").trim();
}

function escapeHtml(value) {
  return clean(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/`/g, "&#096;");
}

