-- SQLite schema for Taobao 5-shop Excel/CSV import V1.
-- Store only authorized, imported business rows. Do not store credentials,
-- cookies, customer PII beyond authorized operational fields, or chat logs.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS shops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_name TEXT NOT NULL,
    shop_code TEXT NOT NULL UNIQUE,
    platform TEXT NOT NULL DEFAULT 'taobao',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_name TEXT NOT NULL,
    product_id TEXT,
    product_title TEXT,
    sku_name TEXT,
    price REAL,
    source_file TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_name TEXT NOT NULL,
    product_id TEXT,
    product_title TEXT,
    sku_name TEXT,
    customer_question TEXT,
    question_time TEXT,
    service_agent TEXT,
    question_type TEXT,
    is_after_sales INTEGER NOT NULL DEFAULT 0 CHECK (is_after_sales IN (0, 1)),
    affects_conversion INTEGER NOT NULL DEFAULT 0 CHECK (affects_conversion IN (0, 1)),
    suggested_action TEXT,
    source_file TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aftersales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_name TEXT NOT NULL,
    product_id TEXT,
    product_title TEXT,
    aftersales_type TEXT,
    aftersales_reason TEXT,
    aftersales_time TEXT,
    source_file TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_service_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date TEXT,
    shop_name TEXT,
    service_account TEXT,
    service_agent TEXT,
    wangwang_nick_raw TEXT,
    first_response_seconds REAL,
    avg_response_seconds REAL,
    consultation_count INTEGER,
    unreplied_count INTEGER,
    avg_service_duration REAL,
    personal_sales_amount REAL,
    wangwang_reply_rate REAL,
    question_answer_ratio REAL,
    effective_reception_count INTEGER,
    inquiry_count INTEGER,
    order_buyer_count INTEGER,
    order_amount REAL,
    sales_buyer_count INTEGER,
    sales_amount REAL,
    sales_quantity INTEGER,
    order_count INTEGER,
    personal_sales_ratio REAL,
    refund_amount REAL,
    net_sales_amount REAL,
    wangwang_type TEXT,
    source_file TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date TEXT NOT NULL,
    shop_name TEXT NOT NULL,
    total_questions INTEGER NOT NULL DEFAULT 0,
    after_sales_questions INTEGER NOT NULL DEFAULT 0,
    conversion_affecting_questions INTEGER NOT NULL DEFAULT 0,
    top_question_type TEXT,
    suggested_action TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_shops_shop_code ON shops(shop_code);
CREATE INDEX IF NOT EXISTS idx_products_shop_name ON products(shop_name);
CREATE INDEX IF NOT EXISTS idx_products_product_id ON products(product_id);
CREATE INDEX IF NOT EXISTS idx_customer_questions_shop_name ON customer_questions(shop_name);
CREATE INDEX IF NOT EXISTS idx_customer_questions_source_file ON customer_questions(source_file);
CREATE INDEX IF NOT EXISTS idx_aftersales_shop_name ON aftersales(shop_name);
CREATE INDEX IF NOT EXISTS idx_aftersales_source_file ON aftersales(source_file);
CREATE INDEX IF NOT EXISTS idx_daily_reports_report_date ON daily_reports(report_date);
CREATE INDEX IF NOT EXISTS idx_customer_service_metrics_stat_date ON customer_service_metrics(stat_date);
CREATE INDEX IF NOT EXISTS idx_customer_service_metrics_shop_name ON customer_service_metrics(shop_name);
CREATE INDEX IF NOT EXISTS idx_customer_service_metrics_service_account ON customer_service_metrics(service_account);
