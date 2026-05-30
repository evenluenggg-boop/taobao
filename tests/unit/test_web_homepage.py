from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOME_PAGE = PROJECT_ROOT / "web" / "index.html"


def test_homepage_exists_and_has_required_sections():
    html = HOME_PAGE.read_text(encoding="utf-8")

    assert "Taobao Collector 本地后台" in html
    assert "店铺接入状态" in html
    assert "常用入口" in html
    assert "SHOP_DEMO_001" in html


def test_homepage_uses_only_demo_data_markers():
    html = HOME_PAGE.read_text(encoding="utf-8")

    assert "示例占位数据" in html
    assert "不包含真实店铺、客户或客服隐私数据" in html
    assert "SHOP_DEMO_" in html
