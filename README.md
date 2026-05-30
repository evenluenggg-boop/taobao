# 淘宝5店铺数据分析系统

面向 **5 个自有或已授权淘宝店铺** 的本地 Excel / CSV 导入版 V1 系统。

本阶段不接淘宝接口、不做爬虫、不做 AI 客服，目标只跑通：**上传 Excel/CSV → 字段清洗 → 写入 SQLite → 网页后台预览数据**。

> 合规提醒：本项目只应处理你拥有或已获得授权的店铺数据。不要提交 Cookie、Token、账号密码、客户聊天记录、真实订单/售后数据、客服个人隐私或任何未授权业务数据。

## V1 已完成功能

- FastAPI + Jinja2 本地网页后台，可访问 `http://127.0.0.1:8000/`。
- 首页显示系统名称：**淘宝5店铺数据分析系统**。
- 首页包含入口：上传数据、数据预览、店铺列表、商品问题库、运营日报。
- 支持上传客服咨询数据、商品数据、售后数据。
- 支持 `.xlsx`、`.xls`、`.csv` 文件格式。
- 上传文件保存到本地 `data/raw/`，该目录默认不提交。
- 导入数据写入 SQLite，默认数据库路径为 `data/local/taobao_5shop.db`。
- 数据预览页可查看 `customer_questions`、`products`、`aftersales` 前 50 行，并显示 `source_file`。
- 商品问题库和运营日报已创建占位页面，完整分析留到下一阶段。

## 项目目录结构

```text
.
├── .env.example             # 环境变量模板，只放示例值，不放真实凭证
├── .gitignore               # 忽略本地环境、业务数据、日志、数据库与上传文件
├── config/                  # 非敏感配置模板与本地配置说明
├── database/                # SQLite 表结构与数据库说明
├── data/                    # 本地数据目录，不提交真实业务数据
│   ├── raw/                 # 上传的原始 Excel/CSV 文件，不提交
│   ├── processed/           # 清洗后的中间数据，不提交
│   ├── exports/             # 导出文件，不提交
│   ├── local/               # 本地 SQLite 数据库，不提交
│   └── templates/           # 虚构示例模板，可提交
├── docs/                    # 需求说明、字段字典、合规说明、接口文档
├── logs/                    # 本地运行日志，不提交
├── scripts/                 # 初始化数据库、启动后台等脚本
├── src/taobao_collector/    # FastAPI 应用、导入逻辑、数据库工具
├── tests/                   # 自动化测试
└── web/                     # Jinja2 页面模板和静态提示页
```

## 安装依赖

建议使用 Python 3.11 或更高版本。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

> `.xls` 读取依赖 `xlrd`；`.xlsx` 读取依赖 `openpyxl`；上传表单依赖 `python-multipart`。

## 启动本地网页后台

方式一：使用项目脚本启动。

```bash
python scripts/serve_admin.py
```

方式二：使用 uvicorn 启动。

```bash
PYTHONPATH=src uvicorn taobao_collector.app:app --host 127.0.0.1 --port 8000
```

启动后访问：<http://127.0.0.1:8000/>

## 初始化 SQLite 数据库

网页后台启动时会自动初始化数据库。也可以手动执行：

```bash
PYTHONPATH=src python scripts/init_db.py
```

默认数据库路径：

```text
data/local/taobao_5shop.db
```

`data/local/` 已加入 `.gitignore`，数据库文件不能提交到 GitHub。

## 上传 Excel / CSV

1. 打开 <http://127.0.0.1:8000/upload>。
2. 选择数据类型：
   - 客服咨询数据
   - 商品数据
   - 售后数据
3. 上传 `.xlsx`、`.xls` 或 `.csv` 文件。
4. 系统会把原文件保存到 `data/raw/`。
5. 系统读取字段、执行基础清洗、写入 SQLite。
6. 打开 <http://127.0.0.1:8000/preview> 查看前 50 行导入结果。

## 示例模板

示例模板位于 `data/templates/`，只能使用虚构数据：

- `customer_questions_template.csv`：客服咨询数据模板。
- `products_template.csv`：商品数据模板。
- `aftersales_template.csv`：售后数据模板。

模板字段支持英文标准字段，也支持部分中文字段映射，例如：

| 中文字段 | 标准字段 |
| --- | --- |
| 店铺名称 | `shop_name` |
| 商品ID | `product_id` |
| 商品标题 | `product_title` |
| SKU | `sku_name` |
| 客户问题 | `customer_question` |
| 问题时间 | `question_time` |
| 客服名称 | `service_agent` |
| 问题类型 | `question_type` |
| 是否售后相关 | `is_after_sales` |
| 是否影响成交 | `affects_conversion` |
| 建议处理动作 | `suggested_action` |

## 数据库表

V1 创建以下数据表：

- `shops`：店铺基础信息。
- `products`：商品数据。
- `customer_questions`：客服咨询数据。
- `aftersales`：售后数据。
- `daily_reports`：运营日报预留表。

完整结构见 `database/schema.sql`。

## 不能提交到 GitHub 的内容

`.gitignore` 已覆盖以下内容：

- `data/raw/`
- `data/processed/`
- `data/exports/`
- `data/local/`
- `*.xlsx`
- `*.xls`
- `*.csv`（只有 `data/templates/*.csv` 例外）
- `.env`、`.env.*`（只有 `.env.example` 例外）
- SQLite 数据库文件：`*.sqlite`、`*.sqlite3`、`*.db`
- 真实客服数据、真实客户聊天记录、真实订单/售后数据

提交前请确认仓库中只包含代码、文档、虚构模板和 `.gitkeep` 占位文件。

## 测试和检查

```bash
python -m compileall src
python -m compileall scripts
pytest -q
```

如果依赖尚未安装，请先执行 `python -m pip install -r requirements.txt`。

## 第二阶段说明

第二阶段 V1 同步说明见 `docs/v1_excel_csv_import_backend.md`，其中包含本地启动、上传流程、数据库路径和不提交真实数据的目录清单。

## 下一阶段建议

- 商品问题库：按商品、SKU、问题类型聚合高频问题。
- 运营日报：根据 `customer_questions` 和 `aftersales` 自动生成每日汇总。
- 导出功能：把预览和日报导出为 Excel。
- 字段配置：将字段映射做成可配置文件。
- 数据校验：增加更详细的行级错误报告和重复数据处理策略。
