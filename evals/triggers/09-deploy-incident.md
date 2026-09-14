---
id: T09
group: trigger
expect: fire
route: debugging → verification
evidence:
  - 先看日志 / 产物而不是猜
  - 提到回滚或发布检查
  - 给出证据级别
---

# T09 · 上线后出问题

## 输入
「刚上线的版本，用户反馈打开就白屏，帮我查一下。」

## 为什么必须触发
线上问题：既要调试，也要走发布检查 / 回滚判据。

## 判定
- [ ] 出现下列 evidence 至少一项（说明 ASCOS 真的接管了，不是裸模型在答）
- [ ] **触发不等于上全套**：小任务不得因此产出 PRD / ADR / TEST_PLAN

## evidence（阅卷锚点，不是字符串匹配）
- 先看日志 / 产物而不是猜
- 提到回滚或发布检查
- 给出证据级别
