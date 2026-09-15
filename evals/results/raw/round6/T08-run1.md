# T08-run1 —「帮我 review 一下这次的改动，看看有什么问题」

## 0. 结论先行

**审查尚未启动。** 请求缺少 `code-review` 的强制输入（diff + 基点），按 Skill 契约必须**立即报错并请求澄清**，不得静默降级为「通读代码随便点评」，也不得凭猜测挑一个提交来假装审过了。

## 1. 判定与路由

| 项 | 结论 |
|---|---|
| 是否命中本 Skill | 命中。用户要求「代码审查」，属于 description 中明确列出的场景 |
| 任务级别 | 暂无法定级。级别依赖 diff 的改动范围（见路由表「信号」列），输入缺失故未判定 |
| 调用链 | 路由表「只要求代码审查」→ `code-review` → `verification` |
| 前置动作 | 本仓库为已有代码库，进入链路前需消费 `CONTEXT.md` / `repository-awareness`；因输入缺失，与主体审查一并挂起 |

`code-review` 契约（SKILL.md 第 86 行）：输入 = **diff + 基点**；失败状态 = **基点不可解析或 diff 为空 → 立即报错**。

## 2. 事实 / 假设 / 建议（严格分开）

### 事实（已核验，来源：本地 git）
- 当前分支：`main`
- `git status --porcelain` 只有一条：`?? evals/results/raw/round6/` —— 即**没有任何已修改或已暂存的跟踪文件改动**（该未跟踪目录是本次评测的产物落盘位置）
- 最近 5 条提交（由新到旧）：
  - `310d9f3` fix(skill): cover in-code UI copy and config edits in the trigger description
  - `255f660` test(evals): rerun must-fire cases 2 and 3 under the faithful arm
  - `293b35e` fix(evals): measure triggering without force-loading the skill
  - `209c848` test(evals): record the first real trigger comparison run
  - `6f304c5` feat(evals): add the eval harness and a 20-case trigger suite

### 假设（未核验，不作为结论）
- 「这次的改动」最可能指最近一次提交 `310d9f3`，或围绕 evals 的那一串提交（`6f304c5..310d9f3`）。
- **这只是概率排序，不是事实。** 在得到确认前，我不会据此产出审查结论。

### 建议（需要你拍板）
请从下面选一种给我，任选其一即可解封：

1. **单个提交**：`310d9f3`（或你指定的 SHA）
2. **提交区间**：例如 `6f304c5..310d9f3`（evals 那一串）
3. **分支 / PR**：例如 `main..<feature-branch>` 或 PR 编号
4. **未提交的工作区改动**：当前为空，若有请告诉我是否包含未跟踪文件（目前只有评测结果目录）
5. **stash / 补丁文件**：贴 diff 或给路径

如果你本意就是「审 HEAD 那一次提交」，回一句「就审 310d9f3」我立刻开始。

## 3. 确认输入后我会交付什么

按 `code-review` 双轴报告 + `verification` 收口：

1. **Standards 轴** — 工程规范：安全、鉴权、输入校验、数据完整性、错误处理、可观测性、测试覆盖、命名与结构一致性。
2. **Spec 轴** — 是否符合本次改动的真实意图（对照提交信息与需求），有无过度设计、有无遗漏的联动文档（CHANGELOG / README / RELEASE_NOTES / SKILL.md 索引）。
3. **证据** — 每条问题附 `文件:行号` 与判定依据；区分「必须改 / 建议改 / 可选」。
4. **验证结论** — 若涉及可执行验证（build / test / lint / `scripts/validate_skill.py`），给出**真实命令与真实输出**；无证据则标注「未验证」，不声称通过。
5. **剩余风险清单** — 必附。

## 4. 本次的剩余风险清单

| # | 风险 | 等级 | 说明 |
|---|---|---|---|
| R1 | 审查范围错误 | 高 | 未确认 diff/基点就开工，可能审错对象，产出全部作废 |
| R2 | 未提交改动被漏审 | 中 | 若「这次的改动」含工作区未提交内容，当前工作区除评测产物外为空，需你确认是否还有其他来源（stash / 其他 worktree） |
| R3 | 仓库上下文未消费 | 中 | `CONTEXT.md` / `repository-awareness` 未纳入，历史约束与既有约定可能遗漏 |
| R4 | 结论被误读为已完成 | 中 | 本文档**不是**审查报告，只是阻断项上报；请勿据此认为改动已通过审查 |

---

**状态：BLOCKED — 等待用户提供 diff 与基点。未产出任何审查结论（不虚构、不猜测、不刷分）。**
