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


def test_customer_service_metrics_template_fields_exist():
    template_path = importer.PROJECT_ROOT / "data" / "templates" / "customer_service_metrics_template.csv"
    dataframe = pd.read_csv(template_path)

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
    }.issubset(dataframe.columns)


def test_normalize_columns_maps_customer_service_metrics_chinese_headers():
    dataframe = pd.DataFrame(
        [
            {
                "数据日期": "2026-01-01",
                "店铺": "示例店铺A",
                "旺旺账号": "ww_demo_a",
                "客服": "客服示例A",
                "首次响应（秒）": "12",
                "平均响应秒数": "38",
                "接待人数": "42",
                "未回复人数": "1",
                "平均服务时长": "00:08:35",
                "个人销售额": "￥1,234.56",
                "旺旺回复率（%）": "95%",
                "答问比": "1.35",
            }
        ]
    )

    normalized = normalize_columns(dataframe)

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
    }.issubset(normalized.columns)


def test_dataframe_to_rows_imports_customer_service_metrics(tmp_path, monkeypatch):
    database_path = initialize_database(tmp_path / "taobao_5shop.db")
    monkeypatch.setattr(importer, "get_connection", lambda: sqlite3.connect(database_path))

    dataframe = pd.DataFrame(
        [
            {
                "日期": "2026-01-01",
                "店铺名称": "示例店铺A",
                "客服账号": "ww_demo_a",
                "客服名称": "客服示例A",
                "首次响应秒数": "12秒",
                "平均响应（秒）": "38",
                "咨询人数": "42",
                "未回复人数": "1",
                "平均服务时长": "8分35秒",
                "个人日销售额": "￥1,234.56",
                "旺旺回复率": "95%",
                "答问比": "1.35",
            },
            {
                "日期": "2026-01-01",
                "店铺名称": "示例店铺B",
                "子账号": "ww_demo_b",
                "平均服务时长": "515秒",
                "个人日销售额": "1,000.00",
                "旺旺回复率": "95.00",
            },
        ]
    )

    result = dataframe_to_rows(dataframe, "customer_service_metrics", "metrics.csv")

    assert result.inserted_rows == 2
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT service_account, avg_service_duration, personal_sales_amount, wangwang_reply_rate
            FROM customer_service_metrics
            ORDER BY service_account
            """
        ).fetchall()
    assert rows == [("ww_demo_a", 515.0, 1234.56, 95.0), ("ww_demo_b", 515.0, 1000.0, 95.0)]
