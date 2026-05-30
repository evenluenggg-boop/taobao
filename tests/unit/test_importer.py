import sqlite3

import pytest

pd = pytest.importorskip("pandas")

from taobao_collector import importer
from taobao_collector.database import initialize_database
from taobao_collector.importer import dataframe_to_rows, normalize_columns


def test_normalize_columns_maps_chinese_headers():
    dataframe = pd.DataFrame(
        [
            {
                " 店铺名称 ": "示例店铺A",
                "商品ID": "DEMO-P-001",
                "客户问题": "是否有赠品",
                "是否影响成交": "是",
            }
        ]
    )

    normalized = normalize_columns(dataframe)

    assert {"shop_name", "product_id", "customer_question", "affects_conversion"}.issubset(
        normalized.columns
    )


def test_dataframe_to_rows_imports_customer_questions(tmp_path, monkeypatch):
    database_path = initialize_database(tmp_path / "taobao_5shop.db")
    monkeypatch.setattr(importer, "get_connection", lambda: sqlite3.connect(database_path))

    dataframe = pd.DataFrame(
        [
            {
                "店铺名称": "示例店铺A",
                "商品ID": "DEMO-P-001",
                "商品标题": "示例保温杯",
                "客户问题": "能否进洗碗机",
                "是否售后相关": "否",
                "是否影响成交": "是",
            },
            {
                "店铺名称": None,
                "商品ID": "DEMO-P-002",
                "客户问题": "这一行缺少店铺名，应跳过",
            },
        ]
    )

    result = dataframe_to_rows(dataframe, "customer_questions", "demo.csv")

    assert result.inserted_rows == 1
    assert result.skipped_rows == 1
    with sqlite3.connect(database_path) as connection:
        question_count = connection.execute("SELECT COUNT(*) FROM customer_questions").fetchone()[0]
        shop_count = connection.execute("SELECT COUNT(*) FROM shops").fetchone()[0]
    assert question_count == 1
    assert shop_count == 1


def test_dataframe_to_rows_reports_missing_required_columns():
    dataframe = pd.DataFrame([{"商品ID": "DEMO-P-001"}])

    result = dataframe_to_rows(dataframe, "customer_questions", "demo.csv")

    assert result.inserted_rows == 0
    assert result.missing_fields == ["shop_name", "customer_question"]
