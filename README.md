# Sanskrit Sahitya Ratnakar — Shop Management System

A Streamlit + SQLite shop management system for a Sanskrit book shop:
dual-script catalog (Devanagari + Roman), inventory, purchases, sales with
printable receipts, and financial reports.

Built per `PRD.md`, `TECHNICAL_DESIGN.md`, `ERD.md`, and `DATABASE_PLAN.md`.

## Features

- **Catalog**: books with Devanagari and Roman titles, searchable in either
  script, duplicate warning, auto codes (`BK-0001`), soft deactivation
- **Purchases**: multi-line entry per supplier, atomic stock increase,
  filterable history, owner-only cancellation
- **Sales**: retail (walk-in) and wholesale, catalog price defaulting with
  per-line override, whole-bill discount, oversell blocked inside the
  transaction, A5 PDF receipt with Devanagari text
- **Inventory**: derived stock (never stored), low-stock flags, per-book
  ledger with running balance, owner-only manual adjustments with reasons
- **Reports**: Sale–Purchase statement, Profit & Loss (owner only, COGS at
  last purchase price), stock report — all exportable to CSV/Excel
- **Users**: 1 owner + employees, bcrypt passwords, forced password change on
  first login, deactivation keeps history intact
- **Money**: stored as integer paise everywhere; rupees only in the UI
- **Backups**: automatic daily copy on app launch, 30-day retention

## Setup

Requires Python 3.11+.

```bash
pip install -r requirements.txt
streamlit run app.py
```

On first run the app creates `data/shop.db`, applies migrations, and seeds
three accounts (all with password `change@123`, which must be changed at
first login):

| Username | Role |
|---|---|
| `owner` | Owner |
| `employee1` | Employee |
| `employee2` | Employee |

### Optional sample data

To load a demo catalog with a few Sanskrit titles and transactions (only
works on an empty catalog):

```bash
python -m db.seed_sample_data
```

## Shop LAN deployment (NFR-8)

Run on the shop's main PC and access from any browser on the local network:

```bash
streamlit run app.py --server.address 0.0.0.0
```

Then open `http://<shop-pc-ip>:8501` from the counter PCs. No internet is
required for daily operation.

## Backup and restore (NFR-6)

- **Backup**: automatic. On the first launch of each day the app copies
  `data/shop.db` to `data/backups/shop-YYYY-MM-DD.db` (sqlite3 backup API,
  safe under WAL). The most recent 30 copies are kept.
- **Restore**: stop the app, copy the chosen backup file over
  `data/shop.db` (also delete `data/shop.db-wal` / `data/shop.db-shm` if
  present), and start the app again.

## Project structure

```
app.py                  Entry point: login gate + role-based navigation
pages/                  Streamlit pages (UI only, no SQL)
services/               Business logic: auth, books, purchases, sales,
                        inventory, reports, contacts
db/                     database.py (connection, migrations, seeding),
                        migrations/*.sql, seed_sample_data.py
utils/                  money, receipt PDF, CSV/Excel exports, backup
assets/                 Noto Sans Devanagari TTF (embedded in PDFs)
data/                   shop.db + backups/ (created at first run, gitignored)
tests/                  pytest suite for the db and service layers
```

## Database

- SQLite file (`data/shop.db`), WAL mode, foreign keys enforced.
- Versioned migrations in `db/migrations/` tracked via `PRAGMA user_version`;
  applied automatically and atomically at startup.
- Current stock is always derived:
  purchases − sales + adjustments, excluding cancelled transactions
  (views `v_current_stock` and `v_stock_ledger`).
- Cancellations are soft (`is_cancelled` + who + why); history is never
  deleted.

## Running tests

```bash
python -m pytest tests/ -q
```
