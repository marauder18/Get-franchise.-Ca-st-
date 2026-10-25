# GetFranchise Website Data Quality Audit

Generated from `output/franchises/GETFRANCHISE_BRAND_DATA_2026-07-18.json` after applying the source firewall.

## Current Website Export
- Brand rows: 484
- Source-less rows: 370
- Source-less rows with numeric screening scores: 0
- Rows containing banned `Estimated (industry benchmark)` language: 0
- Thin-evidence rows with 1-2 sources: 55

## Worst Source Gaps by Category
| Category | Source-less rows |
| --- | ---: |
| limited_service | 89 |
| beverage_dessert | 47 |
| full_service | 24 |
| shipping_printing | 18 |
| staffing | 18 |
| finance | 18 |
| pet_services | 17 |
| hotel | 17 |
| senior_care | 17 |
| real_estate | 17 |
| fitness | 17 |
| education | 17 |
| automotive | 16 |
| home_services | 16 |
| child_services | 12 |
| cleaning | 10 |

## Worst-of-Worst Examples
These records have zero website-grade source links and should be rebuilt from Canadian primary sources before scoring:

- Big O Tires Canada Candidate
- CARSTAR Canada
- CSN Collision Canada Candidate
- Fix Auto Canada
- Great Canadian Oil Change
- LINE-X Canada
- Maaco Canada
- Mister Transmission
- NAPA AUTOPRO Franchise Candidate
- NOVUS Glass Canada
- OK Tire Stores
- Speedy Auto Service
- Take 5 Oil Change Canada
- Tint World Canada
- Valvoline Instant Oil Change Canada
- Ziebart Canada
- Baskin Robbins Canada
- Ben & Jerry's Scoop Shops Canada
- Blenz Coffee
- Bridgehead Coffee

## Next Research Queue
Prioritize categories with the highest public-facing damage first:

1. limited_service
2. beverage_dessert
3. full_service
4. shipping_printing
5. staffing

Each rebuild should start with Canadian disclosure/FDD search, then official Canadian franchisor pages, then registry/legal confirmation, then CFA/FRANdata-style cross-checks.
