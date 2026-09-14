---
id: T05
group: trigger
expect: fire
route: requirements → architecture → implementation → verification
evidence:
  - 提到回调验签或幂等
  - 提到密钥走环境变量
  - 提到金额以服务端为准
---

# T05 · 接支付

## 输入
「接一下微信支付。」

## 为什么必须触发
含支付：强制安全审查；回调幂等、验签、对账缺一不可。

## 判定
- [ ] 出现下列 evidence 至少一项（说明 ASCOS 真的接管了，不是裸模型在答）
- [ ] **触发不等于上全套**：小任务不得因此产出 PRD / ADR / TEST_PLAN

## evidence（阅卷锚点，不是字符串匹配）
- 提到回调验签或幂等
- 提到密钥走环境变量
- 提到金额以服务端为准
