---
name: context-model
description: 领域语言与 CONTEXT.md：在已有仓库中建立并消费共享词汇表，纠正需求补全的歧义。
---

# 领域语言与 CONTEXT.md（Domain Model）

在已有代码库中工作时，建立并消费一份 `CONTEXT.md` 共享词汇表，让 Skill 的术语、测试名、接口名与假设都对齐项目的**真实领域语言**。这直接服务于「需求默认不完整」信念：精确的领域模型，正是缺口被正确补全的方式。

## 何时建立 / 更新
- 在某仓库的首次任务、且该仓库没有 `CONTEXT.md` 时 → 新建。
- 发现同一概念有多种叫法、或用户用语与代码术语冲突时 → 更新。
- 保持**小**。只在术语真正影响实现 / 沟通时才收录。

## 格式（建议，详见 `templates/CONTEXT.md`）
```markdown
# CONTEXT.md

## 术语表
| 术语 | 含义 | 避免的叫法 |
|------|------|-----------|
| 订单 Order | 用户一次结算的单元 | 单子、bill |
| 履约 Fulfillment | 订单从支付到发货的流程 | 发货、配送（易混） |

## 关系
- 一个 Order 拥有多个 Fulfillment。
- Fulfillment 状态由 Payment 结果驱动。

## 已标记的歧义
- "发货" 曾同时指 Fulfillment 与物流单；已统一为 Fulfillment。
```

## 如何被消费
- `repository-awareness.md`：感知代码库时优先读 `CONTEXT.md`，用其术语理解既有组件 / API。
- `testing.md` / TDD：测试与用例命名使用领域词汇（如 `user_can_checkout_with_valid_cart`），而非内部实现名。
- `skills/architecture` / `API_SPEC`：接口与字段名采用领域术语，避免同物异名。
- 需求补全与对抗性审查时，用术语表核对用户口述与系统概念是否一致。

> **从零项目**：在领域实体确定之前**不建**（没有真实领域语言可记，硬写就是编词汇表）；
> 但**第一个实体或核心概念确定后必须建**。
> 「不必强求」指的是**时机**，不是「可以不建」——不要在需求澄清完、术语已经定下来之后
> 还拿这句话当不建的理由。
