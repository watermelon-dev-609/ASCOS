# Fixture: bug-l0-simple

一个可真实运行的最小下单仓库（纯标准库，零依赖）。

**给 Agent 的材料只有 `BUG.md` + 代码 + 现有测试。** 根因、判据、期望步骤写在
`evals/bugs/14-fix-500-error.md` 里（那是阅卷用的，不要放在夹具里）。

## 怎么跑

```bash
cd eval-fixtures/bug-l0-simple
python -m unittest discover -s tests -v     # 现有测试全绿：bug 尚未被覆盖
```

## 维护约定

- **跑完必须还原**：`git checkout -- eval-fixtures/`。
  夹具是坏的才有用；Agent 修对了会真的改文件，提交前一律还原。
- 不要把根因写进 `BUG.md` 或本文件。写进去等于把答案给 Agent，
  L0 用例就退化成"照着答案复现"，测不出是否真会建红环。
