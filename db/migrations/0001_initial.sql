-- 0001_initial: full schema per TECHNICAL_DESIGN.md §4 + DATABASE_PLAN.md §4.1
-- Money columns are INTEGER paise (1 INR = 100 paise). Dates are TEXT ISO.

CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash   TEXT NOT NULL,
    full_name       TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('owner','employee')),
    is_active       INTEGER NOT NULL DEFAULT 1,
    must_change_pw  INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE books (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    code                TEXT NOT NULL UNIQUE,
    title_devanagari    TEXT NOT NULL,
    title_roman         TEXT NOT NULL,
    author_roman        TEXT,
    author_devanagari   TEXT,
    publisher           TEXT,
    category            TEXT,
    language            TEXT,
    isbn                TEXT,
    retail_price        INTEGER NOT NULL DEFAULT 0,
    wholesale_price     INTEGER NOT NULL DEFAULT 0,
    low_stock_threshold INTEGER NOT NULL DEFAULT 5,
    is_active           INTEGER NOT NULL DEFAULT 1,
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_books_title_roman ON books(title_roman COLLATE NOCASE);
CREATE INDEX idx_books_title_dev   ON books(title_devanagari);

CREATE TABLE suppliers (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    contact_person TEXT,
    phone          TEXT,
    address        TEXT,
    notes          TEXT,
    is_active      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE wholesale_customers (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    contact_person TEXT,
    phone          TEXT,
    address        TEXT,
    notes          TEXT,
    is_active      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE purchases (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_date TEXT NOT NULL,
    supplier_id   INTEGER NOT NULL REFERENCES suppliers(id),
    invoice_ref   TEXT,
    notes         TEXT,
    total_amount  INTEGER NOT NULL,
    created_by    INTEGER NOT NULL REFERENCES users(id),
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    is_cancelled  INTEGER NOT NULL DEFAULT 0,
    cancelled_by  INTEGER REFERENCES users(id),
    cancel_reason TEXT
);
CREATE INDEX idx_purchases_date ON purchases(purchase_date);

CREATE TABLE purchase_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL REFERENCES purchases(id),
    book_id     INTEGER NOT NULL REFERENCES books(id),
    quantity    INTEGER NOT NULL CHECK (quantity > 0),
    unit_price  INTEGER NOT NULL
);
CREATE INDEX idx_pitems_book     ON purchase_items(book_id);
CREATE INDEX idx_pitems_purchase ON purchase_items(purchase_id);

CREATE TABLE sales (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_date      TEXT NOT NULL,
    sale_type      TEXT NOT NULL CHECK (sale_type IN ('retail','wholesale')),
    customer_id    INTEGER REFERENCES wholesale_customers(id),
    discount       INTEGER NOT NULL DEFAULT 0,
    notes          TEXT,
    total_amount   INTEGER NOT NULL,
    payment_method TEXT NOT NULL DEFAULT 'cash'
                   CHECK (payment_method IN ('cash','upi','card','cheque')),
    created_by     INTEGER NOT NULL REFERENCES users(id),
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    is_cancelled   INTEGER NOT NULL DEFAULT 0,
    cancelled_by   INTEGER REFERENCES users(id),
    cancel_reason  TEXT,
    CHECK (sale_type = 'retail' OR customer_id IS NOT NULL)
);
CREATE INDEX idx_sales_date ON sales(sale_date);

CREATE TABLE sale_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id    INTEGER NOT NULL REFERENCES sales(id),
    book_id    INTEGER NOT NULL REFERENCES books(id),
    quantity   INTEGER NOT NULL CHECK (quantity > 0),
    unit_price INTEGER NOT NULL
);
CREATE INDEX idx_sitems_book ON sale_items(book_id);
CREATE INDEX idx_sitems_sale ON sale_items(sale_id);

CREATE TABLE stock_adjustments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    adjustment_date TEXT NOT NULL,
    book_id         INTEGER NOT NULL REFERENCES books(id),
    quantity_delta  INTEGER NOT NULL,
    reason          TEXT NOT NULL,
    created_by      INTEGER NOT NULL REFERENCES users(id),
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_adjust_book ON stock_adjustments(book_id);
