# 阶段 1 验收结论 —— 触发与边界稳定性验证

**版本**：ASCOS v1.2.2
**状态**：**阶段 1 完成，冻结。**
**日期**：2026-09-15

---

## 一句话结论

> ASCOS v1.2.2 已完成触发与边界稳定性验证。T01 欠触发已修复并达到 3/3 fire；
> must-not-fire 在 30 次独立会话中 0 误触发，且 0/30 实际加载 `SKILL.md`。
> 当前触发层已达到可冻结状态，后续优化不再改动 `description`，
> 除非新证据证明存在稳定失败模式。

---

## 1. 阶段定义

本阶段只回答一个问题：

> **ASCOS 会不会在该触发的时候触发、在不该触发的时候不触发？**

两个研究对象被严格分开，本阶段只做第一个：

| 研究对象 | 问的是 | 本阶段 |
|---|---|---|
| **Triggering** | 该不该触发（模型看到 name + description 后的决定） | **本阶段，已验收** |
| Always-on robustness | 一旦常开，行为稳不稳 | 下一阶段（Forced-activation 套件） |

混用这两者是本阶段之前最大的测量错误来源，见 §4。

---

## 2. 验收项与证据

| # | 验收项 | 判据 | 实测 | 证据 |
|---|---|---|---|---|
| 1 | must-fire 触发 | 10 例该触发 | Round 6：**12/12**（T01 3/3 + T02–T10 9/9） | `evals/results/round6-description-fix.jsonl` |
| 2 | must-not-fire 误触发 | 30 次 0 误触发 | **0/30** | 同上 |
| 3 | T01 欠触发修复 | 从 3/3 恢复到 ≥2/3 | **3/3**（干净恢复，非边界） | `evals/runs/2026-09-15-round6-description-fix.md` |
| 4 | `loaded` 独立行为信号 | 与 rubric 无关的第二信号 | **0/30**（must-not-fire 侧未读取 SKILL.md） | `evals/results/round6-description-fix.jsonl` 的 `loaded` 字段 |
| 5 | 会话隔离 | 一个 (case, run) 一个全新会话 | 42 次独立会话 | 同上 |
| 6 | 原始回答落盘 | 改 rubric 后仍可回溯复核 | `evals/results/raw/round6/` 42 份 | — |
| 7 | Harness 基础校验 | `check` 通过 | **752 项 / 42 用例 / 62 记录** | `python scripts/eval_harness.py check` |
| 8 | 结构校验 + 单测 | strict 全绿 | validator **235 项** / 单测 **32 个** | `python scripts/validate_skill.py --strict` |
| 9 | 远端同步 | 本地 = 远端 | `e93ad78` = `origin/main` | GitHub API 复核 |
| 10 | 版本收口 | 冻结在 v1.2.2 | `ascos.json` / README / CHANGELOG 一致 | — |

---

## 3. 干预内容（本阶段唯一的规则改动）

只改 `SKILL.md` front-matter 的 `description`，两处，都只针对 T01 的根因：

| 位置 | 改前 | 改后 |
|---|---|---|
| `Use when` | 用户要写码、改码… | 用户要写码、改码**（包括代码中的 UI 文案、配置等局部修改）**… |
| `Not for` | 纯文案润色… | **与代码或软件配置无关的**纯文案润色… |

**为什么两处一起改**：只加 `Use when` 的限定会与既有 `Not for` 打架，
模型仍可能被 `Not for` 排除 —— Round 5 的三次欠触发正是这个原因，
其中一次把理由直说了：

> 它同时明确写了 Not for：**纯文案润色**。

**明确没做**：`code-review` 的覆盖面（T08 的缺口）**没碰**。T08 只有 1/3，
未达门槛，且与 T01 是两个独立缺口，不合并成一条修复。

---

## 4. 本阶段最重要的三条方法论结论

这三条比数字本身更值钱，后续任何一轮评测都必须遵守。

### 4.1 触发行为对「技能怎么装载」极度敏感

同一批 20 例、同一判分标准，三种装载方式的 must-fire 命中率是
**0/10 · 10/10 · 7/10** —— 差异远大于任何 run 间噪声。

> **跨 harness 比较触发率没有意义，除非装载方式也写进协议第一条。**

Round 3 报出的「2 例误触发」后来被证明是强制加载的产物，Round 4 三轮 30 次全未复现，
对应的规则改动**已撤回而不是发布**。

### 4.2 「提到了 Skill」不等于「Skill 被触发」

模型说「这属于文案润色，不走开发编排 Skill」是**正确的负向路由**，不是激活。

> **Negative routing statement is not activation evidence.**

这类观察单独打 `observation: negative-routing` 标签，不进 `misfire_shape`。

### 4.3 交付物名称不能单独当激活证据

裸模型也能写出一张「剩余风险清单」，所以名称匹配会系统性高估触发率。

> **ASCOS 特有交付物只能作为 activation corroboration，不能单独构成 activation evidence.**

判定激活必须有 Primary evidence：声明加载 / 路由链 / 能力特异的行为形态。
rubric 因此拆成 Primary / Supporting / Not activation evidence 三段。

---

## 5. 已识别并接受的风险

### 5.1 rubric 收紧带来的跨轮不可比性

Round 6 之前收紧了两条 rubric，而**更严的 rubric 会机械地压低 fire 计数** ——
所以单看「0/30」**不足以**证明 description 放宽是无害的。

本阶段对此的处置是引入**第二个独立信号**：`loaded`（这次会话到底有没有打开 `SKILL.md`）
是纯行为、与 rubric 版本无关。它也读 **0/30**。

> 结论建立在两个独立信号上，而不是一个可能被 rubric 影响的计数上。

**遗留**：跨轮横向比较仍不可直接做。要真正对比，需要用同一 rubric 补跑一次基线。
这是下一阶段的工作，不阻塞本阶段冻结。

### 5.2 单次观测撑不起稳定性结论

> **有效样本 <2 次判定为 `inconclusive`**，不进命中率、不进修复队列。

因此 T08 保持 `observe`（单次 fire），T05 在合并两次有效观测后才转正（两次均 fire）。

---

## 6. 冻结声明

**本阶段到此冻结。** 具体约束：

1. **不再改动 `description`**，除非新证据证明存在稳定失败模式。
2. 「稳定失败模式」的判定沿用已登记的阈值，不新造标准：
   同一用例在 **≥2 次有效观测中同向失败**（`invalid` 不计入分母）。
   单次观测、环境污染物、rubric 变更引起的计数波动，都**不构成**重开条件。
3. **不因「顺手」而修改任何规则**。本阶段已经吃过一次教训：
   Round 5 我建议把 T01 的修复措辞放宽为「含单处文案 / 配置改动」，
   被否决 —— 「文案」脱离「代码中的」仍会与普通内容润色撞车。
   修复范围必须**只覆盖已观测到的根因**。

---

## 7. 明确不在本阶段范围（下一阶段）

以下项目**已识别、已登记、本阶段一律不碰**：

- per-skill eval（3 × 6 = 18）
- Forced-activation robustness suite（M1 的 8/10 那类常开态失效）
- E01–E22 行为用例
- `seconds` / `tokens` 测量
- 新规则 / 新 Skill / 新 Router 逻辑

同时保留两条遗留观察（**不阻塞冻结，也不构成重开条件**）：

- T05 依赖宿主环境（连接器会截走请求），本机可测性不稳定。
- T08 缺 `code-review` 覆盖面证据，当前 1 次有效观测。

---

## 8. 证据索引

| 类型 | 路径 |
|---|---|
| 本阶段各轮协议与结果 | `evals/runs/2026-09-14-round3-triggers.md` … `2026-09-15-round6-description-fix.md` |
| Round 6 原始记录 | `evals/results/round6-description-fix.jsonl` |
| Round 6 原始回答 | `evals/results/raw/round6/` |
| 修复前的 60 条触发记录（归档） | `evals/results/round4-5-prefix.jsonl` |
| 评分 rubric 与阈值 | `evals/README.md` |
| 聚合报告 | `python scripts/eval_harness.py report --k 1 3` → `evals/results/report.md` |
