# 首页按钮文案：Submit → Create order

已加载 `SKILL.md`（ai-software-company-skill），按「判断 → 路由 → 执行 → 验收」四阶段处理。

## 1. 判断（任务分级）

| 信号 | 判定 |
|------|------|
| 改文案，无外部依赖变更 | 命中「改文案 / 变量名 / 单一明显 Bug」 |
| 不含鉴权 / 支付 / 数据迁移 / 对外接口 | 不触发「至少中」升级条件 |

→ **级别：小**。

按反模式第 2 条：**不产出 PRD / ADR / TEST_PLAN**，走最短路径。

## 2. 路由

按 Skill Routing Table「简单 UI 文案或样式修改」：

```
implementation → verification
```

强制前置（已有代码库）：执行前先做 repository-awareness —— 优先复用既有文案机制，不新增 i18n 方案、不新增常量文件（除非已存在）。

## 3. 执行（implementation）

### 3.1 定位
在首页组件中定位该按钮，判定文案来源，二选一：

- **A. 硬编码**
  ```diff
  - <Button>Submit</Button>
  + <Button>Create order</Button>
  ```
- **B. 走 i18n / 文案表**
  改对应 key 的 en 值（如 `home.hero.submit` / `common.submit`）。

### 3.2 同一处改动必须一并覆盖的点（易漏）
1. 同一按钮的 `aria-label` / `title` / `tooltip` 若写死 `Submit`。
2. loading / disabled / 成功态的文案（如 `Submitting...`）。
3. 快照测试 `__snapshots__/*` 中硬编码的 `Submit`。
4. 单测 / e2e 里按文本选择元素的断言，例如 `getByText('Submit')`、`getByRole('button', { name: 'Submit' })`。
5. 若该按钮文案被用作埋点事件名或自动化选择器（`data-testid` 之外的文本定位），需确认是否影响数据链路。

### 3.3 默认决策（不阻断，若不符请指出）
若走 i18n：**只改 en 值，zh 侧保持原样不动**，因为本次只给了英文文案要求。这条已记入风险清单第 1 项。

## 4. 验收（verification）

DoD 逐项判定，全部需要真实命令输出，不得以推断代替：

| 项 | 命令 / 动作 | 通过条件 |
|---|---|---|
| Type Check | 项目既有 `tsc --noEmit` 或等效 | 0 error |
| Lint | 项目既有 lint 脚本 | 0 error |
| Build | 项目既有 build 脚本 | 成功 |
| Test | 项目既有 test 脚本 | 全绿；若快照失败，需 `jest -u` 后人工 diff 确认差异仅为文案 |
| 目视确认 | 起本地服务打开首页 | 按钮实际渲染为 `Create order` |

质量门禁：上述任一未跑或未通过 → 判定**未完成**。

## 5. 剩余风险清单

1. **i18n 未同步**：若走多语言，其他语种（含 zh）未同步，可能出现中英不一致。默认只改 en。
2. **测试/快照断言硬编码 `Submit`**：改动后 CI 变红，需同步更新快照并人工 diff。
3. **文案被当作选择器/埋点**：按文本定位的 e2e 与埋点事件名可能失效，影响数据链路。
4. **多入口首页**：若首页存在 A/B 实验变体、移动端入口或 SSR/CSR 两套模板，可能漏改其中一处。
5. **设计与文档未联动**：Figma 设计稿、帮助中心文档、发布说明中的 `Submit` 文案未同步（本次不在代码改动范围内）。

## 6. 状态说明

本次按约束未对仓库做全量探索，实际落盘编辑需要在确认按钮所在文件与文案机制（硬编码 / i18n）之后执行；上述 3.1–3.2 即为将要做的最小改动集。可确认后立即落地并按第 4 节跑完整验证。
