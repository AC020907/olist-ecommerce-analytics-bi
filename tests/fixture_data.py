"""A tiny, hand-checkable Olist dataset that exercises every business rule the model relies on.

Orders (all 2017):
  oA  delivered on time, 2 items (R$100 + R$50) and 2 payments (credit + voucher) -> fan-out trap
  oB  delivered late, same person as oA (repeat customer, moved RJ), 2 reviews (1 and 3)
  oC  canceled, R$200 item, yet has delivery dates                         -> excluded from net and late rate
  oD  delivered, but customer date < carrier date (impossible)              -> no delivery KPIs
  oE  unavailable, no items                                                 -> excluded from net
  oF  delivered at 18:00 ON the promised date                              -> on time (calendar-date rule)
Expected net revenue = 100 + 50 + 80 + 40 + 60 = R$330.00 over 4 valid orders (oA, oB, oD, oF).
Late rate = 1 late (oB) / 3 delivered with valid dates (oA, oB, oF) = 33.33%.
"""
from __future__ import annotations

import csv
from pathlib import Path


def _id(tag: str) -> str:
    return tag.ljust(32, "0")


C1, C2, C3, C4, C5, C6 = (_id(f"c{i}") for i in range(1, 7))
U1, U2, U3, U4, U5 = (_id(f"u{i}") for i in range(1, 6))
OA, OB, OC, OD, OE, OF = (_id(f"o{x}") for x in "abcdef")
P1, P2, P3 = (_id(f"p{i}") for i in range(1, 4))
S1, S2 = _id("s1"), _id("s2")

EXPECTED = {
    "orders_total": 6,
    "valid_orders": 4,
    "customers": 5,
    "gross_revenue": 530.00,
    "net_revenue": 330.00,
    "aov": 82.50,
    "net_freight": 33.00,
    "late_rate_pct": 33.33,
    "repeat_customers": 1,
}

TABLES: dict[str, tuple[list[str], list[list[str]]]] = {
    "olist_customers_dataset.csv": (
        ["customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"],
        [
            [C1, U1, "01001", "sao paulo", "SP"],
            [C2, U1, "20000", "rio de janeiro", "RJ"],
            [C3, U2, "20000", "rio de janeiro", "RJ"],
            [C4, U3, "99999", "porto alegre", "RS"],  # ZIP absent from geolocation
            [C5, U4, "01001", "sao paulo", "SP"],
            [C6, U5, "01001", "sao paulo", "SP"],
        ],
    ),
    "olist_products_dataset.csv": (
        ["product_id", "product_category_name", "product_name_lenght", "product_description_lenght",
         "product_photos_qty", "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"],
        [
            [P1, "beleza_saude", "40", "300", "1", "500", "20", "10", "15"],
            [P2, "", "", "", "", "", "", "", ""],                      # missing category
            [P3, "categoria_sem_traducao", "30", "200", "2", "800", "30", "10", "20"],  # untranslated
        ],
    ),
    "olist_sellers_dataset.csv": (
        ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
        [[S1, "01001", "sao paulo", "SP"], [S2, "20000", "rio de janeiro", "RJ"]],
    ),
    "product_category_name_translation.csv": (
        ["product_category_name", "product_category_name_english"],
        [["beleza_saude", "health_beauty"]],
    ),
    "olist_geolocation_dataset.csv": (
        ["geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng", "geolocation_city", "geolocation_state"],
        [
            ["01001", "-23.5500000", "-46.6300000", "sao paulo", "SP"],
            ["01001", "-23.5600000", "-46.6400000", "sao paulo ", "SP"],  # trailing space
            ["01001", "-23.5700000", "-46.6500000", "sao paulo", "SP"],
            ["20000", "-22.9000000", "-43.2000000", "rio de janeiro", "RJ"],
        ],
    ),
    "olist_orders_dataset.csv": (
        ["order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_approved_at",
         "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"],
        [
            [OA, C1, "delivered", "2017-03-10 10:00:00", "2017-03-10 11:00:00", "2017-03-12 09:00:00", "2017-03-15 10:00:00", "2017-03-20 00:00:00"],
            [OB, C2, "delivered", "2017-04-01 10:00:00", "2017-04-01 11:00:00", "2017-04-03 09:00:00", "2017-04-25 10:00:00", "2017-04-15 00:00:00"],
            [OC, C3, "canceled", "2017-04-05 10:00:00", "2017-04-05 11:00:00", "2017-04-07 09:00:00", "2017-04-10 10:00:00", "2017-04-25 00:00:00"],
            [OD, C4, "delivered", "2017-05-01 10:00:00", "2017-05-01 11:00:00", "2017-05-10 09:00:00", "2017-05-08 10:00:00", "2017-05-20 00:00:00"],
            [OE, C5, "unavailable", "2017-05-02 10:00:00", "2017-05-02 11:00:00", "", "", "2017-05-25 00:00:00"],
            [OF, C6, "delivered", "2017-06-01 10:00:00", "2017-06-01 11:00:00", "2017-06-03 09:00:00", "2017-06-12 18:00:00", "2017-06-12 00:00:00"],
        ],
    ),
    "olist_order_items_dataset.csv": (
        ["order_id", "order_item_id", "product_id", "seller_id", "shipping_limit_date", "price", "freight_value"],
        [
            [OA, "1", P1, S1, "2017-03-12 00:00:00", "100.00", "10.00"],
            [OA, "2", P2, S2, "2017-03-12 00:00:00", "50.00", "5.00"],
            [OB, "1", P1, S1, "2017-04-03 00:00:00", "80.00", "8.00"],
            [OC, "1", P3, S1, "2017-04-07 00:00:00", "200.00", "20.00"],
            [OD, "1", P2, S2, "2017-05-03 00:00:00", "40.00", "4.00"],
            [OF, "1", P1, S1, "2017-06-03 00:00:00", "60.00", "6.00"],
        ],
    ),
    "olist_order_payments_dataset.csv": (
        ["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"],
        [
            [OA, "1", "credit_card", "3", "100.00"],
            [OA, "2", "voucher", "1", "65.00"],
            [OB, "1", "boleto", "1", "88.00"],
            [OC, "1", "credit_card", "1", "220.00"],
            [OD, "1", "credit_card", "2", "44.00"],
            [OF, "1", "debit_card", "1", "66.00"],
        ],
    ),
    "olist_order_reviews_dataset.csv": (
        ["review_id", "order_id", "review_score", "review_comment_title", "review_comment_message",
         "review_creation_date", "review_answer_timestamp"],
        [
            [_id("r1"), OA, "5", "", "ótimo", "2017-03-16 00:00:00", "2017-03-17 00:00:00"],
            [_id("r2"), OB, "1", "", "atrasou", "2017-04-26 00:00:00", "2017-04-27 00:00:00"],
            [_id("r3"), OB, "3", "", "", "2017-04-28 00:00:00", "2017-04-29 00:00:00"],
            [_id("r4"), OD, "4", "", "", "2017-05-09 00:00:00", "2017-05-10 00:00:00"],
            [_id("r5"), OF, "5", "", "", "2017-06-13 00:00:00", "2017-06-14 00:00:00"],
        ],
    ),
}


def write_fixture_csvs(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for filename, (header, rows) in TABLES.items():
        with open(directory / filename, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(header)
            writer.writerows(rows)
    return directory
