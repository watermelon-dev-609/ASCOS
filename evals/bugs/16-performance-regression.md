---
id: E16
group: bugs
expect: pass
route: debugging → verification
needs_repo: true
---
# E16 · 接口性能回退

**级别**：bug（性能）｜ **期望路由**：`debugging` → `verification`

## 输入
「上周发布后，商品列表从 200ms 变成 3s。」

## 期望行为
- 走**性能分支**：先建基线测量（计时 harness / profiler / 查询计划），**先测量后修**。
- 优先用二分定位引入回退的提交（`git bisect`）。
- 常见嫌疑：N+1 查询、缺失索引、序列化放大、同步外部调用；用数据验证而非猜。
- 修复后对比基线与修复后的测量数据。

## 判定（任一为否即 Fail）
- [ ] 先有基线测量数字，再谈优化
- [ ] 用二分或数据定位，不是"感觉是 N+1"
- [ ] 优化后给出对比数字
- [ ] 没有靠打日志调试性能问题
