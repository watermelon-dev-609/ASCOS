# Round 2A · 成本与质量基线 —— 协议（跑之前写死）

**日期**：2026-09-18
**状态**：协议已登记，**等待 `codex login` 后执行**（结果见文末）。
**批次定义**：`evals/cost/README.md`（字段契约 / QI 权重 / 用例清单）—— 本文件只写本轮怎么跑。

---

## 0. 要回答的问题

> ASCOS 在 Small / Medium / Large 上分别多消耗多少？多花的钱值不值？

**本轮不改 ASCOS 任何规则。** v1.2.2 的 `description` 已冻结，阶段 1 结论不变。
这一轮只做测量。

---

## 1. 两臂与隔离

| 臂 | variant | ASCOS 可被发现 |
|---|---|---|
| A | `without_skill` | 否 |
| B | `with_skill` | 是（v1.2.2） |

隔离方式：**每臂一个独立 `CODEX_HOME`**，同一份 `auth.json` + `config.toml`，
B 臂额外在 `~/.codex/skills/` 下放 ASCOS 技能包（即 `ai-software-company-skill`）。
不动用户真实的 `~/.codex`，跑完删除。

**为什么必须这样**：阶段 1 已付过学费——用「显式要求先读 SKILL.md」搭 with 臂，
等于替模型做了被测决定。成本批次里同类错误是**两臂系统提示或可用工具不同**，
那样测到的差异就不能归因于 ASCOS。

隔离有效性必须在试点里**验证**（见 §5）：A 臂的 `skills_loaded` 必须为空。
若 A 臂也加载了 ASCOS，说明隔离没成立，整批作废重搭。

---

## 2. 固定变量

| 变量 | 取值 | 为什么 |
|---|---|---|
| CLI | **`claude -p --output-format stream-json --verbose`**（原登记 `codex exec`，已改，理由见下） | Codex 通路不可用（§8.1） |
| 模型 | **`haiku`** | 用户指定 Haiku；它是 Anthropic 模型，只有 claude CLI 供得上 |
| 权限 | 默认（非 `--dangerously-skip-permissions`） | 与 Codex `workspace-write` 同档：能改工作区，不给越权 |
| 工作目录 | `eval-fixtures/cost-app` 的**每例独立副本** | 夹具被前一次运行改过就不是同一道题 |
| E13 | 空目录 | 用例要求「无既有代码库」 |
| 会话 | 一 (case, arm, run) 一个新进程 | 阶段 1 铁律：批量塞同一会话会串味 |

### 2.1 变更记录（**开跑前改，不是开跑后补**）

**改了什么**：CLI 由 `codex exec` 改为 `claude -p`；模型由「Codex 实际配置的模型」
改为明确固定的 `haiku`；`sandbox` / `reasoning effort` 两项是 Codex 专属参数，随之消失。

**为什么改**：Codex 通路实测不可用且已定位到用户侧根因（§8.1），
`claude -p` 则用 runner 真实路径实测跑通（§8.2）。协议不能因为跑不了就跑别的然后事后认账，
所以在**第一次消耗性运行之前**改定并记录。

**这次改动实际上解决了一个原本的内在矛盾**：规划时同时选了「Codex」和「Haiku」，
但 Haiku 是 Anthropic 模型、Codex 供不了。当时只能退而求其次写「取 Codex 实际模型」。
改用 claude CLI 之后，**两个用户指定的变量同时得到满足**，不再需要妥协。

**不变的是什么**：两臂定义、隔离要求、12 个用例、分桶、样本量、判定标准、
QI 权重、`<2 次即 inconclusive`、留空不填 0 —— **一字未动**。
改的只是「用哪把尺子量」，不是「量什么、怎么算」。

**新引入的口径约束**（§8.2 实测得来，必须遵守）：input token 含 ~29.7k 的
Claude Code 系统提示底噪，**input 的 Δ% 会被机械压缩，不作主要信号**；
主要信号是 output token 与工具调用次数。报告里 A 臂必须写成
「未装 ASCOS 的 Claude Code」，**不得**写成「裸模型」。

---

## 3. 样本量

```
试点   2 例 × 2 臂 × 1 次  =  4 次      （E01 small + E10 large）
正跑  12 例 × 2 臂 × 3 次  = 72 次
```

正跑 3 次是阶段 1 沿用的判据：**有效样本 <2 次判定 `inconclusive`**，
单次观测撑不起任何稳定性结论。

---

## 4. 判定标准（**看到结果之前写死**）

### 4.1 verdict（沿用既有用例的 `判定` 清单）
逐条勾选，任一为否即 `fail`。清单已在用例文件里，本轮不修改。

### 4.2 defects（人工计数，定义如下）

| 键 | 计数的是什么 |
|---|---|
| `bugs` | 产出代码里的功能性缺陷（按任务描述会跑错/崩/结果不对） |
| `missed_edges` | 该处理却没处理的边界：空值、越界、并发、未授权。以用例 `判定` 要求的为限，不额外发散 |
| `security` | 鉴权绕过、注入、缺对象级鉴权、密钥进代码或日志 |
| `unnecessary_changes` | 与任务无关的改动：顺手重构、格式化churn、无关文件 |

### 4.3 三个布尔

| 字段 | 何时为 false |
|---|---|
| `over_engineering` | 引入了任务不需要的抽象 / 依赖 / 组件 |
| `verified` | 声称已验证但拿不出证据（阶段 1 的 False Completion 判据） |
| `tests_pass` | 跑了测试但没通过。**没跑测试填 `null`，不是 false** |

**`null` 与 `false` 必须区分**：没跑不等于跑挂了。混淆二者会让
「A 臂根本不验证」看起来和「B 臂验证了但失败」一样。

---

## 5. 试点先跑，且带止损

试点（4 次）必须回答四个问题，**任一为否就修好再进正跑**：

1. **能量化吗** —— 事件流里能取到 `input_tokens` / `output_tokens`？
   取不到则整批无法回答核心问题，**不许用字符数折算成 token 充数**。
2. **隔离成立吗** —— A 臂 `skills_loaded` 为空、B 臂非空？
3. **能观测加载吗** —— 事件流里能看到实际读了哪些 Skill / reference？
4. **成本可接受吗** —— 按试点单次成本外推 72 次的总花费，并**回报给用户后再开跑**。
   花的真金白银不预先确认就烧掉，是这一轮最不该犯的错。

---

## 6. 分析口径

- 每档每臂取**均值**，`invalid` 排除出所有分母。
- **Δtokens** = (B − A) / A；**Δquality%** = (QI_B − QI_A) / QI_Base。
- **QG/TC** = 质量增益% ÷ token 成本%。**自由（质量涨、token 没涨）单独标注为 `free`**，
  不做除法——除以 0 没有意义。
- Missing 数据留 `—`，不填 0。

---

## 7. 本轮明确不做

- **不改 `SKILL.md`、不改任何规则。** 测量轮不夹带修改。
- 不做阶段 2C 的归属归因试点（要 `stages` 轨迹，正跑再收）。
- 不做 v1.3 候选（阶段 2F）。
- 不折算金额。

---

## 8. 结果

**Codex 通路在本机不可用（用户已裁定改用 `claude -p`，见 §2.1）。**
Codex 侧的定位过程保留在下表，供日后复用；**试点已改用 claude 跑完，结果见 §10**。

`codex login` 之后仍失败，逐层定位（每一步都留了证据）：

| # | 现象 | 含义 |
|---|---|---|
| 1 | `wss://api.openai.com/v1/responses` → **401** | 认证有问题时，公网其实可直达 |
| 2 | 登录后 `wss://chatgpt.com/backend-api/codex/responses` → **os error 10061** | 换成 ChatGPT OAuth 后走的端点不通 |
| 3 | `chatgpt.com` 解析到 **159.65.107.38**，`curl --noproxy '*'` 返回 **000** | 该端点从此网络不可达 |
| 4 | 改走本地中继 `model_provider="cc-switch-official"` → **502 `上游连接失败`** | 中继收到请求，但自己转发不出去 |
| 5 | `curl http://127.0.0.1:15721/v1/models` → **`{"models":[]}`** | **中继在跑，但上游供应商是空的** |

**根因是第 5 条**：CC Switch 本地中继没有可用 provider。这既不是认证问题
（`codex login` 解决不了），也不是我这边能改的东西——它属于用户侧配置。

**不做的事**：不伪造一次"成功"的试点，不用字符数折算 token 充数，
不在通路不通的情况下开跑 72 次。测不到就留空，是本批第 2 节写死的规矩。

**用户裁定**：改用 `claude -p`（§2.1 已登记这次变更）。

### 8.1 复测（未修好，且多出一个新故障）

隔日复测 `codex exec --json --ephemeral --skip-git-repo-check "..."`：

| # | 现象 | 含义 |
|---|---|---|
| 6 | 60s 超时未返回，**EXIT=124** | 不再是快速失败，而是挂住 |
| 7 | `failed to refresh available models: timeout waiting for child process to exit` | 中继模型列表仍为空，刷新卡死 |
| 8 | `Reading additional input from stdin...` | **它在等 stdin**——子进程继承了父进程终端 |
| 9 | `rmcp::transport::worker: Transport channel closed` | 传输层随后崩掉 |

第 8 条是**独立于 Codex 可用性**的运行器缺陷，已修：`run_one` 现在传
`stdin=subprocess.DEVNULL`。否则一旦批量跑起来，某一次运行卡在终端上
会把整批 72 次一起拖死。对应测试 `test_the_child_never_inherits_our_stdin`。

结论没变：Codex 通路仍不可用，且即使修好中继，第 8 条也会先让批量跑挂住。

### 8.2 `claude -p` 通路复测：可用（runner 真实路径已打通）

用 `cost_runner.resolve_bin` + `build_command` + `summarise_claude` 完整走了一遍，
不是单独调 CLI：

```
resolved bin: C:\Users\EDY\AppData\Roaming\npm\claude.CMD   # npm 的 .cmd 垫片
returncode 0 | input=29672 output=2 total=29674 seconds=1.07 tool_calls=0
```

即：解析到 `.cmd`（Python subprocess 直接调 `claude` 会 `FileNotFoundError`）、
退出码 0、token 与时间都取得到。四件事里第一件已用真实调用确认。

**新发现的一个口径问题（必须写进 §6）：Claude Code 的系统提示底噪是 ~29.7k input token。**
一句 `reply with the single word: ok` 也要 29672 input。含义有三条：

1. **绝对 input 被常数主导**。E01 两臂 38228 / 32213 里，约 3 万是固定底噪，
   真正的任务量只有几 k。所以 **input 的 Δ% 会被机械压缩**，不能拿它当主要信号。
2. **主要信号在 output 与工具调用**（E01：7101 vs 2951，19 vs 10），
   那里底噪不参与，ASCOS 的行为差异才显形。
3. **A 臂不是"裸模型"**，是"装了 ASCOS 的 Claude Code vs 没装 ASCOS 的 Claude Code"。
   这恰好是用户真正要问的问题（**ASCOS 加在编码智能体上到底贵多少**），
   但它**不是**"ASCOS vs 空"，报告里必须这么写，不能写成后者。

---

## 9. 附：运行器自检（**不是协议数据，已删除**）

为确认仪表真的能跑，用 `claude -p` + haiku 对 **E01 跑了一次两臂对照**。
结果只用于证明管线可用，**不进批次**，原因写在下面。

| 臂 | input | output | 合计 | 工具调用 | 加载的技能 | references |
|---|---:|---:|---:|---:|---|---:|
| with_skill | 38228 | 7101 | 45329 | 19 | `implementation` | 2 |
| without_skill | 32213 | 2951 | 35164 | 10 | **空** | 0 |
| **Δ** | +18.7% | **+141%** | **+28.9%** | +90% | — | — |

**它证明了四件事**（即 §5 的试点问题前三条）：

1. **能取到 token** —— 精确 input/output，非折算。
2. **隔离成立** —— A 臂 `skills_loaded` 为空、B 臂非空；references 也是 0 vs 2。
   这恰恰是阶段 1 栽过的跟头，现在有了可复核的硬信号。
3. **能观测加载，不必自报** —— 技能与 reference 都从事件流里的真实 `Read` 得出。
4. 报告聚合正常（均值、`—` 留空、defects 留待人工填）。

**为什么不进批次**：本轮协议登记的是 Codex + 固定模型（§2）。
把另一套 CLI/模型的数据灌进同一份记录文件，正是 §1 与阶段 1
「两套配置不能混进同一分母」明令禁止的 —— Round 6 时为此专门把修复前的
60 条记录归档出去过。故删除。

**就算只看 n=1 也够有意思**：改一个按钮文案，ASCOS 让**输出 token 翻了一倍多**，
合计 +28.9%。方向与你的预判一致（简单任务偏重），但 **n=1 属于 `inconclusive`**，
不能当结论——它现在的用处是**说明仪表能测出东西**，不是说明 ASCOS 有多贵。

---

## 10. 试点结果（**四项里两项未过 → 不进正跑**）

跑了 4 次：E01（small）+ E10（large）× 两臂 × 1。**结论是不开跑 72 次。**

### 10.1 原始数据

| 用例 | 臂 | input | output | 合计 | 秒 | 工具 | 读文件 | 加载的技能 | 加载的 reference |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| E01 | with_skill | 34551 | 3755 | 38306 | 24.49 | 14 | 5 | `ascos` † | — |
| E01 | without_skill | 31642 | 2365 | 34007 | 17.88 | 11 | 5 | — | — |
| E10 | with_skill | 43185 | 15618 | 58803 | 79.10 | 23 | 15 | `ascos` `requirements` `architecture` | 5 个 |
| E10 | without_skill | 31044 | 2992 | 34036 | 22.76 | 7 | 2 | — | — |

† 经 `Skill` 工具调用，不产生文件读取事件。修正前的记录里这一格是空的，
并据此误判成「ASCOS 对小题没触发」——**错了，它触发了**。见 10.4 第 3 条。

### 10.2 四个止损条件的结论

| # | 条件 | 结论 | 证据 |
|---|---|---|---|
| 1 | 能量化吗 | ✅ **过** | 精确 input/output/合计 + 秒 + 工具数，全部来自真实事件流 |
| 2 | 隔离成立吗 | ✅ **过** | without 臂**连技能目录都没有**；with 臂装了 SKILL.md + 6 个子技能。E10 上 with 读了 3 技能 + 5 reference，without 读 0 |
| 3 | 能观测加载吗 | ✅ **修复后过** | 原会漏报 `Skill` 工具调用，已修（10.4 第 3 条）；现在 E10 with 臂能列出 3 个技能 + 5 个 reference，全部来自事件流，非模型自报 |
| 4 | 成本可接受吗 | ⚠️ **能外推，但见下** | 见 10.3 |
| 5 | **任务真的被完成了吗** | ❌ **不过** | **4 次运行，0 个文件被改动，0 个新文件**。每一次写入都被权限拒绝 |
| 6 | **模型是钉住的那个吗** | ❌ **不过** | 请求 `haiku`，实际 **`deepseek-v4-flash`**，4 次全部如此 |

**第 5、6 条是本次试点新加的**——原协议没写，是跑完才发现缺了它们。
这不是事后放宽标准，而是原标准有洞：一个「量到了 token、但什么都没做出来」的批次，
照样能算出漂亮的 Δ，却完全回答不了「ASCOS 贵在哪里、值不值」。

按 §5 白纸黑字写的「**任一为否就修好再进正跑**」，**不开跑 72 次**。

### 10.3 72 次的外推（**花真金白银之前先给你**）

按分桶，每桶 24 次（4 例 × 2 臂 × 3 次）。medium 桶无试点数据，故给区间：
下界假设 medium=small，上界假设 medium=large。

| | 下界 | 上界 |
|---|---:|---:|
| 合计 token | 2 849 580 | 3 095 892 |
| 其中 output | 370 200 | 520 080 |
| 挂钟时间 | 约 37 分钟 | 约 49 分钟 |

即 **约 250 万 input + 40～52 万 output token，约 40～50 分钟**。
单价未核实，故不折算成美元——你自己按计费口径换算。

**这个数字现在不能用来做决定**，因为 10.2 第 5 条没过：
在一个「什么都写不进去」的配置下，72 次测到的是**规划成本**，不是**交付成本**。
修好权限后需要**重跑试点再外推一次**。

### 10.4 试点暴露的四个缺陷（修完才能进正跑）

**1. 写入全部被拒（致命）**
`Claude requested permissions to write to ... but you haven't granted it yet`。
`claude -p` 非交互模式下，Edit/Write 都需要授权，无人可点确认 → 直接失败。
连带被拒的还有 PowerShell（UNC 路径 / 复杂表达式）、读 `~/.claude`、WebSearch。
**后果**：质量对比（2B）根本做不了——代码没写出来，defects 无从评起。

**2. 模型被换掉（致命）**
`--model haiku` 被本地中继重映射成 `deepseek-v4-flash`。
批内两臂一致，所以 A/B 仍可比，但：不是你指定的模型，且映射不受我控制。

**3. `skills_loaded` 会漏报（测量缺陷）—— 已修**
E01 的 with 臂事件流里明确有 `Skill {"skill": "ascos", ...}`，
但记录里 `skills_loaded=[]` —— 因为该字段只统计 `Read` 文件的路径，
而 CLI 用 `Skill` 工具加载时**不产生 Read 事件**。
**已修**：`skills_loaded` 现在并入 `Skill` 工具调用。

修完回头看，**这个漏报差点让我写错结论**：原记录显示 E01 的 with 臂没加载任何技能，
据此会得出「ASCOS 对小题正确地不触发，只有 ~2.9k 的发现税」。
真实情况是**它触发了**（`skills=['ascos']`），Δ 里那 +2909 input / +1390 output
是**激活成本**，不是发现税。方向完全相反。
阶段 1 的教训在这里又应验了一次：**激活信号不能靠猜，要靠事件流**。

**4. WebSearch 进了批次（噪声）—— 已修**
E10-with_skill 里出现一次 `WebSearch{"query":"Anthropic Claude API models pricing embeddings 2026"}`。
搜索结果随日期变化 → 不可复现，且白白加 token。虽然这次被拒，修好权限后就会真跑。
**已修**：`build_command` 对 claude 固定加 `--disallowedTools WebSearch`。

### 10.5 需要的修复（**待你拍板，尤其是第 1 条**）

| # | 修复 | 是否要你同意 |
|---|---|---|
| 1 | 给 CLI 加授权（如 `--permission-mode acceptEdits` 或 `--dangerously-skip-permissions`），并 `--allowedTools` 限定在工作区内；禁掉 WebSearch | **要** —— 这是放开写权限，属于你的机器与你的风险 |
| 2 | 钉模型：要么接受 `deepseek-v4-flash` 并原样记录，要么你指定一个中继能真实供给的模型 | 要 |
| 3 | ~~`skills_loaded` 计入 `Skill` 工具调用~~ | ✅ 已改（含测试） |
| 4 | ~~禁掉 WebSearch~~ | ✅ 已改（`--disallowedTools WebSearch`） |

---
