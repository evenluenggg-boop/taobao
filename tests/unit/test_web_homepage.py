import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from taobao_collector.app import app


client = TestClient(app)


def test_homepage_has_required_v1_entries():
    response = client.get("/")

    assert response.status_code == 200
    assert "淘宝5店铺数据分析系统" in response.text
    assert "上传数据" in response.text
    assert "数据预览" in response.text
    assert "店铺列表" in response.text
    assert "商品问题库" in response.text
    assert "运营日报" in response.text


def test_placeholder_pages_are_available():
    product_response = client.get("/product-questions")
    report_response = client.get("/daily-reports")

    assert product_response.status_code == 200
    assert report_response.status_code == 200
    assert "V1 占位页面" in product_response.text
    assert "V1 占位页面" in report_response.text


def test_service_metrics_page_is_available():
    response = client.get("/analysis/service-metrics")

    assert response.status_code == 200
    assert "5店铺客服绩效分析" in response.text
    assert "销售额 TOP10" in response.text
