"""FastAPI web application for the Taobao 5-shop import V1 system."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from taobao_collector.database import PROJECT_ROOT, count_rows, fetch_rows, initialize_database
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
    ("上传数据", "/upload"),
    ("数据预览", "/preview"),
    ("店铺列表", "/shops"),
    ("商品问题库", "/product-questions"),
    ("运营日报", "/daily-reports"),
]

PREVIEW_TABLES = {
    "customer_questions": "客服咨询数据",
    "products": "商品数据",
    "aftersales": "售后数据",
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


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    stats = {
        "shops": count_rows("shops"),
        "customer_questions": count_rows("customer_questions"),
        "products": count_rows("products"),
        "aftersales": count_rows("aftersales"),
    }
    return templates.TemplateResponse("home.html", context(request, stats=stats))


@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
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
    return templates.TemplateResponse("shops.html", context(request, rows=rows, columns=columns))


@app.get("/product-questions", response_class=HTMLResponse)
def product_questions(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "placeholder.html",
        context(
            request,
            title="商品问题库",
            message="本阶段只完成数据导入与预览；商品问题库分析将在下一阶段实现。",
        ),
    )


@app.get("/daily-reports", response_class=HTMLResponse)
def daily_reports(request: Request) -> HTMLResponse:
    rows = fetch_rows("daily_reports", limit=50)
    return templates.TemplateResponse(
        "placeholder.html",
        context(
            request,
            title="运营日报",
            message="本阶段只预留运营日报入口；自动日报统计将在下一阶段实现。",
            rows=rows,
        ),
    )
