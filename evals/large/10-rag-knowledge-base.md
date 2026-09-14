---
id: E10
group: large
expect: pass
route: requirements → architecture → implementation → verification
needs_repo: false
---
# E10 · RAG 知识库

**级别**：large ｜ **期望路由**：`requirements` → `architecture` → `implementation` → `verification`

## 输入
「给我们内部文档做个 RAG 问答。」

## 期望行为
- 先对齐领域术语（`CONTEXT.md`），再定文档切片 / 检索 / 重排 / 生成链路。
- 补全用户没说的：召回质量如何评测（评测集）、幻觉兜底与引用溯源、权限过滤（不能检索到无权限文档）、成本与延迟预算、增量更新与重建。
- 反过度设计：先用现有数据库 + 单向量表起步，不默认上独立向量库 / 图数据库；引入要写明收益与成本。
- 变更影响：文档入口、权限体系、既有搜索。

## 判定（任一为否即 Fail）
- [ ] 有评测集或明确的召回质量度量方式
- [ ] 检索结果做了权限过滤
- [ ] 回答带引用 / 溯源，不是裸生成
- [ ] 说明了成本与延迟预算
- [ ] 没有默认堆砌向量库 + 重排服务 + Agent 编排
- [ ] 附了风险清单（幻觉、越权检索、数据泄露）
