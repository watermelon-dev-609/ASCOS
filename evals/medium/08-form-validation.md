---
id: E08
group: medium
expect: pass
route: requirements → implementation → verification
needs_repo: false
---
# E08 · 表单校验与防重复提交

**级别**：medium ｜ **期望路由**：`requirements` → `implementation` → `verification`

## 输入
「用户反馈提交订单表单能连点好几次，生成了重复订单。」

## 期望行为
- 前端：提交后禁用 / 防抖，校验前置，报错信息明确。
- **后端**：幂等键或唯一约束兜底 —— 前端防重复不是安全边界。
- 覆盖异常：网络超时后重试、并发重复提交。
- 明确事务边界，避免部分写入。

## 判定（任一为否即 Fail）
- [ ] 后端有幂等 / 唯一约束，不只靠前端按钮禁用
- [ ] 覆盖了「超时后重试」这一路径
- [ ] 有并发重复的测试或明确说明如何验证
- [ ] 事务边界清晰，无半成品数据
