# Sanskrit Sahitya Ratnakar — User Guide

**संस्कृत साहित्य रत्नाकर — Shop Management System**

| | |
|---|---|
| **Version** | 1.0 |
| **Audience** | Shop owners and employees |
| **Last updated** | June 2026 |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Getting Started](#2-getting-started)
3. [User Roles and Permissions](#3-user-roles-and-permissions)
4. [Dashboard — Your Daily Snapshot](#4-dashboard--your-daily-snapshot)
5. [Book Catalog](#5-book-catalog)
6. [Contacts](#6-contacts)
7. [Purchases](#7-purchases)
8. [Sales](#8-sales)
9. [Online Orders](#9-online-orders)
10. [Inventory](#10-inventory)
11. [Reports](#11-reports)
12. [Analytics](#12-analytics)
13. [User Management (Owner Only)](#13-user-management-owner-only)
14. [Common Workflows](#14-common-workflows)
15. [Tips, FAQ, and Troubleshooting](#15-tips-faq-and-troubleshooting)
16. [Backup and LAN Access](#16-backup-and-lan-access)
17. [Glossary](#17-glossary)

---

## 1. Introduction

### What is this application?

**Sanskrit Sahitya Ratnakar** is a back-office shop management system built for a Sanskrit book shop. It runs in your web browser and helps you manage day-to-day operations from a single place: cataloguing books, tracking stock, recording purchases and sales, printing receipts, generating financial reports, and analysing business performance.

The system supports **dual-script book titles** — both Devanagari (e.g., रामायणम्) and Roman/IAST (e.g., Rāmāyaṇam) — so staff can search and work in whichever script they prefer.

### What you can do

| Area | What it helps with |
|------|-------------------|
| **Book Catalog** | Add and search books in both scripts; set retail and wholesale prices |
| **Contacts** | Maintain suppliers and wholesale customers |
| **Purchases** | Record stock received from suppliers; stock increases automatically |
| **Sales** | Record counter (retail) and bulk (wholesale) sales; print PDF receipts |
| **Online Orders** | Guests place pickup orders without login; staff fulfill and record sales |
| **Inventory** | View current stock, per-book history, and low-stock alerts |
| **Reports** | Formal Sale–Purchase statements, Profit & Loss, and stock reports |
| **Analytics** | Trends, charts, bestsellers, reorder suggestions, and business alerts |
| **Users** | Manage staff accounts (owner only) |

### What this version does not include

The following are **out of scope** for version 1.0:

- GST / tax computation and tax-compliant invoicing (simple sale receipts only)
- Full e-commerce (online payment, shipping, customer accounts) — basic guest
  order placement for shop pickup **is** included (see [Section 9](#9-online-orders))
- Barcode scanning and label printing
- Accounting software integrations (e.g., Tally)
- Multi-branch / multi-shop support
- Machine-learning demand forecasting (analytics uses rule-based calculations only)

### Currency

All amounts in the application are displayed in **Indian Rupees (₹)**. Internally, values are stored precisely in paise (1 ₹ = 100 paise), so you will always see correct rupee amounts in the interface.

---

## 2. Getting Started

### Opening the application

1. Open a web browser (Chrome, Firefox, or Edge recommended).
2. Go to the application address:
   - **On the shop's main PC:** `http://localhost:8501`
   - **From another PC on the shop network:** `http://<shop-pc-ip>:8501` (replace `<shop-pc-ip>` with the main computer's IP address — ask your IT contact if unsure)

[Screenshot: Browser address bar showing the application URL]

3. The **Order Books** page opens by default — a public catalog where customers
   can browse in-stock titles and place pickup orders without logging in.

[Screenshot: Order Books page with catalog and cart]

4. Staff click **Staff Login** in the sidebar to reach the back office (Dashboard,
   Sales, Online Orders, etc.).

[Screenshot: Staff Login screen with username and password fields]

### First-time login

On first installation, three accounts are created automatically. Everyone must change their password on first login.

| Username | Role | Default password |
|----------|------|------------------|
| `owner` | Owner | `change@123` |
| `employee1` | Employee | `change@123` |
| `employee2` | Employee | `change@123` |

**To log in:**

1. Enter your **Username** and **Password**.
2. Click **Log in**.

If the username or password is wrong, or the account has been deactivated, you will see: *"Invalid username or password, or account is deactivated."*

### Changing your password

After first login (or after the owner resets your password), you are taken to the **Change your password** screen before you can use any other page.

[Screenshot: Change Password screen]

1. Enter a **New password** (minimum 6 characters).
2. Re-enter it in **Confirm new password**.
3. Click **Set password**.

You cannot reuse the default password `change@123`. Once saved, you are taken to the Dashboard.

### Navigation

**Without login (guests):** the sidebar shows **Order Books** (default) and
**Staff Login**.

After staff login, the **sidebar** on the left shows:

- Your **full name** and **role** (Owner or Employee)
- A **Log out** button
- Links to all back-office pages you are allowed to access

[Screenshot: Sidebar navigation with user name, role, and page links]

**Page order in the staff sidebar:**

| Page | Available to |
|------|-------------|
| Dashboard | Everyone (opens by default after login) |
| Books | Everyone |
| Purchases | Everyone |
| Sales | Everyone |
| Inventory | Everyone |
| Reports | Everyone |
| Analytics | Everyone (content varies by role) |
| Contacts | Everyone |
| Online Orders | Everyone |
| Users | Owner only |

### Logging out

Click **Log out** in the sidebar at the end of your shift. Always log out if you are leaving the counter PC unattended.

---

## 3. User Roles and Permissions

The system has two roles. Your role determines which pages and actions you can access.

### Owner

The **Owner** has full access to all modules, including financial reports, profit analytics, user management, transaction cancellations, and manual stock adjustments. There is typically one owner account, but additional owner accounts can be created if needed.

### Employee

**Employees** handle day-to-day operations: adding books, recording purchases and sales, and viewing stock and operational analytics. They cannot see profit/COGS figures, cancel transactions, adjust stock manually, or manage users.

### Permission summary

| Capability | Owner | Employee |
|------------|:-----:|:--------:|
| Log in / log out | Yes | Yes |
| Add / edit books | Yes | Yes |
| Deactivate books | Yes | No |
| Record purchases | Yes | Yes |
| Record sales (retail and wholesale) | Yes | Yes |
| Fulfill or cancel pending online orders | Yes | Yes |
| Cancel a purchase or sale | Yes | No |
| View current inventory | Yes | Yes |
| View stock ledger | Yes | Yes |
| Manual stock adjustment | Yes | No |
| Manage suppliers and wholesale customers | Yes | Yes |
| Sale–Purchase report | Yes | Yes |
| Profit & Loss report | Yes | No |
| Analytics — Sales, Purchases, Inventory, Customers | Yes | Yes |
| Analytics — Profit and Staff tabs | Yes | No |
| Analytics — financial totals (stock value, margins, COGS) | Yes | Limited |
| Analytics settings | Yes | No |
| Create / deactivate users, reset passwords | Yes | No |

### Audit trail

Every purchase and sale records **who created it** and when. This appears in history tables as the **By** column. Cancellations are never deleted — they are marked as cancelled with a reason, and the original record stays in the system.

---

## 4. Dashboard — Your Daily Snapshot

The **Dashboard** is the first page you see after login. It gives a quick overview of today's activity and recent business health.

[Screenshot: Dashboard — owner view showing today's metrics, alerts, and charts]

[Screenshot: Dashboard — employee view showing personal activity stats]

### What everyone sees

**Top alerts (up to 3)**

Active business alerts from the analytics engine appear at the top — for example, low-stock warnings, unusually high or low sales today, or items sold below cost. See [Section 12.9 — Insights tab](#129-insights-tab) for the full list of alert types.

**Today's summary (4 metrics)**

| Metric | Meaning |
|--------|---------|
| **Today's sales** | Total rupee amount and number of sale transactions today |
| **Today's purchases** | Total rupee amount and number of purchase transactions today |
| **Low-stock titles** | Count of books currently below their low-stock threshold |
| **Pending online orders** | Guest orders awaiting staff fulfillment |

When pending orders exist, an info banner also appears above the metrics.

**Last 30 days (4 KPIs with % change)**

| Metric | Meaning |
|--------|---------|
| **Sales revenue** | Total revenue in the last 30 days, with % change vs the previous 30 days |
| **Transactions** | Number of sale transactions |
| **Units sold** | Total book copies sold |
| **Avg ticket** | Average sale amount per transaction |

**Charts**

- **Sales revenue trend (30 days)** — daily line chart
- **Retail vs wholesale (this month)** — bar chart comparing channels

**Top 5 bestsellers (this month)**

Table of the five best-selling titles by quantity and revenue for the current calendar month.

**Low-stock alerts**

Table of books currently below their threshold, showing code, title, current stock, and threshold.

**Recent transactions**

The 10 most recent sales and purchases across the shop, with date, type, reference number, amount, who recorded it, and status (OK or CANCELLED).

### What employees additionally see

| Metric | Meaning |
|--------|---------|
| **Your sales today** | Sales you personally recorded today |
| **Your sales this week** | Sales you recorded in the current week |
| **Purchases recorded this week** | Purchases you recorded this week |
| **Sales recorded this week** | Sales you recorded this week |

### What owners additionally see

**Month to date (Owner)**

| Metric | Meaning |
|--------|---------|
| **MTD revenue** | Total sales revenue from the 1st of this month to today |
| **MTD COGS** | Cost of goods sold for the same period |
| **MTD gross profit** | Revenue minus COGS |
| **Margin** | Gross profit as a percentage of revenue |

**Additional owner charts**

- **MTD gross profit trend** — daily line chart for the current month
- **Purchase vs sales cash flow (90 days)** — dual line chart comparing money in (sales) vs money out (purchases)

### Suggested morning routine

1. Open the **Dashboard**.
2. Read any **alerts** at the top.
3. Check **Pending online orders** — fulfill via **Online Orders** if any exist.
4. Check **Low-stock titles** and the low-stock table.
5. Glance at **Today's sales** and **Recent transactions**.
6. Proceed to **Purchases**, **Sales**, or **Online Orders** as needed.

---

## 5. Book Catalog

Use the **Books** page to manage your book catalog. Every purchase and sale links to a book in this catalog.

[Screenshot: Book Catalog — Catalog tab with search results]

### Catalog tab

1. Go to **Books** in the sidebar.
2. On the **Catalog** tab, use the search box: **Search (Roman or Devanagari title, author, or code)**.
   - You can type in either script — the system finds matches in both.
   - Leave the search empty to see all active books.
3. Tick **Show deactivated** to include books that have been deactivated by the owner.
4. The table shows: code, both titles, author, publisher, category, language, ISBN, retail price, wholesale price, low-stock threshold, and status.

[Screenshot: Book Catalog — search box with Devanagari query and results]

### Add book tab

1. Click the **Add book** tab.
2. Fill in the form:

| Field | Required? | Notes |
|-------|-----------|-------|
| Title (Devanagari) | Yes | e.g., रामायणम् |
| Title (Roman) | Yes | e.g., Rāmāyaṇam |
| Author (Devanagari) | No | |
| Author (Roman) | No | |
| Publisher | No | Used for duplicate detection |
| Category | No | Veda, Purana, Kavya, Vyakarana, Darshana, Textbook, Other |
| Language | No | Sanskrit, Sanskrit-Hindi, Sanskrit-English, Other |
| ISBN | No | Many Sanskrit books lack an ISBN |
| Retail price (₹) | Yes | Default price for counter sales |
| Wholesale price (₹) | Yes | Default price for wholesale sales |
| Low-stock threshold | No | Default 5 — alert fires when stock falls to this level or below |

[Screenshot: Add book form with dual titles and prices filled in]

3. Click **Save book**.

**Duplicate warning:** If a book with the same title and publisher already exists, a warning appears listing the existing book code(s). To save anyway, tick **Ignore duplicate warning and save anyway** and click **Save book** again.

On success, the system assigns an auto-generated code (e.g., `BK-0001`, `BK-0002`).

### Edit book tab

1. Click the **Edit book** tab.
2. Select a book from the dropdown (shows code and both titles).
3. Update any fields and click **Save book**.
4. The same duplicate warning applies when changing title or publisher.

> **Owner only:** Below the edit form, owners see additional buttons:
> - **Deactivate this book (hidden from sale screens)** — hides the book from purchase and sale screens; history is preserved.
> - **Reactivate this book** — makes a deactivated book available again.

Employees can edit book details but cannot deactivate books.

---

## 6. Contacts

Use the **Contacts** page to maintain the people and organisations you buy from and sell to in bulk.

### Suppliers tab — Suppliers (publishers/wholesalers)

Every purchase must be linked to a supplier. Add suppliers before recording your first purchase.

**To add a supplier:**

1. Go to **Contacts** → **Suppliers (publishers/wholesalers)** tab.
2. Open the **Add new** expander.
3. Fill in:
   - **Name** (required)
   - Contact person, Phone, Address, Notes (all optional)
4. Click **Add**.

[Screenshot: Contacts — Add new supplier form]

**To edit or deactivate a supplier:**

1. Open the **Edit / deactivate** expander.
2. Select the supplier from the dropdown.
3. Update fields and click **Save changes**, or click **Deactivate** / **Reactivate**.

Tick **Show deactivated** to see inactive suppliers in the list.

### Wholesale customers tab

Every wholesale sale must be linked to a wholesale customer. Retail walk-in customers are **not** registered — they appear as "(walk-in)" in sale records.

The workflow is identical to suppliers: add, edit, and deactivate wholesale customers using the same form fields.

> **Note:** If you try to record a wholesale sale without any wholesale customers, the Sales page will show a warning and ask you to add one here first.

---

## 7. Purchases

Use the **Purchases** page to record stock received from suppliers. Saving a purchase **automatically increases** stock for each book on the purchase.

[Screenshot: Purchases — New purchase tab with line items in cart]

### New purchase tab

**Before you start:** Ensure at least one supplier exists in Contacts and at least one active book exists in the catalog.

**Step-by-step:**

1. Go to **Purchases** → **New purchase** tab.
2. Select the **Supplier** (required).
3. Set the **Purchase date** (defaults to today).
4. Optionally enter an **Invoice / bill reference**.
5. Under **Add line item**:
   - Select a **Book**
   - Enter **Quantity** (minimum 1)
   - Enter **Unit cost (₹)** — the price you paid per copy
   - Click **Add to purchase**
6. Repeat step 5 for each title on the invoice.
7. Review the line items table. To remove a line, select it in **Remove a line** and click **Remove selected line**.
8. Check the **Total** at the bottom.
9. Optionally add **Notes**.
10. Click **Save purchase**.

On success: *"Purchase #\<number\> saved — stock updated."* The cart clears and stock increases immediately.

### History tab

1. Click the **History** tab.
2. Set filters:
   - **From** / **To** date range (default: last 30 days)
   - **Supplier** (All or a specific supplier)
   - **Book** (All or a specific book)
3. Review the purchases table: ID, Date, Supplier, Invoice, Lines, Qty, Total, By, Status.

[Screenshot: Purchases — History tab with purchase list and detail view]

4. Select a purchase number in **View details of purchase #** to see line items.
5. Click **Download** buttons if export is needed (via Reports page for bulk export).

> **Owner only: Cancelling a purchase**
>
> 1. Open the purchase detail in History.
> 2. Enter a **Cancellation reason (required)**.
> 3. Click **Cancel this purchase**.
>
> Stock is reversed automatically. Cancelled purchases show status **CANCELLED** with the reason displayed.

---

## 8. Sales

Use the **Sales** page to record counter (retail) and bulk (wholesale) sales. Saving a sale **automatically decreases** stock. The system **blocks overselling** — you cannot sell more copies than are in stock.

[Screenshot: Sales — New sale tab with retail sale and line items]

### New sale tab

**Before you start:** Ensure books exist in the catalog. For wholesale sales, ensure at least one wholesale customer exists in Contacts.

**Step-by-step:**

1. Go to **Sales** → **New sale** tab.
2. Choose **Sale type**: **Retail** or **Wholesale**.
   - **Retail** — walk-in counter customer; retail price auto-fills.
   - **Wholesale** — select a **Customer** from the dropdown; wholesale price auto-fills.
3. Under **Add line item (price auto-fills from the catalog, editable)**:
   - Select a **Book** (the dropdown shows current stock, e.g., "stock: 12")
   - Enter **Quantity**
   - Adjust **Unit price (₹)** if needed (price override is allowed)
   - Click **Add to sale**
4. Repeat for each title on the bill.
5. Review line items. Remove unwanted lines using **Remove a line** + **Remove selected line**.
6. Set:
   - **Sale date** (defaults to today)
   - **Discount on bill (₹)** — optional whole-bill discount (cannot exceed subtotal)
   - **Payment method**: CASH, UPI, CARD, or CHEQUE
   - **Notes** (optional)
7. Review **Subtotal** and **Total** (after discount).
8. Click **Save sale**.

On success: *"Sale #\<number\> saved — stock updated."* A **Download receipt #\<number\> (PDF)** button appears.

[Screenshot: Sales — PDF receipt download button after saving a sale]

### PDF receipts

- Format: A5 PDF
- Includes Devanagari book titles
- Click **Download receipt #\<number\> (PDF)** immediately after saving, or from History
- File name: `receipt-<sale-id>.pdf`

### History tab

1. Click the **History** tab.
2. Set filters:
   - **From** / **To** (default: last 30 days)
   - **Type**: All, Retail, or Wholesale
   - **Customer**, **Book**, **Recorded by**
3. Review the sales table.
4. Select a sale in **View details of sale #** to see line items.
5. Click **Download receipt #\<number\> (PDF)** to re-print a receipt.

[Screenshot: Sales — History tab with filters and sale detail]

> **Owner only: Cancelling a sale**
>
> 1. Open the sale detail in History (must not already be cancelled).
> 2. Enter a **Cancellation reason (required)**.
> 3. Click **Cancel this sale**.
>
> Stock is restored automatically. Cancelled sales show status **CANCELLED**.

### Common sale errors

| Error | What to do |
|-------|-----------|
| Insufficient stock message | Check **Inventory** → **Current stock**; reduce quantity or record a purchase first |
| "Add a wholesale customer first" | Go to **Contacts** and add the customer |
| "Add books to the catalog first" | Go to **Books** → **Add book** |

---

## 9. Online Orders

Online ordering lets customers browse the catalog and request books for shop
pickup without creating an account. Staff review pending orders and, when the
customer arrives, mark an order complete — which records a retail sale and
updates stock.

> **Important:** Stock is checked when a guest places an order, but it is **not
> reserved**. Counter sales or other fulfilled orders can reduce stock before
> pickup. Staff re-check stock when marking an order complete.

### 9.1 Guest ordering (Order Books page)

The public **Order Books** page is the default landing page when the app opens
without staff login. Share this URL with customers who want to order remotely.

[Screenshot: Order Books page — catalog browse tab and cart]

**Browse catalog tab**

1. Use **Search books** to find titles in Devanagari or Roman (title, author, or code).
2. Only **in-stock** active books are shown.
3. Under **Add to cart**, pick a book, set quantity (limited by available stock
   minus what is already in the cart), and click **Add to cart**.
4. Switch to the **Your cart** tab to review lines, remove items, or proceed to checkout.

**Your cart tab — checkout**

1. Review line items and the order total.
2. Fill in contact details:
   - **Full name** (required)
   - **Phone** (required)
   - **Email** (optional)
   - **Notes** (optional — pickup preferences, etc.)
3. Click **Place order**.

On success, a confirmation message shows the **order number** (e.g., Order #5).
The shop contacts the customer to arrange pickup and payment at the counter.

If stock is insufficient at placement time, an error lists the affected titles.

### 9.2 Managing online orders (staff)

After **Staff Login**, open **Online Orders** in the sidebar.

[Screenshot: Online Orders — Pending tab with order detail and action buttons]

**Pending tab**

Lists all orders awaiting fulfillment.

1. Review the pending orders table (order #, date, customer, phone, email, lines, qty, total).
2. Select an order in **Manage order #** to see line items and customer notes.
3. When the customer picks up and pays:
   - Click **Mark complete**.
   - The system creates a **retail sale** (payment method: cash, notes reference
     the online order), decreases stock, and links the sale to the order.
   - Download the PDF receipt from the success message or the Completed tab.
4. If the order will not be fulfilled:
   - Enter a **Cancellation reason** and click **Cancel order**.
   - Stock is **not** changed; the order moves to the Cancelled tab.

If stock is insufficient when completing, an error explains which titles are short.

**Completed tab**

Filter by date range. Shows completion time, who completed the order, and linked
**Sale #**. Select an order to view line items and re-download the receipt PDF.

**Cancelled tab**

Filter by date range. Shows cancellation time, who cancelled, and the reason.

Both **Owner** and **Employee** can fulfill and cancel pending online orders.

---

## 10. Inventory

Use the **Inventory** page to see how much stock you have, trace the history of any title, and (owners only) record manual adjustments.

### How stock works

Stock is **never typed in directly**. It is always calculated:

```
Current stock = Purchases − Sales + Manual adjustments
```

Cancelled transactions are excluded. This means every purchase, sale, and adjustment you record elsewhere automatically updates inventory.

### Current stock tab

1. Go to **Inventory** → **Current stock** tab.
2. Summary metrics: **Titles**, **Stock value**, **Low-stock titles**.
3. Tick **Include deactivated books** to see inactive catalog entries.
4. Tick **Show only low-stock books** to filter to titles at or below their threshold.
5. The table shows: code, both titles, publisher, stock, threshold, low-stock flag, last purchase price, and stock value.

[Screenshot: Inventory — Current stock tab with low-stock filter enabled]

### Stock ledger tab

The ledger shows every stock movement for a single book with a running balance.

1. Click the **Stock ledger** tab.
2. Select a **Book** from the dropdown.
3. Review the table: Date, Type (purchase/sale/adjustment), Qty +/-, Balance, Ref #, By.
4. The caption at the bottom confirms **Current stock**.

Use this when you need to answer: "Why does this book show 3 copies?" or "When did we last receive stock for this title?"

### Manual adjustment tab

> **Owner only:** Employees see a message: *"Manual stock adjustments are available to the Owner only."*

Use manual adjustments for stock changes that are not purchases or sales — for example, damaged copies, found stock, or corrections.

1. Click the **Manual adjustment** tab.
2. Select a **Book** (dropdown shows current stock).
3. Set the **Date**.
4. Enter **Quantity change**:
   - **Negative** number = stock removed (damaged, lost)
   - **Positive** number = stock added (found, correction)
5. Enter a **Reason** (required).
6. Click **Record adjustment**.

[Screenshot: Inventory — Manual adjustment form]

---

## 11. Reports

Use the **Reports** page for formal financial statements and stock snapshots. Unlike Analytics (Section 12), Reports focus on **tabular statements** suitable for accounting review and export.

[Screenshot: Reports page with date range and Sale–Purchase Statement tab]

### Date range

At the top of the Reports page, set **From** and **To** dates. These apply to the Sale–Purchase Statement and Profit & Loss tabs. The Stock Report always shows the current snapshot regardless of dates.

### Sale–Purchase Statement tab

Available to everyone.

**Totals table** — summary for the selected period:

| Section | Shows |
|---------|-------|
| Purchases | Transaction count, quantity, amount |
| Sales — Retail | Retail sales summary |
| Sales — Wholesale | Wholesale sales summary |
| Sales — Total | Combined sales |

**Breakdown** — choose **Day-wise** or **Month-wise** to see purchases and sales per period.

**Drill-down** — expand **Drill-down: individual transactions** to see every purchase and sale in the period with ID, date, party, quantity, amount, and who recorded it.

**Export:** Click **Download CSV** or **Download Excel** below each table.

### Profit & Loss (Owner) tab

> **Owner only:** This tab is not visible to employees.

Shows profit for the selected date range using the configured COGS method (see Analytics settings).

| Metric | Meaning |
|--------|---------|
| **Revenue** | Total sales after discounts |
| **COGS** | Cost of goods sold |
| **Gross profit** | Revenue minus COGS |
| **Margin** | Gross profit as % of revenue |

Additional tables:
- **By sale type** — retail vs wholesale breakdown
- **Top profitable books** — top 20 by profit

A warning appears if any books were sold but never purchased (COGS counted as zero for those).

**Export:** CSV and Excel available on each table.

### Stock Report tab

Available to everyone. Shows a point-in-time snapshot:

- Summary: Titles, Units in stock, Stock value
- Full stock table with code, titles, publisher, stock, last purchase price, stock value, low-stock flag
- **Low-stock books** sub-table if any titles are below threshold

**Export:** CSV and Excel available.

### Reports vs Analytics — when to use which

| Need | Use |
|------|-----|
| Formal P&L or Sale–Purchase statement for a date range | **Reports** |
| Export a stock list for accounting | **Reports** → Stock Report |
| See sales trends, bestsellers, busy hours | **Analytics** → Sales tab |
| Find what to reorder, dead stock, ABC classification | **Analytics** → Inventory tab |
| Compare employee activity | **Analytics** → Staff tab (owner) |

---

## 12. Analytics

The **Analytics** page is the business intelligence centre of the application. It turns the purchases, sales, and inventory data you record daily into trends, rankings, charts, and proactive alerts.

[Screenshot: Analytics page — period selector, filters expander, and Sales tab]

### 12.1 Analytics overview

**Purpose:** Understand business performance beyond the daily totals on the Dashboard — spot trends, identify bestsellers and slow movers, plan reorders, monitor margins, and track customer and staff activity.

**Who sees what:**

| View | Owner | Employee |
|------|:-----:|:--------:|
| Number of tabs | 7 | 5 |
| Tabs available | Sales, Purchases, Inventory, **Profit**, Customers, **Staff**, Insights | Sales, Purchases, Inventory, Customers, Insights |
| Financial detail (COGS, margins, stock value total) | Full | Hidden or shown as "—" |
| Analytics settings | Yes | No |

**Important principles:**

- Analytics is **read-only**. It does not change any data. Accurate analytics depends on you recording purchases and sales promptly.
- Cancelled transactions are **excluded by default**. Owners can include them via the **Include cancelled** filter.
- There is **no machine-learning forecasting**. All insights use clear, rule-based calculations (e.g., days of supply = stock ÷ average daily sales).

**How data flows into Analytics:**

The purchases, sales, and stock adjustments you enter on their respective pages are stored in the database. Analytics reads that data and summarises it. Better data entry habits — recording purchases the day stock arrives, recording every sale at the counter — produce more accurate and timely analytics.

### 12.2 Global controls

These controls appear at the top of the Analytics page and affect **all tabs**.

#### Period selector

Choose how far back to analyse:

| Preset | Covers |
|--------|--------|
| Today | Current day only |
| Yesterday | Previous day |
| Last 7 days | Rolling 7 days including today |
| Last 30 days | Rolling 30 days including today (default) |
| This month | 1st of current month to today |
| Last month | Full previous calendar month |
| This quarter | Current calendar quarter to today |
| This year | 1st January to today |
| Custom range | Pick **From** and **To** dates manually |

[Screenshot: Analytics — Period dropdown set to Last 30 days with Custom range date inputs]

#### Filters expander

Click **Filters** to narrow all analytics to a subset of your data:

| Filter | Options |
|--------|---------|
| Sale type | Both, Retail, Wholesale |
| Payment | All, cash, upi, card, cheque |
| Category | All + book categories |
| Publisher | All + publishers |
| Language | All + languages |
| Recorded by | All + staff names |
| Supplier | All + active suppliers |
| Wholesale customer | All + active customers |

> **Owner only — additional filters:**
> - **Include cancelled** — show cancelled transactions in calculations
> - **Include inactive books** — include deactivated catalog entries

[Screenshot: Analytics — Filters expander open showing all filter dropdowns]

#### Chart granularity

Select how trend charts group data:

- **daily** — one point per day
- **weekly** — one point per week
- **monthly** — one point per month

Use daily for short periods (Today, Last 7 days), weekly or monthly for longer ranges (This year).

### 12.3 Sales tab

Understand how your shop is selling: revenue patterns, channels, bestsellers, and customer payment behaviour.

#### Key metrics (top row)

| Metric | Meaning | Comparison |
|--------|---------|------------|
| **Revenue** | Total sales amount after discounts | % vs previous period of same length |
| **Units sold** | Total copies sold | % vs previous period |
| **Avg ticket** | Revenue ÷ number of transactions | % vs previous period |
| **Transactions** | Number of sale bills | % vs previous period |

The percentage shown (e.g., "+12.5% vs prev period") compares your selected period to the immediately preceding period of equal length.

#### Charts

- **Revenue over time** — line chart
- **Units sold over time** — line chart
- **Retail vs wholesale** — bar chart and summary table (revenue, units, transactions, avg ticket per channel)

[Screenshot: Analytics — Sales tab with revenue trend chart and retail vs wholesale bar chart]

#### Tables and sections

**Bestsellers**

Top 50 titles by revenue for the selected period. Columns: Code, Title, Category, Qty, Revenue, % of revenue.

- **Drill-down book:** Select a book from the dropdown to see per-book sales trend, purchase trend, and (owner) period P&L in an expander.
- **Export:** Download CSV / Download Excel

**Slow movers**

Titles that have stock on hand but had **no sales** in the configured number of days (default: 90 days). These may need promotion or price review.

**Discount analysis** (Owner only)

- Total discounts given in the period
- Discount as % of gross revenue
- Top 10 sales with the highest discounts

**Payment methods**

Breakdown by cash, UPI, card, and cheque — transaction count, revenue, and bar chart.

**Sales by weekday**

Average daily revenue for each day of the week (Monday–Sunday). Use this to plan staffing and opening hours.

**Sales by hour of day**

Revenue by hour. Useful for understanding peak counter hours.

**Price overrides** (Owner only)

Caption showing how many sale lines had a price different from the catalog default, total units affected, and net price delta.

**Category performance**

Units and revenue by book category (Veda, Purana, Kavya, etc.).

### 12.4 Purchases tab

Track what you are buying, from whom, and how spending trends over time.

#### Key metrics

| Metric | Meaning |
|--------|---------|
| **Spend** | Total purchase amount in the period |
| **Units purchased** | Total copies bought |
| **Transactions** | Number of purchase bills |

#### Charts

- **Purchase spend over time** — line chart
- **Units purchased over time** — line chart

#### Tables

**Supplier ranking**

All suppliers ranked by spend. Columns: Supplier, Purchases (count), Qty, Spend, Avg unit cost, Last purchase date.

- **Export:** CSV / Excel
- **Owner only:** Caption showing what % of total spend came from the **top 3 suppliers** (supplier concentration risk)

**Top purchased titles**

Top 20 books by quantity purchased in the period.

### 12.5 Inventory tab

Monitor stock health: what is moving, what is stuck, and what needs reordering.

#### Key metrics

| Metric | Everyone | Owner |
|--------|:--------:|:-----:|
| Titles in stock | Yes | Yes |
| Total units | Yes | Yes |
| Stock value | — | Yes |

**Stock movement (period)** — single-row summary:

| Column | Meaning |
|--------|---------|
| Units in (purchases) | Copies added via purchases in the period |
| Units out (sales) | Copies sold in the period |
| Net adjustments | Net manual adjustments |
| Net change | Overall stock change |

**Inventory turnover** (Owner only)

- Formula: COGS ÷ average inventory value
- Shows: Turnover ratio, COGS, Avg inventory, Closing value

#### Tables and sections

**Days of supply (flag < N days)**

Shows titles running low relative to recent sales pace. **Days of supply** = current stock ÷ average daily sales (based on last 30 days). Titles below the threshold (default: 14 days) are flagged.

**Dead stock (N+ days without sales)**

Titles with stock on hand but no sale in the configured period (default: 180 days). Owner sees **Tied-up capital** (stock value locked in unsold books).

**Out of stock (sold in period, now zero)**

Books that had sales in the selected period but currently have zero stock — immediate reorder candidates.

**ABC classification (12 months)** (Owner only)

Classifies titles by revenue contribution over the last 12 months:

| Class | Typical share of revenue | Action |
|-------|-------------------------|--------|
| **A** | Top ~80% | Prioritise stock and shelf space |
| **B** | Next ~15% | Monitor regularly |
| **C** | Remaining ~5% | Review whether to keep stocking |

**Reorder suggestions**

Suggested order quantities for titles that are low on stock or low on days of supply. Use this list when calling suppliers.

**Stock adjustments** (Owner only)

Summary of manual adjustments in the period by reason.

[Screenshot: Analytics — Inventory tab showing reorder suggestions and days of supply tables]

### 12.6 Profit tab (Owner only)

> **Owner only:** This tab is not visible to employees. Employees see the caption: *"Employee view — operational sales and inventory insights (no profit/COGS)."*

Monitor profitability: margins, profit by channel, and loss-making sales.

#### Key metrics

| Metric | Meaning |
|--------|---------|
| **Revenue** | Total sales after discounts |
| **COGS** | Cost of goods sold (method shown in caption) |
| **Gross profit** | Revenue minus COGS |
| **Margin** | Gross profit as % of revenue |

#### Charts

- **Gross profit trend** — line chart over the selected period
- **Margin % trend** — line chart
- **Purchase-to-sales ratio** — table comparing purchases vs sales per time bucket

#### Tables

| Section | What it shows |
|---------|--------------|
| **Profit by sale type** | Retail vs wholesale: revenue, COGS, profit, margin % |
| **Profit by book** | Full sortable list of every title sold with profit and margin |
| **Loss-making line items** | Sales where unit price was below last purchase cost |
| **Profit by category** | Margin by book category |
| **Profit by publisher** | Margin by publisher |

A warning appears for books sold but never purchased (COGS = 0).

[Screenshot: Analytics — Profit tab with gross profit trend and margin chart]

### 12.7 Customers tab

Understand your wholesale customer base. Retail walk-in customers are anonymous — only aggregate totals are shown.

#### Wholesale customer ranking

All wholesale customers ranked by revenue. Columns: Customer, Orders, Revenue, Units, Avg order, Last order date.

- **Export:** CSV / Excel
- Caption: Top 5 customers as % of wholesale revenue (concentration risk)
- **Customer drill-down:** Select a customer to see their top purchased books in the period

#### Order frequency (repeat customers)

Customers with more than one order: order count and average days between orders.

#### Inactive wholesale customers (90+ days)

Customers who have not placed an order in 90 or more days. Use this for follow-up calls.

#### Retail (walk-in) aggregate

Total walk-in transaction count and revenue for the period. Individual walk-in customers are not tracked.

### 12.8 Staff tab (Owner only)

> **Owner only:** This tab is not visible to employees.

Review staff activity and accountability.

#### Employee activity table

Per employee: Name, Sales (count), Purchases (count), Sales revenue, Retail avg sale, Wholesale avg sale, Discounts granted, Cancel rate %.

**Export:** CSV / Excel

#### Daily sales by user

Pivot table showing sale counts per day per staff member. Use this to see who was active on which days and compare workload.

[Screenshot: Analytics — Staff tab with employee activity table]

### 12.9 Insights tab

The Insights tab brings together **proactive alerts** and **analytics configuration**.

#### Active alerts

The system continuously checks your data and displays warnings and information messages. If there are no issues, you see: *"No active alerts."*

| Alert | Level | What triggers it |
|-------|-------|-----------------|
| Low stock | Warning | One or more titles below their low-stock threshold; may note how many became low this week |
| Dead stock capital | Warning | Total capital tied up in dead stock exceeds the configured ₹ threshold |
| Margin drop | Warning | Month-to-date margin has fallen more than the configured number of points vs last month |
| Sales spike | Info | Today's sales are more than 2× the 30-day daily average |
| Sales drop | Info | Today's sales are below half the 30-day daily average |
| Loss-making today | Error | One or more sale lines today were priced below cost |
| Reorder suggestions | Info | One or more titles are flagged for reorder |

Alerts also appear on the **Dashboard** (top 3) so you see critical items without opening Analytics.

[Screenshot: Analytics — Insights tab showing active alerts]

#### Analytics settings (Owner only)

> **Owner only:** The settings form is not visible to employees.

Configure thresholds and calculation methods. Click **Save settings** after making changes.

| Setting | Default | Purpose |
|---------|---------|---------|
| Fiscal year start month (1–12) | 4 (April) | Defines fiscal year for future reporting |
| Dead stock days | 180 | How long without a sale before a title is "dead stock" |
| Slow mover days | 90 | How long without a sale before a title appears in Slow movers |
| Days-of-supply alert threshold | 14 | Flag titles with fewer days of supply than this |
| Dead stock capital alert (₹) | ₹50,000 | Warning when total dead-stock value exceeds this |
| Margin drop alert (points) | 5 | Warning when MTD margin drops this many points vs last month |
| COGS method | Last purchase price | How cost of goods sold is calculated (see Glossary) |

**COGS method options:**

- **Last purchase price** — each sold copy is costed at the most recent purchase price for that book.
- **Weighted average** — each sold copy is costed at the average of all purchase prices for that book.

Changing the COGS method affects Profit analytics and Reports P&L. Choose the method that best matches how your shop accounts for stock.

[Screenshot: Analytics — Insights tab showing Analytics settings form]

### 12.10 Analytics exports

Most tables in Analytics have export buttons below them:

- **Download CSV** — UTF-8 with BOM (Devanagari titles open correctly in Excel)
- **Download Excel** — .xlsx format

File names follow the pattern: `{report-name}-{start-date}-{end-date}.csv` or `.xlsx`

Example: `bestsellers-2026-05-12-2026-06-11.xlsx`

### 12.11 How to read common metrics

| Term | Plain-language meaning |
|------|----------------------|
| **Avg ticket** | Average amount per sale bill. Higher avg ticket means customers buy more per visit or buy pricier titles. |
| **Days of supply** | How many days your current stock will last at the recent sales rate. Low days of supply = reorder soon. |
| **Dead stock** | Books sitting on the shelf with no sales for a long time (default: 180+ days). Ties up money. |
| **Slow movers** | Similar to dead stock but shorter window (default: 90 days). Still have stock but not selling. |
| **ABC classification** | Ranks titles by revenue importance. Focus stocking effort on A-class titles. |
| **Reorder suggestions** | System-recommended order quantity based on threshold and recent sales. A starting point for purchase orders. |
| **Margin %** | Gross profit ÷ revenue × 100. A 30% margin means you keep ₹30 profit per ₹100 of sales (before other expenses). |
| **COGS** | Cost of Goods Sold — what you paid for the books that were sold in the period. |
| **Inventory turnover** | How many times your inventory "turned over" (sold and replaced) in the period. Higher is generally better. |
| **Supplier / customer concentration** | What % of spend or revenue comes from your top few partners. High concentration = dependency risk. |
| **Cancel rate %** | Percentage of an employee's sales that were cancelled. Useful for spotting data-entry issues. |
| **% vs prev period** | Compares the selected date range to the immediately preceding range of equal length. +10% means 10% growth. |

---

## 13. User Management (Owner Only)

> **Owner only:** The **Users** page appears in the sidebar only for the Owner role.

Use this page to add staff, deactivate departed employees, and reset passwords.

[Screenshot: User Management — user list and Add user tab]

### User list

The top table shows all users: ID, username, full name, role, status (Active/Deactivated), whether a password change is pending, and creation date.

### Add user tab

1. Click the **Add user** tab.
2. Fill in:
   - **Username** — used at login (no spaces; must be unique)
   - **Full name** — displayed in the sidebar and audit trail
   - **Role** — Employee (default) or Owner
   - **Initial password** — minimum 6 characters
3. Click **Create user**.

The new user must change their password on first login.

### Manage existing user tab

1. Click the **Manage existing user** tab.
2. Select a user (your own account is not listed here).

**Account status**

- **Deactivate account** — user cannot log in; all their past purchases and sales remain attributed to them.
- **Reactivate account** — restore access.

**Reset password**

1. Enter a **New temporary password** (minimum 6 characters).
2. Click **Reset password**.

The user must change this password at next login.

**Delete user permanently**

- Only possible if the user has **no** purchase, sale, or adjustment records.
- For staff who have worked in the system, use **Deactivate** instead of delete.
- Tick the confirmation checkbox, then click **Delete user**.

---

## 14. Common Workflows

Quick-reference guides for everyday tasks.

### Start of day

1. **Dashboard** — read alerts, check today's sales/purchases so far
2. Check **pending online orders** → **Online Orders** → Pending tab
3. Review **low-stock** count and table
4. If reorder needed → **Analytics** → Inventory → Reorder suggestions

### Receive stock from a supplier

1. **Contacts** — add supplier first if new
2. **Purchases** → **New purchase** — enter supplier, line items, save
3. **Inventory** → **Current stock** — verify stock increased

### Counter (retail) sale

1. **Sales** → **New sale** — select **Retail**
2. Add line items, apply discount if any, select payment method
3. Click **Save sale**
4. Click **Download receipt** and print for the customer

### Wholesale order

1. **Contacts** — add wholesale customer first if new
2. **Sales** → **New sale** — select **Wholesale**, choose customer
3. Add line items (wholesale prices auto-fill), save, download receipt if needed

### Fulfill an online order (guest pickup)

1. **Dashboard** — note pending online order count (or customer shares order #)
2. **Online Orders** → **Pending** — select the order and verify line items
3. When the customer pays at the counter, click **Mark complete**
4. **Download receipt** PDF for the customer if needed

If the order cannot be fulfilled (customer cancelled, stock unavailable), enter a
**Cancellation reason** and cancel instead — stock is not changed.

### Check why stock is wrong

1. **Inventory** → **Stock ledger** — select the book, review all movements
2. Look for missing purchases, uncancelled errors, or needed manual adjustment (owner)

### Month-end financial review (Owner)

1. **Reports** → set date range to the full month
2. **Sale–Purchase Statement** — export for records
3. **Profit & Loss (Owner)** — review margin, export
4. **Analytics** → **Profit** tab — drill into profit by category and loss-making lines
5. **Analytics** → **Purchases** tab — review supplier spend

### Reorder planning

1. **Analytics** → **Inventory** tab
2. Review **Days of supply**, **Out of stock**, and **Reorder suggestions**
3. **Analytics** → **Purchases** tab → **Supplier ranking** to decide whom to order from
4. **Purchases** → **New purchase** — record when stock arrives

### Investigate slow sales

1. **Analytics** → **Sales** tab → **Slow movers**
2. **Analytics** → **Inventory** tab → **Dead stock**
3. Consider promotions, price changes, or stopping reorders for those titles

### Onboard a new employee (Owner)

1. **Users** → **Add user** — create account with Employee role
2. Give the employee their username and temporary password
3. Ask them to change password on first login
4. Walk them through: Dashboard → Sales → Purchases → Books

---

## 15. Tips, FAQ, and Troubleshooting

### Tips for accurate data

- Record purchases the **same day** stock arrives — delays make inventory and analytics inaccurate.
- Record every sale at the counter — missing sales cause overselling errors and wrong revenue figures.
- Use consistent book titles and publishers — duplicate warnings exist for a reason.
- Set realistic **low-stock thresholds** per book when adding to the catalog.
- Review **Analytics → Insights** alerts weekly.

### Frequently asked questions

**Q: I get "insufficient stock" when saving a sale. What do I do?**

A: Check **Inventory** → **Current stock** for that book. Either reduce the sale quantity or record a **Purchase** first to add stock.

**Q: I cannot record a wholesale sale.**

A: You need at least one active wholesale customer in **Contacts** → **Wholesale customers**. Retail sales do not need a registered customer.

**Q: An employee says they cannot see Profit & Loss.**

A: This is by design. Only the **Owner** role can see P&L in Reports and the Profit tab in Analytics.

**Q: Why does stock value show "—" for an employee?**

A: Total stock value and financial analytics are restricted to the Owner. Employees still see unit counts and operational metrics.

**Q: Profit numbers look wrong or COGS is zero for some books.**

A: Those books may have been sold without a prior purchase recorded. Check the warning listing book codes. Record the missing purchase history if applicable. Also verify the **COGS method** in **Analytics** → **Insights** → **Analytics settings**.

**Q: How do I fix a wrong purchase or sale?**

A: Only the **Owner** can cancel transactions. Open the transaction in **History**, enter a cancellation reason, and cancel. Then re-enter the correct transaction. Stock adjusts automatically.

**Q: How do I handle damaged or lost books?**

A: **Owner** → **Inventory** → **Manual adjustment**. Enter a negative quantity with a reason (e.g., "Water damage — 2 copies").

**Q: I forgot my password.**

A: Ask the Owner to reset it via **Users** → **Manage existing user** → **Reset password**.

**Q: Can I undo a book deactivation?**

A: Yes. **Owner** → **Books** → **Edit book** → select the book → **Reactivate this book**.

**Q: How do customers order books online?**

A: Share the app URL — the **Order Books** page opens without login. Customers browse
in-stock titles, add to cart, and place an order with name and phone. Staff fulfill
orders from **Online Orders** after the customer arrives to pay and collect.

**Q: Why can't I complete an online order — insufficient stock?**

A: Stock is not reserved when a guest places an order. Another sale may have reduced
stock since the order was placed. Check **Inventory**, adjust the counter sale or
purchase stock, or cancel the online order with a reason.

**Q: Do I need internet to use the app?**

A: No. The app runs on the shop's local network (LAN). Internet is not required for daily operation.

**Q: Analytics shows no data for my selected period.**

A: Ensure purchases and sales were recorded in that date range. Check that filters (sale type, category, etc.) are not too narrow. Try widening the period to **Last 30 days**.

**Q: What is the difference between Reports and Analytics?**

A: **Reports** gives formal statements (P&L, Sale–Purchase) for a date range — best for accounting. **Analytics** gives trends, charts, rankings, and alerts — best for day-to-day business decisions.

### Troubleshooting

| Problem | Likely cause | Solution |
|---------|-------------|----------|
| Cannot log in | Wrong password or deactivated account | Check caps lock; ask Owner to reset or reactivate |
| Page shows "Change your password" | First login or password was reset | Set a new password (min 6 chars, not the default) |
| "Add a supplier first" on Purchases | No suppliers in Contacts | Add supplier in Contacts |
| "Add books to the catalog first" | Empty catalog | Add books in Books → Add book |
| Receipt PDF missing Devanagari | Font not installed on server | Contact IT — Noto Sans Devanagari font required |
| Numbers differ between Reports P&L and Analytics Profit | Different date ranges or filters | Align the date range and filters; both should reconcile when settings match |
| Slow performance | Large date range with many transactions | Use shorter periods or monthly granularity |

---

## 16. Backup and LAN Access

### Accessing from multiple PCs

The application runs on the shop's main computer. Other PCs on the same local network can access it through a browser:

1. The main PC runs the application (your IT contact starts it).
2. On any shop PC, open a browser and go to: `http://<shop-pc-ip>:8501`
3. Log in with your username and password.

No internet connection is needed. All data stays on the shop's computer.

[Screenshot: Browser on a counter PC accessing the application via LAN IP]

### Automatic backups

The system creates an automatic backup of your data on the **first launch of each day**:

- Backups are stored on the main PC in the application's data folder.
- The 30 most recent daily backups are kept; older ones are removed automatically.
- Backups use a safe copy method that does not corrupt data even if the app is running.

### Restoring from a backup

If data is lost or corrupted, contact your IT person or the Owner. Restoration requires:

1. Stopping the application.
2. Copying the chosen backup file over the main database file.
3. Restarting the application.

**Do not attempt restoration while the app is running.** This is an IT/maintenance task, not a daily staff operation.

---

## 17. Glossary

| Term | Definition |
|------|-----------|
| **ABC classification** | A method of ranking inventory by revenue contribution. A = top ~80% of revenue, B = next ~15%, C = remainder. |
| **Avg ticket** | Average sale amount per transaction (Revenue ÷ Transactions). |
| **COGS** | Cost of Goods Sold — the cost of the books that were sold in a period. |
| **Days of supply** | Estimated days until stock runs out at the current sales rate (Stock ÷ average daily sales over 30 days). |
| **Dead stock** | Books with stock on hand but no sales for a long period (default: 180+ days). |
| **Devanagari** | The script used for Sanskrit text (e.g., रामायणम्). |
| **Gross profit** | Revenue minus COGS. Does not include rent, salaries, or other shop expenses. |
| **IAST / Roman** | Roman-letter transliteration of Sanskrit (e.g., Rāmāyaṇam). |
| **Low-stock threshold** | Per-book setting. When stock falls to this number or below, the title is flagged as low stock. |
| **Margin %** | Gross profit as a percentage of revenue. |
| **Paise** | Smallest currency unit (100 paise = 1 ₹). Used internally for precise calculations. |
| **Retail sale** | Sale to a walk-in customer at the counter. Uses retail price by default. |
| **Reorder suggestion** | System-calculated quantity recommended for purchase to restore stock to a safe level. |
| **Roman script** | See IAST / Roman. |
| **Slow mover** | A book with stock on hand but no recent sales (default: 90+ days). |
| **Soft cancellation** | A transaction marked as cancelled with a reason, but kept in the system for audit purposes. Stock is reversed. |
| **Stock ledger** | Per-book history of every stock movement (purchases, sales, adjustments) with running balance. |
| **Supplier** | A publisher or wholesaler you purchase books from. |
| **Weighted average (COGS)** | COGS method using the average of all purchase prices for a book. |
| **Last purchase price (COGS)** | COGS method using the most recent purchase price for a book. |
| **Wholesale customer** | A registered bulk buyer (another shop or reseller). Required for wholesale sales. |
| **Wholesale sale** | Sale to a registered wholesale customer. Uses wholesale price by default. |
| **Online order** | A guest request for books via the public Order Books page, fulfilled as a retail sale on pickup. |
| **Order fulfillment** | Staff action that marks a pending online order complete, records a sale, and decreases stock. |

---

*End of User Guide*

*For technical setup and developer information, see the project README. For questions about access or backups, contact your shop Owner or IT support.*
