---
id: T08
group: trigger
expect: fire
route: code-review → verification
evidence:
  - 先固定对比基点
  - 按 Standards / Spec 分轴
  - 缺陷优先排序
---

# T08 · 审查这个 diff

## 输入
「帮我 review 一下这次的改动，看看有什么问题。」

## 为什么必须触发
明确的代码审查请求，走双轴审查（Standards vs Spec）。

## 判定
- [ ] 出现下列 evidence 至少一项（说明 ASCOS 真的接管了，不是裸模型在答）
- [ ] **触发不等于上全套**：小任务不得因此产出 PRD / ADR / TEST_PLAN

## evidence（阅卷锚点，不是字符串匹配）
- 先固定对比基点
- 按 Standards / Spec 分轴
- 缺陷优先排序
