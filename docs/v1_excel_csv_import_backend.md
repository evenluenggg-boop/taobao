# 第二阶段 V1：Excel / CSV 导入版本地系统

本文档用于说明本分支同步到 GitHub 的第二阶段 V1 功能范围。当前版本仍然只面向本地运行，不接淘宝接口，不做爬虫，不做 AI 客服。

## 功能范围

- 本地 FastAPI 网页后台：`http://127.0.0.1:8000/`。
- 首页名称：**淘宝5店铺数据分析系统**。
- 功能入口：上传数据、数据预览、店铺列表、商品问题库、运营日报。
- 上传类型：客服咨询数据、商品数据、售后数据。
- 文件格式：`.xlsx`、`.xls`、`.csv`。
- 入库流程：保存上传文件到 `data/raw/`，读取表格字段，执行字段清洗和中文字段映射，写入 SQLite。
- 预览范围：`customer_questions`、`products`、`aftersales` 前 50 行。
- 占位功能：商品问题库、运营日报仅保留页面入口，完整分析放到下一阶段。

## 本地启动

```bash
python -m pip install -r requirements.txt
python scripts/serve_admin.py
```

访问：<http://127.0.0.1:8000/>

也可以直接使用 uvicorn：

```bash
PYTHONPATH=src uvicorn taobao_collector.app:app --host 127.0.0.1 --port 8000
```

## 上传 Excel / CSV

1. 打开 <http://127.0.0.1:8000/upload>。
2. 选择数据类型：客服咨询数据、商品数据或售后数据。
3. 选择 `.xlsx`、`.xls` 或 `.csv` 文件。
4. 点击“上传并导入”。
5. 打开 <http://127.0.0.1:8000/preview> 预览导入结果。

## 数据库位置

默认 SQLite 数据库文件：

```text
data/local/taobao_5shop.db
```

该目录已被 `.gitignore` 忽略，不应提交数据库文件。

## 不提交真实数据的目录和文件

以下内容不会提交到 GitHub：

- `data/raw/`
- `data/processed/`
- `data/exports/`
- `data/local/`
- `.env`、`.env.*`
- `*.xlsx`
- `*.xls`
- `*.csv`（仅 `data/templates/*.csv` 虚构模板例外）
- `*.sqlite`、`*.sqlite3`、`*.db`

请勿提交真实业务数据、真实客服数据、真实客户聊天记录、真实订单数据或真实售后数据。
