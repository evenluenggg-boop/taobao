# scripts

存放本地开发和运维辅助脚本。

## 当前脚本

- `init_db.py`：初始化 SQLite 数据库，默认路径为 `data/local/taobao_5shop.db`。
- `serve_admin.py`：启动 FastAPI 本地网页后台，默认访问地址为 <http://127.0.0.1:8000/>。

## 使用示例

```bash
PYTHONPATH=src python scripts/init_db.py
python scripts/serve_admin.py
```

脚本不得硬编码真实账号、Cookie、Token、客服隐私或店铺业务数据。
