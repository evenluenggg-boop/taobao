# 数据库结构

本目录存放 Excel / CSV 导入版 V1 的 SQLite 数据库结构。默认本地数据库路径为 `data/local/taobao_5shop.db`，该目录已被 `.gitignore` 忽略，数据库文件不能提交到 GitHub。

## 文件说明

- `schema.sql`：V1 表结构、检查约束和常用索引。

## 表结构概览

| 表名 | 用途 |
| --- | --- |
| `shops` | 从导入数据中自动识别的店铺基础信息。 |
| `products` | 上传的商品数据，包含商品 ID、标题、SKU、价格和来源文件名。 |
| `customer_questions` | 上传的客服咨询数据，包含客户问题、问题时间、客服、问题类型、是否售后相关、是否影响成交、建议动作和来源文件名。 |
| `aftersales` | 上传的售后数据，包含售后类型、售后原因、售后时间和来源文件名。 |
| `daily_reports` | 运营日报预留表，本阶段只建表，不实现完整自动分析。 |

## 初始化数据库

在仓库根目录执行：

```bash
PYTHONPATH=src python scripts/init_db.py
```

也可以通过网页后台首次启动自动初始化。

## 安全约定

1. 不要在数据库中保存 Cookie、Token、账号密码、App Secret 或登录态。
2. 不要保存真实客户聊天记录、未授权客服个人隐私或未授权订单/售后数据。
3. 本地生成的 SQLite 数据库文件应放在 `data/local/`，该目录默认被 `.gitignore` 忽略。
4. 提交结构变更时，只提交 SQL、代码和文档，不提交真实数据库文件。
