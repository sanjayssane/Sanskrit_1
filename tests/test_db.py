"""Database layer verification (DATABASE_PLAN.md §6)."""

import sqlite3

import bcrypt
import pytest

from db import database


@pytest.fixture()
def conn(tmp_path):
    connection = database.init_db(tmp_path / "test.db")
    yield connection
    connection.close()


def _add_book(conn, code="BK-0001", title_dev="\u0930\u093e\u092e\u093e\u092f\u0923\u092e\u094d",
              title_roman="Ramayanam"):
    cur = conn.execute(
        "INSERT INTO books (code, title_devanagari, title_roman, retail_price, wholesale_price)"
        " VALUES (?, ?, ?, 25000, 20000)",
        (code, title_dev, title_roman),
    )
    conn.commit()
    return cur.lastrowid


def _add_supplier(conn, name="Chowkhamba"):
    cur = conn.execute("INSERT INTO suppliers (name) VALUES (?)", (name,))
    conn.commit()
    return cur.lastrowid


def _add_purchase(conn, supplier_id, book_id, qty, unit_price=10000, user_id=1,
                  date="2026-06-01"):
    with conn:
        cur = conn.execute(
            "INSERT INTO purchases (purchase_date, supplier_id, total_amount, created_by)"
            " VALUES (?, ?, ?, ?)",
            (date, supplier_id, qty * unit_price, user_id),
        )
        purchase_id = cur.lastrowid
        conn.execute(
            "INSERT INTO purchase_items (purchase_id, book_id, quantity, unit_price)"
            " VALUES (?, ?, ?, ?)",
            (purchase_id, book_id, qty, unit_price),
        )
    return purchase_id


def _add_sale(conn, book_id, qty, unit_price=25000, user_id=1, date="2026-06-02"):
    with conn:
        cur = conn.execute(
            "INSERT INTO sales (sale_date, sale_type, total_amount, created_by)"
            " VALUES (?, 'retail', ?, ?)",
            (date, qty * unit_price, user_id),
        )
        sale_id = cur.lastrowid
        conn.execute(
            "INSERT INTO sale_items (sale_id, book_id, quantity, unit_price)"
            " VALUES (?, ?, ?, ?)",
            (sale_id, book_id, qty, unit_price),
        )
    return sale_id


def _stock(conn, book_id):
    return conn.execute(
        "SELECT stock FROM v_current_stock WHERE book_id = ?", (book_id,)
    ).fetchone()["stock"]


# 1. Migration -------------------------------------------------------------

def test_migrate_reaches_latest_version_and_is_idempotent(conn):
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    assert version >= 2
    assert database.migrate(conn) == version  # second run is a no-op

    tables = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()}
    assert {"users", "books", "suppliers", "wholesale_customers", "purchases",
            "purchase_items", "sales", "sale_items", "stock_adjustments"} <= tables
    views = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'view'").fetchall()}
    assert {"v_current_stock", "v_stock_ledger"} <= views


# 2. Seed ------------------------------------------------------------------

def test_seeded_users(conn):
    rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    assert [r["username"] for r in rows] == ["owner", "employee1", "employee2"]
    assert [r["role"] for r in rows] == ["owner", "employee", "employee"]
    for row in rows:
        assert row["must_change_pw"] == 1
        assert bcrypt.checkpw(b"change@123", row["password_hash"].encode())

    database.seed_initial_users(conn)  # must not duplicate
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 3


# 3. Constraints -----------------------------------------------------------

def test_duplicate_username_case_insensitive(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO users (username, password_hash, full_name, role)"
            " VALUES ('OWNER', 'x', 'Dup', 'employee')")


def test_duplicate_book_code_rejected(conn):
    _add_book(conn)
    with pytest.raises(sqlite3.IntegrityError):
        _add_book(conn, code="BK-0001", title_roman="Other")


def test_non_positive_quantity_rejected(conn):
    book = _add_book(conn)
    supplier = _add_supplier(conn)
    purchase = _add_purchase(conn, supplier, book, 1)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO purchase_items (purchase_id, book_id, quantity, unit_price)"
            " VALUES (?, ?, 0, 100)", (purchase, book))


def test_wholesale_sale_requires_customer(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO sales (sale_date, sale_type, total_amount, created_by)"
            " VALUES ('2026-06-01', 'wholesale', 100, 1)")


def test_foreign_keys_enforced(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO purchases (purchase_date, supplier_id, total_amount, created_by)"
            " VALUES ('2026-06-01', 999, 0, 1)")


def test_invalid_payment_method_rejected(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO sales (sale_date, sale_type, total_amount, payment_method, created_by)"
            " VALUES ('2026-06-01', 'retail', 100, 'bitcoin', 1)")


# 4. Unicode ---------------------------------------------------------------

def test_devanagari_round_trip_and_search(conn):
    title = "\u0930\u093e\u092e\u093e\u092f\u0923\u092e\u094d"  # रामायणम्
    book = _add_book(conn, title_dev=title)
    row = conn.execute("SELECT title_devanagari FROM books WHERE id = ?", (book,)).fetchone()
    assert row["title_devanagari"] == title
    found = conn.execute(
        "SELECT id FROM books WHERE title_devanagari LIKE ?", (f"%{title[:3]}%",)
    ).fetchall()
    assert [r["id"] for r in found] == [book]


# 5. Stock derivation ------------------------------------------------------

def test_stock_derivation_and_cancellation(conn):
    book = _add_book(conn)
    supplier = _add_supplier(conn)
    assert _stock(conn, book) == 0

    _add_purchase(conn, supplier, book, 10)
    assert _stock(conn, book) == 10

    sale = _add_sale(conn, book, 3)
    assert _stock(conn, book) == 7

    with conn:
        conn.execute(
            "INSERT INTO stock_adjustments (adjustment_date, book_id, quantity_delta, reason, created_by)"
            " VALUES ('2026-06-03', ?, -1, 'damaged copy', 1)", (book,))
    assert _stock(conn, book) == 6

    with conn:
        conn.execute(
            "UPDATE sales SET is_cancelled = 1, cancelled_by = 1, cancel_reason = 'test'"
            " WHERE id = ?", (sale,))
    assert _stock(conn, book) == 9


def test_last_purchase_price(conn):
    book = _add_book(conn)
    supplier = _add_supplier(conn)
    _add_purchase(conn, supplier, book, 5, unit_price=10000, date="2026-06-01")
    _add_purchase(conn, supplier, book, 5, unit_price=12000, date="2026-06-05")
    row = conn.execute(
        "SELECT last_purchase_price FROM v_current_stock WHERE book_id = ?", (book,)
    ).fetchone()
    assert row["last_purchase_price"] == 12000


# 6. Ledger ----------------------------------------------------------------

def test_stock_ledger_order_and_signs(conn):
    book = _add_book(conn)
    supplier = _add_supplier(conn)
    _add_purchase(conn, supplier, book, 10, date="2026-06-01")
    _add_sale(conn, book, 3, date="2026-06-02")
    with conn:
        conn.execute(
            "INSERT INTO stock_adjustments (adjustment_date, book_id, quantity_delta, reason, created_by)"
            " VALUES ('2026-06-03', ?, -1, 'lost', 1)", (book,))

    rows = conn.execute(
        "SELECT movement_type, quantity_delta FROM v_stock_ledger"
        " WHERE book_id = ? ORDER BY movement_date, created_at", (book,)
    ).fetchall()
    assert [(r["movement_type"], r["quantity_delta"]) for r in rows] == [
        ("purchase", 10), ("sale", -3), ("adjustment", -1)]


# 7. Atomicity -------------------------------------------------------------

def test_failed_transaction_rolls_back_whole_purchase(conn):
    book = _add_book(conn)
    supplier = _add_supplier(conn)
    with pytest.raises(sqlite3.IntegrityError):
        with conn:
            cur = conn.execute(
                "INSERT INTO purchases (purchase_date, supplier_id, total_amount, created_by)"
                " VALUES ('2026-06-01', ?, 10000, 1)", (supplier,))
            conn.execute(
                "INSERT INTO purchase_items (purchase_id, book_id, quantity, unit_price)"
                " VALUES (?, ?, -5, 100)", (cur.lastrowid, book))  # CHECK fails
    assert conn.execute("SELECT COUNT(*) FROM purchases").fetchone()[0] == 0
    assert _stock(conn, book) == 0
