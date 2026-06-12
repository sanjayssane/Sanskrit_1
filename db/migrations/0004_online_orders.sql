-- 0004_online_orders: guest online orders with staff fulfillment workflow.

CREATE TABLE online_orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_date      TEXT NOT NULL,
    customer_name   TEXT NOT NULL,
    customer_phone  TEXT NOT NULL,
    customer_email  TEXT,
    notes           TEXT,
    total_amount    INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','completed','cancelled')),
    sale_id         INTEGER REFERENCES sales(id),
    completed_by    INTEGER REFERENCES users(id),
    completed_at    TEXT,
    cancelled_by    INTEGER REFERENCES users(id),
    cancelled_at    TEXT,
    cancel_reason   TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_online_orders_status ON online_orders(status);
CREATE INDEX idx_online_orders_date ON online_orders(order_date);

CREATE TABLE online_order_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER NOT NULL REFERENCES online_orders(id),
    book_id     INTEGER NOT NULL REFERENCES books(id),
    quantity    INTEGER NOT NULL CHECK (quantity > 0),
    unit_price  INTEGER NOT NULL
);
CREATE INDEX idx_oitems_order ON online_order_items(order_id);
CREATE INDEX idx_oitems_book ON online_order_items(book_id);
