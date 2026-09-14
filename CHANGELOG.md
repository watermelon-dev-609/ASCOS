# Changelog

## 1.1.0
架构重构：从「大 Skill + 大量 reference」升级为「编排器 + 能力 Skill」。

**新增**
- `skills/requirements`、`architecture`、`implementation`、`debugging`、`code-review`、`verification` 六个能力 Skill，每个带 front-matter、契约（输入 / 输出 / 失败状态）与反模式
- `SKILL.md` 的 **Skill Routing Table**：按用户意图直接路由到调用链
- `evals/` 回归测试集：21 个用例（small / medium / large / bugs / adversarial）+ 通用评分表
- `scripts/validate_skill.py`：结构校验（front-matter、命名、死链、孤儿 Skill、必需章节、体积、重复规则、元数据）
- `references/engineering-standards.md`：跨技术栈工程硬约束摘要（从 `SKILL.md` 外移）
- 深模块词汇与三条硬判据（删除测试 / 接口即测试面 / 一个 adapter 是假 seam）进入 `skills/architecture`
- 调试流程重写为「反馈环优先」：能变红的紧命令 → 最小化 → 3–5 个可证伪假设 → 插桩 → 修复 → 回归测试 → 清理
- 调试增加**证据分级与降级**（L0 红环 / L1 灰环 / L2 静态推理），核心原则：**证据不足 ≠ 停止思考，证据不足 = 降低结论强度**
- L1 / L2 均为**自动降级，不阻断分析、不需要用户许可**（与"能推进就不狂问"一致）；降级后必须标注证据级别 + 置信度 + 支撑证据，禁称"已定位 / 已修复 / 已验证"，并写明升级路径
- **L2 下不得直接修改生产代码**：顺序是 L2 → 假设 → 补观测 → L1 → L0 → 再修
- 停下来问用户的条件从"证据不足"改为"**下一步不可逆**"（生产写操作 / 删除迁移 / 收费资源 / 对外发消息 / 敏感权限）
- `evals/bugs/22-no-repro-degradation.md`：覆盖「只有日志、无法复现」场景，含双向判据 —— 停住 Fail，L2 直接改生产代码同样 Fail

**变更**
- `SKILL.md` 瘦身为编排器：只保留触发、判断、路由、验收；核心信念与不可妥协规则保留，工程规范细节外移
- 能力型文档上移为 Skill 并删除原文件：`architecture`、`debugging`、`verification`、`quality-gate`、`definition-of-done`、`code-review`
- `references/` 收敛为纯知识层，全部补上 front-matter（name / description）
- `AGENTS.md`：去掉不存在的 RFC 模板引用，改为 PRD + API_SPEC，并要求提交前跑 Validator
- `repository-awareness.md`：明确先读 `CONTEXT.md`

**修复**
- `AGENTS.md` / `CHANGELOG` 都引用了不存在的 RFC 模板（死链）
- `context-model.md` 要求感知阶段读 `CONTEXT.md`，但 `repository-awareness.md` 未提及（链路断开）

## 1.0.0
- Added canonical SKILL.md
- Added dynamic role dispatch
- Added planning, decision, research, reflection and quality engines
- Added engineering departments
- Added coding, API, security, testing and deployment standards
- Added PRD, ADR, API, test and release templates
- Added adapters for major AI coding assistants
