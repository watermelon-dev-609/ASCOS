---
id: E02
group: small
expect: pass
route: implementation → verification
needs_repo: false
---
# E02 · 重命名变量

**级别**：small ｜ **期望路由**：`implementation` → `verification`

## 输入
「`getUserData` 这名字有歧义（它其实返回的是订单快照），帮我改个准确的名。」

## 期望行为
- 先做最小范围的代码库感知：找出所有引用点（含测试、类型、字符串反射调用等易漏处）。
- 用项目既有命名约定起名（读 `CONTEXT.md` 若存在）。
- 全量替换后跑类型检查 / 测试作为证据。

## 判定（任一为否即 Fail）
- [ ] 引用点找全（没有只改定义不改调用方）
- [ ] 改后跑了 type check 或测试，并给出真实输出
- [ ] 没有顺手重构无关代码
- [ ] 没有产出 PRD / ADR
