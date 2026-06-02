import sqlite3

from taobao_collector.database import initialize_database


def test_initialize_database_creates_v1_tables(tmp_path):
    database_path = initialize_database(tmp_path / "taobao_5shop.db")

    with sqlite3.connect(database_path) as connection:
        table_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert {
        "shops",
        "products",
        "customer_questions",
        "aftersales",
        "daily_reports",
        "customer_service_metrics",
    }.issubset(table_names)


def test_schema_enforces_shop_code_uniqueness(tmp_path):
    database_path = initialize_database(tmp_path / "taobao_5shop.db")

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO shops (shop_code, shop_name, platform)
            VALUES ('SHOP_DEMO_001', '示例店铺A', 'taobao')
            """
        )

        try:
            connection.execute(
                """
                INSERT INTO shops (shop_code, shop_name, platform)
                VALUES ('SHOP_DEMO_001', '示例店铺B', 'taobao')
                """
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("duplicate shop_code should violate the unique constraint")
