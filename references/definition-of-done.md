# 完成定义（Definition of Done）— P0

任务真正交付完成需同时满足以下全部条件：

- [ ] 实现完成（需求与补全项均已落地）
- [ ] 验证完成（Build / Test / Lint / Type Check 通过，或有明确未验证说明）
- [ ] 关键测试通过（正常 / 边界 / 异常；安全 / 权限相关含攻击路径）
- [ ] Code Review 完成
- [ ] 安全与权限检查完成（鉴权 / 授权 / 注入 / XSS / 越权 / 脱敏）
- [ ] 风险清单已输出
- [ ] 必要文档同步更新（PRD / ADR / API_SPEC / TEST_PLAN 按需）

## 规则
- 未完成上述任一项，不应声称「完成」。
- 虚构分数禁令见 `references/non-negotiables.md` 第 1 条；必附风险清单见第 2 条。
- 与质量门禁（`quality-gate.md`）互补：门禁判定「能否放行」，DoD 定义「是否真正做完」。
