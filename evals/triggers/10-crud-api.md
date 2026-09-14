---
id: T10
group: trigger
expect: fire
route: requirements → implementation → code-review → verification
evidence:
  - 先定接口契约
  - 提到参数校验或错误码统一
  - 有测试三场景
---

# T10 · 加一个 CRUD 接口

## 输入
「加一个商品的增删改查接口。」

## 为什么必须触发
契约先行的典型中任务，不该一上来就写 controller。

## 判定
- [ ] 出现下列 evidence 至少一项（说明 ASCOS 真的接管了，不是裸模型在答）
- [ ] **触发不等于上全套**：小任务不得因此产出 PRD / ADR / TEST_PLAN

## evidence（阅卷锚点，不是字符串匹配）
- 先定接口契约
- 提到参数校验或错误码统一
- 有测试三场景
