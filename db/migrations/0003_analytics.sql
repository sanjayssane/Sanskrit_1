-- Analytics: app settings + query indexes (ADVANCED_ANALYTICS_REQUIREMENTS.md §7.4)

CREATE TABLE IF NOT EXISTS app_settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT OR IGNORE INTO app_settings (key, value) VALUES
    ('fiscal_year_start_month', '4'),
    ('dead_stock_days', '180'),
    ('slow_mover_days', '90'),
    ('days_of_supply_threshold', '14'),
    ('dead_stock_capital_alert_paise', '5000000'),
    ('margin_drop_alert_points', '5'),
    ('cogs_method', 'last_purchase');

CREATE INDEX IF NOT EXISTS idx_sales_type_date ON sales(sale_type, sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_created_by ON sales(created_by);
CREATE INDEX IF NOT EXISTS idx_purchases_supplier ON purchases(supplier_id);
CREATE INDEX IF NOT EXISTS idx_books_category ON books(category);
CREATE INDEX IF NOT EXISTS idx_books_publisher ON books(publisher);
