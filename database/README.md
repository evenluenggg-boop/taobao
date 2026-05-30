# 数据库结构

本目录存放项目的基础数据库结构定义。当前默认使用 SQLite 作为本地开发和小规模数据整理的落地格式，后续如需迁移到 MySQL/PostgreSQL，可基于 `schema.sql` 中的表结构调整字段类型和约束。

## 文件说明

- `schema.sql`：基础表结构、外键、唯一约束和常用索引。

## 表结构概览

| 表名 | 用途 |
| --- | --- |
| `shops` | 5 个自有或已授权店铺的基础信息。 |
| `customer_service_agents` | 店铺下公开或授权维护的客服别名与角色信息。 |
| `shop_public_snapshots` | 店铺公开信息的采集快照，例如公开评分、商品数量、客服入口。 |
| `customer_service_metrics` | 授权后台导出的客服接待、响应、转化等统计指标。 |
| `collection_jobs` | 每次采集、导入或清洗任务的执行记录。 |
| `collection_job_events` | 任务执行过程中的事件日志。 |

## 安全约定

1. 不要在数据库中保存 Cookie、Token、账号密码、App Secret 或登录态。
2. 不要保存真实客户个人信息、聊天记录或未授权客服个人隐私。
3. 本地生成的 SQLite 数据库文件应放在 `data/processed/`，该目录默认被 `.gitignore` 忽略。
4. 提交结构变更时，只提交 SQL、代码和文档，不提交真实数据库文件。
