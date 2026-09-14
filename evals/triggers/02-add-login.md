---
id: T02
group: trigger
expect: fire
route: requirements → architecture → implementation → verification
evidence:
  - 先补全需求再说实现
  - 提到安全审查
  - 提到会话 / 口令存储 / 防枚举
---

# T02 · 加登录

## 输入
「给我这个项目加个登录功能。」

## 为什么必须触发
中任务 + 含鉴权，按分级表强制安全审查。这是 ASCOS 最典型的场景。

## 判定
- [ ] 出现下列 evidence 至少一项（说明 ASCOS 真的接管了，不是裸模型在答）
- [ ] **触发不等于上全套**：小任务不得因此产出 PRD / ADR / TEST_PLAN

## evidence（阅卷锚点，不是字符串匹配）
- 先补全需求再说实现
- 提到安全审查
- 提到会话 / 口令存储 / 防枚举
