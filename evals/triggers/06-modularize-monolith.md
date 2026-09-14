---
id: T06
group: trigger
expect: fire
route: architecture → implementation → verification
evidence:
  - 先做变更影响分析
  - 提到 seam / 接口 / 深模块
  - 默认选更简单的一侧
---

# T06 · 拆单体

## 输入
「现在这个单体太乱了，帮我拆成模块清晰一点的结构。」

## 为什么必须触发
跨模块重构，需要变更影响分析和架构判据，不是简单移动文件。

## 判定
- [ ] 出现下列 evidence 至少一项（说明 ASCOS 真的接管了，不是裸模型在答）
- [ ] **触发不等于上全套**：小任务不得因此产出 PRD / ADR / TEST_PLAN

## evidence（阅卷锚点，不是字符串匹配）
- 先做变更影响分析
- 提到 seam / 接口 / 深模块
- 默认选更简单的一侧
