import sqlite3

from taobao_collector.database import initialize_database


def test_initialize_database_creates_expected_tables(tmp_path):
    database_path = initialize_database(tmp_path / "taobao_collector.sqlite3")

    with sqlite3.connect(database_path) as connection:
        table_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert {
        "shops",
        "customer_service_agents",
        "shop_public_snapshots",
        "customer_service_metrics",
        "collection_jobs",
        "collection_job_events",
    }.issubset(table_names)


def test_schema_enforces_shop_code_uniqueness(tmp_path):
    database_path = initialize_database(tmp_path / "taobao_collector.sqlite3")

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO shops (shop_code, shop_name, shop_url)
            VALUES ('SHOP_DEMO_001', '示例店铺A', 'https://example.com/taobao-shop-a')
            """
        )

        try:
            connection.execute(
                """
                INSERT INTO shops (shop_code, shop_name, shop_url)
                VALUES ('SHOP_DEMO_001', '示例店铺B', 'https://example.com/taobao-shop-b')
                """
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("duplicate shop_code should violate the unique constraint")
