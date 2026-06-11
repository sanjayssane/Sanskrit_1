# Entity Relationship Diagram (ERD)

## Shop Management System — "Sanskrit Sahitya Ratnakar"

| | |
|---|---|
| **Document Version** | 1.0 |
| **Date** | 10 June 2026 |
| **Based On** | PRD.md v1.0, TECHNICAL_DESIGN.md v1.0 |

---

## 1. ER Diagram

```mermaid
erDiagram
    USERS {
        int id PK
        text username UK "unique, case-insensitive"
        text password_hash "bcrypt"
        text full_name
        text role "owner | employee"
        int is_active "soft deactivate"
        int must_change_pw "force change on first login"
        text created_at
    }

    BOOKS {
        int id PK
        text code UK "auto BK-0001"
        text title_devanagari
        text title_roman
        text author_roman
        text author_devanagari
        text publisher
        text category "Veda, Purana, Kavya..."
        text language "Sanskrit, Sanskrit-Hindi..."
        text isbn "optional"
        int retail_price "paise"
        int wholesale_price "paise"
        int low_stock_threshold "default 5"
        int is_active
        text created_at
    }

    SUPPLIERS {
        int id PK
        text name
        text contact_person
        text phone
        text address
        text notes
        int is_active
    }

    WHOLESALE_CUSTOMERS {
        int id PK
        text name
        text contact_person
        text phone
        text address
        text notes
        int is_active
    }

    PURCHASES {
        int id PK
        text purchase_date
        int supplier_id FK
        text invoice_ref "optional"
        text notes
        int total_amount "paise, denormalized"
        int created_by FK "audit FR-1.6"
        text created_at
        int is_cancelled "soft cancel"
        int cancelled_by FK "nullable"
        text cancel_reason
    }

    PURCHASE_ITEMS {
        int id PK
        int purchase_id FK
        int book_id FK
        int quantity "must be > 0"
        int unit_price "paise"
    }

    SALES {
        int id PK
        text sale_date
        text sale_type "retail | wholesale"
        int customer_id FK "NULL for retail"
        int discount "paise, whole-bill"
        text notes
        int total_amount "paise, after discount"
        int created_by FK
        text created_at
        int is_cancelled
        int cancelled_by FK "nullable"
        text cancel_reason
    }

    SALE_ITEMS {
        int id PK
        int sale_id FK
        int book_id FK
        int quantity "must be > 0"
        int unit_price "paise, editable at sale time"
    }

    STOCK_ADJUSTMENTS {
        int id PK
        text adjustment_date
        int book_id FK
        int quantity_delta "+found / -damaged"
        text reason "mandatory FR-6.4"
        int created_by FK "owner only"
        text created_at
    }

    USERS ||--o{ PURCHASES : "records (created_by)"
    USERS ||--o{ SALES : "records (created_by)"
    USERS ||--o{ STOCK_ADJUSTMENTS : "makes (created_by)"
    USERS |o--o{ PURCHASES : "cancels (cancelled_by)"
    USERS |o--o{ SALES : "cancels (cancelled_by)"

    SUPPLIERS ||--o{ PURCHASES : "supplies"
    WHOLESALE_CUSTOMERS |o--o{ SALES : "buys (wholesale only)"

    PURCHASES ||--|{ PURCHASE_ITEMS : "contains"
    SALES ||--|{ SALE_ITEMS : "contains"

    BOOKS ||--o{ PURCHASE_ITEMS : "purchased in"
    BOOKS ||--o{ SALE_ITEMS : "sold in"
    BOOKS ||--o{ STOCK_ADJUSTMENTS : "adjusted by"
```

---

## 2. Relationship Summary

| Relationship | Cardinality | Notes |
|---|---|---|
| USERS → PURCHASES (created_by) | 1 : many | Audit trail (FR-1.6) |
| USERS → SALES (created_by) | 1 : many | Audit trail (FR-1.6) |
| USERS → STOCK_ADJUSTMENTS (created_by) | 1 : many | Owner only (FR-6.4) |
| USERS → PURCHASES / SALES (cancelled_by) | 0..1 : many | Owner-only soft cancellation |
| SUPPLIERS → PURCHASES | 1 : many | Every purchase requires a supplier (FR-3.3) |
| WHOLESALE_CUSTOMERS → SALES | 0..1 : many | Required for wholesale, NULL for retail walk-ins (FR-3.3) |
| PURCHASES → PURCHASE_ITEMS | 1 : 1..many | Header / line-item split |
| SALES → SALE_ITEMS | 1 : 1..many | Header / line-item split |
| BOOKS → PURCHASE_ITEMS | 1 : many | Per-unit cost captured at purchase time |
| BOOKS → SALE_ITEMS | 1 : many | Per-unit price captured at sale time (FR-5.3) |
| BOOKS → STOCK_ADJUSTMENTS | 1 : many | Damage / loss / found / correction |

---

## 3. Key Modeling Notes

- **No stored stock entity**: current stock is derived, never stored —
  `Σ purchase_items.quantity − Σ sale_items.quantity + Σ stock_adjustments.quantity_delta`,
  excluding cancelled transactions (TDD §4, FR-6.1).
- **`SALES.customer_id` is optional**: retail walk-in sales have no customer; a `CHECK`
  constraint enforces that wholesale sales must have one (FR-3.3).
- **Header / line-item split**: `PURCHASES` and `SALES` are transaction headers;
  `PURCHASE_ITEMS` and `SALE_ITEMS` hold one row per book, capturing the per-unit price
  at transaction time. Catalog prices in `BOOKS` are only defaults (FR-5.3).
- **Soft delete / cancel everywhere**: `is_active` flags on users, books, suppliers, and
  customers; `is_cancelled` + `cancelled_by` + `cancel_reason` on purchases and sales —
  history is never destroyed (FR-2.5, FR-4.5, FR-5.8, NFR-7).
- **Audit trail**: every transaction-creating table carries `created_by` → `USERS` and
  `created_at` (FR-1.6, NFR-7).
- **Money as integer paise** in all price/amount columns to avoid floating-point drift;
  converted to rupees only at the UI layer (TDD §5.5).
- **Stock ledger (FR-6.5)** is a computed view that unions purchases, sales, and
  adjustments per book in chronological order — not a stored table.
