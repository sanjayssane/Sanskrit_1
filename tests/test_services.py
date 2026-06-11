"""Service-layer tests against a temporary database."""

import pytest

from db import database


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point every service at a fresh temp database."""
    path = tmp_path / "shop.db"
    monkeypatch.setattr(database, "DB_PATH", path)
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    conn = database.init_db(path)
    conn.close()
    yield path


# --- Auth and user lifecycle (AC-1, AC-8) ------------------------------------

def test_auth_lifecycle():
    from services import auth_service

    # Seeded users log in with the default password and must change it.
    user = auth_service.authenticate("owner", "change@123")
    assert user and user["role"] == "owner" and user["must_change_pw"]
    assert auth_service.authenticate("owner", "wrong") is None

    # Owner adds a new employee; the employee logs in and changes the password.
    new_id = auth_service.create_user("employee3", "New Hire", "temp@123")
    with pytest.raises(ValueError):
        auth_service.create_user("EMPLOYEE3", "Case Dup", "temp@123")
    emp = auth_service.authenticate("employee3", "temp@123")
    assert emp["must_change_pw"]
    auth_service.change_password(new_id, "my-own-pw")
    emp = auth_service.authenticate("employee3", "my-own-pw")
    assert not emp["must_change_pw"]

    # Deactivation blocks login; reset forces a change at next login.
    auth_service.set_active(new_id, False)
    assert auth_service.authenticate("employee3", "my-own-pw") is None
    auth_service.set_active(new_id, True)
    auth_service.reset_password(new_id, "reset@123")
    assert auth_service.authenticate("employee3", "reset@123")["must_change_pw"]


def test_delete_user_without_history():
    from services import auth_service

    new_id = auth_service.create_user("tempuser", "Temp User", "temp@123")
    assert auth_service.delete_block_reason(new_id, acting_user_id=1) is None
    auth_service.delete_user(new_id, acting_user_id=1)
    assert all(u["username"] != "tempuser" for u in auth_service.list_users())


def test_delete_user_blocked_for_self_or_only_owner():
    from services import auth_service

    assert auth_service.delete_block_reason(1, acting_user_id=1) is not None
    assert auth_service.delete_block_reason(1, acting_user_id=2) is not None


def test_delete_user_blocked_after_recording_transaction():
    from services import auth_service, book_service, contact_service, purchase_service

    emp_id = auth_service.create_user("worker", "Worker", "temp@123")
    book_id = book_service.add_book({
        "title_devanagari": "\u0915\u093e\u0924\u094d\u092f", "title_roman": "Test",
        "author_roman": None, "author_devanagari": None, "publisher": "P",
        "category": None, "language": None, "isbn": None,
        "retail_price": 10000, "wholesale_price": 8000, "low_stock_threshold": 5,
    })
    supplier_id = contact_service.add_contact("supplier", {"name": "S"})
    purchase_service.create_purchase(
        "2026-06-01", supplier_id,
        [{"book_id": book_id, "quantity": 1, "unit_price": 5000}],
        user_id=emp_id)
    assert auth_service.delete_block_reason(emp_id, acting_user_id=1) is not None
    with pytest.raises(ValueError):
        auth_service.delete_user(emp_id, acting_user_id=1)


def test_daily_backup_creates_one_copy_per_day():
    from utils import backup

    first = backup.backup_if_needed()
    assert first is not None
    assert backup.backup_if_needed() is None  # second call same day: no-op


# --- Books (AC-2) ----------------------------------------------------------

def _sample_book(**overrides):
    fields = {
        "title_devanagari": "\u0930\u093e\u092e\u093e\u092f\u0923\u092e\u094d",  # रामायणम्
        "title_roman": "Ramayanam",
        "author_roman": "Valmiki",
        "author_devanagari": None,
        "publisher": "Chowkhamba",
        "category": "Kavya",
        "language": "Sanskrit",
        "isbn": None,
        "retail_price": 25000,
        "wholesale_price": 20000,
        "low_stock_threshold": 5,
    }
    fields.update(overrides)
    return fields


def test_add_book_generates_code_and_search_finds_both_scripts():
    from services import book_service

    book_id = book_service.add_book(_sample_book())
    book = book_service.get_book(book_id)
    assert book["code"] == "BK-0001"

    by_roman = book_service.search_books("ramaya")
    by_dev = book_service.search_books("\u0930\u093e\u092e\u093e")
    by_code = book_service.search_books("BK-0001")
    assert [b["id"] for b in by_roman] == [book_id]
    assert [b["id"] for b in by_dev] == [book_id]
    assert [b["id"] for b in by_code] == [book_id]


def test_duplicate_detection_same_title_and_publisher():
    from services import book_service

    book_service.add_book(_sample_book())
    dups = book_service.find_duplicates(
        "RAMAYANAM", "\u0905\u0928\u094d\u092f", "Chowkhamba")
    assert len(dups) == 1
    assert not book_service.find_duplicates("Ramayanam", "x", "Other Publisher")


def test_deactivated_book_hidden_from_default_search():
    from services import book_service

    book_id = book_service.add_book(_sample_book())
    book_service.set_active(book_id, False)
    assert book_service.search_books("Ramayanam") == []
    assert len(book_service.search_books("Ramayanam", include_inactive=True)) == 1


# --- Purchases (AC-3 purchase half) -----------------------------------------

def _stock_of(book_id):
    from services import book_service

    return next(b["stock"] for b in book_service.list_active_books()
                if b["id"] == book_id)


def test_purchase_increases_stock_and_cancel_reverses():
    from services import book_service, contact_service, purchase_service

    book_id = book_service.add_book(_sample_book())
    supplier_id = contact_service.add_contact("supplier", {"name": "Chowkhamba"})

    purchase_id = purchase_service.create_purchase(
        "2026-06-01", supplier_id,
        [{"book_id": book_id, "quantity": 10, "unit_price": 10000}],
        user_id=1, invoice_ref="INV-1")
    assert _stock_of(book_id) == 10

    headers = purchase_service.list_purchases("2026-06-01", "2026-06-30")
    assert headers[0]["total_amount"] == 100000
    assert headers[0]["supplier_name"] == "Chowkhamba"

    purchase_service.cancel_purchase(purchase_id, owner_id=1, reason="entry error")
    assert _stock_of(book_id) == 0
    with pytest.raises(ValueError):
        purchase_service.cancel_purchase(purchase_id, owner_id=1, reason="again")


def test_purchase_rejects_empty_or_invalid_items():
    from services import contact_service, purchase_service

    supplier_id = contact_service.add_contact("supplier", {"name": "S"})
    with pytest.raises(ValueError):
        purchase_service.create_purchase("2026-06-01", supplier_id, [], user_id=1)
    with pytest.raises(ValueError):
        purchase_service.create_purchase(
            "2026-06-01", supplier_id,
            [{"book_id": 1, "quantity": 0, "unit_price": 100}], user_id=1)


# --- Sales (AC-3 sale half, AC-4) -------------------------------------------

def _stocked_book(qty=10):
    from services import book_service, contact_service, purchase_service

    book_id = book_service.add_book(_sample_book())
    supplier_id = contact_service.add_contact("supplier", {"name": "S"})
    purchase_service.create_purchase(
        "2026-06-01", supplier_id,
        [{"book_id": book_id, "quantity": qty, "unit_price": 10000}], user_id=1)
    return book_id


def test_sale_decreases_stock_and_cancel_restores():
    from services import sale_service

    book_id = _stocked_book(10)
    sale_id = sale_service.create_sale(
        "2026-06-02", "retail",
        [{"book_id": book_id, "quantity": 3, "unit_price": 25000}], user_id=1,
        discount=5000)
    assert _stock_of(book_id) == 7

    sale = sale_service.get_sale(sale_id)
    assert sale["total_amount"] == 3 * 25000 - 5000

    sale_service.cancel_sale(sale_id, owner_id=1, reason="returned")
    assert _stock_of(book_id) == 10


def test_oversell_is_blocked(): 
    from services import sale_service
    from services.sale_service import InsufficientStockError

    book_id = _stocked_book(5)
    with pytest.raises(InsufficientStockError):
        sale_service.create_sale(
            "2026-06-02", "retail",
            [{"book_id": book_id, "quantity": 6, "unit_price": 25000}], user_id=1)
    # Two lines of the same book exceeding stock together are also blocked.
    with pytest.raises(InsufficientStockError):
        sale_service.create_sale(
            "2026-06-02", "retail",
            [{"book_id": book_id, "quantity": 3, "unit_price": 25000},
             {"book_id": book_id, "quantity": 3, "unit_price": 25000}], user_id=1)
    assert _stock_of(book_id) == 5  # nothing was written


def test_wholesale_requires_customer_and_discount_bounds():
    from services import contact_service, sale_service

    book_id = _stocked_book(5)
    with pytest.raises(ValueError):
        sale_service.create_sale(
            "2026-06-02", "wholesale",
            [{"book_id": book_id, "quantity": 1, "unit_price": 20000}], user_id=1)
    with pytest.raises(ValueError):
        sale_service.create_sale(
            "2026-06-02", "retail",
            [{"book_id": book_id, "quantity": 1, "unit_price": 20000}],
            user_id=1, discount=99999999)

    customer_id = contact_service.add_contact("customer", {"name": "Bharatiya Pustak"})
    sale_id = sale_service.create_sale(
        "2026-06-02", "wholesale",
        [{"book_id": book_id, "quantity": 2, "unit_price": 20000}],
        user_id=1, customer_id=customer_id)
    assert sale_service.get_sale(sale_id)["customer_name"] == "Bharatiya Pustak"


# --- Inventory (AC-6) ---------------------------------------------------------

def test_adjustment_requires_reason_and_ledger_balance():
    from services import inventory_service, sale_service

    book_id = _stocked_book(10)
    sale_service.create_sale(
        "2026-06-02", "retail",
        [{"book_id": book_id, "quantity": 3, "unit_price": 25000}], user_id=1)

    with pytest.raises(ValueError):
        inventory_service.add_adjustment(book_id, "2026-06-03", -1, "  ", user_id=1)
    with pytest.raises(ValueError):
        inventory_service.add_adjustment(book_id, "2026-06-03", 0, "reason", user_id=1)

    inventory_service.add_adjustment(book_id, "2026-06-03", -1, "damaged", user_id=1)
    ledger = inventory_service.stock_ledger(book_id)
    assert [e["balance"] for e in ledger] == [10, 7, 6]
    assert inventory_service.low_stock_books() == []  # 6 > threshold 5


# --- Receipt PDF (AC-4) ---------------------------------------------------------

# --- Reports (AC-5, AC-7) -------------------------------------------------------

def test_sale_purchase_statement_and_pnl_figures():
    from services import contact_service, report_service, sale_service

    book_id = _stocked_book(10)  # 10 units @ 100.00 cost
    customer_id = contact_service.add_contact("customer", {"name": "W"})
    sale_service.create_sale(
        "2026-06-02", "retail",
        [{"book_id": book_id, "quantity": 2, "unit_price": 25000}], user_id=1,
        discount=1000)
    sale_service.create_sale(
        "2026-06-03", "wholesale",
        [{"book_id": book_id, "quantity": 3, "unit_price": 20000}], user_id=1,
        customer_id=customer_id)
    cancelled = sale_service.create_sale(
        "2026-06-04", "retail",
        [{"book_id": book_id, "quantity": 1, "unit_price": 25000}], user_id=1)
    sale_service.cancel_sale(cancelled, owner_id=1, reason="test")

    stmt = report_service.sale_purchase_statement("2026-06-01", "2026-06-30")
    assert stmt["purchases"] == {"cnt": 1, "qty": 10, "amount": 100000}
    assert stmt["sales"]["retail"] == {"cnt": 1, "qty": 2, "amount": 49000}
    assert stmt["sales"]["wholesale"] == {"cnt": 1, "qty": 3, "amount": 60000}
    assert stmt["sales_total"]["amount"] == 109000  # cancelled sale excluded
    assert len(stmt["daily"]) == 3  # purchase day + 2 sale days

    pnl = report_service.profit_and_loss("2026-06-01", "2026-06-30")
    assert pnl["revenue"] == 109000
    assert pnl["cogs"] == 5 * 10000  # 5 units sold @ last purchase price 100.00
    assert pnl["gross_profit"] == 59000
    assert pnl["by_type"]["retail"]["profit"] == 49000 - 20000
    assert pnl["by_type"]["wholesale"]["profit"] == 60000 - 30000
    # Per-book profit is pre-discount (whole-bill discounts are not line-attributable).
    assert pnl["top_books"][0]["profit"] == 60000
    assert pnl["never_purchased_codes"] == []


def test_exports_produce_csv_and_excel_bytes():
    import pandas as pd

    from utils import exports

    df = pd.DataFrame([{"Title": "\u0930\u093e\u092e\u093e\u092f\u0923\u092e\u094d",
                        "Qty": 3}])
    csv = exports.df_to_csv_bytes(df)
    assert csv.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM for Excel
    assert "\u0930\u093e\u092e".encode("utf-8") in csv
    xlsx = exports.df_to_excel_bytes(df)
    assert xlsx[:2] == b"PK"  # xlsx zip container


# --- Receipt PDF (AC-4) ---------------------------------------------------------

def test_receipt_pdf_is_generated():
    from services import sale_service
    from utils import receipt_pdf

    book_id = _stocked_book(5)
    sale_id = sale_service.create_sale(
        "2026-06-02", "retail",
        [{"book_id": book_id, "quantity": 1, "unit_price": 25000}], user_id=1)
    pdf = receipt_pdf.build_receipt_pdf(
        sale_service.get_sale(sale_id), sale_service.get_sale_items(sale_id))
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000
