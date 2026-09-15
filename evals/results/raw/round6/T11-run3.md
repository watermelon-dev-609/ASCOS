# SQL 教程：一次讲清楚 JOIN 的几种类型

> 目标：读完你能回答三个问题 —— 有哪几种 JOIN、每种各自返回哪些行、什么时候该用哪一种。

---

## 0. 先准备两张小表

理解 JOIN 最好的办法是拿一张"能对上、也有对不上"的最小数据集。下面这两张表刻意留了三类数据：

- 能对上的（员工有部门，部门也有员工）
- 左边有、右边没有的（员工没部门 / 部门号在部门表里不存在）
- 右边有、左边没有的（部门一个人都没有）

```sql
-- 员工表（左表）
CREATE TABLE employees (
  id      INT PRIMARY KEY,
  name    VARCHAR(20),
  dept_id INT            -- 外键，允许为 NULL
);

-- 部门表（右表）
CREATE TABLE departments (
  id   INT PRIMARY KEY,
  name VARCHAR(20)
);

INSERT INTO employees VALUES
  (1, '张三', 10),
  (2, '李四', 20),
  (3, '王五', NULL),   -- 没部门
  (4, '赵六', 40);     -- 部门号 40 在部门表里根本不存在

INSERT INTO departments VALUES
  (10, '技术部'),
  (20, '市场部'),
  (30, '财务部'),      -- 一个员工都没有
  (50, '法务部');      -- 一个员工都没有
```

两张表长这样：

| employees.id | name | dept_id |
|---|---|---|
| 1 | 张三 | 10 |
| 2 | 李四 | 20 |
| 3 | 王五 | NULL |
| 4 | 赵六 | 40 |

| departments.id | name |
|---|---|
| 10 | 技术部 |
| 20 | 市场部 |
| 30 | 财务部 |
| 50 | 法务部 |

---

## 1. JOIN 到底在干什么

JOIN 的本质只有一句话：**按某个条件把两张表的行两两配对，把配成的对拼成一行。**

它背后是关系代数里的"笛卡尔积 + 筛选 + 补 NULL"三步：

1. 先算笛卡尔积：左表 4 行 × 右表 4 行 = 16 种组合（这就是 CROSS JOIN）；
2. 再用 `ON` 条件筛掉不匹配的（这就是 INNER JOIN）；
3. 外连接则反过来把"被筛掉的那边"再补回来，缺失的那一侧全部填 `NULL`（这就是 LEFT / RIGHT / FULL）。

把这三步记住，所有 JOIN 都是它的变体，不需要死记。

---

## 2. INNER JOIN（内连接）—— 只要能对上的

```sql
SELECT e.name AS 员工, d.name AS 部门
FROM employees e
INNER JOIN departments d ON e.dept_id = d.id;
```

结果（2 行）：

| 员工 | 部门 |
|---|---|
| 张三 | 技术部 |
| 李四 | 市场部 |

`INNER` 可以省略，直接写 `JOIN` 就是内连接。

**什么时候用**：只关心"两边都存在"的记录。比如"查询有有效部门的员工""查询已下单的用户"。

---

## 3. LEFT JOIN（左外连接）—— 左边全留

```sql
SELECT e.name AS 员工, d.name AS 部门
FROM employees e
LEFT JOIN departments d ON e.dept_id = d.id;
```

结果（4 行，左表 4 行一行不少）：

| 员工 | 部门 |
|---|---|
| 张三 | 技术部 |
| 李四 | 市场部 |
| 王五 | NULL |
| 赵六 | NULL |

左边没匹配上的，右边补 `NULL`。注意：王五（`dept_id` 是 NULL）和赵六（部门号 40 不存在）都会出现，因为 `LEFT JOIN` 不要求它匹配得上。

**什么时候用**：
- "列出全部员工，顺便带上部门名（没有就空着）" —— 主表必须完整；
- **查"不存在的"数据**：配合 `WHERE 右表.主键 IS NULL`，这是 LEFT JOIN 最经典的用法。

```sql
-- 找出没有有效部门的员工（王五、赵六）
SELECT e.name
FROM employees e
LEFT JOIN departments d ON e.dept_id = d.id
WHERE d.id IS NULL;
```

这个技巧叫 **反连接（Anti Join）**，比 `NOT IN` 更安全可靠（见第 9 节）。

---

## 4. RIGHT JOIN（右外连接）—— 右边全留

```sql
SELECT e.name AS 员工, d.name AS 部门
FROM employees e
RIGHT JOIN departments d ON e.dept_id = d.id;
```

结果（4 行，右表每一行都保留）：

| 员工 | 部门 |
|---|---|
| 张三 | 技术部 |
| 李四 | 市场部 |
| NULL | 财务部 |
| NULL | 法务部 |

**什么时候用**：和 LEFT JOIN 完全对称，只是保留方向相反。实践中**很少用** —— 任何 `A RIGHT JOIN B` 都能改成 `B LEFT JOIN A`，而人的阅读习惯是从左往右，所以统一用 LEFT JOIN 团队协作更省事。

---

## 5. FULL OUTER JOIN（全外连接）—— 两边都全留

```sql
SELECT e.name AS 员工, d.name AS 部门
FROM employees e
FULL OUTER JOIN departments d ON e.dept_id = d.id;
```

结果（6 行 = 匹配的 2 行 + 左表独有的 2 行 + 右表独有的 2 行）：

| 员工 | 部门 |
|---|---|
| 张三 | 技术部 |
| 李四 | 市场部 |
| 王五 | NULL |
| 赵六 | NULL |
| NULL | 财务部 |
| NULL | 法务部 |

**什么时候用**：做数据比对、对账时最有用，比如"把线上表和离线表对齐，看看两边各丢了哪些数据"：

```sql
SELECT COALESCE(a.id, b.id) AS id,
       CASE WHEN a.id IS NULL THEN '只在新表有'
            WHEN b.id IS NULL THEN '只在旧表有'
            ELSE '两边都有' END AS 状态
FROM old_table a
FULL OUTER JOIN new_table b ON a.id = b.id
WHERE a.id IS NULL OR b.id IS NULL;
```

注意：**MySQL 不支持 `FULL OUTER JOIN`**，需要用 `LEFT JOIN ... UNION ... RIGHT JOIN` 模拟。

---

## 6. CROSS JOIN（交叉连接）—— 全组合

```sql
SELECT e.name, d.name
FROM employees e
CROSS JOIN departments d;   -- 16 行 = 4 × 4
```

**什么时候用**：需要"全组合"的场景，而不是业务关联。典型例子：

- 生成报表骨架：每个日期 × 每个商品都要有一行（即使当天没销量，也要显示 0）；
- 生成测试数据、笛卡尔积枚举。

```sql
-- 每个日期 × 每个商品都出一行，缺失销量补 0
SELECT d.day, p.product_name, COALESCE(SUM(s.amount), 0) AS 销量
FROM dim_date d
CROSS JOIN dim_product p
LEFT JOIN sales s ON s.day = d.day AND s.product_id = p.id
GROUP BY d.day, p.product_name;
```

> 警告：CROSS JOIN 的结果行数是两表行数的乘积，10000 × 10000 = 1 亿行，容易直接把库跑挂。用之前先确认行数。

---

## 7. SELF JOIN（自连接）—— 自己和自己连

不是新的 JOIN 语法，而是"同一张表用两个别名当两张表来连"。

```sql
-- 员工表加一列 manager_id（上级的 id）
SELECT e.name AS 员工, m.name AS 上级
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;
```

**典型场景**：层级结构（上下级、分类树）、同一表内的行比较。

```sql
-- 找出和市场部同部门的其他员工
SELECT e2.name
FROM employees e1
JOIN employees e2 ON e1.dept_id = e2.dept_id
WHERE e1.name = '李四' AND e2.name <> '李四';
```

**必须给表起别名**，否则数据库分不清哪个是左表哪个是右表。

---

## 8. 另外两个"没有语法但有概念"的 JOIN

| 名称 | 概念 | 标准写法 |
|---|---|---|
| **半连接（Semi Join）** | 只返回左表中"在右表存在匹配"的行，且不复制行 | `WHERE EXISTS (...)` |
| **反连接（Anti Join）** | 只返回左表中"在右表不存在匹配"的行 | `WHERE NOT EXISTS (...)` 或 `LEFT JOIN ... IS NULL` |

```sql
-- 半连接：下过单的用户（一个用户只出现一次，不会因为多笔订单而重复）
SELECT * FROM users u
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);

-- 反连接：从没下过单的用户
SELECT * FROM users u
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);
```

为什么不用 `JOIN` + `DISTINCT`？因为 `EXISTS` 一旦找到第一条匹配就停止扫描，语义清晰且通常更快。

顺带一提 `NATURAL JOIN`（按同名列自动连接）和 `USING (col)` 是语法糖，**生产环境不推荐**：表结构一加列，`NATURAL JOIN` 的语义会悄悄变化。老老实实写 `ON a.id = b.id`。

---

## 9. 最容易踩的 5 个坑

### 坑 1：LEFT JOIN 被 WHERE 写成了 INNER JOIN

```sql
-- 错误：想要"所有员工"，结果只拿到有部门的 2 行
SELECT e.name, d.name
FROM employees e
LEFT JOIN departments d ON e.dept_id = d.id
WHERE d.name = '技术部';   -- 王五、赵六的 d.name 是 NULL，被过滤掉了
```

`WHERE` 是在 JOIN 之后执行的，对 `NULL` 的比较结果是 `UNKNOWN`，直接被丢掉。

**正确写法：把条件放进 ON**

```sql
SELECT e.name, d.name
FROM employees e
LEFT JOIN departments d ON e.dept_id = d.id AND d.name = '技术部';
-- 结果：4 行，只有张三有部门名，其余 NULL
```

**判断口诀**：想"过滤右表但保留左表" → 放 `ON`；想"过滤最终结果" → 放 `WHERE`。

### 坑 2：一对多导致行数膨胀，聚合结果翻倍

一个用户 3 笔订单、5 条地址，`JOIN` 后会变 15 行，直接 `SUM(amount)` 会把金额算 3 遍或 5 遍。

**解法**：先聚合再连接，不要先连接再聚合。

```sql
-- 正确：先把订单聚合到"用户粒度"，再连
SELECT u.name, COALESCE(o.total, 0) AS 总金额
FROM users u
LEFT JOIN (
  SELECT user_id, SUM(amount) AS total
  FROM orders GROUP BY user_id
) o ON o.user_id = u.id;
```

### 坑 3：NOT IN 遇到 NULL 会返回空集

```sql
SELECT * FROM employees WHERE dept_id NOT IN (SELECT id FROM departments);
-- 如果 departments.id 里有 NULL，结果为空 —— NOT IN (…, NULL) 永远 UNKNOWN
```

**解法**：用 `NOT EXISTS` 或 `LEFT JOIN ... IS NULL`，它们对 NULL 的行为是正确的。同时把连接列声明为 `NOT NULL`。

### 坑 4：连接条件漏写，变成 CROSS JOIN

```sql
FROM a, b WHERE a.x = 1   -- 忘了写 a.id = b.id，得到笛卡尔积
```

用显式 `JOIN ... ON` 语法（而不是逗号 + WHERE）能从语法层面避免这个问题。

### 坑 5：连接列类型不一致，索引失效

`a.user_id` 是 `VARCHAR`、`b.id` 是 `INT` 时，数据库要做隐式类型转换，索引可能用不上，大表上直接慢成全表扫描。**连接列必须同类型**。

---

## 10. 一张表总结

| 类型 | 保留左表全部 | 保留右表全部 | 典型行数 | 常用度 |
|---|---|---|---|---|
| `INNER JOIN` | 否 | 否 | 匹配数 | ★★★★★ |
| `LEFT JOIN` | 是 | 否 | ≥ 左表行数 | ★★★★★ |
| `RIGHT JOIN` | 否 | 是 | ≥ 右表行数 | ★ |
| `FULL OUTER JOIN` | 是 | 是 | 两边不匹配的都补上 | ★★ |
| `CROSS JOIN` | 是 | 是 | 左表 × 右表 | ★★ |
| `SELF JOIN` | — | — | 视条件 | ★★★ |
| `EXISTS` / 半连接 | 是（去重） | — | ≤ 左表行数 | ★★★★ |

**选择口诀**：

- 只要两边都有 → `INNER JOIN`
- 主表一条都不能少 → `LEFT JOIN`
- 找"缺的那部分" → `LEFT JOIN` + `WHERE 右表.主键 IS NULL`
- 判断"存在/不存在" → `EXISTS` / `NOT EXISTS`
- 需要全组合 → `CROSS JOIN`
- 表内层级关系 → `SELF JOIN`

---

## 11. 性能小贴士

1. **给连接列建索引**：通常是右表的外键列（如 `orders.user_id`）。左表一般走全表扫描。
2. **小表驱动大表**：优化器通常会自己选，但可以显式控制，MySQL 里可用 `STRAIGHT_JOIN`。
3. **先过滤再连接**：把能提前 `WHERE` 的条件写成子查询，减少参与连接的数据量。
4. **用 `EXPLAIN` 看执行计划**：重点看 `type`（避免出现 `ALL`，即全表扫描）和 `rows`。
5. **连接层数别太多**：超过 5~6 张表的大 JOIN 要拆分成临时表或分步查询，可读性和性能都会更好。

---

## 12. 三个练习（答案思路）

1. **查询每个部门的员工人数，包含 0 人的部门。**
   思路：`departments LEFT JOIN employees`，`GROUP BY d.id`，用 `COUNT(e.id)`（注意不能用 `COUNT(*)`，会数出 1）。

2. **查询从没下过单的用户。**
   思路：`users LEFT JOIN orders ON ... WHERE orders.id IS NULL`，或 `NOT EXISTS`。

3. **查询同时购买了商品 A 和商品 B 的用户。**
   思路：`orders` 自连接两次（或 `GROUP BY user_id HAVING COUNT(DISTINCT product_id) = 2`）。

---

## 附：MySQL 不支持 FULL OUTER JOIN 的替代写法

```sql
SELECT e.name AS 员工, d.name AS 部门
FROM employees e LEFT JOIN departments d ON e.dept_id = d.id
UNION          -- UNION 会去重，UNION ALL 不去重
SELECT e.name, d.name
FROM employees e RIGHT JOIN departments d ON e.dept_id = d.id;
```

SQLite 3.39+、PostgreSQL、SQL Server、Oracle 原生支持 `FULL OUTER JOIN`，MySQL 需要用上面的方式模拟。
