-- Base SQLite schema for authorized Taobao shop and customer-service data.
-- This schema stores normalized metadata and metrics only; do not insert
-- real customer PII, chat records, credentials, cookies, or access tokens.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS shops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_code TEXT NOT NULL UNIQUE,
    shop_name TEXT NOT NULL,
    shop_url TEXT NOT NULL,
    seller_id TEXT,
    main_category TEXT,
    ownership_status TEXT NOT NULL DEFAULT 'authorized',
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_service_agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER NOT NULL,
    agent_alias TEXT NOT NULL,
    public_wangwang_nickname TEXT,
    service_role TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE,
    UNIQUE (shop_id, agent_alias)
);

CREATE TABLE IF NOT EXISTS shop_public_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER NOT NULL,
    public_rating REAL,
    item_count INTEGER CHECK (item_count IS NULL OR item_count >= 0),
    announcement TEXT,
    customer_service_entry_name TEXT,
    online_status TEXT,
    data_source TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS customer_service_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER NOT NULL,
    agent_id INTEGER,
    stat_date TEXT NOT NULL,
    reception_count INTEGER NOT NULL DEFAULT 0 CHECK (reception_count >= 0),
    avg_response_seconds INTEGER CHECK (avg_response_seconds IS NULL OR avg_response_seconds >= 0),
    first_response_seconds INTEGER CHECK (first_response_seconds IS NULL OR first_response_seconds >= 0),
    conversion_count INTEGER NOT NULL DEFAULT 0 CHECK (conversion_count >= 0),
    conversion_rate REAL CHECK (conversion_rate IS NULL OR (conversion_rate >= 0 AND conversion_rate <= 1)),
    after_sales_count INTEGER NOT NULL DEFAULT 0 CHECK (after_sales_count >= 0),
    data_source TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES customer_service_agents(id) ON DELETE SET NULL,
    UNIQUE (shop_id, agent_id, stat_date, data_source)
);

CREATE TABLE IF NOT EXISTS collection_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name TEXT NOT NULL,
    data_source TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'success', 'failed', 'skipped')),
    started_at TEXT,
    finished_at TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS collection_job_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES collection_jobs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_customer_service_agents_shop_id
    ON customer_service_agents(shop_id);

CREATE INDEX IF NOT EXISTS idx_shop_public_snapshots_shop_collected
    ON shop_public_snapshots(shop_id, collected_at);

CREATE INDEX IF NOT EXISTS idx_customer_service_metrics_shop_date
    ON customer_service_metrics(shop_id, stat_date);

CREATE INDEX IF NOT EXISTS idx_collection_jobs_status_created
    ON collection_jobs(status, created_at);
