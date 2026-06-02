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
            COALESCE(SUM(unreplied_count), 0) AS unreplied_count,
            ROUND(COALESCE(AVG(avg_response_seconds), 0), 2) AS avg_response_seconds,
            ROUND(COALESCE(SUM(personal_sales_amount), 0), 2) AS personal_sales_amount,
            ROUND(COALESCE(AVG(wangwang_reply_rate), 0), 2) AS wangwang_reply_rate,
            ROUND(COALESCE(AVG(question_answer_ratio), 0), 2) AS question_answer_ratio
        FROM customer_service_metrics
        {where_sql}
    """
    detail_sql = f"""
        SELECT stat_date, shop_name, service_account, service_agent,
               first_response_seconds, avg_response_seconds, consultation_count,
               unreplied_count, avg_service_duration, personal_sales_amount,
               wangwang_reply_rate, question_answer_ratio
        FROM customer_service_metrics
        {where_sql}
        ORDER BY stat_date DESC, shop_name, service_account
        LIMIT 200
    """
    ranking_sql = {
        "consultation_top10": (
            "咨询人数 TOP10",
            f"""
            SELECT stat_date, shop_name, service_account, service_agent, consultation_count AS metric_value
            FROM customer_service_metrics
            {where_sql}
            ORDER BY consultation_count DESC, id DESC
            LIMIT 10
            """,
        ),
        "sales_top10": (
            "个人日销售额 TOP10",
            f"""
            SELECT stat_date, shop_name, service_account, service_agent, personal_sales_amount AS metric_value
            FROM customer_service_metrics
            {where_sql}
            ORDER BY personal_sales_amount DESC, id DESC
            LIMIT 10
            """,
        ),
        "fast_response_top10": (
            "平均响应最快 TOP10",
            f"""
            SELECT stat_date, shop_name, service_account, service_agent, avg_response_seconds AS metric_value
            FROM customer_service_metrics
            {where_sql} {'AND' if where_sql else 'WHERE'} avg_response_seconds IS NOT NULL
            ORDER BY avg_response_seconds ASC, id DESC
            LIMIT 10
            """,
        ),
        "unreplied_top10": (
            "未回复人数最多 TOP10",
            f"""
            SELECT stat_date, shop_name, service_account, service_agent, unreplied_count AS metric_value
            FROM customer_service_metrics
            {where_sql}
            ORDER BY unreplied_count DESC, id DESC
            LIMIT 10
            """,
        ),
        "low_reply_rate_top10": (
            "旺旺回复率最低 TOP10",
            f"""
            SELECT stat_date, shop_name, service_account, service_agent, wangwang_reply_rate AS metric_value
            FROM customer_service_metrics
            {where_sql} {'AND' if where_sql else 'WHERE'} wangwang_reply_rate IS NOT NULL
            ORDER BY wangwang_reply_rate ASC, id DESC
            LIMIT 10
            """,
        ),
        "qa_ratio_abnormal_top10": (
            "答问比异常 TOP10",
            f"""
            SELECT stat_date, shop_name, service_account, service_agent, question_answer_ratio AS metric_value
            FROM customer_service_metrics
            {where_sql} {'AND' if where_sql else 'WHERE'} question_answer_ratio IS NOT NULL
            ORDER BY ABS(question_answer_ratio - 1.0) DESC, id DESC
            LIMIT 10
            """,
        ),
    }

    with get_connection() as connection:
        summary = dict(connection.execute(summary_sql, params).fetchone())
        details = [dict(row) for row in connection.execute(detail_sql, params).fetchall()]
        rankings = {
            key: {"title": title, "rows": [dict(row) for row in connection.execute(sql, params).fetchall()]}
            for key, (title, sql) in ranking_sql.items()
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
