# Fixture: bug-l1-observable

一个可真实运行的最小支付仓库（纯标准库，零依赖）。

**给 Agent 的材料只有代码、`stress.py`、`logs/payments-sample.log` 和一句症状描述。**
根因、判据、期望步骤写在 `evals/bugs/15-duplicate-charge.md` 里（阅卷用，不要放夹具里）。

## 怎么跑

```bash
cd eval-fixtures/bug-l1-observable

python stress.py 1 8                        # 单轮 8 线程
python stress.py 200 8                      # 200 轮聚合
RACE_CHANCE=0.3 python stress.py 20 8       # 提高竞态概率（相当于"加压"）
```

`stress.py` 签名：`python stress.py <rounds> <threads>`，输出 `duplicate_rounds` 与 `rate`。

结构化事件写入 `logs/payments.log`（运行时生成，已 gitignore）。
`logs/payments-sample.log` 是**预捕获的生产样本**，Agent 可以直接 grep。

## 维护约定

- **跑完必须还原**：`git checkout -- eval-fixtures/`，并删掉运行时生成的 `logs/payments.log`。
- 不要把根因写进本文件。本例要观察的是"Agent 会不会主动提高复现率"，
  一旦 README 告诉他能加压，测的就成了阅读理解。
- 竞态窗口由 `RACE_CHANCE`（默认 0.03）控制；调成 0 / 1 可做双向对照实验。
