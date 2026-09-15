# 把首页按钮文案从 Submit 改成 Create order

## 结论先行

这是一个**单处文案替换**的微改动，**不启动** `ai-software-company-skill` 编排器，直接改即可。

## 为什么不加载该 Skill

`ai-software-company-skill` 的自我定位是"软件开发总控（编排器）"，用于把中等以上规模的开发任务路由给 requirements / architecture / implementation / debugging / code-review / verification 等子 Skill。它同时明确写了 Not for：**纯文案润色**。

本次请求的特征：

- 改动范围：1 个字符串字面量（或 1 个 i18n key 的 value）
- 涉及架构：无
- 涉及接口/数据/状态：无
- 回归风险：极低（仅可能影响快照测试、E2E 里按文本选择器的断言、以及 i18n 缺失 key 告警）

为一个单词的替换拉起整套编排流水线（需求澄清 → 架构 → 实现 → 验证 → 汇总 → 风险清单），成本远大于收益。所以这里**直接回答、直接改**，不走编排。

## 当前无法落地修改的原因

本次会话的输入被限制为"Skill 元数据 + 你的请求"，不允许我读取或检索仓库中的任何其他文件。因此我**无法定位首页组件的具体文件**，也就无法把改动真正写进磁盘。

## 需要你补充的信息（二选一）

1. **首页组件的文件路径**（例如 `src/pages/Home/index.tsx`、`app/page.tsx`、`components/Hero.tsx` 等）；或
2. 告诉我技术栈与目录约定，我再定位。

另外需要确认一点：**这段文字是硬编码还是走 i18n？**

- 硬编码 → 直接替换字符串；
- 走 i18n → 应改语言包里的 value（如 `en-US.json` 中对应 key），**不要改 key 名**，否则其他语种会丢翻译、并可能触发 missing-key 告警。

## 落地改法

情况 A：硬编码字面量

```diff
- <Button type="primary">Submit</Button>
+ <Button type="primary">Create order</Button>
```

情况 B：i18n key（推荐，不动 key 名）

```diff
// src/locales/en-US.json
- "home.hero.submit": "Submit",
+ "home.hero.submit": "Create order",
```

```tsx
// 用法保持不变
<Button type="primary">{t('home.hero.submit')}</Button>
```

## 改完后建议顺手做两件小事

1. 全仓搜一遍 `Submit`（大小写敏感 + 按词匹配），确认没有第二处同文案的按钮被漏掉，也确认没有更合适的"创建订单"语义入口。
2. 跑一遍受影响的测试。重点看**按文本选择器**定位的用例，例如：

   - `getByText('Submit')`
   - `getByRole('button', { name: 'Submit' })`
   - Percy / Storybook 等视觉快照

   这些是最可能因为改文案而红的地方，改成 `Create order` 即可。

## 剩余风险清单

| 风险 | 等级 | 说明 |
| --- | --- | --- |
| 测试选择器失效 | 低 | E2E / 单测中按 `Submit` 文本定位的断言需同步改 |
| 视觉快照 diff | 低 | 文案变长，按钮宽度可能变化，需更新基线快照 |
| 多语种不一致 | 低 | 若走 i18n，其他语种仍是"提交"语义，属预期；但需确认 key 名未被误改 |
| 布局溢出 | 极低 | `Create order` 比 `Submit` 长，窄屏/固定宽按钮需目测确认不换行或截断 |

总结：**无需编排，属一次性微改；提供文件路径后我可直接完成替换。** 当前会话限制导致我无法自行检索定位该文件，这是唯一阻塞点。
