# Git rebase 和 merge 到底有什么区别？我该用哪个？

这是纯概念/知识类问题，不涉及写码、改码、查 Bug 或上线交付，因此没有加载 `ai-software-company-skill`（该 Skill 明确不适用于「通用知识问答」）。下面直接回答。

## 一、本质区别：一个是「搬运」，一个是「汇合」

假设从 `main` 的 `C` 点拉出了特性分支 `feature`：

```
      E---F---G   feature
     /
A---B---C---D     main
```

### merge（合并）

把两条线的最新状态**汇合成一个新的提交**。默认会产生一个「merge commit」，它有两个父提交。

```
      E---F---G
     /         \
A---B---C---D---H   main（H 是 merge commit，父 = D 和 G）
```

- 历史**原样保留**，你能看到「确实存在过一个分支，在某某时刻被合并进来」。
- 提交对象一个都没被改写，只是新增了一个 H。
- 结果是非线性的、有分叉有汇合的真实历史。

### rebase（变基）

把 `feature` 上的 `E/F/G` 三个提交**逐个"摘下来重放"**到 `main` 的最新提交 `D` 之后，形成新的提交 `E'/F'/G'`（内容相同，哈希不同）。

```
              E'---F'---G'   feature（改写后）
             /
A---B---C---D               main
```

然后再做一次 fast-forward 合并或直接把 `main` 指过去：

```
A---B---C---D---E'---F'---G'   main
```

- 历史变成**一条直线**，看起来就像你是在最新代码上一次性写完的。
- 原有提交被**改写**（新的 commit hash = 新身份）。

## 二、关键差异对照

| 维度 | merge | rebase |
|---|---|---|
| 历史形态 | 保留分叉，非线性 | 拉直成线性 |
| 是否改写已有提交 | 否（只新增 merge commit） | 是（生成全新 hash） |
| 冲突处理 | 一次性解决一个大冲突 | 逐个提交解决，可能要解决多次 |
| 安全性 | 高，不破坏任何已有提交 | 若对**已推送的公共分支**执行，会制造分叉历史 |
| 信息保真度 | 高，保留了真实的开发脉络与合并时间点 | 低，抹掉了"这里曾经有个分支"的事实 |
| 日志可读性 | 分叉多时 `git log` 较乱 | 干净，一条线 |
| bisect 调试 | merge commit 可能造成干扰 | 线性历史，定位问题更顺 |

## 三、我该用哪个？—— 一条铁律 + 三条经验

### 铁律：只对「还没给别人看的提交」做 rebase

> **永远不要 rebase 已经推送到公共分支、且别人可能基于它工作的提交。**

因为 rebase 会改写 hash。你本地 rebase 完强推上去，同事手里的旧提交就和你的新历史对不上了，他们再 pull 会产生诡异的重复提交和混乱冲突。修复起来很痛。

个人分支、还没 push 的本地提交 —— 随便 rebase，这是你的私人草稿。

### 经验 1：拉主干更新到自己分支时 → 优先 rebase

你在 `feature` 上开发，主干已经往前走了，需要同步主干的改动：

```bash
git fetch origin
git rebase origin/main       # 把我的改动重放到最新主干上
# 有冲突就解决 → git add . → git rebase --continue
# 想放弃：git rebase --abort
```

好处是你的提交始终"骑在"最新代码上，最后合回主干时历史是直的、冲突最少。

（用 merge 也能同步，只是会往你的特性分支里塞进一堆主干的 merge commit，最后合回去时历史很脏。）

### 经验 2：把特性分支合回主干时 → 用 merge

```bash
git checkout main
git merge --no-ff feature    # --no-ff 强制保留 merge commit
```

主干上的 merge commit 是有价值的记录：它标记了「这个功能是在何时作为一个整体被集成进来的」，需要回滚时 `git revert -m 1 <merge-commit>` 可以一次性撤掉整个功能。

### 经验 3：本地脏提交整理 → 用交互式 rebase

push 之前把一堆 "fix typo"、"wip"、"改一下" 整理成几个干净的提交：

```bash
git rebase -i HEAD~5    # squash / fixup / reword / reorder / drop
```

这是 rebase 最无可替代的用法。

## 四、一句话决策

- **已经 push 出去了 / 是共享分支** → `merge`
- **只是自己本地的提交** → `rebase`（同步主干、整理提交）
- **拿不准** → `merge`，它更安全，最坏情况只是历史有点乱，不会破坏别人的工作

## 五、一个折中方案（很多团队在用）

- 日常同步主干：个人分支 `git rebase origin/main`
- 合回主干：走 Pull Request / Merge Request，用 "Merge commit" 或 "Squash merge"（后者把整个 PR 压成一个提交再合入，兼顾主干整洁与可回滚）

两种策略都成立，关键是**团队内统一**，别一半人 rebase 一半人 merge，那历史会非常难读。

## 附：常用救命命令

```bash
git rebase --abort          # rebase 中途反悔，回到起点
git rebase --continue       # 解决冲突后继续
git rebase --skip           # 跳过当前这个提交
git reflog                  # rebase 搞砸了？reflog 里几乎什么都能找回来
git reset --hard ORIG_HEAD  # 回到危险操作前的状态
```
