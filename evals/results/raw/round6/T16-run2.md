# Git rebase 和 merge 到底有什么区别？我该用哪个？

## 一句话结论

- **merge**：把两条历史**合在一起**，保留分叉的真实形状，产生一个新的合并提交。
- **rebase**：把你的提交**搬到**目标分支的顶端，历史变成一条直线，不产生合并提交。

选哪个：**已经推送出去、别人可能基于它工作的分支用 merge；还没推送、只是自己本地整理提交用 rebase。**

---

## 1. 两者做了什么

假设这样：

```
main:    A — B — C
              \
feature:       D — E
```

### merge（在 feature 上执行 `git merge main`，或反过来）

```
main:    A — B — C —————————┐
              \              ↓
feature:       D — E ———— M(合并提交)
```

- 创建一个新的**合并提交 M**，它有两个父提交。
- 两个分支的所有提交**一个都不改**，原样保留。
- 历史如实记录了"这里曾经分叉、后来合并了"。

### rebase（在 feature 上执行 `git rebase main`）

```
main:    A — B — C
                  \
feature:           D' — E'
```

- feature 上的 D、E 被**逐个"重放"**到 C 之后，产生新的提交 D'、E'（内容相同，**commit id 变了**）。
- 原来的 D、E 变成孤儿，最终被 GC 回收。
- 历史是一条直线，看起来像是你从最新的 main 上开始开发的。

---

## 2. 核心区别对照

| 维度 | merge | rebase |
|---|---|---|
| 提交历史 | 保留分叉与合并点，真实但有"毛刺" | 线性、干净，像一直在最新代码上开发 |
| 是否改写历史 | **否**（只新增一个提交） | **是**（被变基的提交 hash 全部改变） |
| 合并提交 | 有 | 无 |
| 冲突处理 | 一次性解决一次冲突 | 每个被重放的提交都可能各自冲突，需多次解决 |
| 对已推送分支 | 安全，可直接 push | **危险**，需要 `push --force`，会坑队友 |
| 可追溯性 | 强，能看出分支何时合入 | 弱，丢掉了"何时从哪个点分叉"的信息 |
| 出问题后回滚 | 直接 revert 合并提交即可 | 相对麻烦 |

---

## 3. 什么时候用哪个

### 用 merge 的场景

1. **把公共分支（main / develop / release）合进自己的特性分支**之后，再把特性分支合回公共分支 —— 合回时通常用 merge（或 squash merge），保留一个明确的"这个功能在此合入"的锚点。
2. **分支已经 push 到远程、且别人可能基于它工作**。此时绝不能 rebase。
3. **你希望保留完整的开发脉络**，比如排查"这个 bug 是什么时候、从哪条分支进来的"。
4. **合并长期存在、提交很多的大分支**，rebase 会让冲突解决过程变成一场噩梦。

### 用 rebase 的场景

1. **同步主干最新代码到自己未推送的本地分支**：`git switch feature && git rebase main`，比 merge 干净，不用留一个无意义的 "merge main into feature" 提交。
2. **整理本地提交**：`git rebase -i HEAD~5`，把"修 typo""再修一次""真的修好了"压缩成一个提交，再提 PR。
3. **保持线性历史的项目规范**（很多开源项目强制要求 PR 前 rebase）。
4. **想把某个提交移到另一条分支上**：`git rebase --onto`。

### 一条铁律（Golden Rule of Rebasing）

> **永远不要对已经推送到公共仓库、且他人可能基于其工作的提交执行 rebase。**

如果你非要 force push，请用 `git push --force-with-lease`（而不是 `-f`），它会在远程有你没见过的新提交时拒绝推送，避免直接覆盖别人的工作。

---

## 4. 常用命令速查

```bash
# 同步主干到当前分支（你的分支还没 push）
git fetch origin
git rebase origin/main
# 冲突时：改完 → git add <file> → git rebase --continue
# 想放弃：git rebase --abort

# 交互式整理最近 3 个提交（squash / reorder / reword / drop）
git rebase -i HEAD~3

# 用 merge 合回主干（推荐在公共分支上）
git switch main
git merge --no-ff feature/login   # --no-ff 强制保留合并提交

# 只想要一个干净的提交进主干
git merge --squash feature/login && git commit -m "feat: 登录功能"

# 已经 rebase 过、必须更新远程
git push --force-with-lease

# 保险绳：rebase 前先记下当前位置，随时能回来
git branch backup/feature-before-rebase
git reflog   # 出事后查被"改写"掉的旧提交
```

---

## 5. 推荐的日常工作流（最省心版）

```bash
# 1. 开分支
git switch -c feature/xxx

# 2. 开发中：分支没 push 过 → 用 rebase 跟主保持同步
git fetch origin && git rebase origin/main

# 3. 提交前：压成一个好提交
git rebase -i origin/main

# 4. push（第一次正常 push；若之前 push 过又 rebase 了，用 --force-with-lease）

# 5. 合入主干：走 PR/MR，用 Merge 或 Squash Merge
#    —— 不要在 main 上 rebase，永远
```

一句话记忆：**本地整理用 rebase，公开合入用 merge。**

> 补充：如果你实在不想记规则，有个折中方案 —— **个人分支上随便 rebase 保持整洁，合入主干时统一用 `merge --no-ff` 或 squash merge**。这样既有干净的提交粒度，又有清晰的合入节点，也是多数团队的默认做法。
