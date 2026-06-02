# 示例数据模板

本目录只存放**虚构示例数据模板**，用于说明 Excel/CSV 导入版 V1 期望的数据字段。这里的店铺名称、商品标题、客服昵称、问题内容、售后原因和统计数值均为占位示例，不对应任何真实淘宝店铺、商品、客户、客服人员或业务数据。

## V1 导入模板

- `customer_questions_template.csv`：客服咨询数据模板。
- `products_template.csv`：商品数据模板。
- `aftersales_template.csv`：售后数据模板。

## 早期结构参考模板

- `shop_public_info.csv`：店铺公开信息与公开客服入口字段模板。
- `customer_service_metrics.csv`：授权后台导出的客服统计字段模板。

## 使用约定

1. 不要把真实店铺、客户、客服个人信息、商品数据、订单数据、聊天记录或业务统计数据提交到本目录。
2. 真实后台导出文件应放在 `data/raw/`，该目录默认被 `.gitignore` 忽略。
3. 如需增加字段，请先更新本目录模板和 `README.md` 中的字段说明，再实现对应的数据处理逻辑。

- `customer_service_metrics_template.csv`：客服绩效数据模板，包含响应、接待、销售额、回复率和答问比等虚构示例字段。
