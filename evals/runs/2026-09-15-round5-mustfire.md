# Round 5 · must-fire 补跑 —— 协议（跑之前写死）

**日期**：2026-09-15
**状态**：协议已登记，**结果见文末**（跑完后追加）。

## 为什么跑这一轮

Round 4 的 must-fire 只跑了 1 轮：**7/10**，其中

| 用例 | run 1 | 定性 |
|---|:--:|---|
| T01 改按钮文案 | 未触发 | 真实欠触发（候选） |
| T08 review 改动 | 未触发 | 真实欠触发（候选） |
| T05 接微信支付 | 未触发 | **环境污染物**：被宿主里的微信支付连接器截走，ASCOS 根本没被评估 |

而 Round 3/4 只预登记了**误触发**侧的阈值（≥2/3），**没有**欠触发侧。
**现在拿 1 次失败去改 `description`，等于看完数据才决定门槛** —— 和 Round 3 犯的是同一类错。

所以本轮先冻结阈值，再补跑。

## 协议（预先登记）

### 1. 装载方式：忠实臂 M2（与 Round 4 完全一致，不改）
子会话只拿到 skill 的 `name` + `description`，然后：

> If the request below warrants it, read `SKILL.md` and follow it; if not, just answer directly.

**这一条必须写在协议第一条。** Round 4 已经证明装载方式能造成 0/10 vs 10/10 vs 7/10 的差异，
差异远大于任何 run 间噪声。

### 2. 判定：Activation vs Not-activation（完整版见 `evals/README.md`）

**Activation evidence（算命中）**
1. 明确声明正在使用 / 已进入 ASCOS 或某 capability Skill
2. 明确给出 ASCOS capability 的**正向**调用 / 路由链
3. 输出 ASCOS 特有交付物（PRD / ADR / TEST_PLAN / DoD / 剩余风险清单 / 变更影响清单）
4. `requirements` / `architecture` 特有的「补全 + 分叉点追问」形态

**Not activation evidence（不算命中）**
- 仅说明 ASCOS / 某 Skill 不适用于该请求
- 仅说明将直接回答
- 仅引用 Skill 名称来解释**为什么不使用它**

> **Negative routing statement is not activation evidence.**
> 提到 Skill 不等于激活 Skill。若规定"出现 Skill 两个字就算触发"，
> 模型越清楚地解释"我为什么不触发"反而越容易被判成误触发 ——
> 那是在惩罚**可观察的路由决策**，而我们要测的是**真正的激活**。

### 3. 修复阈值（本次新增，与误触发侧对称）

| 方向 | 阈值 |
|---|---|
| **欠触发**（must-fire） | 同一用例 3 次中 **≥2 次未触发** → 候选修复队列；**1/3 → observe，不改**；0 → 无需处理 |
| **不可测** | `invalid` **不进分母**，必须在 `note` 写原因，清理污染后补跑 |

两侧用同一个形状（≥2/3），避免"哪边松哪边紧看数据决定"。

### 4. T05 的专门处理
T05「接一下微信支付」在 Round 4 被宿主里的微信支付连接器截走，
模型直接走了连接器的开通流程，**ASCOS 从未被评估**。
因此：
- T05 **既不算 fail，也不算 pass**，记 `invalid`
- 每轮都跑，每轮都如实记；若三轮全部 `invalid`，则 T05 **从分母中整体剔除**，
  并在结论里写明"本环境下 T05 不可测"

### 5. T01 与 T08 不绑成同一个修复
即使两者都满足 ≥2/3，也**不作为同一条修复**处理：

| 用例 | 缺的是什么 |
|---|---|
| T01 | **极小代码修改**是否属于 ASCOS（description 的 "改码" 覆盖面） |
| T08 | **code review** 是否属于 ASCOS（另一个覆盖缺口） |

只加一句"单处文案/配置改动也算改码"**只能解释 T01，解释不了 T08**。

### 6. 覆盖范围
- **run 2 / run 3 = T01–T10**（must-fire 全 10 例）
- run 1 沿用 Round 4 的忠实臂数据，不重跑
- 不跑 T11–T20：must-not-fire 已 30/30，且本轮新增的"negative routing"规则
  **只会让判定更宽松**，不会把已判 `not_fire` 的翻成误触发

### 7. 本轮不改任何 ASCOS 能力规则
无论结果如何，本轮结束后：
- **不**给 `non-negotiables` 加反向边界（Round 4 已裁定动机被证伪）
- **不**改 `SKILL.md` 的 `description`
本轮只产出"要不要改"的证据。

---

## 结果

20 次运行全部完成（T01–T10 × run 2/3，忠实臂 M2，每个用例一个全新子会话）。
原始回答留档在 `evals/results/raw/round5/`，记录入库 `evals/results/round5-mustfire.jsonl`。

### 逐用例

| 用例 | run 1 | run 2 | run 3 | 未触发 | 判定（≥2/3） |
|---|:--:|:--:|:--:|:--:|---|
| T01 改按钮文案 | not_fire | not_fire | not_fire | **3/3** | **进候选修复队列** |
| T02 加登录 | fire | fire | fire | 0/3 | 无需处理 |
| T03 线上 500 | fire | fire | fire | 0/3 | 无需处理 |
| T04 从零搭 SaaS | fire | fire | fire | 0/3 | 无需处理 |
| T05 接微信支付 | `invalid` | `invalid` | fire | — | 本环境 2/3 不可测 |
| T06 拆单体 | fire | fire | fire | 0/3 | 无需处理 |
| T07 分页搜索 | fire | fire | fire | 0/3 | 无需处理 |
| T08 review 改动 | not_fire | fire | fire | **1/3** | **observe，不改** |
| T09 上线白屏 | fire | fire | fire | 0/3 | 无需处理 |
| T10 CRUD 接口 | fire | fire | fire | 0/3 | 无需处理 |

**must-fire 合计（剔除 T05 的 2 次 invalid）**：27 次可测运行，命中 23 次 = **85.2%**。

### T01：3/3，满足阈值

三次都是**显式负向路由**，不是"没注意"：

- run 1：裸模型式回答，无分级、无路由、无 ASCOS 交付物
- run 2：明确写「**不启动** `ai-software-company-skill` 编排器，直接改即可」
- run 3：明确写「**未加载** `ai-software-company-skill`」，判为"字符串级替换，零架构影响"

三次的理由指向同一个缺口，而且 run 2 把话说得很直白：

> 它同时明确写了 Not for：**纯文案润色**。

模型把「把按钮文案从 Submit 改成 Create order」读成了 **纯文案润色**，于是被 `description` 自己的 Not for 排除掉了。
**这正是 T01 缺的那个覆盖面：改代码里的 UI 文案 ≠ 纯文案润色。**

三次同形、同一原因 → 不是噪声，是 `description` 的真实覆盖缺口。

### T08：1/3，observe

run 2 / run 3 都加载了 `SKILL.md`，给出了 ASCOS 路由表（"按总控路由表归类 → 调用链 `code-review` → `verification`"），
并输出了 ASCOS 专属交付物（双轴 Standards/Spec 审查契约、阻塞/建议/可选三档、DoD 判定、**剩余风险清单**）——
是明确激活，不是"提到了 Skill"。

它们停在"缺 diff + 基点"的契约失败态，那是 `code-review` 契约要求的行为（"基点不可解析 → 立即报错，不得静默降级"），
属于**激活后正确地停下来**，不是未激活。

run 1 是唯一一次未触发。**1/3 → 按预登记阈值 observe，不改。**

### T05：2/3 不可测

| run | 情况 |
|---|---|
| run 1 | 走连接器开通流程，ASCOS 从未被评估 → `invalid` |
| run 2 | 未触发的理由是「微信支付领域已有**专用技能**，专用技能优先于通用编排器」——这是**宿主特有**的理由，干净环境里不存在 → `invalid` |
| run 3 | ASCOS 正常触发（受理单 / 分级 / 路由 / 剩余风险清单）；宿主连接器只注入了一个多余的"开通 AI 专属卡"分支，**没有改变路由结果** → 记为 fire |

协议写的是"三轮全 invalid 才整体剔除"，实际是 2/3。
**因此 T05 的结论是：本宿主环境下 T05 不可靠，不进修复队列，也不写进稳定命中率。**
要么换干净宿主重跑，要么把 T05 标记为 environment-dependent —— 本轮不做，留作待办。

（两种处理都不改变结论：即便把 run 3 也判 invalid，T05 一样不进修复队列。）

### 本轮发现的一个判定缺口（不本轮修，供下一轮预先登记）

T01 run 2 的回答里**有一张"剩余风险清单"**——而 rubric 的 Activation evidence 第 3 条正是
「输出 ASCOS 特有交付物（… / 剩余风险清单 / …）」。裸模型也能随手写出一张风险表，
**按交付物名字匹配会把它误判成激活。**

- 本轮对该条的实际判法：以「明确声明使用 / 给出路由链 / 自报是否加载了 SKILL.md」为准，交付物只能作为佐证，不能单独成立。
- **这不影响本轮结论**：即使把 T01 run 2 翻成 fire，T01 仍是 2/3，依然满足 ≥2/3。
- 建议下一轮预先登记为规则：**交付物名称单独出现不构成激活证据，必须与分级/路由链/显式声明同时出现。**

### 一个流程修正

Round 4 只留了 verdict + note，**没有留原始回答** —— 导致本轮无法复核 run 1 的判分，只能引用当时的 note。
本轮起全部原始回答落盘 `evals/results/raw/<round>/`，判分可复核。

### 结论

1. **T01 满足 ≥2/3，进入 v1.3 候选修复队列。** 按 §7 本轮不改 `description`，修改放到下一轮，并会先登记措辞与回归判据。
2. **T08 不满足（1/3），维持 observe。** T01 与 T08 依 §5 不合并处理。
3. **v1.3 规则队列目前只有 T01 一条**，且是 `description` 覆盖面问题，不是能力规则问题。
4. must-not-fire 侧维持 **30/30，稳定误触发率 0%**，本轮未重跑（新增规则只会让判定更宽松）。
