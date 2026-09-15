# Git rebase 和 merge 到底有什么区别？我该用哪个？

## 一句话区别

两者都是为了「把一个分支的改动整合进另一个分支」，但方式完全不同：

- **merge**：把两个分支的历史**汇合**，生成一个**新的合并提交**（merge commit），保留两条分支的真实分叉结构。
- **rebase**：把当前分支的提交「**摘下来**」，在目标分支的**最新提交后面重新播放一遍**，提交被**改写**（产生新的 commit hash），历史变成一条直线。

## 具体发生了什么

假设从 `main` 的 `C1` 切出 `feature`，之后两边各有提交：

```
main:    C1 ─ C2 ─ C3
feature:  └─ F1 ─ F2
```

### merge（`git checkout feature && git merge main`）

```
main:    C1 ─ C2 ─ C3 ─────────┐
feature:  └─ F1 ─ F2 ─────── M ┘   (M = 新的合并提交，有两个父提交)
```

- 不改动任何已有提交，`F1`/`F2` 的 hash 不变。
- 出现一个 merge commit `M`，它有两个 parent（`F2` 和 `C3`）。
- 冲突只需**解决一次**，解决完就结束了。
- 历史**真实但会有分叉**，分支多的时候 `git log --graph` 会像一团毛线。

### rebase（`git checkout feature && git rebase main`）

```
main:    C1 ─ C2 ─ C3
                      └─ F1' ─ F2'   (F1'/F2' 是新的提交，hash 变了)
```

- Git 先找到 `feature` 和 `main` 的**共同祖先** `C1`。
- 把 `F1`/`F2` 存成临时补丁，把 `feature` 指针重置到 `C3`。
- 依次把补丁**重新应用**，生成全新的提交 `F1'`/`F2'`（内容相同，但 hash、 committer date 变了，parent 也变了）。
- 历史是**一条直线**，看起来像你一开始就基于最新的 `main` 开发的。
- 代价：**每个提交都可能单独报冲突**，要逐个解决（`git rebase --continue` 继续）。
- 后续把 `feature` 合回 `main` 时通常可以**快进（fast-forward）**，不会再产生 merge commit。

## 核心差异对照

| 维度 | merge | rebase |
|---|---|---|
| 历史结构 | 保留分叉，真实 | 线性，干净 |
| 已有提交 | 不改写 | **改写**（hash 变化） |
| 冲突处理 | 一次解决 | 可能逐提交解决 |
| 可追溯性 | 能看到「什么时候合过一次」 | 丢失合并的时间点信息 |
| 安全性 | 非破坏性操作 | 破坏性（改写历史） |
| 排查问题 | 二分（bisect）友好 | 中间提交可能本身是坏的 |

## 一条最重要的铁律（别违反）

> **只对「本地、还没推送给别人」的提交做 rebase；已经推送到公共分支、别人可能基于它工作的提交，绝对不要 rebase。**

原因：rebase 改写了 commit hash。如果你 rebase 并强制推送（`--force`）了别人正在用的分支，队友本地的历史就和远端对不上了，再 pull 会产生重复提交、混乱的冲突，甚至丢代码。

**补救**：万一必须强推，用 `git push --force-with-lease` 而不是 `--force`，它会在远端有你没见过的新提交时拒绝推送，避免覆盖队友的工作。

## 那我该用哪个？

### 用 merge 的场景

1. **把功能分支合回共享分支**（`main`/`develop`）—— 公共历史不该改写，保留「这个功能是在这里合入的」这个信息很有价值。
2. **团队协作的分支** —— 别人可能已经 pull 过，不能改写。
3. **你想保留完整的上下文** —— 比如排查 bug 时需要知道分支什么时候分叉、什么时候合并。
4. **团队还在学 Git** —— merge 心智负担低，不容易搞砸。

### 用 rebase 的场景

1. **在个人本地分支上同步主干**：你在 `feature` 上开发，主干已经往前走了，`git rebase main` 把你的改动「挪」到最新主干上，历史保持线性。
   ```bash
   git fetch origin
   git rebase origin/main
   ```
2. **整理自己的本地提交**：`git rebase -i HEAD~3` 可以合并（squash）、重排、改写提交信息，让提交历史干净再发起 PR。
3. **想让 PR 的 diff 干净** —— 评审者看到的是「相对最新主干的增量」，而不是混着一堆主干中间提交的噪音。
4. **追求线性历史的项目** —— 很多开源项目（如 Git 自身、不少 Linux 子系统的维护者）要求 PR 先 rebase 再合入。

### 一个常见且好用的折中：rebase + merge（no-ff）

1. 开发时用 rebase 保持你的分支跟主干同步、提交干净；
2. 合入主干时用 `git merge --no-ff`，产生一个明确的合并提交，把整个功能「打包」成一个可追溯的单元（也方便一键 revert）。

很多团队（包括 GitHub 的 "Rebase and merge" / "Squash and merge" 之外的传统流派）都采用这种做法：
**本地 rebase 整理，合入时 merge --no-ff 留痕。**

## 常用命令速查

```bash
# 同步主干到当前分支（推荐这个组合，省一次 checkout）
git fetch origin
git rebase origin/main

# 交互式整理最近 3 个提交：pick/squash/reword/drop
git rebase -i HEAD~3

# rebase 中解决冲突后继续 / 放弃
git add <file> && git rebase --continue
git rebase --abort          # 回到 rebase 前的状态，放心用

# 只 rebase，但保留分叉（不拉平成直线）
git rebase --no-ff main

# rebase 时保留 merge commit（默认会被丢弃）
git rebase --rebase-merges main

# 合入主干（保留合并记录）
git merge --no-ff feature

# 已经 rebase 过本地分支，需要强推时用
git push --force-with-lease
```

## 实践建议

- 设置 `git config --global pull.rebase true`，让 `git pull` 默认用 rebase（`git pull --rebase`），避免每次同步主干都产生无意义的 "Merge branch 'main'" 提交。
- 不确定的时候，**用 merge**。merge 的结果永远可以被人工还原，rebase 改写的历史则很难追溯。
- 如果 rebase 过程中搞乱了，`git rebase --abort` 一键回退；即使已经 rebase 完成，`git reflog` 里还能找到原来的提交（`git reset --hard <原HEAD>`）救回来。
- 一个判断口诀：
  > **自己的、没推送的 → 可以 rebase；共享的、已推送的 → 用 merge。**
