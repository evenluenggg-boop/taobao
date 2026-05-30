"""Excel/CSV import utilities for Taobao 5-shop data."""

from __future__ import annotations

import re
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from taobao_collector.database import PROJECT_ROOT, get_connection

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

DATASET_CONFIGS: dict[str, dict[str, Any]] = {
    "customer_questions": {
        "label": "客服咨询数据",
        "table": "customer_questions",
        "required": ["shop_name", "customer_question"],
        "columns": [
            "shop_name",
            "product_id",
            "product_title",
            "sku_name",
            "customer_question",
            "question_time",
            "service_agent",
            "question_type",
            "is_after_sales",
            "affects_conversion",
            "suggested_action",
            "source_file",
        ],
    },
    "products": {
        "label": "商品数据",
        "table": "products",
        "required": ["shop_name", "product_title"],
        "columns": [
            "shop_name",
            "product_id",
            "product_title",
            "sku_name",
            "price",
            "source_file",
        ],
    },
    "aftersales": {
        "label": "售后数据",
        "table": "aftersales",
        "required": ["shop_name", "aftersales_type", "aftersales_reason"],
        "columns": [
            "shop_name",
            "product_id",
            "product_title",
            "aftersales_type",
            "aftersales_reason",
            "aftersales_time",
            "source_file",
        ],
    },
}

COLUMN_ALIASES = {
    "店铺名称": "shop_name",
    "店铺": "shop_name",
    "商品ID": "product_id",
    "商品id": "product_id",
    "商品编号": "product_id",
    "商品标题": "product_title",
    "商品名称": "product_title",
    "SKU": "sku_name",
    "sku": "sku_name",
    "SKU名称": "sku_name",
    "价格": "price",
    "售价": "price",
    "客户问题": "customer_question",
    "咨询问题": "customer_question",
    "问题内容": "customer_question",
    "问题时间": "question_time",
    "咨询时间": "question_time",
    "客服名称": "service_agent",
    "客服": "service_agent",
    "问题类型": "question_type",
    "是否售后相关": "is_after_sales",
    "是否售后": "is_after_sales",
    "是否影响成交": "affects_conversion",
    "影响成交": "affects_conversion",
    "建议处理动作": "suggested_action",
    "建议动作": "suggested_action",
    "售后类型": "aftersales_type",
    "售后原因": "aftersales_reason",
    "售后时间": "aftersales_time",
}


@dataclass
class ImportResult:
    """Result returned after importing one uploaded file."""

    dataset_type: str
    source_file: str
    saved_path: Path
    inserted_rows: int = 0
    skipped_rows: int = 0
    missing_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not self.missing_fields


def safe_upload_filename(original_filename: str) -> str:
    """Create a local filename that does not trust the browser-provided path."""

    suffix = Path(original_filename).suffix.lower()
    stem = Path(original_filename).stem or "upload"
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem).strip("._") or "upload"
    return f"{safe_stem}_{uuid.uuid4().hex[:8]}{suffix}"


def save_upload_file(file_obj: Any, original_filename: str, raw_dir: Path = RAW_DATA_DIR) -> Path:
    """Persist an uploaded file under data/raw/."""

    suffix = Path(original_filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("仅支持 .xlsx、.xls、.csv 文件")

    raw_dir.mkdir(parents=True, exist_ok=True)
    destination = raw_dir / safe_upload_filename(original_filename)
    with destination.open("wb") as output:
        shutil.copyfileobj(file_obj, output)
    return destination


def read_table_file(path: Path) -> pd.DataFrame:
    """Read CSV/XLS/XLSX into a DataFrame without assuming real Taobao sources."""

    suffix = path.suffix.lower()
    if suffix == ".csv":
        try:
            return pd.read_csv(path, dtype=str, encoding="utf-8-sig")
        except UnicodeDecodeError:
            return pd.read_csv(path, dtype=str, encoding="gb18030")
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, dtype=str)
    raise ValueError("仅支持 .xlsx、.xls、.csv 文件")


def normalize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Trim field names and map Chinese headers to standard English fields."""

    normalized_columns = []
    for column in dataframe.columns:
        cleaned = str(column).strip()
        normalized_columns.append(COLUMN_ALIASES.get(cleaned, cleaned))

    normalized = dataframe.copy()
    normalized.columns = normalized_columns
    return normalized


def normalize_bool(value: Any) -> int:
    """Convert common Chinese/English yes-no values to 0/1."""

    if value is None or pd.isna(value):
        return 0
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "是", "有", "售后", "影响"}:
        return 1
    if text in {"0", "false", "no", "n", "否", "无", "不影响"}:
        return 0
    return 0


def clean_value(value: Any) -> Any:
    """Normalize scalar values while preserving empty cells as None."""

    if value is None or pd.isna(value):
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return value


def normalize_price(value: Any) -> float | None:
    """Parse a price value if present."""

    cleaned = clean_value(value)
    if cleaned is None:
        return None
    try:
        return float(str(cleaned).replace(",", ""))
    except ValueError:
        return None


def shop_code_from_name(shop_name: str) -> str:
    """Generate a stable local shop code from a shop name."""

    safe = re.sub(r"\W+", "_", shop_name, flags=re.UNICODE).strip("_") or "SHOP"
    return f"SHOP_{safe}"[:64]


def ensure_shops(rows: list[dict[str, Any]]) -> None:
    """Upsert shops discovered in imported rows."""

    names = sorted({row.get("shop_name") for row in rows if row.get("shop_name")})
    if not names:
        return

    with get_connection() as connection:
        connection.executemany(
            """
            INSERT OR IGNORE INTO shops (shop_name, shop_code, platform)
            VALUES (?, ?, 'taobao')
            """,
            [(name, shop_code_from_name(str(name))) for name in names],
        )


def dataframe_to_rows(dataframe: pd.DataFrame, dataset_type: str, source_file: str) -> ImportResult:
    """Standardize a DataFrame and insert valid rows into SQLite."""

    if dataset_type not in DATASET_CONFIGS:
        raise ValueError("未知数据类型")

    config = DATASET_CONFIGS[dataset_type]
    normalized = normalize_columns(dataframe)
    missing_fields = [field for field in config["required"] if field not in normalized.columns]
    result = ImportResult(dataset_type=dataset_type, source_file=source_file, saved_path=Path(source_file))
    result.missing_fields = missing_fields
    if missing_fields:
        return result

    rows: list[dict[str, Any]] = []
    for row_number, (_, raw_row) in enumerate(normalized.iterrows(), start=2):
        row = {column: clean_value(raw_row[column]) if column in raw_row else None for column in config["columns"]}
        row["source_file"] = source_file

        if dataset_type == "customer_questions":
            row["is_after_sales"] = normalize_bool(row.get("is_after_sales"))
            row["affects_conversion"] = normalize_bool(row.get("affects_conversion"))
        if dataset_type == "products":
            row["price"] = normalize_price(row.get("price"))

        missing_required_value = [field for field in config["required"] if not row.get(field)]
        if missing_required_value:
            result.skipped_rows += 1
            result.warnings.append(f"第 {row_number} 行缺少必要值：{', '.join(missing_required_value)}，已跳过")
            continue
        rows.append(row)

    if not rows:
        return result

    ensure_shops(rows)
    columns = config["columns"]
    placeholders = ", ".join(["?"] * len(columns))
    column_sql = ", ".join(columns)
    values = [[row.get(column) for column in columns] for row in rows]

    with get_connection() as connection:
        connection.executemany(
            f"INSERT INTO {config['table']} ({column_sql}) VALUES ({placeholders})",
            values,
        )

    result.inserted_rows = len(rows)
    return result


def import_file(dataset_type: str, path: Path) -> ImportResult:
    """Read, standardize, and import a saved upload file."""

    dataframe = read_table_file(path)
    result = dataframe_to_rows(dataframe, dataset_type=dataset_type, source_file=path.name)
    result.saved_path = path
    return result
