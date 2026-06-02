import sqlite3

import pytest

pd = pytest.importorskip("pandas")

from taobao_collector import importer
from taobao_collector.database import initialize_database
from taobao_collector.importer import (
    dataframe_to_rows,
    extract_stat_date_from_filename,
    normalize_columns,
    split_wangwang_nick,
)


REAL_EXPORT_FILENAME = "客服绩效-业绩分析-汇总分析_20260601_20260601_全部.xlsx"


def test_wangwang_nick_splits_shop_and_service_account():
    shop_name, service_account, service_agent = split_wangwang_nick("钱运来旗舰店:贞贞")

    assert shop_name == "钱运来旗舰店"
    assert service_account == "贞贞"
    assert service_agent == "贞贞"


def test_stat_date_is_extracted_from_real_export_filename():
    assert extract_stat_date_from_filename(REAL_EXPORT_FILENAME) == "2026-06-01"


def test_real_sales_amount_header_maps_to_personal_and_sales_amount():
    dataframe = pd.DataFrame([{"销售额": "788"}])

    normalized = normalize_columns(dataframe)

    assert "personal_sales_amount" in normalized.columns
    assert "sales_amount" in normalized.columns
    assert normalized.loc[0, "personal_sales_amount"] == "788"
    assert normalized.loc[0, "sales_amount"] == "788"


def test_real_export_summary_and_average_rows_are_skipped(tmp_path, monkeypatch):
    database_path = initialize_database(tmp_path / "taobao_5shop.db")
    monkeypatch.setattr(importer, "get_connection", lambda: sqlite3.connect(database_path))
    dataframe = pd.DataFrame(
        [
            {"旺旺昵称": "汇总值", "咨询人数": "100", "销售额": "9999"},
            {"旺旺昵称": "平均值", "咨询人数": "10", "销售额": "999"},
            {"旺旺昵称": "钱运来旗舰店:贞贞", "咨询人数": "5", "销售额": "788"},
        ]
    )

    result = dataframe_to_rows(dataframe, "customer_service_metrics", REAL_EXPORT_FILENAME)

    assert result.inserted_rows == 1
    assert result.skipped_rows == 2


def test_delayed_inquiry_count_does_not_fail_import(tmp_path, monkeypatch):
    database_path = initialize_database(tmp_path / "taobao_5shop.db")
    monkeypatch.setattr(importer, "get_connection", lambda: sqlite3.connect(database_path))
    dataframe = pd.DataFrame(
        [
            {
                "旺旺昵称": "钱运来旗舰店:贞贞",
                "咨询人数": "5",
                "询单人数": "延时统计",
                "销售额": "788",
            }
        ]
    )

    result = dataframe_to_rows(dataframe, "customer_service_metrics", REAL_EXPORT_FILENAME)

    assert result.inserted_rows == 1
    with sqlite3.connect(database_path) as connection:
        inquiry_count = connection.execute(
            "SELECT inquiry_count FROM customer_service_metrics"
        ).fetchone()[0]
    assert inquiry_count is None


def test_real_export_structure_imports_service_metrics(tmp_path, monkeypatch):
    database_path = initialize_database(tmp_path / "taobao_5shop.db")
    monkeypatch.setattr(importer, "get_connection", lambda: sqlite3.connect(database_path))
    dataframe = pd.DataFrame(
        [
            {
                "旺旺昵称": "钱运来旗舰店:贞贞",
                "咨询人数": "15",
                "有效接待人数": "12",
                "询单人数": "延时统计",
                "下单人数": "3",
                "下单金额": "￥1,234.56",
                "销售人数": "2",
                "销售额": "788",
                "销售量": "4",
                "订单量": "3",
                "个人销售额占比": "32.97%",
                "成功退款金额": "100",
                "净销售额": "688",
                "旺旺类型": "售前",
            }
        ]
    )

    result = dataframe_to_rows(dataframe, "customer_service_metrics", REAL_EXPORT_FILENAME)

    assert result.inserted_rows == 1
    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT shop_name, service_account, consultation_count, sales_amount, net_sales_amount, stat_date
            FROM customer_service_metrics
            """
        ).fetchone()
    assert row == ("钱运来旗舰店", "贞贞", 15, 788.0, 688.0, "2026-06-01")
