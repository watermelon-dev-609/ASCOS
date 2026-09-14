---
id: T16
group: trigger
expect: not_fire
near_miss: 工具用法咨询
evidence:
  - 直接对比两者
  - 给出选择建议
  - 没有开始改代码
---

# T16 · rebase 和 merge 的区别

## 输入
「Git rebase 和 merge 到底有什么区别？我该用哪个？」

## 为什么不能触发
工具用法咨询，通用知识问答。答完即可，无需路由到任何能力 Skill。

## 判定
- [ ] 直接回答问题，没有出现任务分级或路由推演
- [ ] 没有产出 PRD / ADR / TEST_PLAN / DoD / 剩余风险清单
- [ ] 没有拉起 13 个角色视角
- [ ] 出现下列 evidence 至少一项（说明它当成普通问答处理了）

## evidence（阅卷锚点，不是字符串匹配）
- 直接对比两者
- 给出选择建议
- 没有开始改代码
