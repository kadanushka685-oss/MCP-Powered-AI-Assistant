# Sample questions and the output the demo mode produced

Numbers come from the shipped sample database (data generated on 2026-11-23). If you regenerate the database with `python -m database.init_db --reset` the figures will differ, but the structure stays the same.


## Question: Analyze last month's sales.

**Tools executed:** generate_sales_summary, find_best_selling_products, create_business_insights

_Demo mode: I matched your question to these tools: `generate_sales_summary`, `find_best_selling_products`, `create_business_insights`._

### Sales summary - October 2026
- **Revenue:** $48,497.15 from **168 orders** (259 units, 53 customers)
- **Average order value:** $288.67
- **Profit:** $19,333.15 (39.9% margin), average discount 3.5%
- **Top product:** Nova X Smartphone ($13,982.50)
- **Top category:** Phones (58.7% of revenue)
- **Top customer:** Chen Davis ($3,325.00)
- **Best day:** 2026-10-18 ($4,593.00)
- **Versus September 2026:** revenue +1.2%, orders +21.7%, AOV -16.9%

**Revenue by region**
| Region | Revenue | Share |
|---|---|---|
| North America | $18,765.80 | 38.7% |
| Asia-Pacific | $17,442.55 | 36.0% |
| Europe | $12,288.80 | 25.3% |

### Top products by revenue - October 2026
| # | Product | Category | Revenue | Units |
|---|---|---|---|---|
| 1 | Nova X Smartphone | Phones | $13,982.50 | 18 |
| 2 | Nova Lite Smartphone | Phones | $10,094.70 | 26 |
| 3 | ProBook 14 Laptop | Laptops | $4,427.50 | 4 |
| 4 | Nova Max Pro Smartphone | Phones | $4,396.00 | 4 |
| 5 | OfficeSuite 1-Year License | Software | $2,059.20 | 21 |

**Nova X Smartphone** leads with $13,982.50 (28.8% of revenue) and 18 units.

### Business insights - October 2026
- [i] **Revenue is stable.** Revenue changed by +1.2% compared with the previous period. _Action: Test a targeted promotion on high-margin products to lift growth._
- [!] **Average order value dropped 16.9%.** AOV is now $288.67. _Action: Bundle accessories with devices to lift order value._
- [i] **Nova X Smartphone is the top revenue product.** It generated $13,982.50 (28.8% of revenue) from 18 units. _Action: Make sure it never runs out of stock and feature it in campaigns._
- [i] **Phones is the strongest category.** 58.7% of revenue. Tablets is the smallest at 2.3%. _Action: Look for cross-selling between Phones and Tablets._
- [!] **12 products are under-performing.** They earn less than half of the average product revenue. Weakest: WorkStation 16 Laptop, ClearView 32 4K Monitor, Setup and Install Service. _Action: Run a promotion, bundle them with best sellers, or review whether to keep stocking them._
- [!] **Revenue depends on a few customers.** The top 5 customers account for 29.5% of revenue. _Action: Start a loyalty or account-management plan for them, and grow the wider customer base._
- [+] **Healthy discount discipline.** The average discount is only 3.5% with a 39.9% profit margin. _Action: Keep discounts targeted._
- [i] **North America leads regional sales.** Europe is the smallest region with 25.3% of revenue. _Action: Consider a local campaign in Europe._


## Question: Which product generated the highest revenue?

**Tools executed:** find_best_selling_products

_Demo mode: I matched your question to these tools: `find_best_selling_products`._

### Top products by revenue - All time
| # | Product | Category | Revenue | Units |
|---|---|---|---|---|
| 1 | Nova X Smartphone | Phones | $84,574.15 | 109 |
| 2 | ProBook 14 Laptop | Laptops | $64,112.50 | 58 |
| 3 | Nova Lite Smartphone | Phones | $51,431.10 | 133 |

**Nova X Smartphone** leads with $84,574.15 (18.4% of revenue) and 109 units.


## Question: Show monthly revenue.

**Tools executed:** calculate_monthly_sales

_Demo mode: I matched your question to these tools: `calculate_monthly_sales`._

### Monthly revenue
| Month | Revenue | Orders | AOV | Growth |
|---|---|---|---|---|
| 2025-12 | $36,480.70 | 168 | $217.15 | +418.4% |
| 2026-01 | $34,349.60 | 99 | $346.97 | -5.8% |
| 2026-02 | $25,781.10 | 87 | $296.33 | -24.9% |
| 2026-03 | $37,459.75 | 110 | $340.54 | +45.3% |
| 2026-04 | $28,081.85 | 116 | $242.08 | -25.0% |
| 2026-05 | $32,806.40 | 131 | $250.43 | +16.8% |
| 2026-06 | $38,812.80 | 126 | $308.04 | +18.3% |
| 2026-07 | $29,502.70 | 124 | $237.92 | -24.0% |
| 2026-08 | $41,139.80 | 133 | $309.32 | +39.4% |
| 2026-09 | $47,943.60 | 138 | $347.42 | +16.5% |
| 2026-10 | $48,497.15 | 168 | $288.67 | +1.2% |
| 2026-11 | $51,645.75 | 145 | $356.18 | +6.5% |

_The latest month may be incomplete (month to date). Data through 2026-11-23._


## Question: Find the top 5 selling products.

**Tools executed:** find_best_selling_products

_Demo mode: I matched your question to these tools: `find_best_selling_products`._

### Top products by units - All time
| # | Product | Category | Revenue | Units |
|---|---|---|---|---|
| 1 | ShieldCase Phone Case | Accessories | $6,381.15 | 346 |
| 2 | AeroBuds Wireless Earbuds | Accessories | $23,147.00 | 301 |
| 3 | ChargeFast 65W Charger | Accessories | $11,155.95 | 296 |
| 4 | ErgoMouse Wireless Mouse | Accessories | $6,327.80 | 227 |
| 5 | USB-C Hub 7-in-1 | Accessories | $8,072.75 | 170 |

**ShieldCase Phone Case** leads with 346 units sold.


## Question: Compare this month and last month.

**Tools executed:** compare_periods

_Demo mode: I matched your question to these tools: `compare_periods`._

### Comparison
| Metric | November 2026 (month to date) | October 2026 | Change |
|---|---|---|---|
| Revenue | $51,645.75 | $48,497.15 | +6.5% |
| Orders | 145 | 168 | -13.7% |
| Units | 216 | 259 | -16.6% |
| Average order value | $356.18 | $288.67 | +23.4% |

November 2026 (month to date) is incomplete, so it is also compared with the same 23 days of October 2026. Like-for-like revenue change: **+39.4%** (versus $37,038.15).


## Question: Generate a PDF sales report.

**Tools executed:** generate_report

_Demo mode: I matched your question to these tools: `generate_report`._

### Report created
- **File:** `sales_report_<period>_<timestamp>.pdf` (PDF, 6.7 KB)
- **Period:** October 2026
- Download it with the button below, or from the **Reports** page.


## Question: Give me business growth suggestions.

**Tools executed:** create_business_insights

_Demo mode: I matched your question to these tools: `create_business_insights`._

### Business insights - Last 90 days (Aug 26 - Nov 23, 2026)
- [+] **Revenue grew 42.4%.** Revenue was $153,954.50 versus $108,143.45 in the previous period. _Action: Find out which channels and products drove the growth and repeat them._
- [+] **Average order value rose 11.6%.** AOV is now $322.76. _Action: Keep promoting bundles and premium models._
- [i] **Nova X Smartphone is the top revenue product.** It generated $34,037.40 (22.1% of revenue) from 44 units. _Action: Make sure it never runs out of stock and feature it in campaigns._
- [i] **Phones is the strongest category.** 45.1% of revenue. Services is the smallest at 2.0%. _Action: Look for cross-selling between Phones and Services._
- [!] **12 products are under-performing.** They earn less than half of the average product revenue. Weakest: Setup and Install Service, TabMini 8 Tablet, SecureNet Antivirus. _Action: Run a promotion, bundle them with best sellers, or review whether to keep stocking them._
- [!] **Best sellers with low stock.** UltraSlim 13 Laptop (25 left) _Action: Reorder soon to avoid lost sales._
- [!] **Revenue depends on a few customers.** The top 5 customers account for 27.1% of revenue. _Action: Start a loyalty or account-management plan for them, and grow the wider customer base._
- [+] **Healthy discount discipline.** The average discount is only 3.4% with a 37.4% profit margin. _Action: Keep discounts targeted._
- [i] **Asia-Pacific leads regional sales.** Europe is the smallest region with 25.2% of revenue. _Action: Consider a local campaign in Europe._


## Question: Analyze last month's sales and create a detailed report.

**Tools executed:** generate_sales_summary, find_best_selling_products, create_business_insights, generate_report

_Demo mode: I matched your question to these tools: `generate_sales_summary`, `find_best_selling_products`, `create_business_insights`, `generate_report`._

### Sales summary - October 2026
- **Revenue:** $48,497.15 from **168 orders** (259 units, 53 customers)
- **Average order value:** $288.67
- **Profit:** $19,333.15 (39.9% margin), average discount 3.5%
- **Top product:** Nova X Smartphone ($13,982.50)
- **Top category:** Phones (58.7% of revenue)
- **Top customer:** Chen Davis ($3,325.00)
- **Best day:** 2026-10-18 ($4,593.00)
- **Versus September 2026:** revenue +1.2%, orders +21.7%, AOV -16.9%

**Revenue by region**
| Region | Revenue | Share |
|---|---|---|
| North America | $18,765.80 | 38.7% |
| Asia-Pacific | $17,442.55 | 36.0% |
| Europe | $12,288.80 | 25.3% |

### Top products by revenue - October 2026
| # | Product | Category | Revenue | Units |
|---|---|---|---|---|
| 1 | Nova X Smartphone | Phones | $13,982.50 | 18 |
| 2 | Nova Lite Smartphone | Phones | $10,094.70 | 26 |
| 3 | ProBook 14 Laptop | Laptops | $4,427.50 | 4 |
| 4 | Nova Max Pro Smartphone | Phones | $4,396.00 | 4 |
| 5 | OfficeSuite 1-Year License | Software | $2,059.20 | 21 |

**Nova X Smartphone** leads with $13,982.50 (28.8% of revenue) and 18 units.

### Business insights - October 2026
- [i] **Revenue is stable.** Revenue changed by +1.2% compared with the previous period. _Action: Test a targeted promotion on high-margin products to lift growth._
- [!] **Average order value dropped 16.9%.** AOV is now $288.67. _Action: Bundle accessories with devices to lift order value._
- [i] **Nova X Smartphone is the top revenue product.** It generated $13,982.50 (28.8% of revenue) from 18 units. _Action: Make sure it never runs out of stock and feature it in campaigns._
- [i] **Phones is the strongest category.** 58.7% of revenue. Tablets is the smallest at 2.3%. _Action: Look for cross-selling between Phones and Tablets._
- [!] **12 products are under-performing.** They earn less than half of the average product revenue. Weakest: WorkStation 16 Laptop, ClearView 32 4K Monitor, Setup and Install Service. _Action: Run a promotion, bundle them with best sellers, or review whether to keep stocking them._
- [!] **Revenue depends on a few customers.** The top 5 customers account for 29.5% of revenue. _Action: Start a loyalty or account-management plan for them, and grow the wider customer base._
- [+] **Healthy discount discipline.** The average discount is only 3.5% with a 39.9% profit margin. _Action: Keep discounts targeted._
- [i] **North America leads regional sales.** Europe is the smallest region with 25.3% of revenue. _Action: Consider a local campaign in Europe._

### Report created
- **File:** `sales_report_<period>_<timestamp>.pdf` (PDF, 6.7 KB)
- **Period:** October 2026
- Download it with the button below, or from the **Reports** page.


## Question: Search customers in London

**Tools executed:** search_customers

_Demo mode: I matched your question to these tools: `search_customers`._

### Customers matching 'london' (3 found)
| ID | Name | City | Segment | Orders | Spent |
|---|---|---|---|---|---|
| 15 | Harper Miller | London | Enterprise | 12 | $3,306.55 |
| 9 | Emma Reed | London | Enterprise | 9 | $2,312.50 |
| 51 | Ava Garcia | London | Consumer | 12 | $2,191.05 |


## Question: How is the Nova X Smartphone performing?

**Tools executed:** analyze_product_performance

_Demo mode: I matched your question to these tools: `analyze_product_performance`._

### Nova X Smartphone (Phones)
- **Verdict:** Top performer - rank 1 of 22 by revenue
- **Revenue:** $84,574.15 (18.4% of all revenue), 109 units, 94 orders
- **Profit:** $27,894.15, unit margin 34.9%, average discount 2.8%
- **Stock on hand:** 120

**Recent monthly trend**
| Month | Revenue | Units |
|---|---|---|
| 2026-06 | $3,915.10 | 5 |
| 2026-07 | $6,911.35 | 9 |
| 2026-08 | $9,388.25 | 12 |
| 2026-09 | $4,594.25 | 6 |
| 2026-10 | $13,982.50 | 18 |
| 2026-11 | $13,862.65 | 18 |


## Question: Send a summary to Slack

**Tools executed:** send_report_to_slack

_Demo mode: I matched your question to these tools: `send_report_to_slack`._

### Integration result
- **Mode:** MOCK
- MOCK: message saved to mock_slack_outbox.jsonl. Nothing was sent to Slack.
