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


def test_initialize_database_creates_customer_service_metrics_table(tmp_path):
    database_path = initialize_database(tmp_path / "taobao_5shop.db")

    with sqlite3.connect(database_path) as connection:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(customer_service_metrics)")
        }

    assert {
        "stat_date",
        "shop_name",
        "service_account",
        "service_agent",
        "first_response_seconds",
        "avg_response_seconds",
        "consultation_count",
        "unreplied_count",
        "avg_service_duration",
        "personal_sales_amount",
        "wangwang_reply_rate",
        "question_answer_ratio",
        "source_file",
    }.issubset(columns)
