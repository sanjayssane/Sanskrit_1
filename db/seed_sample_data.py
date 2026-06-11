"""Optional sample data for demos and manual UI testing.

Never auto-run. Usage (from the project root, on an initialized database):

    python -m db.seed_sample_data

Refuses to run if the catalog already has books.
"""

from __future__ import annotations

from db import database

SAMPLE_BOOKS = [
    # (title_devanagari, title_roman, author_roman, publisher, category, language,
    #  retail ₹, wholesale ₹)
    ("\u0930\u093e\u092e\u093e\u092f\u0923\u092e\u094d", "Ramayanam",
     "Valmiki", "Chowkhamba", "Kavya", "Sanskrit", 450.00, 380.00),
    ("\u092d\u0917\u0935\u0926\u094d\u0917\u0940\u0924\u093e", "Bhagavad Gita",
     "Vyasa", "Gita Press", "Darshana", "Sanskrit-Hindi", 120.00, 95.00),
    ("\u0905\u0937\u094d\u091f\u093e\u0927\u094d\u092f\u093e\u092f\u0940", "Ashtadhyayi",
     "Panini", "Chowkhamba", "Vyakarana", "Sanskrit", 650.00, 540.00),
    ("\u0905\u092d\u093f\u091c\u094d\u091e\u093e\u0928\u0936\u093e\u0915\u0941\u0928\u094d\u0924\u0932\u092e\u094d",
     "Abhijnanashakuntalam", "Kalidasa", "Motilal Banarsidass", "Kavya",
     "Sanskrit-English", 320.00, 270.00),
    ("\u090b\u0917\u094d\u0935\u0947\u0926\u0903", "Rigveda",
     None, "Chowkhamba", "Veda", "Sanskrit", 1200.00, 1000.00),
]


def seed() -> None:
    from services import book_service, contact_service, purchase_service, sale_service
    from utils.money import to_paise

    conn = database.init_db()
    try:
        if conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]:
            raise SystemExit("Catalog is not empty — refusing to seed sample data.")
        owner_id = conn.execute(
            "SELECT id FROM users WHERE role = 'owner' ORDER BY id LIMIT 1"
        ).fetchone()[0]
    finally:
        conn.close()

    book_ids = []
    for dev, roman, author, publisher, category, language, retail, wholesale in SAMPLE_BOOKS:
        book_ids.append(book_service.add_book({
            "title_devanagari": dev, "title_roman": roman,
            "author_roman": author, "author_devanagari": None,
            "publisher": publisher, "category": category, "language": language,
            "isbn": None, "retail_price": to_paise(retail),
            "wholesale_price": to_paise(wholesale), "low_stock_threshold": 5,
        }))

    supplier_id = contact_service.add_contact("supplier", {
        "name": "Chowkhamba Sanskrit Series", "contact_person": "Ramesh Gupta",
        "phone": "0542-2335020", "address": "Varanasi", "notes": None})
    contact_service.add_contact("supplier", {
        "name": "Gita Press", "contact_person": None, "phone": "0551-2334721",
        "address": "Gorakhpur", "notes": None})
    customer_id = contact_service.add_contact("customer", {
        "name": "Bharatiya Pustak Bhandar", "contact_person": "Suresh Shah",
        "phone": "011-23258801", "address": "Delhi", "notes": "Monthly bulk buyer"})

    purchase_service.create_purchase(
        "2026-06-01", supplier_id,
        [{"book_id": book_ids[0], "quantity": 20, "unit_price": to_paise(300.00)},
         {"book_id": book_ids[1], "quantity": 50, "unit_price": to_paise(70.00)},
         {"book_id": book_ids[2], "quantity": 10, "unit_price": to_paise(450.00)},
         {"book_id": book_ids[3], "quantity": 15, "unit_price": to_paise(220.00)},
         {"book_id": book_ids[4], "quantity": 5, "unit_price": to_paise(850.00)}],
        user_id=owner_id, invoice_ref="CH-2026-101")

    sale_service.create_sale(
        "2026-06-05", "retail",
        [{"book_id": book_ids[1], "quantity": 2, "unit_price": to_paise(120.00)},
         {"book_id": book_ids[0], "quantity": 1, "unit_price": to_paise(450.00)}],
        user_id=owner_id, discount=to_paise(10.00))
    sale_service.create_sale(
        "2026-06-07", "wholesale",
        [{"book_id": book_ids[1], "quantity": 20, "unit_price": to_paise(95.00)},
         {"book_id": book_ids[3], "quantity": 5, "unit_price": to_paise(270.00)}],
        user_id=owner_id, customer_id=customer_id)

    print("Sample data seeded: 5 books, 2 suppliers, 1 customer,"
          " 1 purchase, 2 sales.")


if __name__ == "__main__":
    seed()
