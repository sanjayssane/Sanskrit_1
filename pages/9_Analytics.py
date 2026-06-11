"""Advanced analytics: sales, purchases, inventory, profit, customers, staff (AR-UI)."""

import datetime as dt

import pandas as pd
import streamlit as st

from services import analytics_service, auth_service
from services.analytics_service import AnalyticsFilters
from utils import analytics_ui, exports
from utils.money import fmt_inr

user = auth_service.require_login()
is_owner = user["role"] == "owner"

st.title("Analytics")
st.caption(
    "Owner view — full financial and staff analytics."
    if is_owner
    else "Employee view — operational sales and inventory insights (no profit/COGS)."
)

preset, start, end = analytics_ui.render_period_selector("an_main")
filters = analytics_ui.render_filters_bar(is_owner, "an_main")
granularity = st.radio("Chart granularity", ["daily", "weekly", "monthly"],
                       horizontal=True, key="an_gran")

owner_tabs = ["Sales", "Purchases", "Inventory", "Profit", "Customers", "Staff", "Insights"]
employee_tabs = ["Sales", "Purchases", "Inventory", "Customers", "Insights"]
tabs = st.tabs(owner_tabs if is_owner else employee_tabs)

tab_sales = tabs[0]
tab_purchases = tabs[1]
tab_inventory = tabs[2]
tab_idx = 3

# --- Sales --------------------------------------------------------------------

with tab_sales:
    summary = analytics_service.sales_summary(start, end, filters)
    kpis = analytics_service.dashboard_kpis(start, end, filters)
    c1, c2, c3, c4 = st.columns(4)
    analytics_ui.metric_delta("Revenue", fmt_inr(summary["revenue"]), kpis["revenue_change_pct"])
    analytics_ui.metric_delta("Units sold", str(summary["units"]), kpis["units_change_pct"])
    analytics_ui.metric_delta("Avg ticket", fmt_inr(summary["avg_ticket"]),
                              kpis["avg_ticket_change_pct"])
    analytics_ui.metric_delta("Transactions", str(summary["txn_count"]), kpis["txn_change_pct"])

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Revenue over time")
        trend = analytics_service.sales_trend(start, end, granularity, filters)
        analytics_ui.trend_line_chart(trend, "revenue", "Revenue (paise)")
    with c2:
        st.subheader("Units sold over time")
        analytics_ui.trend_line_chart(trend, "units", "Units")

    st.subheader("Retail vs wholesale")
    by_type = analytics_service.sales_by_type(start, end, filters)
    type_df = pd.DataFrame([{
        "Type": t.capitalize(),
        "Revenue": fmt_inr(v["revenue"]),
        "Units": v["units"],
        "Transactions": v["txn_count"],
        "Avg ticket": fmt_inr(v["avg_ticket"]),
    } for t, v in by_type.items()])
    st.dataframe(type_df, hide_index=True, width="stretch")
    split_df = pd.DataFrame([
        {"Type": "Retail", "Revenue": by_type["retail"]["revenue"]},
        {"Type": "Wholesale", "Revenue": by_type["wholesale"]["revenue"]},
    ]).set_index("Type")
    st.bar_chart(split_df, width="stretch")

    st.subheader("Bestsellers")
    best = analytics_service.bestsellers(start, end, 50, filters)
    if best:
        bdf = pd.DataFrame([{
            "Code": b["code"],
            "Title": analytics_ui.book_title_row(b),
            "Category": b["category"],
            "Qty": b["qty"],
            "Revenue": fmt_inr(b["line_revenue"]),
            "% of revenue": f"{b['pct_of_revenue']:.1f}%",
        } for b in best])
        st.dataframe(bdf, hide_index=True, width="stretch")
        exports.download_buttons(bdf, f"bestsellers-{start}-{end}", "an_best")
        sel = st.selectbox("Drill-down book", ["—"] + [b["code"] for b in best], key="an_best_sel")
        if sel != "—":
            bid = next(b["book_id"] for b in best if b["code"] == sel)
            with st.expander(f"Book detail: {sel}", expanded=True):
                analytics_ui.render_book_drilldown(bid, start, end, is_owner)
    else:
        st.info("No sales in the selected range.")

    settings = analytics_service.get_settings()
    slow_days = int(settings.get("slow_mover_days", "90"))
    st.subheader(f"Slow movers (no sales in {slow_days} days, stock > 0)")
    slow = analytics_service.slow_movers(slow_days, filters)
    if slow:
        sdf = pd.DataFrame([{
            "Code": s["code"], "Title": analytics_ui.book_title_row(s),
            "Stock": s["stock"], "Category": s.get("category") or "",
        } for s in slow])
        st.dataframe(sdf, hide_index=True, width="stretch")
        exports.download_buttons(sdf, f"slow-movers-{end}", "an_slow")
    else:
        st.success("No slow movers for the current threshold.")

    if is_owner:
        st.subheader("Discount analysis")
        disc = analytics_service.discount_analysis(start, end, filters)
        c1, c2 = st.columns(2)
        c1.metric("Total discounts", fmt_inr(disc["total_discount"]))
        c2.metric("Discount % of gross", f"{disc['discount_pct']:.1f}%")
        if disc["top_sales"]:
            ddf = pd.DataFrame([{
                "Sale ID": r["id"], "Date": r["sale_date"], "Type": r["sale_type"],
                "Customer": r["customer_name"], "Discount": fmt_inr(r["discount"]),
                "Total": fmt_inr(r["total_amount"]),
            } for r in disc["top_sales"]])
            st.dataframe(ddf, hide_index=True, width="stretch")
            exports.download_buttons(ddf, f"top-discounts-{start}-{end}", "an_disc")

    st.subheader("Payment methods")
    pay = analytics_service.payment_method_breakdown(start, end, filters)
    if pay:
        pdf = pd.DataFrame([{
            "Method": p["payment_method"], "Transactions": p["txn_count"],
            "Revenue": fmt_inr(p["revenue"]),
        } for p in pay])
        st.dataframe(pdf, hide_index=True, width="stretch")
        exports.download_buttons(pdf, f"payment-methods-{start}-{end}", "an_pay")
        st.bar_chart(pd.DataFrame(pay).set_index("payment_method")[["revenue"]], width="stretch")

    st.subheader("Sales by weekday")
    dow = analytics_service.sales_by_weekday(start, end, filters)
    if dow:
        analytics_ui.bar_chart(dow, "weekday", "revenue", "Avg daily revenue (paise)")

    hour = analytics_service.sales_by_hour(start, end, filters)
    if hour:
        st.subheader("Sales by hour of day")
        analytics_ui.bar_chart(
            [{"hour": f"{h['hour']:02d}:00", "revenue": h["revenue"]} for h in hour],
            "hour", "revenue", "Revenue")

    if is_owner:
        override = analytics_service.price_override_analysis(start, end, filters)
        st.caption(
            f"Price overrides: {override['override_line_count']} lines, "
            f"{override['override_units']} units, "
            f"net delta {fmt_inr(override['total_delta'])}"
        )

    cat_perf = analytics_service.dimension_performance(start, end, "category", filters)
    if cat_perf:
        st.subheader("Category performance")
        cdf = pd.DataFrame([{
            "Category": c["label"], "Units": c["qty"], "Revenue": fmt_inr(c["revenue"]),
        } for c in cat_perf])
        st.dataframe(cdf, hide_index=True, width="stretch")
        exports.download_buttons(cdf, f"category-{start}-{end}", "an_cat")

# --- Purchases ----------------------------------------------------------------

with tab_purchases:
    ps = analytics_service.purchase_summary(start, end, filters)
    c1, c2, c3 = st.columns(3)
    c1.metric("Spend", fmt_inr(ps["spend"]))
    c2.metric("Units purchased", ps["units"])
    c3.metric("Transactions", ps["txn_count"])

    ptrend = analytics_service.purchase_trend(start, end, granularity, filters)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Purchase spend over time")
        analytics_ui.trend_line_chart(ptrend, "spend", "Spend (paise)")
    with c2:
        st.subheader("Units purchased over time")
        analytics_ui.trend_line_chart(ptrend, "units", "Units")

    st.subheader("Supplier ranking")
    suppliers = analytics_service.supplier_ranking(start, end, filters)
    if suppliers:
        sup_df = pd.DataFrame([{
            "Supplier": s["supplier_name"], "Purchases": s["purchase_count"],
            "Qty": s["total_qty"], "Spend": fmt_inr(s["total_spend"]),
            "Avg unit cost": fmt_inr(s["avg_unit_cost"]),
            "Last purchase": s["last_purchase_date"],
        } for s in suppliers])
        st.dataframe(sup_df, hide_index=True, width="stretch")
        exports.download_buttons(sup_df, f"suppliers-{start}-{end}", "an_sup")
        if is_owner:
            conc = analytics_service.supplier_concentration(start, end, filters)
            st.caption(f"Top 3 suppliers: {conc['top3_pct']:.1f}% of spend")
    else:
        st.info("No purchases in the selected range.")

    st.subheader("Top purchased titles")
    top_p = analytics_service.top_purchased_titles(start, end, 20, filters)
    if top_p:
        tdf = pd.DataFrame([{
            "Code": t["code"], "Title": analytics_ui.book_title_row(t),
            "Qty": t["qty"], "Spend": fmt_inr(t["spend"]),
        } for t in top_p])
        st.dataframe(tdf, hide_index=True, width="stretch")
        exports.download_buttons(tdf, f"top-purchases-{start}-{end}", "an_tp")

# --- Inventory ----------------------------------------------------------------

with tab_inventory:
    inv = analytics_service.inventory_valuation(filters.include_inactive_books)
    c1, c2, c3 = st.columns(3)
    c1.metric("Titles in stock", inv["total_titles"])
    c2.metric("Total units", inv["total_units"])
    if is_owner:
        c3.metric("Stock value", fmt_inr(inv["total_value"]))
    else:
        c3.metric("Stock value", "—")

    move = analytics_service.stock_movement_summary(start, end)
    st.subheader("Stock movement (period)")
    mdf = pd.DataFrame([{
        "Units in (purchases)": move["units_in"],
        "Units out (sales)": move["units_out"],
        "Net adjustments": move["net_adjustments"],
        "Net change": move["net_change"],
    }])
    st.dataframe(mdf, hide_index=True, width="stretch")

    if is_owner:
        turn = analytics_service.inventory_turnover(start, end)
        st.subheader("Inventory turnover")
        st.caption(f"Formula: COGS ÷ average inventory value. Method: {turn['method']}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Turnover ratio",
                  f"{turn['turnover_ratio']:.2f}" if turn["turnover_ratio"] else "N/A")
        c2.metric("COGS", fmt_inr(turn["cogs"]))
        c3.metric("Avg inventory", fmt_inr(turn["average_inventory_value"]))
        c4.metric("Closing value", fmt_inr(turn["closing_value"]))

    thresh = int(analytics_service.get_setting("days_of_supply_threshold", "14"))
    st.subheader(f"Days of supply (flag < {thresh} days)")
    dos = analytics_service.days_of_supply(thresh)
    low_dos = [d for d in dos if d.get("below_threshold")]
    if low_dos:
        ddf = pd.DataFrame([{
            "Code": d["code"], "Title": analytics_ui.book_title_row(d),
            "Stock": d["stock"], "Sold (30d)": d["sold_30d"],
            "Days of supply": f"{d['days_of_supply']:.1f}" if d["days_of_supply"] else "∞",
        } for d in low_dos[:50]])
        st.dataframe(ddf, hide_index=True, width="stretch")
        exports.download_buttons(ddf, f"days-of-supply-{end}", "an_dos")
    else:
        st.success("No titles below the days-of-supply threshold.")

    dead_days = int(analytics_service.get_setting("dead_stock_days", "180"))
    st.subheader(f"Dead stock ({dead_days}+ days without sales)")
    dead = analytics_service.dead_stock(dead_days, filters)
    if dead:
        dead_df = pd.DataFrame([{
            "Code": d["code"], "Title": analytics_ui.book_title_row(d),
            "Stock": d["stock"],
            "Tied-up capital": fmt_inr(d.get("tied_up_capital", 0)) if is_owner else "—",
        } for d in dead])
        st.dataframe(dead_df, hide_index=True, width="stretch")
        exports.download_buttons(dead_df, f"dead-stock-{end}", "an_dead")
    else:
        st.success("No dead stock titles.")

    st.subheader("Out of stock (sold in period, now zero)")
    oos = analytics_service.out_of_stock_with_recent_sales(start, end)
    if oos:
        odf = pd.DataFrame([{
            "Code": o["code"], "Title": analytics_ui.book_title_row(o),
            "Sold in period": o["sold_in_period"],
        } for o in oos])
        st.dataframe(odf, hide_index=True, width="stretch")
        exports.download_buttons(odf, f"out-of-stock-{start}-{end}", "an_oos")
    else:
        st.info("None.")

    abc = analytics_service.abc_classification()
    if abc and is_owner:
        st.subheader("ABC classification (12 months)")
        adf = pd.DataFrame([{
            "Class": a["abc_class"], "Code": a["code"], "Title": analytics_ui.book_title_row(a),
            "Revenue": fmt_inr(a["line_revenue"]), "Cumulative %": f"{a['cumulative_pct']:.1f}",
        } for a in abc[:30]])
        st.dataframe(adf, hide_index=True, width="stretch")
        exports.download_buttons(adf, f"abc-{end}", "an_abc")

    reorder = analytics_service.reorder_suggestions()
    if reorder:
        st.subheader("Reorder suggestions")
        rdf = pd.DataFrame([{
            "Code": r["code"], "Title": analytics_ui.book_title_row(r),
            "Stock": r["stock"], "Threshold": r["threshold"],
            "Suggested qty": r["suggested_qty"],
        } for r in reorder])
        st.dataframe(rdf, hide_index=True, width="stretch")
        exports.download_buttons(rdf, f"reorder-{end}", "an_reorder")

    if is_owner:
        adj = analytics_service.adjustment_analytics(start, end)
        if adj:
            st.subheader("Stock adjustments")
            adj_df = pd.DataFrame(adj)
            st.dataframe(adj_df, hide_index=True, width="stretch")
            exports.download_buttons(adj_df, f"adjustments-{start}-{end}", "an_adj")

# --- Profit (owner) -----------------------------------------------------------

if is_owner:
    with tabs[tab_idx]:
        tab_idx += 1
        cogs_method = analytics_service.get_setting("cogs_method", "last_purchase")
        st.caption(f"COGS method: {analytics_service.cogs_method_label(cogs_method)}")

        pnl = analytics_service.profit_and_loss(start, end, cogs_method, filters)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Revenue", fmt_inr(pnl["revenue"]))
        c2.metric("COGS", fmt_inr(pnl["cogs"]))
        c3.metric("Gross profit", fmt_inr(pnl["gross_profit"]))
        c4.metric("Margin", f"{pnl['margin_pct']:.1f}%")

        if pnl["never_purchased_codes"]:
            st.warning("Sold but never purchased: " + ", ".join(pnl["never_purchased_codes"]))

        ptrend = analytics_service.profit_trend(start, end, granularity, cogs_method, filters)
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Gross profit trend")
            analytics_ui.trend_line_chart(ptrend, "gross_profit", "Gross profit (paise)")
        with c2:
            st.subheader("Margin % trend")
            if ptrend:
                mdf = pd.DataFrame(ptrend).set_index("bucket")[["margin_pct"]]
                st.line_chart(mdf, width="stretch")

        st.subheader("Profit by sale type")
        ptype_df = pd.DataFrame([{
            "Type": t.capitalize(),
            "Revenue": fmt_inr(v["revenue"]),
            "COGS": fmt_inr(v["cogs"]),
            "Profit": fmt_inr(v["profit"]),
            "Margin %": f"{v['margin_pct']:.1f}",
        } for t, v in pnl["by_type"].items()])
        st.dataframe(ptype_df, hide_index=True, width="stretch")
        exports.download_buttons(ptype_df, f"profit-by-type-{start}-{end}", "an_ptype")

        st.subheader("Profit by book")
        if pnl["by_book"]:
            pbdf = pd.DataFrame([{
                "Code": b["code"], "Title": analytics_ui.book_title_row(b),
                "Qty": b["qty"], "Revenue": fmt_inr(b["revenue"]),
                "COGS": fmt_inr(b["cogs"]), "Profit": fmt_inr(b["profit"]),
                "Margin %": f"{b['margin_pct']:.1f}",
            } for b in pnl["by_book"]])
            st.dataframe(pbdf, hide_index=True, width="stretch")
            exports.download_buttons(pbdf, f"profit-by-book-{start}-{end}", "an_pbook")

        st.subheader("Loss-making line items")
        loss = analytics_service.loss_making_sales(start, end, filters)
        c1, c2, c3 = st.columns(3)
        c1.metric("Lines below cost", loss["line_count"])
        c2.metric("Units", loss["units"])
        c3.metric("Total loss", fmt_inr(loss["total_loss"]))
        if loss["lines"]:
            ldf = pd.DataFrame([{
                "Date": ln["sale_date"], "Code": ln["code"], "Title": ln["title_roman"],
                "Qty": ln["quantity"], "Sale price": fmt_inr(ln["unit_price"]),
                "Cost": fmt_inr(ln["last_purchase_price"]),
            } for ln in loss["lines"]])
            st.dataframe(ldf, hide_index=True, width="stretch")
            exports.download_buttons(ldf, f"loss-making-{start}-{end}", "an_loss")

        for dim, label in (("category", "Category"), ("publisher", "Publisher")):
            pdim = analytics_service.profit_by_dimension(start, end, dim, cogs_method, filters)
            if pdim:
                st.subheader(f"Profit by {label.lower()}")
                ddf = pd.DataFrame([{
                    label: d["label"], "Revenue": fmt_inr(d["revenue"]),
                    "Profit": fmt_inr(d["profit"]), "Margin %": f"{d['margin_pct']:.1f}",
                } for d in pdim])
                st.dataframe(ddf, hide_index=True, width="stretch")
                exports.download_buttons(ddf, f"profit-{dim}-{start}-{end}", f"an_p{dim}")

        ps_ratio = analytics_service.purchase_to_sales_ratio_trend(start, end, granularity)
        if ps_ratio:
            st.subheader("Purchase-to-sales ratio")
            rdf = pd.DataFrame(ps_ratio)
            st.dataframe(rdf.assign(
                purchases=rdf["purchases"].apply(fmt_inr),
                sales=rdf["sales"].apply(fmt_inr),
            ), hide_index=True, width="stretch")

# --- Customers ----------------------------------------------------------------

cust_tab = tabs[tab_idx if is_owner else 3]
with cust_tab:
    tab_idx += 1 if is_owner else 0
    st.subheader("Wholesale customer ranking")
    ranking = analytics_service.wholesale_customer_ranking(start, end, filters)
    if ranking:
        rdf = pd.DataFrame([{
            "Customer": r["customer_name"], "Orders": r["txn_count"],
            "Revenue": fmt_inr(r["revenue"]), "Units": r["units"],
            "Avg order": fmt_inr(r["avg_order_value"]),
            "Last order": r["last_order_date"],
        } for r in ranking])
        st.dataframe(rdf, hide_index=True, width="stretch")
        exports.download_buttons(rdf, f"customers-{start}-{end}", "an_cust")
        conc = analytics_service.customer_concentration(start, end)
        st.caption(f"Top 5 customers: {conc['top5_pct']:.1f}% of wholesale revenue")
        sel_c = st.selectbox("Customer drill-down", ["—"] + [r["customer_name"] for r in ranking],
                             key="an_cust_sel")
        if sel_c != "—":
            cid = next(r["customer_id"] for r in ranking if r["customer_name"] == sel_c)
            books = analytics_service.customer_top_books(cid, start, end)
            if books:
                cbdf = pd.DataFrame([{
                    "Code": b["code"], "Title": analytics_ui.book_title_row(b),
                    "Qty": b["qty"], "Revenue": fmt_inr(b["revenue"]),
                } for b in books])
                st.dataframe(cbdf, hide_index=True, width="stretch")
    else:
        st.info("No wholesale sales in the selected range.")

    freq = analytics_service.customer_frequency(start, end)
    if freq:
        st.subheader("Order frequency (repeat customers)")
        fdf = pd.DataFrame([{
            "Customer": f["name"], "Orders": f["order_count"],
            "Avg days between": f"{f['avg_days_between_orders']:.1f}",
        } for f in freq])
        st.dataframe(fdf, hide_index=True, width="stretch")

    inactive = analytics_service.inactive_customers(90)
    if inactive:
        st.subheader("Inactive wholesale customers (90+ days)")
        idf = pd.DataFrame(inactive)
        st.dataframe(idf, hide_index=True, width="stretch")

    retail = analytics_service.retail_aggregate(start, end)
    st.subheader("Retail (walk-in) aggregate")
    st.caption(f"{retail['txn_count']} transactions, {fmt_inr(retail['revenue'])} revenue")

# --- Staff (owner) ------------------------------------------------------------

if is_owner:
    with tabs[tab_idx]:
        tab_idx += 1
        st.subheader("Employee activity")
        staff = analytics_service.employee_activity(start, end)
        if staff:
            sdf = pd.DataFrame([{
                "Name": s["full_name"], "Sales": s["sales_count"],
                "Purchases": s["purchase_count"],
                "Sales revenue": fmt_inr(s["sales_revenue"]),
                "Retail avg": fmt_inr(s["retail_avg_sale"]),
                "Wholesale avg": fmt_inr(s["wholesale_avg_sale"]),
                "Discounts": fmt_inr(s["discount_total"]),
                "Cancel rate %": f"{s['cancellation_rate']:.1f}",
            } for s in staff])
            st.dataframe(sdf, hide_index=True, width="stretch")
            exports.download_buttons(sdf, f"staff-{start}-{end}", "an_staff")
        timeline = analytics_service.employee_daily_timeline(start, end)
        if timeline["sales"]:
            st.subheader("Daily sales by user")
            tdf = pd.DataFrame(timeline["sales"])
            pivot = tdf.pivot_table(index="day", columns="created_by", values="cnt",
                                    aggfunc="sum", fill_value=0)
            st.dataframe(pivot, width="stretch")

# --- Insights -----------------------------------------------------------------

insights_tab = tabs[-1]
with insights_tab:
    st.subheader("Active alerts")
    analytics_ui.render_alerts()

    if is_owner:
        st.subheader("Analytics settings")
        settings = analytics_service.get_settings()
        with st.form("an_settings"):
            c1, c2 = st.columns(2)
            fiscal = c1.number_input("Fiscal year start month (1–12)",
                                     min_value=1, max_value=12,
                                     value=int(settings["fiscal_year_start_month"]))
            dead_d = c2.number_input("Dead stock days",
                                     value=int(settings["dead_stock_days"]))
            slow_d = c1.number_input("Slow mover days",
                                       value=int(settings["slow_mover_days"]))
            dos_t = c2.number_input("Days-of-supply alert threshold",
                                    value=int(settings["days_of_supply_threshold"]))
            cap_alert = c1.number_input(
                "Dead stock capital alert (₹)",
                value=int(settings["dead_stock_capital_alert_paise"]) / 100)
            margin_drop = c2.number_input(
                "Margin drop alert (points)",
                value=int(settings["margin_drop_alert_points"]))
            cogs = st.selectbox(
                "COGS method",
                ["last_purchase", "weighted_average"],
                index=0 if settings["cogs_method"] == "last_purchase" else 1,
            )
            if st.form_submit_button("Save settings"):
                from utils.money import to_paise

                analytics_service.set_setting("fiscal_year_start_month", str(fiscal))
                analytics_service.set_setting("dead_stock_days", str(dead_d))
                analytics_service.set_setting("slow_mover_days", str(slow_d))
                analytics_service.set_setting("days_of_supply_threshold", str(dos_t))
                analytics_service.set_setting("dead_stock_capital_alert_paise",
                                              str(to_paise(cap_alert)))
                analytics_service.set_setting("margin_drop_alert_points", str(margin_drop))
                analytics_service.set_setting("cogs_method", cogs)
                st.success("Settings saved.")
                st.rerun()

st.caption(f"Data as of {dt.datetime.now().strftime('%Y-%m-%d %H:%M')} · Period {start} to {end}")
