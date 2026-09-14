---
id: E07
group: medium
expect: pass
route: requirements → implementation → verification
needs_repo: false
---
# E07 · 列表分页与搜索

**级别**：medium ｜ **期望路由**：`requirements` → `implementation` → `verification`

## 输入
「订单列表现在一次返回全部，加分页和按订单号搜索。」

## 期望行为
- 补全：分页边界（首/末页、超大 page）、搜索空串与特殊字符、排序稳定性、总数是否已存在接口。
- 后端分页而非前端切数组（除非数据量明确很小并说明）。
- 搜索走参数化查询，索引评估。
- 前端：loading / 空结果 / 报错三态。

## 判定（任一为否即 Fail）
- [ ] 分页在后端，不是拉全量再切
- [ ] 处理了空搜索串与特殊字符
- [ ] 前端有空结果与错误态
- [ ] 说明了索引影响
- [ ] 没有为列表引入 Elasticsearch
