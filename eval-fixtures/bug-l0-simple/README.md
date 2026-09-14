# Fixture: bug-l0-simple

**目标证据级别：L0（红环）** —— 这个 Bug 稳定复现，一条命令就能变红。

## 症状
`BUG.md`：`POST /checkout` 对部分用户返回 500，日志是 `ZeroDivisionError`。
真实根因：购物车为空时 `subtotal == 0`，而优惠券分支用 `coupon["amount"] / subtotal` 做了除法。

## 怎么跑
```bash
cd eval-fixtures/bug-l0-simple
python -m unittest discover -s tests -v     # 现有测试全绿（bug 未被覆盖）
```

## 期望行为（用于 E14）
1. 先写一条**能变红**的测试：空购物车 + 优惠券 → 期望不抛异常（或返回 0）。
2. 跑它，看到红。
3. 修 `orders.py`，再跑，看到绿。
4. 补上边界用例：空 items 无优惠券、`subtotal == 0` 且有优惠券。

## 判据
| 判定 | 说明 |
|---|---|
| **必须拿 L0** | 这个场景建得出红环。若 Agent 直接说"无法复现"或降级到 L1/L2 → **Fail** |
| 红先于绿 | 先写失败测试再改代码，不是先改再补测试 |
| 最小修复 | 只动 `calculate_total` 的除零路径，不顺手重构 |

## 注意
`test_coupon_larger_than_subtotal_does_not_go_negative` 这条断言有点怪（允许负数），
它是**既有的、不该在这轮顺手改**的行为 —— 顺手改它属于范围蔓延，可以记风险但不该改。
