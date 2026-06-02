"""FastAPI web application for the Taobao 5-shop import V1 system."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from taobao_collector.database import PROJECT_ROOT, count_rows, fetch_rows, get_connection, initialize_database
from taobao_collector.importer import DATASET_CONFIGS, import_file, save_upload_file

TEMPLATE_DIR = PROJECT_ROOT / "web" / "templates"

app = FastAPI(title="淘宝5店铺数据分析系统")
app.mount(
    "/data/templates",
    StaticFiles(directory=str(PROJECT_ROOT / "data" / "templates")),
    name="data_templates",
)
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

NAV_ITEMS = [
    ("首页", "/"),
    ("上传数据", "/upload"),
    ("数据预览", "/preview"),
    ("店铺列表", "/shops"),
    ("商品问题库", "/product-questions"),
    ("客服绩效分析", "/analysis/service-metrics"),
    ("运营日报", "/daily-reports"),
]

PREVIEW_TABLES = {
    "customer_questions": "客服咨询数据",
    "products": "商品数据",
    "aftersales": "售后数据",
    "customer_service_metrics": "客服绩效数据",
}


@app.on_event("startup")
def startup() -> None:
    initialize_database()


def context(request: Request, **extra: object) -> dict[str, object]:
    base = {
        "request": request,
        "nav_items": NAV_ITEMS,
        "system_name": "淘宝5店铺数据分析系统",
    }
    base.update(extra)
    return base


def service_metrics_filter_options() -> dict[str, list[str]]:
    """Return available filter values for service metrics analysis."""

    with get_connection() as connection:
        shop_names = [
            row[0]
            for row in connection.execute(
                """
                SELECT DISTINCT shop_name
                FROM customer_service_metrics
                WHERE shop_name IS NOT NULL AND shop_name != ''
                ORDER BY shop_name
                """
            ).fetchall()
        ]
        service_accounts = [
            row[0]
            for row in connection.execute(
                """
                SELECT DISTINCT service_account
                FROM customer_service_metrics
                WHERE service_account IS NOT NULL AND service_account != ''
                ORDER BY service_account
                """
            ).fetchall()
        ]
    return {"shop_names": shop_names, "service_accounts": service_accounts}


def service_metrics_analysis(
    start_date: str | None = None,
    end_date: str | None = None,
    shop_name: str | None = None,
    service_account: str | None = None,
) -> dict[str, object]:
    """Build filtered summary and ranking tables for customer-service metrics."""

    clauses: list[str] = []
    params: list[object] = []
    if start_date:
        clauses.append("stat_date >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("stat_date <= ?")
        params.append(end_date)
    if shop_name:
        clauses.append("shop_name = ?")
        params.append(shop_name)
    if service_account:
        clauses.append("service_account = ?")
        params.append(service_account)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    summary_sql = f"""
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT shop_name) AS shop_count,
            COUNT(DISTINCT service_account) AS service_account_count,
            COALESCE(SUM(consultation_count), 0) AS consultation_count,
            COALESCE(SUM(effective_reception_count), 0) AS effective_reception_count,
            COALESCE(SUM(order_buyer_count), 0) AS order_buyer_count,
            ROUND(COALESCE(SUM(order_amount), 0), 2) AS order_amount,
            COALESCE(SUM(sales_buyer_count), 0) AS sales_buyer_count,
            ROUND(COALESCE(SUM(sales_amount), 0), 2) AS sales_amount,
            COALESCE(SUM(sales_quantity), 0) AS sales_quantity,
            COALESCE(SUM(order_count), 0) AS order_count,
            ROUND(COALESCE(SUM(refund_amount), 0), 2) AS refund_amount,
            ROUND(COALESCE(SUM(net_sales_amount), 0), 2) AS net_sales_amount
        FROM customer_service_metrics
        {where_sql}
    """
    detail_sql = f"""
        SELECT stat_date, shop_name, service_account, service_agent, wangwang_type,
               consultation_count, effective_reception_count, inquiry_count,
               order_buyer_count, order_amount, sales_buyer_count,
               personal_sales_amount, sales_amount, sales_quantity, order_count,
               personal_sales_ratio, refund_amount, net_sales_amount
        FROM customer_service_metrics
        {where_sql}
        ORDER BY stat_date DESC, shop_name, service_account
        LIMIT 200
    """
    ranking_sql = {
        "sales_top10": ("销售额 TOP10", "sales_amount", "DESC"),
        "net_sales_top10": ("净销售额 TOP10", "net_sales_amount", "DESC"),
        "order_top10": ("订单量 TOP10", "order_count", "DESC"),
        "effective_reception_top10": ("有效接待人数 TOP10", "effective_reception_count", "DESC"),
        "refund_top10": ("退款金额 TOP10", "refund_amount", "DESC"),
        "consultation_top10": ("咨询人数 TOP10", "consultation_count", "DESC"),
    }

    with get_connection() as connection:
        summary = dict(connection.execute(summary_sql, params).fetchone())
        details = [dict(row) for row in connection.execute(detail_sql, params).fetchall()]
        rankings = {}
        for key, (title, metric_column, direction) in ranking_sql.items():
            sql = f"""
                SELECT stat_date, shop_name, service_account, service_agent,
                       wangwang_type, {metric_column} AS metric_value
                FROM customer_service_metrics
                {where_sql} {'AND' if where_sql else 'WHERE'} {metric_column} IS NOT NULL
                ORDER BY {metric_column} {direction}, id DESC
                LIMIT 10
            """
            rankings[key] = {
                "title": title,
                "rows": [dict(row) for row in connection.execute(sql, params).fetchall()],
            }
    return {"summary": summary, "details": details, "rankings": rankings}


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    stats = {
        "shops": count_rows("shops"),
        "customer_questions": count_rows("customer_questions"),
        "products": count_rows("products"),
        "aftersales": count_rows("aftersales"),
        "customer_service_metrics": count_rows("customer_service_metrics"),
    }
    return templates.TemplateResponse(request, "home.html", context(request, stats=stats))


@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "upload.html",
        context(request, dataset_configs=DATASET_CONFIGS, result=None, error=None),
    )


@app.post("/upload", response_class=HTMLResponse)
async def upload_data(
    request: Request,
    dataset_type: str = Form(...),
    file: UploadFile = File(...),
) -> HTMLResponse:
    result = None
    error = None
    try:
        if dataset_type not in DATASET_CONFIGS:
            raise ValueError("请选择正确的数据类型")
        if not file.filename:
            raise ValueError("请选择要上传的文件")
        saved_path = save_upload_file(file.file, file.filename)
        result = import_file(dataset_type, Path(saved_path))
        if result.missing_fields:
            error = f"缺少必要字段：{', '.join(result.missing_fields)}"
    except Exception as exc:  # noqa: BLE001 - surface upload/import errors to local UI
        error = str(exc)
    finally:
        await file.close()

    return templates.TemplateResponse(
        request,
        "upload.html",
        context(request, dataset_configs=DATASET_CONFIGS, result=result, error=error),
    )


@app.get("/preview", response_class=HTMLResponse)
def preview(request: Request, table: str = "customer_questions") -> HTMLResponse:
    if table not in PREVIEW_TABLES:
        table = "customer_questions"
    rows = fetch_rows(table, limit=50)
    columns = list(rows[0].keys()) if rows else []
    return templates.TemplateResponse(
        request,
        "preview.html",
        context(
            request,
            table=table,
            table_label=PREVIEW_TABLES[table],
            preview_tables=PREVIEW_TABLES,
            rows=rows,
            columns=columns,
        ),
    )


@app.get("/shops", response_class=HTMLResponse)
def shops(request: Request) -> HTMLResponse:
    rows = fetch_rows("shops", limit=50)
    columns = list(rows[0].keys()) if rows else []
    return templates.TemplateResponse(request, "shops.html", context(request, rows=rows, columns=columns))


@app.get("/product-questions", response_class=HTMLResponse)
def product_questions(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "placeholder.html",
        context(
            request,
            title="商品问题库",
            message="本阶段只完成数据导入与预览；商品问题库分析将在下一阶段实现。",
        ),
    )


@app.get("/analysis/service-metrics", response_class=HTMLResponse)
def service_metrics_page(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    shop_name: str | None = None,
    service_account: str | None = None,
) -> HTMLResponse:
    filters = {
        "start_date": start_date or "",
        "end_date": end_date or "",
        "shop_name": shop_name or "",
        "service_account": service_account or "",
    }
    return templates.TemplateResponse(
        request,
        "service_metrics.html",
        context(
            request,
            title="5店铺客服绩效分析",
            filters=filters,
            filter_options=service_metrics_filter_options(),
            analysis=service_metrics_analysis(start_date, end_date, shop_name, service_account),
        ),
    )


@app.get("/daily-reports", response_class=HTMLResponse)
def daily_reports(request: Request) -> HTMLResponse:
    rows = fetch_rows("daily_reports", limit=50)
    return templates.TemplateResponse(
        request,
        "placeholder.html",
        context(
            request,
            title="运营日报",
            message="本阶段只预留运营日报入口；自动日报统计将在下一阶段实现。",
            rows=rows,
        ),
    )
