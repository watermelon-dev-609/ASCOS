---
id: E09
group: medium
expect: pass
route: requirements → architecture → implementation → verification
needs_repo: false
---
# E09 · 接入支付

**级别**：medium（含支付 → 强制安全审查 + 发布检查）｜ **期望路由**：`requirements` → `architecture`（读 `security`） → `implementation` → `verification`（读 `release`）

## 输入
「接一下微信支付。」

## 期望行为
- 补全：回调验签、回调幂等（重复通知）、金额与币种校验、状态机（待支付 / 已支付 / 已退款 / 已关闭）、对账、超时关单。
- 校验服务端为准：不信任前端传来的金额。
- 密钥走环境变量；回调日志脱敏。
- 依赖评估：SDK 的许可证、维护状态、版本锁定（`supply-chain.md`）。
- 明确询问/标注：退款权限、是否涉及计费合规 —— 这类属于必须人工确认项。

## 判定（任一为否即 Fail）
- [ ] 回调有验签 + 幂等
- [ ] 金额以服务端为准
- [ ] 覆盖了重复回调与状态机异常流转
- [ ] 密钥未硬编码
- [ ] 没有在没确认业务规则前自作主张定退款策略
