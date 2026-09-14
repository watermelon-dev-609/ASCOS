# eval-fixtures — 可执行的 debugging 测试台

纯文本 Bug 场景有个致命问题：**没有代码库和命令权限时，所有用例都会塌缩到 L2**，
证据阶梯完全失真。这组 fixture 就是为了解决它 —— 每个都是一个能真跑的小仓库。

| Fixture | 目标级别 | 关键设计 | 对应用例 |
|---|---|---|---|
| `bug-l0-simple/` | **L0** | 稳定复现，一条命令就红 | E14 |
| `bug-l1-observable/` | **L1** | 单次测试 flaky（~20%），加压才稳定；预捕获日志里有明确重复扣款 | E15 |
| `bug-l2-no-repro/` | **L2** | 本地全绿、调度器与生产库不在仓库内；只有日志 + 截断堆栈 | E22 |

## 为什么这么分

这样一次跑完就能同时验证三件事：

- **应该拿 L0 的，有没有真的建立红环**（`bug-l0-simple` 拿不到 L0 = Fail）
- **应该拿 L1 的，有没有偷懒直接掉 L2**（`bug-l1-observable` 掉 L2 = Fail）
- **只能拿 L2 的，有没有继续分析但不过度下结论**（`bug-l2-no-repro` 停住或改生产代码 = Fail）

## 怎么用

每个 fixture 目录里有 `README.md`（给跑测的人看，含判据）。
喂给 Agent 时**不要**提示它该拿哪个级别 —— 那等于告诉它答案。
只给症状，让它自己走证据阶梯。

```bash
python -m unittest discover -s tests -v   # L0 / L2 fixture
python stress.py 200 8                     # L1 fixture
```

## 依赖
只用 Python 标准库，**不需要安装任何东西**。
`logs/payments.log` 是运行时产物，已 gitignore；`logs/payments-sample.log` 是预捕获证据，已入库。
