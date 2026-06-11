"""Analytics service tests (AR-NFR-1, AR-NFR-6)."""

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
    from services import book_service

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
    return book_service.add_book(fields)


def _stock_and_sell():
    from services import contact_service, purchase_service, sale_service

    book_id = _sample_book()
    supplier_id = contact_service.add_contact("supplier", {"name": "Chowkhamba"})
    purchase_service.create_purchase(
        "2026-06-01", supplier_id,
        [{"book_id": book_id, "quantity": 20, "unit_price": 10000}],
        user_id=1, invoice_ref="INV-1")
    customer_id = contact_service.add_contact("customer", {"name": "Wholesale Co"})
    sale_service.create_sale(
        "2026-06-02", "retail",
        [{"book_id": book_id, "quantity": 2, "unit_price": 25000}],
        user_id=1, discount=1000)
    sale_service.create_sale(
        "2026-06-03", "wholesale",
        [{"book_id": book_id, "quantity": 3, "unit_price": 20000}],
        user_id=1, customer_id=customer_id)
    return book_id


def test_sales_trend_and_summary_match_reports():
    from services import analytics_service, report_service

    _stock_and_sell()
    start, end = "2026-06-01", "2026-06-30"

    summary = analytics_service.sales_summary(start, end)
    assert summary["revenue"] == 109000
    assert summary["units"] == 5
    assert summary["txn_count"] == 2

    trend = analytics_service.sales_trend(start, end, "daily")
    assert sum(t["revenue"] for t in trend) == 109000

    stmt = report_service.sale_purchase_statement(start, end)
    assert stmt["sales_total"]["amount"] == summary["revenue"]


def test_bestsellers_and_pnl_consistency():
    from services import analytics_service, report_service

    _stock_and_sell()
    start, end = "2026-06-01", "2026-06-30"

    best = analytics_service.bestsellers(start, end, 10)
    assert len(best) == 1
    assert best[0]["qty"] == 5

    pnl_report = report_service.profit_and_loss(start, end)
    pnl_analytics = analytics_service.profit_and_loss(start, end)
    assert pnl_analytics["revenue"] == pnl_report["revenue"]
    assert pnl_analytics["cogs"] == pnl_report["cogs"]
    assert pnl_analytics["gross_profit"] == pnl_report["gross_profit"]


def test_slow_movers_and_dead_stock():
    from services import analytics_service, sale_service

    book_id = _stock_and_sell()
    # One more book with stock but no sales
    idle_id = _sample_book(title_roman="Idle Book", title_devanagari="\u0905\u0928\u094d\u092f")
    from services import contact_service, purchase_service
    supplier_id = contact_service.add_contact("supplier", {"name": "Other Pub"})
    purchase_service.create_purchase(
        "2026-06-01", supplier_id,
        [{"book_id": idle_id, "quantity": 5, "unit_price": 5000}],
        user_id=1)

    slow = analytics_service.slow_movers(90)
    codes = {s["code"] for s in slow}
    assert any("BK-" in c for c in codes)

    dead = analytics_service.dead_stock(1)  # 1 day — idle book qualifies
    dead_codes = {d["code"] for d in dead}
    assert len(dead_codes) >= 1


def test_supplier_ranking_and_customer_ranking():
    from services import analytics_service

    _stock_and_sell()
    suppliers = analytics_service.supplier_ranking("2026-06-01", "2026-06-30")
    assert suppliers[0]["supplier_name"] == "Chowkhamba"
    assert suppliers[0]["total_qty"] == 20

    customers = analytics_service.wholesale_customer_ranking("2026-06-01", "2026-06-30")
    assert customers[0]["customer_name"] == "Wholesale Co"
    assert customers[0]["revenue"] == 60000


def test_employee_activity_and_settings():
    from services import analytics_service

    _stock_and_sell()
    staff = analytics_service.employee_activity("2026-06-01", "2026-06-30")
    owner_row = next(s for s in staff if s["username"] == "owner")
    assert owner_row["sales_count"] == 2
    assert owner_row["purchase_count"] == 1

    analytics_service.set_setting("slow_mover_days", "60")
    assert analytics_service.get_setting("slow_mover_days") == "60"


def test_dashboard_kpis_and_alerts():
    from services import analytics_service

    _stock_and_sell()
    kpis = analytics_service.dashboard_kpis("2026-06-02", "2026-06-03")
    assert kpis["revenue"] == 109000
    assert kpis["txn_count"] == 2

    alerts = analytics_service.active_alerts()
    assert isinstance(alerts, list)


def test_inventory_movement_and_turnover():
    from services import analytics_service

    _stock_and_sell()
    move = analytics_service.stock_movement_summary("2026-06-01", "2026-06-30")
    assert move["units_in"] == 20
    assert move["units_out"] == 5
    assert move["net_change"] == 15

    turn = analytics_service.inventory_turnover("2026-06-01", "2026-06-30")
    assert turn["cogs"] == 50000
    assert turn["turnover_ratio"] is not None


def test_loss_making_sales_detection():
    from services import contact_service, purchase_service, sale_service
    from services import analytics_service

    book_id = _sample_book(retail_price=8000, wholesale_price=8000)
    supplier_id = contact_service.add_contact("supplier", {"name": "S"})
    purchase_service.create_purchase(
        "2026-06-01", supplier_id,
        [{"book_id": book_id, "quantity": 5, "unit_price": 10000}],
        user_id=1)
    sale_service.create_sale(
        "2026-06-02", "retail",
        [{"book_id": book_id, "quantity": 1, "unit_price": 8000}],
        user_id=1)
    loss = analytics_service.loss_making_sales("2026-06-01", "2026-06-30")
    assert loss["line_count"] == 1
    assert loss["total_loss"] == 2000
