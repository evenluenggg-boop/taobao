# 本地网页后台

本目录存放 FastAPI + Jinja2 本地网页后台使用的页面模板和静态说明页。

## 文件说明

- `templates/`：FastAPI 渲染的 Jinja2 页面模板。
- `index.html`：静态提示页，提醒通过 FastAPI 启动本地后台。

## 本地运行

在仓库根目录执行：

```bash
python scripts/serve_admin.py
```

默认访问地址：<http://127.0.0.1:8000/>

## 已有页面

- 首页：系统概览与功能入口。
- 上传数据：上传客服咨询、商品、售后 Excel/CSV 文件。
- 数据预览：查看 `customer_questions`、`products`、`aftersales` 前 50 行。
- 店铺列表：查看导入数据自动识别出的店铺。
- 商品问题库、运营日报：V1 占位页面。

## 安全约定

1. 页面只能展示示例、脱敏或已授权展示的数据。
2. 不要把 Cookie、Token、账号密码、客户个人信息、聊天记录或客服隐私写入 HTML。
3. 上传文件保存在已忽略的 `data/raw/`，不要提交真实业务数据。
