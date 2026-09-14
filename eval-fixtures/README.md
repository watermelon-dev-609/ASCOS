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

喂给 Agent 时**不要**提示它该拿哪个级别 —— 那等于告诉它答案。只给症状，让它自己走证据阶梯。

**各 fixture 的 `README.md` 只写"怎么跑"和"怎么维护"。**
根因、判据、期望步骤一律写在 `evals/bugs/*.md` 的「夹具判据（阅卷用）」段落里。
第一轮踩过这个坑：判据写在夹具里，Agent 先读到答案再"复现"，L0 用例退化成默写。

```bash
python -m unittest discover -s tests -v   # L0 / L2 fixture
python stress.py 200 8                     # L1 fixture
```

## 维护约定（跑测的人必读）

1. **跑完必须还原**：`git checkout -- eval-fixtures/`，并删掉运行时生成的 `logs/payments.log`。
   夹具是坏的才有用；Agent 修对了会真的写文件，不还原就污染下一轮。
2. **一次只跑一个用例**。多个 Agent 并行会共享同一个工作区：
   修 `bug-l0-simple` 的那个会让跑 `bug-l1-observable` 的 Agent 看到莫名其妙的 diff，
   污染它的"仓库感知"判断。要并行就先把 fixture 各拷一份到临时目录。
3. **不要在日志 / artifacts 里留答案**。线索和结论要有区别，
   "把线索直接当结论宣布"本身就是一项 Fail 判据。

## 依赖
只用 Python 标准库，**不需要安装任何东西**。
`logs/payments.log` 是运行时产物，已 gitignore；`logs/payments-sample.log` 是预捕获证据，已入库。
