---
id: T07
group: trigger
expect: fire
route: requirements → implementation → verification
evidence:
  - 提到空数据 / 加载中 / 报错 / 无权限
  - 提到深翻页或索引
  - 有真实验证命令
---

# T07 · 列表分页搜索

## 输入
「给订单列表加分页和关键字搜索。」

## 为什么必须触发
中任务，需要补全边界（深翻页、空结果、注入）并验证。

## 判定
- [ ] 出现下列 evidence 至少一项（说明 ASCOS 真的接管了，不是裸模型在答）
- [ ] **触发不等于上全套**：小任务不得因此产出 PRD / ADR / TEST_PLAN

## evidence（阅卷锚点，不是字符串匹配）
- 提到空数据 / 加载中 / 报错 / 无权限
- 提到深翻页或索引
- 有真实验证命令
