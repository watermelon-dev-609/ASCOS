# Changelog

## 1.2.2 — 修掉 T01 的欠触发（description 覆盖面）

只改 `SKILL.md` 的 `description`，改两处，都只针对 T01 的根因：

| 位置 | 改前 | 改后 |
|---|---|---|
| `Use when` | 用户要写码、改码… | 用户要写码、改码**（包括代码中的 UI 文案、配置等局部修改）**… |
| `Not for` | 纯文案润色… | **与代码或软件配置无关的**纯文案润色… |

**为什么**：Round 5 实测 T01「把按钮文案从 Submit 改成 Create order」**3/3 欠触发**，
其中一次把原因直说了 —— `Not for` 里写着「纯文案润色」，模型于是把改按钮文案读成
文案润色，把自己排除掉了。只加 `Use when` 的限定会和既有 `Not for` 打架，所以第二处一起改。

**明确没做**：`code-review` 覆盖面（T08 的缺口）**没碰**。T08 是 1/3，未达 ≥2/3 门槛，
且 T01 与 T08 是两个独立缺口，不合并成一条修复。

**完整 20 例回归（42 次全新子会话，忠实臂 M2）**：

| 判据 | 要求 | 实测 |
|---|---|---|
| T01 恢复 | ≥2/3 触发 | **3/3**（干净，非边界） |
| must-not-fire 无新增 | 30 次 0 误触发 | **0/30** |
| 是否加载了 SKILL.md（rubric 无关） | — | **0/30** |

T01 触发后仍正确**不产出** PRD / ADR / TEST_PLAN —— 触发不等于上全套。

**同轮生效的两条评测规则**（都源于 Round 5 暴露的问题）：
- **ASCOS 特有交付物只能作为 corroboration，不能单独构成 activation evidence。**
  裸模型也能写一张风险表；必须同时有 Primary evidence（声明加载 / 路由链 / 能力特异形态）。
- **有效样本 <2 次判定为 `inconclusive`**，不进命中率、不进修复队列。
  T05 曾有 2 次 `invalid` + 1 次有效，单次观测撑不起任何稳定性结论。

**归档**：修复前的 60 条 `with_skill` 触发记录移出 `records.jsonl`，
存到 `evals/results/round4-5-prefix.jsonl` —— Round 6 复用 run 1/2/3，
直接覆盖会把两个不同配置的数据混在一起。

## 1.2.1 — 触发评测的装载方式修正
不新增规则，只修正「怎么测触发」——以及撤回一个基于错误测量得出的结论。

**背景**：v1.2.0 的首次触发跑（Round 3）报出 T18 / T20 两例 `risk-tail` 误触发。
本轮发现**那次测量的 with 臂搭错了**：子会话不会被注入 `AGENTS.md`，
于是当时改用显式「先读 `SKILL.md`」指令 —— 而**强制加载等于替模型做了"要不要触发"这个决定**，
抹掉的正是被测变量。

**三种装载方式对照**（同一批 20 例、同一判分标准）：

| 机制 | must-fire 命中 | must-not-fire 正确 |
|---|:--:|:--:|
| M0 无装载（子会话不注射任何东西） | 0 / 10 | 臂未建立，无意义 |
| M1 强制加载（显式要求先读 `SKILL.md`） | 10 / 10 | **2 / 10** |
| M2 忠实装载（只给 description，触发时才加载） | 7 / 10 | **30 / 30** |

**触发行为对装载方式极度敏感**（0/10 vs 10/10 vs 7/10，差异远大于任何 run 间噪声）。
结论：**跨 harness 比较触发率没有意义，除非装载方式也写进协议。**

**结果（`evals/runs/2026-09-14-round4-faithful-arm.md`）**
- must-not-fire 三轮 **30/30 零误触发** → 按预先登记判据（≥2/3 才修），
  **T18/T20 不进入 v1.3 修复队列**，`non-negotiables` 的反向边界**先不加**
- must-fire 7/10，两例真实欠触发（T01 改文案、T08 review），一例环境污染物（T05 被微信支付连接器截走）
- 登记两个未决项：① 欠触发是否要修（n=1，先观察）② `misfire_shape` 分类表有个洞 ——
  4 例（T13/T15/T17/T19）出现"点名 Skill 但无分级无调用链"的范围声明，
  按用户给的示例判为 `none`，**若裁定"点名 Skill 本身即越界"则结论反转**

**新增**
- `misfire_shape` 字段（`none` / `risk-tail` / `router-language` / `PRD-overreach` /
  `DoD-overreach` / `subskill-name-leak`）：只记录误触发**长什么样**，不评分。
  must-not-fire 记录**必须**带，且与 verdict 矛盾时 `ingest` / `check` 双向拒绝
- `report` 新增 Misfire shapes 表：按 variant 分桶（跨臂混算会让 without 臂的噪声
  污染 with 臂的修复决策），并列出涉及用例 —— "跨用例同 shape"这条判据需要看是哪些用例
- `report` 在 Behaviour delta 下加永久警示：must-fire 那一半的 delta **按定义成立**，
  只能证明两臂隔离有效，不能证明 ASCOS 让答案变好
- `scripts/test_eval_tools.py`（19 项单测，已进 CI）：pass@k 边界、frontmatter 不被正文
  水平线截断、阅卷备注剔除、`misfire_shape` 的五种非法组合

**修复**
- `_misfire_section` 的 tally 原先跨臂混算
- Round 3 运行文档里新增章节把有序列表打断，第 5 条被孤立
- Round 3 的 with 臂记录移出 `records.jsonl`，归档为 `round3-pilot-forced-arm.jsonl`；
  `records.jsonl` 是唯一真源，其余是归档快照

## 1.2.0 — Eval Harness
规则冻结后的第一个版本：**不新增任何规则**，只把「ASCOS 到底有没有改变行为」从感觉变成可重复测量。

**新增**
- **`scripts/eval_harness.py`**，四个子命令：
  - `check` —— 语料体检（id 唯一 / group 合法 / expect 有效 / 路由指向真实 Skill /
    判定与输入存在 / 触发组至少 10+10 / 已灌入的记录引用存在的用例）。CI 跑这个
  - `prompt` —— 导出可直接发送的输入，支持 `--id` / `--group` / `plain` / `jsonl`
  - `ingest` —— 灌入运行记录（JSONL），校验 case / variant / run / verdict 一致性，
    重复 `(case, variant, run)` 默认报错，需显式 `--replace`
  - `report` —— 聚合成 `evals/results/report.md`：命中率、**pass@k**、mean seconds / tokens、
    **Behaviour Delta**（`with_skill` − `without_skill`）
- **`evals/triggers/` 20 例触发评测**：10 例必须触发（改文案 / 加登录 / 查 Bug / 从零搭 /
  接支付 / 拆单体 / 分页搜索 / 审 diff / 上线事故 / CRUD）+ 10 例必须**不**触发
  （SQL 教程 / 解释深模块 / 润色文案 / 延期邮件 / 翻译 / rebase-vs-merge / 总结文章 /
  起名 / 会议纪要 / 库用法）。其中 T12 专门测"ASCOS 自己的术语出现在问题里"会不会误触发
- 22 个既有用例补上机器可读 frontmatter（`id` / `group` / `expect` / `route` / `needs_repo`），
  由一次性脚本从标题与「期望路由」行**抽取**，不是重打一遍，避免抄错

**修复**
- `scripts/eval_common.py` 切分正文时原先按分隔符 `split`，正文里出现 `---` 水平线就会被截断 ——
  E14 / E15 / E22 三个 fixture 用例命中，导致「判定」「输入」被判为缺失。改为按闭合分隔符的偏移量切片
- `validate_skill.py` 不再对 `evals/triggers/` 要求「期望路由」（触发用例测的是该不该接管，
  没有路由可期望），也不再把用例之间共用的判定模板行当成跨文件重复规则
- `prompt` 导出会剔除 `## 输入` 里的 `>` 引用块：那是阅卷备注，不能让 Agent 看见评测设置

**明确不做**（边界写在这里，防止后面被好心加回来）
- **没有 live 模式、不联网、不调 API**。判定由跑用例的人或 Agent 给出，作为数据灌入；
  harness 只做校验 / 存储 / 汇总。会悄悄退化成"模型自己说没问题"的 eval 比没有 eval 更糟
- **不自带基线**。`evals/results/` 首次运行前是空的，不预置任何数字
- **不自己打分**。汇总表里 `—` = 样本不足（runs < k）、不算测量，不是 0

## 1.1.2
规则边界修补 —— 这是 v1.2 之前的**最后一次规则改动**，之后冻结规则，只做 Eval Harness。

**修复**
- **architecture 的两条硬判据缺适用边界**（判据过强会误伤正常重构）：
  - *删除测试*：只适用于**已经存在的模块**。为需求引入的新模块，删除测试必然通过
    （删了就没人调用），此时改用「接口即测试面」和「两个 adapter」判定 ——
    没有已存在的第二个实现或第二个调用方，就先写成函数
  - *一个 adapter 是假 seam*：只约束**对外接口 / 抽象**是否成立。
    把 200 行函数拆成 3 个私有函数、把重复的 20 行抽成 helper，不产生新接口，
    目的是降低认知负担，**不需要**满足"两个实现"
- **root 补一条边界**：root 只描述**决策条件**，不描述**执行方法**。
  「什么时候需要安全审查」在 root，「安全审查具体查什么」在 `references/security.md`；
  「什么时候需要降级」在 root，「L0/L1/L2 每一级怎么判定」在 `skills/debugging/SKILL.md`

**新增 / 改进**
- **Rule Drift Detection 升级为显式 `CANONICAL_RULES`**（`scripts/validate_skill.py`）：
  每条规则显式声明 `name` / `source` / `forbidden_duplicates`，语义是
  「除 source 外，任何文件**同时**出现这些短语 = 复制了这条规则」。
  原来的 `SOLE_SOURCE_RULES` 与 `FORBIDDEN_DRIFT` 两套机制合并为一套，
  并新增「安全审查触发条件」一条（`references/security.md`）。
  `references/worked-example.md` 与 `evals/README.md` 显式豁免：它们的作用是**示范与陈述期望**，
  必然点名这些概念，不算第二事实来源
- 工具链：抽出 `scripts/eval_common.py`（front-matter 解析 / 语料遍历 / 结果收集），
  `validate_skill.py` 与后续 `eval_harness.py` 共用一份实现，避免两处漂移

## 1.1.1
规则冲突修补，不重构。输入来自一次针对根 `SKILL.md` 与六个能力 Skill 的逐份复审。

**修复**
- **根契约与 debugging 漂移**：根契约仍写「无法构建红环 → 停止并请求环境」，
  而 `debugging` 早已改为 L0→L1→L2 显式降级。现在根契约只写
  「L0 不可得 → 显式降级；仅无 L2 证据才停止」，细节归 `skills/debugging`
- **verification 的 DoD 自相矛盾**：一边"全部满足才算完成"，一边把
  「Build/Test 通过，**或有未验证说明**」塞进同一勾选项，导致"核心路径没跑但解释了原因"
  也能勾成完成。改为三态：`Complete / Complete with accepted risk / Incomplete`；
  **未验证 ≠ 未完成，但未验证核心路径 = 未完成**
- **verification 复制了 non-negotiables 第 2 条**：后者明确声明自己是唯一事实来源。
  现改为只引用，不复制清单
- **implementation 无条件要求与用户确认 seam**：与「能合理推断就不狂问」冲突。
  改为内部决策，只在公共 API / 多方案影响架构边界 / 需要新造 seam 三种情况才询问
- **code-review 三点改进**：① 对比基点先自动推断（upstream → 默认分支 → merge-base），
  推断不出才问；② 无 subagent 的宿主走串行两遍 fallback，并显式防锚定；
  ③ 两轴都按 defect-first 排序（Blocking > Regression > Spec miss > Maintainability > Smell），
  避免"可维护性建议很多、真正的 Bug 被淹没"
- **README**：21 → 22 cases；canonical clone URL 改为 `ASCOS.git`（旧地址仍重定向）；
  可移植性表述改为「designed to be portable / verified on Codex / other hosts best-effort」，
  不再声称在所有宿主上行为完全一致

**新增**
- **Rule Drift Detection**（`scripts/validate_skill.py`）：校验器不再只问"文件在不在"，
  还会问"这条规则是不是有两个版本"。两种机制：
  - `SOLE_SOURCE_RULES`：检测 `non-negotiables.md` 声明独占的规则是否被别处复制
  - `FORBIDDEN_DRIFT`：把已发生过的漂移写成回归护栏
  已用反向测试验证：把两处 P0 注入回去，校验器准确报出 2 个 error 并返回退出码 1
- **根文件防膨胀硬规则**：只有 Trigger / Classification / Routing / Acceptance 四类内容
  允许进入根 `SKILL.md`；行数上限从 220 收紧到 **160**（当前 120）

## 1.1.0 - 2026-09-14

v1.1.0 refactors ASCOS from a single large skill plus many references into a compact orchestrator backed by focused capability skills.

### Added

- Six capability skills under `skills/`: `requirements`, `architecture`, `implementation`, `debugging`, `code-review`, and `verification`.
- A `SKILL.md` routing table that maps user intent and task size to the correct capability chain.
- A regression-evaluation suite under `evals/`, covering small, medium, large, debugging, and adversarial scenarios.
- Executable debugging fixtures under `eval-fixtures/` for L0/L1/L2 evidence-level cases.
- `scripts/validate_skill.py`, a structural validator for front matter, links, orphaned skill files, required sections, metadata, and size checks.
- A v1.1 baseline report at `evals/runs/2026-09-14-baseline.md` with 22 evaluated cases and seven quality metrics.

### Changed

- Slimmed `SKILL.md` down to the canonical orchestrator: trigger, classify, route, and accept.
- Moved detailed engineering rules into `references/`, keeping behaviour in `skills/` and knowledge in reference documents.
- Reworked the debugging flow around an evidence ladder:
  - L0: reproducible red loop.
  - L1: observable but not fully stable reproduction.
  - L2: static reasoning from logs, traces, or incomplete evidence.
- Made L1/L2 downgrades non-blocking when useful progress is still possible, while requiring confidence level, supporting evidence, and escalation path to be stated.
- Clarified that L2 evidence is not enough to directly modify production code.
- Extended the evaluation rubric with `Output/Scale Fit` so small tasks are not overburdened with oversized process output.

### Fixed

- Removed stale references to a non-existent RFC template in release-facing documentation.
- Clarified repository-awareness guidance so `CONTEXT.md` is checked when domain terminology affects implementation.
- Removed answer leakage from debugging fixtures by moving expected reasoning into evaluator prompts.
- Documented that executable fixtures should be run one at a time to avoid cross-case workspace pollution.
- Clarified `context-model.md` guidance: greenfield projects do not need a context model before the domain vocabulary is known, but should add one once those terms matter.

### Evaluation

- Completed all 22 regression cases.
- Baseline highlights:
  - Routing: 21/21 applicable cases.
  - Evidence discipline: 22/22.
  - False completion: 0.
  - Security misses: 0.
  - Overengineering blocks held across adversarial cases.

## 1.0.0

- Added canonical `SKILL.md`.
- Added dynamic role dispatch.
- Added planning, decision, research, reflection, and quality engines.
- Added engineering departments.
- Added coding, API, security, testing, and deployment standards.
- Added PRD, ADR, API, test, and release templates.
- Added adapters for major AI coding assistants.
