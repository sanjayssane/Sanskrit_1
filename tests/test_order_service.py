"""Tests for online order service."""

import pytest

from db import database


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    path = tmp_path / "shop.db"
    monkeypatch.setattr(database, "DB_PATH", path)
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    conn = database.init_db(path)
    conn.close()
    yield path


def _sample_book(**overrides):
    fields = {
        "title_devanagari": "\u0930\u093e\u092e\u093e\u092f\u0923\u092e\u094d",
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


def _stocked_book(qty=10):
    from services import book_service, contact_service, purchase_service

    book_id = book_service.add_book(_sample_book())
    supplier_id = contact_service.add_contact("supplier", {"name": "S"})
    purchase_service.create_purchase(
        "2026-06-01", supplier_id,
        [{"book_id": book_id, "quantity": qty, "unit_price": 10000}], user_id=1)
    return book_id


def _stock_of(book_id):
    from services import book_service

    return next(b["stock"] for b in book_service.list_active_books()
                if b["id"] == book_id)


def test_create_order_pending():
    from services import order_service

    book_id = _stocked_book(10)
    order_id = order_service.create_order(
        "2026-06-05", "Rama Sharma", "9876543210",
        [{"book_id": book_id, "quantity": 2, "unit_price": 25000}],
        customer_email="rama@example.com",
        notes="Call before pickup",
    )
    order = order_service.get_order(order_id)
    assert order["status"] == "pending"
    assert order["total_amount"] == 50000
    assert order["customer_name"] == "Rama Sharma"
    assert order["customer_email"] == "rama@example.com"
    assert _stock_of(book_id) == 10  # stock not reserved


def test_create_order_insufficient_stock():
    from services import order_service
    from services.sale_service import InsufficientStockError

    book_id = _stocked_book(3)
    with pytest.raises(InsufficientStockError):
        order_service.create_order(
            "2026-06-05", "Guest", "9999999999",
            [{"book_id": book_id, "quantity": 5, "unit_price": 25000}])


def test_create_order_requires_contact_and_items():
    from services import order_service

    book_id = _stocked_book(5)
    with pytest.raises(ValueError, match="name"):
        order_service.create_order(
            "2026-06-05", "  ", "9876543210",
            [{"book_id": book_id, "quantity": 1, "unit_price": 25000}])
    with pytest.raises(ValueError, match="Phone"):
        order_service.create_order(
            "2026-06-05", "Guest", "",
            [{"book_id": book_id, "quantity": 1, "unit_price": 25000}])
    with pytest.raises(ValueError, match="line item"):
        order_service.create_order("2026-06-05", "Guest", "9876543210", [])


def test_complete_order_creates_sale_and_decreases_stock():
    from services import order_service, sale_service

    book_id = _stocked_book(10)
    order_id = order_service.create_order(
        "2026-06-05", "Guest", "9876543210",
        [{"book_id": book_id, "quantity": 3, "unit_price": 25000}])
    sale_id = order_service.complete_order(order_id, user_id=1)
    order = order_service.get_order(order_id)
    assert order["status"] == "completed"
    assert order["sale_id"] == sale_id
    assert order["completed_by"] == 1
    assert _stock_of(book_id) == 7

    sale = sale_service.get_sale(sale_id)
    assert sale["sale_type"] == "retail"
    assert sale["total_amount"] == 75000
    assert "Online order" in sale["notes"]


def test_complete_already_completed_raises():
    from services import order_service

    book_id = _stocked_book(5)
    order_id = order_service.create_order(
        "2026-06-05", "Guest", "9876543210",
        [{"book_id": book_id, "quantity": 1, "unit_price": 25000}])
    order_service.complete_order(order_id, user_id=1)
    with pytest.raises(ValueError, match="pending"):
        order_service.complete_order(order_id, user_id=1)


def test_cancel_pending_order():
    from services import order_service

    book_id = _stocked_book(5)
    order_id = order_service.create_order(
        "2026-06-05", "Guest", "9876543210",
        [{"book_id": book_id, "quantity": 2, "unit_price": 25000}])
    order_service.cancel_order(order_id, user_id=2, reason="customer changed mind")
    order = order_service.get_order(order_id)
    assert order["status"] == "cancelled"
    assert order["cancel_reason"] == "customer changed mind"
    assert order["cancelled_by"] == 2
    assert _stock_of(book_id) == 5


def test_cancel_requires_reason():
    from services import order_service

    book_id = _stocked_book(5)
    order_id = order_service.create_order(
        "2026-06-05", "Guest", "9876543210",
        [{"book_id": book_id, "quantity": 1, "unit_price": 25000}])
    with pytest.raises(ValueError, match="reason"):
        order_service.cancel_order(order_id, user_id=1, reason="  ")


def test_complete_fails_if_stock_ran_out():
    from services import order_service, sale_service
    from services.sale_service import InsufficientStockError

    book_id = _stocked_book(5)
    order_id = order_service.create_order(
        "2026-06-05", "Guest A", "1111111111",
        [{"book_id": book_id, "quantity": 5, "unit_price": 25000}])
    sale_service.create_sale(
        "2026-06-05", "retail",
        [{"book_id": book_id, "quantity": 5, "unit_price": 25000}], user_id=1)
    assert _stock_of(book_id) == 0
    with pytest.raises(InsufficientStockError):
        order_service.complete_order(order_id, user_id=1)
    assert order_service.get_order(order_id)["status"] == "pending"


def test_pending_count():
    from services import order_service

    assert order_service.pending_count() == 0
    book_id = _stocked_book(5)
    order_service.create_order(
        "2026-06-05", "Guest", "9876543210",
        [{"book_id": book_id, "quantity": 1, "unit_price": 25000}])
    assert order_service.pending_count() == 1
