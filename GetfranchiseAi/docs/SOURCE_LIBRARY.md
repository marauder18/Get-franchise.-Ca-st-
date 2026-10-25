# GetFranchise AI Source Library

Use these source families for franchise research. Rank Canadian primary sources above U.S., global, aggregator, scraped, or anecdotal sources. The website should expose weak evidence instead of smoothing it over.

## Source Hierarchy Protocol
- Target 95% of investor-facing report claims from reliability 80+ sources.
- Search first for a Canadian Franchise Disclosure Document, Canadian disclosure package, CFA disclosure listing, or franchise registry record.
- Use official Canadian franchisor pages as the secondary anchor for fee schedules, locations, territory terms, training, and contact details.
- Use Canadian federal or provincial corporation registries to verify the exact legal franchisor/signing entity, active status, and incorporation details.
- Use CFA, FRANdata, and source-backed franchise directories only as cross-checks. If the official website and an aggregator disagree on unit count, use the official number and flag the discrepancy.
- Mark every publicly extracted fee, investment, royalty, AUV, closure, litigation, renewal, and transfer field as `Franchisor Confirmation: Required` until confirmed directly.

## Primary / Highest Priority
- The franchisor's official website
- The franchisor's official franchising page, commonly formatted like franchise.brand.com or brand.com/franchising
- Canadian Franchise Disclosure Document / Canadian disclosure package where applicable
- Franchise Disclosure Document (FDD), when U.S.-only, labelled as U.S. context only
- Official Canadian franchisor communication or franchise application materials
- Public filings and earnings reports for public franchisors
- Canadian legal/corporate registry records for the signing franchisor entity

## Franchise Directories and FDD Sources
- Canadian Franchise Association (CFA) Directory or international directory equivalents
- International Franchise Association (IFA)
- Franchimp
- Franchise Help
- The FDD Store
- FDD Exchange
- FRANdata
- Franchise Business Review

## Reference and Context Sources
- Wikipedia for background only, never final investment terms
- Investopedia franchise articles for education/context only
- Business Insider or similar FDD-cost explainers for U.S. context only
- Franchise consultants, used cautiously and labelled as secondary

## Risk, Legal, and Diligence Sources
- Bankruptcy and insolvency records
- Court/litigation databases, including CanLII and provincial court databases
- Health inspection reports
- Statistics Canada market demographics
- Job postings to gauge hiring pressure and expansion signals
- LinkedIn for company growth and leadership changes
- YouTube interviews with franchisees or operators
- Lender/SBA-style financing information where applicable, labelled as U.S. context when not Canadian

## Source Rules
- Do not present U.S. FDD or SBA data as Canadian investment data.
- Do not count global store count, founding year, or brand history as verified Canadian investment evidence.
- Do not assign numeric scores to unknown fields.
- If a Canadian FDD/disclosure package, franchisee interviews, or store-level P&L is not publicly available, mark it as Not publicly available, not Unknown.
- Every investor-facing report must separate Canadian-verified data, U.S. context-only data, public secondary data, and required private due diligence.
- Do not use Wikipedia for financials, unit counts, screening scores, or ownership status.
- Do not use generic QSR, home-service, cleaning, tutoring, staffing, or category benchmarks to estimate EBITDA, profit margin, payback, or AUV. Write `Not Verified`.
- Do not use Reddit, Facebook, forums, or unsourced reviews in the screening score. They may be directional sentiment only and must be labelled `Not Verified`.
- Do not use U.S. AUV, Item 19, SBA, or FDD figures as Canadian unit economics. Canadian-specific data is required, otherwise leave the field blank or `Not Verified`.

## Investor-Grade Gate
- Set `Investor-Grade Status: Not investment-ready` unless the Canadian disclosure document, CAD fee schedule, Canadian AUV, transfer terms, 5-year closure history, and current franchisee contact list are obtained or confirmed.
- Screening scores with failed evidence gates are directional only and must not be used for financing.
