---
name: roles
description: 13 个专家视角（角色）的清单、激活信号与组合模式；视角是思维框架而非独立 Agent。
---

# 动态角色（视角切换指南）

角色不是独立 Agent，而是 AI 在思考同一任务时可以切换的「专家视角」。目标是用不同专业框架审查问题，避免单一视角盲区。

## 角色清单与激活信号

| 角色 | 关注点 | 典型激活信号 |
|------|--------|--------------|
| Product（产品） | 用户价值、范围、验收标准 | 新功能、需求模糊、需要明确「做成什么」 |
| UX / 产品体验 | 交互、可用性、四态 | 页面、表单、用户操作流程 |
| Architect（架构） | 结构、模块边界、技术选型 | 多模块、需要分层/边界/决策 |
| Frontend（前端） | 组件、状态、渲染、体验 | 页面、UI、交互 |
| Backend（后端） | 业务逻辑、接口、IO、事务 | API、服务端逻辑 |
| Database（数据库） | 数据模型、查询、一致性 | 存储、迁移、性能 |
| AI Engineer | 模型 / RAG / 提示 / 评测 | RAG、智能体、模型集成 |
| Data Engineer | 数据管道、向量化、ETL | 知识库、批处理、特征 |
| Security（安全） | 鉴权、授权、注入、XSS、脱敏 | 登录、权限、外部输入、敏感数据 |
| QA（测试） | 正常 / 边界 / 异常覆盖 | 任何交付前的验证 |
| DevOps | 部署、CI/CD、可观测性 | 上线、运维、监控 |
| Reviewer | 代码质量、可维护性 | 设计 / 编码后的审查 |
| CTO | 全局权衡、最终放行 | 流程末端的最终检查 |

## 组合模式（参考）
- 登录 / 权限 → Architect + Backend + Security + QA
- 页面 / 前端功能 → Product + UX + Frontend + Reviewer
- 后端 API → Architect + Backend + Database + Security + QA
- RAG / 知识库 → AI Engineer + Data Engineer + Backend + Security + QA
- 全栈应用 → Product → UX → Architect → Database → Backend → Frontend → Security → QA → DevOps → Reviewer → CTO
- 部署上线 → DevOps + Backend + QA + Reviewer
- 简单 Bug / 文案 → Engineer + Reviewer（精简约版）

## 使用方式
1. 在「自动选择角色」步骤，根据需求从上述清单挑出**必要**角色。
2. 在思考和输出时显式标注当前视角（如「【安全视角】这里需要校验 token 并做服务端权限判断」），让切换可见但不冗余。
3. 小任务只激活 1–3 个角色；不要为简单需求拉满全部角色。

## 角色数量边界
当前固定 **13 个角色**已足够覆盖常见开发任务，**不再新增角色**。需要新能力时，优先扩展既有角色的视角或新增 reference 文档，而非新增角色。

## 输出自适应（Output Adaptation）
输出裁剪规则、必附风险清单、虚构分数禁令统一见 `references/non-negotiables.md`，本章不再复述。
