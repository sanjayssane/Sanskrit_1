-- 0002_views: derived stock views per DATABASE_PLAN.md §4.2.
-- Stock is never stored; both views exclude cancelled transactions.

DROP VIEW IF EXISTS v_current_stock;
CREATE VIEW v_current_stock AS
SELECT b.id  AS book_id,
       b.code,
       b.title_devanagari,
       b.title_roman,
       b.publisher,
       b.category,
       b.retail_price,
       b.wholesale_price,
       b.low_stock_threshold,
       b.is_active,
       COALESCE(p.qty, 0) - COALESCE(s.qty, 0) + COALESCE(a.qty, 0) AS stock,
       COALESCE((SELECT pi.unit_price
                 FROM purchase_items pi
                 JOIN purchases pu ON pu.id = pi.purchase_id
                 WHERE pi.book_id = b.id AND pu.is_cancelled = 0
                 ORDER BY pu.purchase_date DESC, pi.id DESC
                 LIMIT 1), 0) AS last_purchase_price
FROM books b
LEFT JOIN (SELECT pi.book_id, SUM(pi.quantity) AS qty
           FROM purchase_items pi
           JOIN purchases pu ON pu.id = pi.purchase_id
           WHERE pu.is_cancelled = 0
           GROUP BY pi.book_id) p ON p.book_id = b.id
LEFT JOIN (SELECT si.book_id, SUM(si.quantity) AS qty
           FROM sale_items si
           JOIN sales sa ON sa.id = si.sale_id
           WHERE sa.is_cancelled = 0
           GROUP BY si.book_id) s ON s.book_id = b.id
LEFT JOIN (SELECT book_id, SUM(quantity_delta) AS qty
           FROM stock_adjustments
           GROUP BY book_id) a ON a.book_id = b.id;

DROP VIEW IF EXISTS v_stock_ledger;
CREATE VIEW v_stock_ledger AS
SELECT pi.book_id,
       pu.purchase_date     AS movement_date,
       pu.created_at        AS created_at,
       'purchase'           AS movement_type,
       pi.quantity          AS quantity_delta,
       pu.id                AS reference_id,
       pu.created_by        AS created_by
FROM purchase_items pi
JOIN purchases pu ON pu.id = pi.purchase_id
WHERE pu.is_cancelled = 0
UNION ALL
SELECT si.book_id,
       sa.sale_date,
       sa.created_at,
       'sale',
       -si.quantity,
       sa.id,
       sa.created_by
FROM sale_items si
JOIN sales sa ON sa.id = si.sale_id
WHERE sa.is_cancelled = 0
UNION ALL
SELECT book_id,
       adjustment_date,
       created_at,
       'adjustment',
       quantity_delta,
       id,
       created_by
FROM stock_adjustments;
