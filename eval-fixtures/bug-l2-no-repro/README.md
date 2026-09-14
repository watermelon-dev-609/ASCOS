# Fixture: bug-l2-no-repro

一个可真实运行的最小批处理仓库（纯标准库，零依赖）。

**给 Agent 的材料只有代码、现有测试、`artifacts/` 下的日志与堆栈，和一句症状描述。**
根因线索、判据、期望步骤写在 `evals/bugs/22-no-repro-degradation.md` 里（阅卷用，不要放夹具里）。

## 怎么跑

```bash
cd eval-fixtures/bug-l2-no-repro
python -m unittest discover -s tests -v     # 全绿 —— 这正是它降级到 L2 的原因
```

## 仓库里有什么

- `nightly_job.py` —— 扫 `pending` 并推进的批处理
- `tests/test_nightly_job.py` —— 本地全绿，小数据集下不触发问题
- `artifacts/gateway.log` —— 4 天的网关日志（含 `scanned` / `moved` 计数）
- `artifacts/sentry_stack.txt` —— Sentry 自定义事件 + 截断的堆栈 + breadcrumbs

调度器（K8s CronJob）与生产库**不在这个仓库里**，所以拿不到真实数据量与多副本环境。

## 维护约定

- **跑完必须还原**：`git checkout -- eval-fixtures/`。
- 不要在 `artifacts/` 里写明根因，也不要在日志里留"答案"。
  日志中的计数差值是**线索**不是结论 —— Agent 把它当结论直接宣布，本身就该判 Fail。
