# Fixture: bug-l1-observable

**目标证据级别：L1（可观测）** —— 单次测试不稳定复现，但日志里有明确证据。
用来验证「Agent 会不会偷懒直接从 L0 跳到 L2」。

## 症状
支付回调并发时，同一个 `order_id` 偶尔被扣两次。用户一个月投诉几次，本地跑一次测试**经常是绿的**。

## 根因（不要提前告诉 Agent）
`payments.py` 的 `charge()` 是 check-then-act：
`ledger.has(order_id)` 与 `ledger.append(...)` 之间没有加锁，
中间那次"外部风控调用"（概率性 `time.sleep`）就是竞态窗口。

## 怎么跑
```bash
cd eval-fixtures/bug-l1-observable

python stress.py 1 8      # 单轮 8 线程：约 20% 概率复现 → 单次测试是 flaky 的
python stress.py 200 8    # 200 轮：几乎必然复现 → 聚合断言可以变成稳定的 L0
RACE_CHANCE=0.3 python stress.py 20 8   # 提高复现率（相当于"加压"})
```

结构化事件写入 `logs/payments.log`（运行时生成，已 gitignore）。
`logs/payments-sample.log` 是**预捕获的生产样本**：60 个订单、360 条事件，
其中 `ORD-00005 / 00009 / 00017 / 00020 / 00059` 各被 `charged` 了 2 次。

## 期望行为（用于 E15）
1. **先尝试建 L0**：单轮测试 → 发现 flaky；加压 / 多轮聚合 → 可能拿到稳定红环。
2. 至少用**日志证据**定位：`grep '"event": "charged"' | sort | uniq -c | sort -rn` 就能看到重复的 `order_id`。
3. 修在根因（唯一约束 / 原子 upsert / 加锁），不是加个 `if has(): return` 的二次判断。

## 判据
| 判定 | 说明 |
|---|---|
| **不得直接掉 L2** | 明明有日志 + 可加压脚本，却说"无法复现" → **Fail** |
| 允许 L0 或 L1 | 加压后拿到稳定红环 = L0（优秀）；用日志差分定位 = L1（合格） |
| 修根因 | `has()` / `append()` 之间的窗口必须被消除，不是再判断一次 |
| 补回归测试 | 并发 seam 上的回归测试，或明确说明为何无法补并给出人工复验步骤 |

## 提示（给跑测的人）
这个 fixture 的关键观察点是：**Agent 有没有主动去"提高复现率"**，
而不是看到单次测试绿就宣布无法复现。这正是 debugging skill 里
「非确定性 bug：目标不是干净复现，而是更高的复现率」那条。
