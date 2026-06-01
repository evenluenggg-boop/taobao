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

## PR 收尾检查结果

本 PR 收尾时已核对以下内容：

- README 中的启动命令与实际脚本一致：`python scripts/serve_admin.py`。
- README 中的 uvicorn 启动命令与 FastAPI 应用路径一致：`PYTHONPATH=src uvicorn taobao_collector.app:app --host 127.0.0.1 --port 8000`。
- 默认数据库路径与代码一致：`data/local/taobao_5shop.db`。
- 上传页面路径与代码一致：`/upload`。
- 示例模板文件均存在：`customer_questions_template.csv`、`products_template.csv`、`aftersales_template.csv`。
- `.gitignore` 已覆盖本地上传、导出、中间数据、本地数据库、Excel/CSV 上传文件、`.env` 文件和 SQLite/DB 文件。

## 已知限制

- 商品问题库和运营日报目前只是占位页面，暂未实现完整分析逻辑。
- 当前系统只做本地导入和预览，不接淘宝开放平台接口，不做爬虫。
- 当前基础测试会在缺少 FastAPI 或 pandas 的环境中跳过相关测试；安装 `requirements.txt` 后可运行完整测试。
- `.xls` 文件读取依赖 `xlrd`，实际使用前需要确保依赖已安装。
