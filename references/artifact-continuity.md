# 文档连续性（Artifact Continuity）— P1

PRD、ADR、API_SPEC、TEST_PLAN 不是互相独立的文件，而是上下游链路。

## 关系
- **PRD**：需求源（含需求补全记录）。
- **ADR**：记录关键架构决策及取舍（对应 PRD 中的重大技术选择）。
- **API_SPEC**：接口对应 PRD 的功能与 ADR 的约束。
- **TEST_PLAN**：用例对应 PRD 的验收标准与风险清单。

## 规则
- 需求变更时，同步更新下游文档（PRD → ADR → API_SPEC → TEST_PLAN）。
- 交付前确认文档与实现一致，避免文档与代码脱节。
- 小任务可省略部分模板，但 PRD 的「需求补全记录」与交付「风险清单」建议始终保留。
