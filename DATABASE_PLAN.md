# Database Design & Migration Plan

## Shop Management System — "Sanskrit Sahitya Ratnakar"

| | |
|---|---|
| **Document Version** | 1.0 |
| **Date** | 10 June 2026 |
| **Based On** | PRD.md v1.0, TECHNICAL_DESIGN.md v1.0, ERD.md v1.0 |
| **Scope** | Database layer only: schema, migrations, seeding, verification |

---

## 1. Goals

1. Implement the 9-table schema from TECHNICAL_DESIGN.md §4 / ERD.md in SQLite.
2. Provide a **versioned migration mechanism** so the schema can evolve safely after the shop's database has live data.
3. Seed initial users (owner, employee1, employee2) per PRD §3.3 / TDD §5.1.
4. Provide derived views for current stock and the per-book stock ledger (FR-6.1, FR-6.5).
5. Verify everything with an automated smoke test.

## 2. Design Decisions (confirmed from existing docs)

| Decision | Choice | Source |
|---|---|---|
| Engine | SQLite file at `data/shop.db`, stdlib `sqlite3`, no ORM | TDD §1 |
| Connection settings | `PRAGMA foreign_keys = ON` and `journal_mode = WAL` on every connection | TDD §4, §5.2 |
| Money | `INTEGER` paise everywhere; rupees only in UI | TDD §5.5 |
| Dates | `TEXT` ISO — `YYYY-MM-DD` for business dates, `datetime('now')` UTC for audit timestamps | TDD §4 |
| Stock | Never stored; derived from purchases − sales + adjustments, excluding cancelled | ERD §3 |
| Deletes | Soft only: `is_active` on master data, `is_cancelled` + `cancelled_by` + `cancel_reason` on transactions | ERD §3 |
| Audit | `created_by` → `users.id` and `created_at` on every transaction table | FR-1.6, NFR-7 |
| Book code | `BK-0001` style, generated in the repository layer (zero-padded `MAX(id)+1`), `UNIQUE` in schema | FR-2.1 |

### 2.1 SampleUI deviations — resolved in favor of PRD/TDD

The `SampleUI` mockup (`lib/types.ts`) differs from the approved design in ways that will **not** be carried into the schema:

| SampleUI feature | Decision | Reason |
|---|---|---|
| `gstPercent` / `gstAmount` on purchases & sales, `gstin` on contacts | **Excluded** | GST explicitly out of scope for v1.0 (PRD §1.2) |
| `stock` stored on Book | **Excluded** | Stock is derived, never stored (ERD §3, NFR-4) |
| Single book per purchase/sale | **Excluded** | Header/line-item split is the approved model (FR-4.1, FR-5.2) |
| Unified `Contact` (supplier + customer in one table) | **Excluded** | Separate `suppliers` and `wholesale_customers` tables (TDD §4) |
| Stored `StockLedger` table | **Excluded** | Ledger is a computed view (ERD §3) |
| `paymentMethod` (cash/upi/card/cheque) on Sale | **Included as `payment_method`** | Cheap to add now, painful to backfill later; defaults to `'cash'`; not in any v1.0 report |
| `receiptNumber` on Sale | **Excluded** | Sale `id` serves as the receipt number on the printed receipt |
| `email` on users/contacts | **Excluded** | Login is username-based (FR-1.1); shop operates offline |

> The one schema addition vs. TDD §4 is `sales.payment_method TEXT NOT NULL DEFAULT 'cash' CHECK (payment_method IN ('cash','upi','card','cheque'))`. If not wanted, drop it from `0001_initial.sql` — nothing else depends on it.

## 3. Migration Mechanism

No ORM, so use SQLite's built-in **`PRAGMA user_version`** as the schema version counter with plain `.sql` migration files applied in order.

### 3.1 Layout

```
db/
├── database.py                 # get_connection(), migrate(), seed_initial_users()
└── migrations/
    ├── 0001_initial.sql        # all 9 tables + indexes
    ├── 0002_views.sql          # v_current_stock, v_stock_ledger
    └── ...                     # future: 0003_xxx.sql
```

### 3.2 Runner behavior (`database.py`)

1. `get_connection()` — opens `data/shop.db`, sets `row_factory = sqlite3.Row`, executes `PRAGMA foreign_keys = ON` and `PRAGMA journal_mode = WAL`.
2. `migrate(conn)` — called once at app startup (from `app.py`):
   - Reads `PRAGMA user_version` (0 on a fresh file).
   - Lists `db/migrations/*.sql`, sorted by numeric prefix.
   - For each file with prefix > current version: run its statements and `PRAGMA user_version = N` **inside one transaction**, so a failed migration leaves the DB untouched.
   - Idempotent: running at every startup is safe; already-applied files are skipped.
3. `seed_initial_users(conn)` — runs after migrations, in Python (not SQL, because bcrypt hashing needs Python): if `users` is empty, insert `owner`, `employee1`, `employee2` with role per PRD §3.3, default password `change@123` (bcrypt-hashed), `must_change_pw = 1`.

### 3.3 Rules for future migrations

- Never edit an applied migration file; always add a new numbered file.
- SQLite has limited `ALTER TABLE`; column drops/renames use the standard recreate-and-copy pattern inside the migration's transaction.
- Views are dropped and recreated (`DROP VIEW IF EXISTS` + `CREATE VIEW`) whenever their definition changes.
- A migration must never destroy transaction history (NFR-7).

## 4. Migration Contents

### 4.1 `0001_initial.sql` — tables and indexes

Exactly the DDL from TECHNICAL_DESIGN.md §4 (9 tables), plus `sales.payment_method` (§2.1 above):

1. `users` — unique case-insensitive `username`, `role` CHECK, `must_change_pw`
2. `books` — unique `code`, dual-script titles/authors, prices in paise, `low_stock_threshold`
3. `suppliers`
4. `wholesale_customers`
5. `purchases` — supplier FK NOT NULL, audit + soft-cancel columns
6. `purchase_items` — quantity CHECK `> 0`
7. `sales` — `sale_type` CHECK, `CHECK (sale_type = 'retail' OR customer_id IS NOT NULL)`, `payment_method`, audit + soft-cancel columns
8. `sale_items` — quantity CHECK `> 0`
9. `stock_adjustments` — mandatory `reason`

Indexes (search and join performance, NFR-3):

- `idx_books_title_roman` (NOCASE), `idx_books_title_dev` — dual-script search (FR-2.3)
- `idx_pitems_book`, `idx_sitems_book` — stock derivation joins
- Additional to TDD (cheap, helps every history filter): `idx_pitems_purchase(purchase_id)`, `idx_sitems_sale(sale_id)`, `idx_purchases_date(purchase_date)`, `idx_sales_date(sale_date)`, `idx_adjust_book(book_id)`

### 4.2 `0002_views.sql` — derived views

**`v_current_stock`** — the TDD §4 stock query as a view: per book, `COALESCE(purchased,0) − COALESCE(sold,0) + COALESCE(adjusted,0)`, excluding cancelled transactions. Also exposes `last_purchase_price` (most recent non-cancelled purchase item per book) so the inventory screen (FR-6.2) and COGS (FR-7.2) read from one place.

**`v_stock_ledger`** — `UNION ALL` of three movement sources per book, each row: `book_id, movement_date, created_at, movement_type ('purchase'|'sale'|'adjustment'), quantity_delta (+/−), reference_id, created_by`. Excludes cancelled transactions. Running balance computed in the service layer (or via a window function `SUM() OVER (ORDER BY ...)`) — FR-6.5.

Views keep the repository layer thin and guarantee every screen/report derives stock identically (NFR-4 correctness).

## 5. Implementation Steps

| # | Step | Deliverable |
|---|---|---|
| 1 | Project scaffolding | `db/`, `db/migrations/`, `data/` (gitignored), `requirements.txt` (add `bcrypt`, `pytest` for tests), `.gitignore` for `data/shop.db*` |
| 2 | `0001_initial.sql` | Full DDL per §4.1 |
| 3 | `0002_views.sql` | `v_current_stock`, `v_stock_ledger` |
| 4 | `db/database.py` | `get_connection()`, `migrate()`, `seed_initial_users()` per §3.2 |
| 5 | Verification tests | `tests/test_db.py` per §6 |
| 6 | (Optional) sample data seed | `db/seed_sample_data.py` — a few Sanskrit titles (Devanagari + Roman), suppliers, transactions for manual UI testing; never auto-run |

## 6. Verification (step 5 detail)

`pytest` suite against a temp-file database:

1. **Migration**: fresh DB migrates to latest `user_version`; running `migrate()` twice is a no-op.
2. **Seed**: 3 users exist with correct roles; passwords verify with bcrypt; `must_change_pw = 1`.
3. **Constraints**: reject duplicate username (case-insensitive), duplicate book code, `quantity <= 0`, wholesale sale with NULL customer, FK violations (e.g., purchase with bad `supplier_id`).
4. **Unicode**: insert and search a Devanagari title (e.g., रामायणम्) via `LIKE` — round-trips intact (NFR-1).
5. **Stock derivation**: purchase 10 + sell 3 + adjust −1 → `v_current_stock` = 6; cancel the sale → 9 (FR-4.2, FR-5.4, FR-6.1).
6. **Ledger**: `v_stock_ledger` returns the 3 movements in chronological order with correct signs.
7. **Atomicity**: a failing insert mid-transaction rolls back the whole purchase (NFR-4).

## 7. Out of Scope for This Plan

- Service layer (stock check on sale, COGS, totals) — consumes the views but lives in `services/` (TDD milestone M1+).
- Streamlit pages, auth/session flow, receipts, exports, backups.
- These follow in TDD §8 milestones M1–M6; this plan completes the database portion of M1.
