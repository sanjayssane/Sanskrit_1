# Advanced Analytics Requirements

## Shop Management System — "Sanskrit Sahitya Ratnakar"

| | |
|---|---|
| **Document Version** | 1.0 |
| **Date** | 11 June 2026 |
| **Status** | Draft — pending owner approval |
| **Based On** | PRD.md v1.0, TECHNICAL_DESIGN.md v1.0, DATABASE_PLAN.md v1.0, ERD.md v1.0 |
| **Scope** | Advanced analytics and business intelligence layer (v2.0+) |

---

## 1. Introduction

### 1.1 Purpose

This document defines the functional and non-functional requirements for **advanced analytics** in the Sanskrit Sahitya Ratnakar shop management system. It extends the baseline reporting delivered in v1.0 (FR-7, FR-8) with interactive insights, trend analysis, forecasting aids, and operational dashboards that help the owner make stocking, pricing, and purchasing decisions.

### 1.2 Relationship to v1.0

v1.0 already provides:

| Module | Current capability |
|---|---|
| **Dashboard (FR-8)** | Today's sales/purchases, low-stock count, recent transactions; owner MTD revenue, COGS, gross profit, margin |
| **Sale–Purchase Statement (FR-7.1)** | Period totals, retail vs wholesale split, day-wise and month-wise breakdown, transaction drill-down, CSV/Excel export |
| **Profit & Loss (FR-7.2)** | Owner-only P&L with last-purchase-price COGS, breakdown by sale type, top 20 profitable books |
| **Stock Report (FR-7.3)** | Current stock valuation, low-stock list, CSV/Excel export |

Advanced analytics **does not replace** these reports. It adds a dedicated **Analytics** area (or enhanced Dashboard/Reports sections) with charts, comparisons, rankings, alerts, and drill-downs that v1.0 does not provide.

### 1.3 Business Goals

| Goal | How analytics supports it |
|---|---|
| **Stock smarter** | Identify fast movers, dead stock, and reorder candidates before shelves go empty |
| **Improve margins** | Spot titles sold below cost, excessive discounting, and wholesale vs retail profitability gaps |
| **Understand demand** | See seasonal patterns, category trends, and bestsellers by script-friendly titles |
| **Manage suppliers & customers** | Rank suppliers by volume/cost; rank wholesale customers by revenue and frequency |
| **Monitor staff performance** | Compare transaction volume and accuracy across employees (audit-friendly, not punitive by default) |
| **Plan cash flow** | Visualize purchase vs sales cash outflow/inflow over time |

### 1.4 Out of Scope (this document)

The following remain **out of scope** unless explicitly added in a later revision:

- GST/tax analytics (PRD §1.2)
- Online/e-commerce or web traffic analytics
- Barcode or POS hardware integration
- Multi-branch consolidated analytics
- External BI tools (Power BI, Metabase) as mandatory dependencies
- Machine-learning demand forecasting beyond simple statistical projections
- Customer credit/ledger (udhaar) analytics — depends on a future credit module
- Real-time streaming analytics; batch/on-demand computation is sufficient

---

## 2. Users and Access Control

### 2.1 Roles

Analytics permissions extend the v1.0 permission matrix (PRD §3.2). The default policy is **owner-centric**: employees see operational summaries only; financial deep-dives are owner-only.

| Analytics area | Owner | Employee |
|---|---|---|
| Enhanced dashboard KPIs & charts | Full | Limited (see §2.2) |
| Sales trends & bestsellers | Full | Yes — aggregates only, no margin/COGS |
| Purchase & supplier analytics | Full | Summary only (totals, no supplier margin comparison) |
| Inventory & turnover analytics | Full | Yes — stock levels and movement, no valuation totals |
| Profit, margin & COGS analytics | Full | **No** |
| Wholesale customer analytics | Full | Yes — customer names and volumes, no profit |
| Employee performance comparison | Full | **No** (sees own stats only) |
| Export analytics data (CSV/Excel) | Full | Per permitted views only |
| Configure analytics settings (thresholds, fiscal year) | Full | **No** |

### 2.2 Employee-visible analytics (minimum)

Employees shall see a simplified analytics panel useful at the counter:

- Today's and this week's sales count and revenue (no COGS)
- Top 10 bestselling titles (current month)
- Low-stock and out-of-stock alerts
- Personal transaction count for the current day/week (self only)

---

## 3. Global Analytics Conventions

These rules apply across all analytics modules.

### 3.1 Data inclusion rules (AR-GLOBAL-1)

- **Cancelled transactions** (`is_cancelled = 1`) shall be **excluded** from all analytics unless the user explicitly toggles "Include cancelled" (owner only, off by default).
- **Deactivated books** (`is_active = 0`) shall be included in historical analytics but excluded from active assortment metrics unless toggled.
- **Deactivated users** remain attributed in historical employee analytics.
- **Stock adjustments** shall be included in inventory movement analytics and flagged separately from purchases/sales.

### 3.2 Date and time (AR-GLOBAL-2)

- Business dates use existing `TEXT` ISO `YYYY-MM-DD` fields (`sale_date`, `purchase_date`, `adjustment_date`).
- Default period presets: Today, Yesterday, Last 7 days, Last 30 days, This month, Last month, This quarter, This year, Custom range.
- Fiscal year start month shall be configurable (default: **April** — common in India); stored in app settings, not hard-coded.
- Comparison modes where applicable: **vs previous period** (same length) and **vs same period last year** (when ≥12 months of data exist).

### 3.3 Money and COGS (AR-GLOBAL-3)

- All internal calculations use **integer paise**; display uses existing `fmt_inr` formatting.
- Default COGS method remains **last purchase price per book** (PRD §9.4) for consistency with v1.0 P&L.
- Advanced analytics shall optionally support **weighted-average purchase price** as an alternate COGS view (owner toggle, clearly labeled). FIFO remains a future enhancement (PRD §11).
- Analytics that show "profit" or "margin" shall display the active COGS method in a caption.

### 3.4 Dimensions and filters (AR-GLOBAL-4)

All analytics views shall support a consistent filter bar where data exists:

| Filter | Applies to |
|---|---|
| Date range / preset | All |
| Sale type (retail / wholesale / both) | Sales, P&L, customer |
| Book (search Roman or Devanagari) | Most modules |
| Category | Book, sales, inventory |
| Publisher | Book, sales, inventory |
| Language | Book, sales |
| Supplier | Purchases, inventory inbound |
| Wholesale customer | Sales, customer analytics |
| Payment method (cash / UPI / card / cheque) | Sales |
| Created by (user) | Sales, purchases, employee analytics |

Filters shall be combinable. Clearing filters resets to module defaults.

### 3.5 Visualization standards (AR-GLOBAL-5)

- Primary chart library: **Streamlit-native** (`st.line_chart`, `st.bar_chart`, `st.area_chart`) or **Altair** / **Plotly** if added to `requirements.txt` — decision at implementation time.
- Charts must render Devanagari labels correctly (UTF-8, NFR-1).
- Every chart/table with >20 rows shall support CSV/Excel export via existing `utils/exports.py` patterns (FR-7.4).
- Color palette shall be accessible (sufficient contrast) and consistent across modules.
- Empty states shall show a clear message ("No data for the selected filters") rather than blank widgets.

### 3.6 Performance (AR-GLOBAL-6)

- Analytics queries shall complete within **3 seconds** on a database with ≥50,000 line items on the shop's target PC (aligns with NFR-3 spirit).
- Heavy aggregations shall use SQL in `services/analytics_service.py` (new) or materialized summary tables (see §8) — not row-by-row Python over full history.
- Date-range queries shall leverage existing indexes (`idx_sales_date`, `idx_purchases_date`, `idx_sitems_book`, etc.).

---

## 4. Module Requirements

Requirements are prefixed **AR-** (Analytics Requirement). Priority: **P1** (must-have for v2.0 analytics MVP), **P2** (should-have), **P3** (nice-to-have).

---

### 4.1 Enhanced Dashboard Analytics (AR-DASH)

Extends FR-8 with visual and comparative KPIs.

| ID | Priority | Requirement |
|---|---|---|
| AR-DASH-1 | P1 | Show **sales revenue trend** for the last 30 days as a line or area chart (daily buckets). |
| AR-DASH-2 | P1 | Show **retail vs wholesale revenue split** for the current month (donut or stacked bar). |
| AR-DASH-3 | P1 | Display **comparison metrics** vs previous period: sales revenue, transaction count, average ticket size, units sold. Show absolute and percentage change with up/down indicator. |
| AR-DASH-4 | P1 | Owner: **MTD gross profit trend** (daily cumulative or weekly bars). |
| AR-DASH-5 | P2 | Show **payment method breakdown** for sales in the selected period (cash vs UPI vs card vs cheque). |
| AR-DASH-6 | P2 | Show **top 5 bestselling titles** (by quantity) for the current month with quick links to book detail. |
| AR-DASH-7 | P2 | Show **purchase vs sales cash flow** chart (dual line: daily purchase total vs daily sales total) for last 90 days — owner only. |
| AR-DASH-8 | P3 | Configurable dashboard widgets: owner chooses which cards/charts appear (persisted in session or settings). |

---

### 4.2 Sales Analytics (AR-SALE)

| ID | Priority | Requirement |
|---|---|---|
| AR-SALE-1 | P1 | **Revenue over time** chart with selectable granularity: daily, weekly, monthly. |
| AR-SALE-2 | P1 | **Units sold over time** chart (same granularities). |
| AR-SALE-3 | P1 | **Average transaction value** and **average units per transaction** for the period. |
| AR-SALE-4 | P1 | **Bestsellers table**: rank books by quantity sold and by revenue; columns: code, titles (both scripts), category, qty, revenue, % of total revenue. |
| AR-SALE-5 | P1 | **Slow movers table**: active books with stock > 0 but zero sales in the last N days (N configurable, default 90). |
| AR-SALE-6 | P1 | **Discount analysis**: total discounts given, discount as % of gross revenue, top 10 sales by discount amount — owner only. |
| AR-SALE-7 | P2 | **Price override analysis**: count and volume of line items where `unit_price` ≠ catalog default (retail/wholesale); average override delta — owner only. |
| AR-SALE-8 | P2 | **Day-of-week heatmap or bar chart**: average sales by weekday (helps staffing decisions). |
| AR-SALE-9 | P2 | **Hour-of-day distribution** if `created_at` timestamp is used (counter busy hours). |
| AR-SALE-10 | P2 | **Retail vs wholesale** side-by-side: revenue, units, transaction count, avg ticket, margin — owner for margin columns. |
| AR-SALE-11 | P3 | **Category performance**: revenue and units by `books.category`. |
| AR-SALE-12 | P3 | **Publisher performance**: revenue and units by `books.publisher`. |

---

### 4.3 Purchase Analytics (AR-PUR)

| ID | Priority | Requirement |
|---|---|---|
| AR-PUR-1 | P1 | **Purchase spend over time** (daily / weekly / monthly). |
| AR-PUR-2 | P1 | **Units purchased over time**. |
| AR-PUR-3 | P1 | **Supplier ranking table**: supplier name, purchase count, total qty, total spend, avg unit cost across all items, last purchase date. |
| AR-PUR-4 | P1 | **Top purchased titles**: by quantity and by spend. |
| AR-PUR-5 | P2 | **Supplier concentration**: % of spend from top 3 suppliers (insight for dependency risk). |
| AR-PUR-6 | P2 | **Purchase price trend** per book: line chart of unit price over time for a selected book (detect cost increases). |
| AR-PUR-7 | P2 | **Lead time proxy**: days between consecutive purchases of the same book (when purchase history allows). |
| AR-PUR-8 | P3 | **New titles added to catalog** count per month (from `books.created_at`). |

---

### 4.4 Inventory Analytics (AR-INV)

Builds on FR-6 and `v_current_stock` / `v_stock_ledger`.

| ID | Priority | Requirement |
|---|---|---|
| AR-INV-1 | P1 | **Inventory valuation summary**: total titles, total units, total value (qty × last purchase price) — matches stock report but with trend. |
| AR-INV-2 | P1 | **Stock movement summary** for period: units in (purchases), units out (sales), net adjustments, net change. |
| AR-INV-3 | P1 | **Inventory turnover ratio** (owner): COGS for period ÷ average inventory value; document formula in UI. |
| AR-INV-4 | P1 | **Days of supply** per book (or category): current stock ÷ average daily sales (last 30 days); flag titles below configurable threshold (default 14 days). |
| AR-INV-5 | P1 | **Dead stock report**: books with stock > 0 and no sales in last N days (default 180); show tied-up capital (stock × last purchase price). |
| AR-INV-6 | P1 | **Out-of-stock events**: titles that had sales in period but current stock = 0 (lost sales indicator). |
| AR-INV-7 | P2 | **ABC classification**: A = top 80% revenue, B = next 15%, C = remaining 5% (by book revenue in last 12 months). |
| AR-INV-8 | P2 | **Reorder suggestions**: books where stock ≤ low_stock_threshold OR days of supply < threshold; suggest reorder qty = max(threshold, 30-day sales) − current stock. |
| AR-INV-9 | P2 | **Adjustment analytics**: count and net qty of adjustments by reason keyword / reason text — owner only. |
| AR-INV-10 | P3 | **Stock aging**: for each book, days since last inbound movement (purchase or positive adjustment). |

---

### 4.5 Profitability & Financial Analytics (AR-FIN)

Extends FR-7.2 P&L with deeper financial views. **Owner only.**

| ID | Priority | Requirement |
|---|---|---|
| AR-FIN-1 | P1 | **Gross profit trend** over time (daily / weekly / monthly). |
| AR-FIN-2 | P1 | **Margin % trend** over time. |
| AR-FIN-3 | P1 | **Profit by sale type** (retail vs wholesale) — chart + table; extends existing P&L `by_type`. |
| AR-FIN-4 | P1 | **Profit by book**: full sortable table (not limited to top 20) with margin % per book. |
| AR-FIN-5 | P1 | **Loss-making sales detection**: line items where `unit_price` < last purchase price; aggregate count, units, and rupee loss. |
| AR-FIN-6 | P2 | **Profit by category** and **profit by publisher**. |
| AR-FIN-7 | P2 | **Period comparison P&L**: side-by-side two date ranges (e.g., this quarter vs last quarter). |
| AR-FIN-8 | P2 | **Purchase-to-sales ratio** over time (inventory investment vs revenue). |
| AR-FIN-9 | P2 | Optional **weighted-average COGS** toggle with reconciliation note vs last-purchase method. |
| AR-FIN-10 | P3 | **Break-even daily sales** estimate: average daily fixed costs proxy (optional manual input in settings) vs average margin. |

---

### 4.6 Customer Analytics (AR-CUST)

Wholesale customers only; retail walk-ins are anonymous aggregate.

| ID | Priority | Requirement |
|---|---|---|
| AR-CUST-1 | P1 | **Wholesale customer ranking**: name, transaction count, total revenue, total units, avg order value, last order date. |
| AR-CUST-2 | P1 | **Customer concentration**: % revenue from top 5 wholesale customers. |
| AR-CUST-3 | P2 | **Customer purchase frequency**: avg days between orders per customer. |
| AR-CUST-4 | P2 | **Titles per customer**: which books each wholesale customer buys most (drill-down). |
| AR-CUST-5 | P2 | **Inactive customers**: wholesale customers with no orders in last N days (default 90) but historical orders exist. |
| AR-CUST-6 | P3 | **Retail aggregate**: count of retail transactions and revenue (no customer identity — data model limitation). |

---

### 4.7 Employee Analytics (AR-EMP)

**Owner only** for cross-user comparison; employees see AR-EMP-6 only.

| ID | Priority | Requirement |
|---|---|---|
| AR-EMP-1 | P1 | **Transactions recorded** per user: sales count, purchase count, total sales revenue entered, period filter. |
| AR-EMP-2 | P1 | **Average sale size** per user (retail and wholesale separately). |
| AR-EMP-3 | P2 | **Cancellation rate**: % of transactions cancelled by user (numerator/denominator clearly defined). |
| AR-EMP-4 | P2 | **Discount granted** total per user (owner concern for policy compliance). |
| AR-EMP-5 | P2 | **Activity timeline**: transactions per day per user (heatmap or table). |
| AR-EMP-6 | P1 | **Self-service stats** for employees: own transaction counts for today / this week on dashboard. |

---

### 4.8 Alerts & Insights (AR-ALERT)

Proactive notifications surfaced on Dashboard and/or a dedicated **Insights** panel.

| ID | Priority | Requirement |
|---|---|---|
| AR-ALERT-1 | P1 | **Low stock** — already in FR-8; analytics adds trend ("3 more titles went low this week"). |
| AR-ALERT-2 | P1 | **Dead stock capital alert**: total rupees tied up in dead stock exceeds configurable threshold. |
| AR-ALERT-3 | P1 | **Margin drop alert**: MTD margin % dropped > X points vs last month (X configurable, default 5). |
| AR-ALERT-4 | P2 | **Sales spike/drop**: daily sales > 2× or < 0.5× trailing 30-day average. |
| AR-ALERT-5 | P2 | **Loss-making sale today**: any line item sold below cost today — owner notification on dashboard. |
| AR-ALERT-6 | P3 | **Reorder reminders**: list from AR-INV-8 pushed to dashboard. |

Alerts are **informational** (in-app banners/cards), not email/SMS unless a future notification module is added.

---

## 5. User Interface Requirements

### 5.1 Navigation (AR-UI-1)

- Add a Streamlit page **`9_Analytics.py`** (or split into sub-pages if content is large).
- Alternatively, reorganize as tabs under an expanded **Reports & Analytics** section — implementation choice, but all AR modules must be reachable within **2 clicks** from the sidebar.
- Page title: **Analytics**; subtitle clarifies owner vs employee view.

### 5.2 Layout pattern (AR-UI-2)

Each analytics submodule follows a consistent layout:

1. **Filter bar** (§3.4) at top
2. **KPI metric row** (3–6 `st.metric` widgets)
3. **Primary chart(s)**
4. **Detail table** with export buttons
5. **Footnotes**: COGS method, last refreshed time, row count

### 5.3 Drill-down (AR-UI-3)

- Clicking a book in a bestseller or dead-stock table shall open an **Book Analytics detail** expander or modal section showing: sales trend, purchase trend, current stock, margin history, stock ledger link.
- Clicking a supplier or customer row opens analogous detail for that entity.

### 5.4 Mobile / LAN browsers (AR-UI-4)

- Layouts shall remain usable at **1280×720** (typical shop counter monitor) and degrade gracefully on tablet-width browsers (NFR-8).
- Charts stack vertically on narrow widths; tables horizontal-scroll.

### 5.5 Language and scripts (AR-UI-5)

- All analytics labels in **English** for v2.0 (shop staff convention from v1.0 UI).
- Book titles always show **both Roman and Devanagari** where a book name is displayed.

---

## 6. Export and Reporting (AR-EXP)

| ID | Priority | Requirement |
|---|---|---|
| AR-EXP-1 | P1 | Every analytics table exportable to CSV and Excel via `utils/exports.py`. |
| AR-EXP-2 | P2 | **Analytics snapshot PDF**: owner can export a summary PDF of current dashboard/analytics view (reuse `reportlab` from receipts). |
| AR-EXP-3 | P2 | Export filename includes report name, date range, and generation date (existing convention). |
| AR-EXP-4 | P3 | Scheduled weekly analytics summary — out of scope unless job runner added; document as future. |

---

## 7. Technical Architecture

### 7.1 Application structure

```
services/
  analytics_service.py    # NEW: all analytics queries and aggregations
pages/
  9_Analytics.py          # NEW: Streamlit UI (or multiple pages 9a, 9b, ...)
db/migrations/
  0003_analytics_indexes.sql   # OPTIONAL: extra indexes for analytics queries
  0004_analytics_summaries.sql # OPTIONAL: summary tables (see §7.3)
tests/
  test_analytics.py       # NEW: unit tests for key metrics
```

- **No SQL in Streamlit pages** — same three-layer rule as TECHNICAL_DESIGN.md §2.
- `analytics_service.py` returns plain dicts, lists, and pandas DataFrames consumable by the UI.

### 7.2 Service function catalog (minimum)

Implementations shall expose functions such as:

| Function | Returns |
|---|---|
| `sales_trend(start, end, granularity, filters)` | time series revenue, units, txn count |
| `bestsellers(start, end, limit, filters)` | ranked book list |
| `slow_movers(days, filters)` | books with stock, no recent sales |
| `purchase_trend(start, end, granularity, filters)` | time series |
| `supplier_ranking(start, end, filters)` | ranked suppliers |
| `inventory_turnover(start, end)` | ratio + components |
| `dead_stock(days, filters)` | tied-up capital list |
| `reorder_suggestions(filters)` | suggested quantities |
| `profit_trend(start, end, granularity, cogs_method)` | owner only |
| `profit_by_dimension(start, end, dimension, cogs_method)` | category, publisher, book |
| `wholesale_customer_ranking(start, end, filters)` | customer table |
| `employee_activity(start, end, user_id=None)` | owner or self |
| `dashboard_kpis(period, compare_period)` | metric dict for dashboard |
| `active_alerts(settings)` | list of alert objects |

Exact signatures are defined at implementation time; behavior must match this requirements document.

### 7.3 Optional database optimizations

If performance targets (AR-GLOBAL-6) are not met with indexed queries alone:

| Optimization | Purpose |
|---|---|
| Index on `sales(sale_type, sale_date)` composite | Filtered sales trends |
| Index on `sale_items(book_id, sale_id)` | Book-level joins |
| Materialized table `daily_sales_summary(date, sale_type, revenue, units, txn_count)` | Refreshed on each sale/purchase cancel | Fast dashboard |
| Materialized table `book_sales_stats(book_id, period, qty, revenue)` | Monthly rollup | Bestseller / ABC |

Materialized summaries must be updated **within the same transaction** as the triggering write or via an explicit refresh on app startup — never stale by more than one session.

### 7.4 Settings storage

Analytics configuration (fiscal year start, dead-stock days, alert thresholds, default COGS method toggle) stored in a new table or JSON file:

```sql
-- Option A: key-value settings table (preferred)
CREATE TABLE app_settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

Owner edits via **Settings** subsection on Analytics page or existing admin area.

### 7.5 Dependencies

| Package | Purpose | Required |
|---|---|---|
| `pandas` | Already in requirements | Yes |
| `altair` or `plotly` | Richer charts | P2 — add if native Streamlit charts insufficient |
| `reportlab` | PDF export | Already present |

---

## 8. Data Quality and Edge Cases

| Scenario | Expected behavior |
|---|---|
| Book sold but never purchased | COGS = 0; flag in profit analytics (extends existing `never_purchased_codes` warning) |
| Zero sales in period | Margin and turnover show "N/A" or 0%; no division-by-zero errors |
| Single transaction in period | Trends show single point; comparison metrics hidden or marked "insufficient data" |
| Cancelled sale after period closed | Excluded from analytics; if "include cancelled" on, shown with CANCELLED badge |
| Manual stock adjustment | Appears in movement summary; does not affect revenue metrics |
| Book with no category/publisher | Grouped under "(Uncategorized)" / "(Unknown publisher)" |
| Wholesale sale without customer | Should not occur (DB CHECK); exclude from customer analytics if data anomaly |

---

## 9. Non-Functional Requirements

| ID | Requirement |
|---|---|
| AR-NFR-1 | **Accuracy**: Analytics totals for revenue and units shall match FR-7 reports for the same date range and filters (automated test). |
| AR-NFR-2 | **Auditability**: Analytics are read-only; they never mutate business data. |
| AR-NFR-3 | **Security**: Owner-only endpoints guarded by `auth_service` role check before query execution. |
| AR-NFR-4 | **Offline**: All analytics work without internet (NFR-8, PRD §9.6). |
| AR-NFR-5 | **Backup compatibility**: Analytics queries run against the same `data/shop.db`; daily backups include all data needed for analytics. |
| AR-NFR-6 | **Testability**: Each P1 metric has at least one unit test with seeded fixtures (`db/seed_sample_data.py` extended as needed). |

---

## 10. Implementation Phases

### Phase 1 — Analytics MVP (P1 items)

- `analytics_service.py` with core queries
- `9_Analytics.py` with Sales, Inventory, and Dashboard enhancements
- Owner/employee permission split
- CSV/Excel export on all tables
- Tests for revenue trend, bestsellers, dead stock, P&L consistency

**Estimated modules:** AR-DASH (1–4), AR-SALE (1–6), AR-PUR (1–4), AR-INV (1–6), AR-FIN (1–5), AR-CUST (1–2), AR-EMP (1–2, 6), AR-ALERT (1–3)

### Phase 2 — Operational depth (P2 items)

- Customer and employee deep-dives
- ABC, reorder suggestions, price override analysis
- Payment method and day-of-week charts
- PDF snapshot export
- Optional chart library and indexes

### Phase 3 — Refinement (P3 items)

- Configurable dashboard widgets
- Weighted-average COGS option
- Advanced alerts and break-even tooling
- Publisher/category advanced views

---

## 11. Acceptance Criteria

Advanced analytics v2.0 is accepted when:

1. Owner can open Analytics, select "Last 30 days", and see sales revenue trend, bestsellers, and gross profit trend that reconcile with existing P&L for the same range (AR-NFR-1).
2. Employee login shows only permitted views; profit/margin/employee-comparison views are inaccessible (§2.1).
3. Dead stock and reorder suggestion reports identify known test titles from an extended seed dataset.
4. All P1 analytics tables export to CSV and Excel.
5. Dashboard loads P1 widgets within 3 seconds on seed data ≥1,000 transactions (AR-GLOBAL-6).
6. Cancelled transactions are excluded by default; owner toggle includes them with clear labeling.
7. Automated tests pass for `test_analytics.py` and existing `test_services.py` / `test_db.py` remain green.

---

## 12. Appendix A — Metric Definitions

| Metric | Formula / definition |
|---|---|
| **Revenue** | Sum of `sales.total_amount` (after bill-level discount) for non-cancelled sales in range |
| **Gross revenue (pre-discount)** | Sum of `sale_items.quantity × sale_items.unit_price` |
| **COGS** | Sum of `sale_items.quantity × last_purchase_price` at time of sale (v1.0 method) |
| **Gross profit** | Revenue − COGS |
| **Margin %** | (Gross profit ÷ Revenue) × 100 |
| **Average ticket** | Revenue ÷ transaction count |
| **Inventory turnover** | COGS for period ÷ ((opening stock value + closing stock value) / 2) |
| **Days of supply** | Current stock ÷ (units sold in last 30 days ÷ 30) |
| **Dead stock** | Stock > 0 AND no sales in last N days |
| **Slow mover** | Same as dead stock with shorter N (default 90) |
| **ABC class A** | Books contributing to first 80% of cumulative revenue (12-month window) |

---

## 13. Appendix B — Suggested UI Wireframe (Analytics page)

```
┌─────────────────────────────────────────────────────────────────┐
│ Analytics                    [Date: Last 30 days ▼] [Filters ▼] │
├─────────────────────────────────────────────────────────────────┤
│ [Sales] [Purchases] [Inventory] [Profit] [Customers] [Staff]    │
├─────────────────────────────────────────────────────────────────┤
│  Revenue        Units sold      Avg ticket       Transactions   │
│  ₹1,24,500      342             ₹1,108           112              │
│  ▲ 12% vs prev                                                    │
├──────────────────────────┬──────────────────────────────────────┤
│  Revenue trend (chart)   │  Retail vs Wholesale (chart)         │
├──────────────────────────┴──────────────────────────────────────┤
│  Bestsellers (table)                              [CSV] [Excel] │
└─────────────────────────────────────────────────────────────────┘
```

---

## 14. Document History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 11 June 2026 | — | Initial advanced analytics requirements |
