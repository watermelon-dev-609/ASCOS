# Changelog

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
