# SQL JOIN 完全教程：把几种 JOIN 讲清楚

> 说明：这不是一次代码库开发任务（没有需求评审/架构设计/实现/调试/审查环节），而是一份面向读者的教学文档，因此直接撰写，不走软件开发编排流程。

---

## 一、先建立心智模型：JOIN 到底在干什么

JOIN 的本质只有一句话：**把两张表按某个条件"横向拼起来"**。

- 纵向拼接用 `UNION`（行变多，列不变）
- 横向拼接用 `JOIN`（列变多，行的数量取决于 JOIN 类型）

所有 JOIN 都可以理解为同一个两步流程：

1. 把左右两张表做**笛卡尔积**（左表 m 行 × 右表 n 行 = m×n 行候选组合）
2. 用 `ON` 后面的条件**过滤**这些组合；某些类型在过滤后还会把「没配上对的行」用 `NULL` 补回来

掌握这一点，后面所有类型都是同一个流程的不同变体。

### 示例数据

全文使用这两张表（故意留了不匹配的数据，方便观察差异）。

`users`（用户表）

| id | name  | dept_id |
|----|-------|---------|
| 1  | 张三  | 10      |
| 2  | 李四  | 20      |
| 3  | 王五  | NULL    |
| 4  | 赵六  | 40      |

`depts`（部门表）

| id | dept_name |
|----|-----------|
| 10 | 研发部    |
| 20 | 市场部    |
| 30 | 财务部    |
| 40 | 研发部    |

注意三个"陷阱点"：
- 王五的 `dept_id` 是 `NULL`（左表有，右表配不上）
- 财务部（id=30）没有任何用户（右表有，左表配不上）
- 研发部出现两次（id=10 和 40，会造成**一对多放大**）

---

## 二、七种 JOIN 类型

### 1. INNER JOIN（内连接）

**语义**：只保留两边都能匹配上的行。

```sql
SELECT u.name, d.dept_name
FROM users u
INNER JOIN depts d ON u.dept_id = d.id;
```

结果：

| name | dept_name |
|------|-----------|
| 张三 | 研发部    |
| 李四 | 市场部    |
| 赵六 | 研发部    |

- 王五（`dept_id IS NULL`）被丢掉：`NULL = 30` 的结果是 `UNKNOWN`，不是 `TRUE`
- 财务部被丢掉：没有用户引用它

要点：
- `INNER` 可以省略，写 `JOIN` 默认就是 `INNER JOIN`
- 它是最常用、性能通常最好的一种

### 2. LEFT JOIN / LEFT OUTER JOIN（左外连接）

**语义**：左表的行**全部保留**；右表配不上就补 `NULL`。

```sql
SELECT u.name, d.dept_name
FROM users u
LEFT JOIN depts d ON u.dept_id = d.id;
```

结果：

| name | dept_name |
|------|-----------|
| 张三 | 研发部    |
| 李四 | 市场部    |
| 王五 | NULL      |
| 赵六 | 研发部    |

要点：
- `OUTER` 关键字可省略，`LEFT JOIN` == `LEFT OUTER JOIN`
- 行数 ≥ 左表行数（一对多时会变多）
- 常见用途：**找"没有匹配项"的记录**，配合 `WHERE d.id IS NULL`

```sql
-- 找出还没有部门的用户
SELECT u.name
FROM users u
LEFT JOIN depts d ON u.dept_id = d.id
WHERE d.id IS NULL;
```

### 3. RIGHT JOIN / RIGHT OUTER JOIN（右外连接）

**语义**：右表全保留，左表配不上补 `NULL`。就是 LEFT JOIN 换个方向。

```sql
SELECT u.name, d.dept_name
FROM users u
RIGHT JOIN depts d ON u.dept_id = d.id;
```

结果：

| name | dept_name |
|------|-----------|
| 张三 | 研发部    |
| 李四 | 市场部    |
| NULL | 财务部    |
| 赵六 | 研发部    |

要点：
- 功能上完全等价于把两张表调换顺序的 `LEFT JOIN`
- 实践中**建议统一用 LEFT JOIN**，从左到右读更符合直觉，团队协作更少出错；RIGHT JOIN 主要出现在多层嵌套或改写旧 SQL 时

### 4. FULL OUTER JOIN（全外连接）

**语义**：两边都保留，谁缺谁补 `NULL`。等于 `LEFT JOIN UNION RIGHT JOIN`。

```sql
SELECT u.name, d.dept_name
FROM users u
FULL OUTER JOIN depts d ON u.dept_id = d.id;
```

结果：

| name | dept_name |
|------|-----------|
| 张三 | 研发部    |
| 李四 | 市场部    |
| 王五 | NULL      |
| 赵六 | 研发部    |
| NULL | 财务部    |

要点：
- **MySQL 不支持** `FULL OUTER JOIN`，需要用 `LEFT JOIN ... UNION ... RIGHT JOIN`（或反向 LEFT JOIN）模拟：

```sql
SELECT u.name, d.dept_name
FROM users u LEFT JOIN depts d ON u.dept_id = d.id
UNION
SELECT u.name, d.dept_name
FROM users u RIGHT JOIN depts d ON u.dept_id = d.id;
```

- 典型用途：数据对账、找出两边差异

### 5. CROSS JOIN（交叉连接 / 笛卡尔积）

**语义**：不加任何条件，m × n 行全组合。

```sql
SELECT u.name, d.dept_name
FROM users u
CROSS JOIN depts d;
```

结果：4 × 4 = 16 行。

要点：
- 等价于 `FROM users u, depts d`（老式写法，容易漏写 WHERE 导致事故）
- 合法用途：生成日期序列、生成「所有组合」的维度表、补齐缺失的统计行
- **危险**：大表 CROSS JOIN 会瞬间爆炸（1 万 × 1 万 = 1 亿行）

### 6. SELF JOIN（自连接）

**语义**：不是新的 JOIN 类型，而是**同一张表跟自己 JOIN**，靠取不同的别名区分。

```sql
-- 找出和"研发部"重名的部门 id
SELECT a.id, b.id AS same_name_id
FROM depts a
JOIN depts b ON a.dept_name = b.dept_name AND a.id < b.id;
```

结果：`(10, 40)`。

要点：
- 典型场景：员工-上级（`e.manager_id = m.id`）、查找同组/同名记录、计算同表内的行间关系
- `a.id < b.id`（而不是 `!=`）可以避免自配对和重复对

### 7. NATURAL JOIN 与 USING（了解即可）

```sql
SELECT * FROM users NATURAL JOIN depts;   -- 自动按同名列连接
SELECT * FROM users JOIN depts USING (id); -- 指定按同名列 id 连接
```

要点：
- `NATURAL JOIN` 会自动匹配**所有同名列**。一旦有人给表加了一个同名字段，查询结果就会悄悄变化 —— **生产环境强烈不建议使用**
- `USING(col)` 比 `NATURAL` 安全（显式指定列），但仍不如 `ON` 明确，推荐统一用 `ON`

---

## 三、一图速查

| 类型 | 保留左表未匹配 | 保留右表未匹配 | 典型用途 |
|------|---------------|---------------|---------|
| INNER JOIN | ✗ | ✗ | 只要有关联的数据 |
| LEFT JOIN | ✓ | ✗ | 主表补全信息 / 找缺失 |
| RIGHT JOIN | ✗ | ✓ | 同 LEFT，方向相反 |
| FULL OUTER JOIN | ✓ | ✓ | 对账、差异分析 |
| CROSS JOIN | —（全组合） | —（全组合） | 生成维度组合 |
| SELF JOIN | 视所用类型 | 视所用类型 | 表内层级/配对关系 |

---

## 四、最容易踩的四个坑

### 坑 1：`ON` 和 `WHERE` 不是一回事（尤其在外连接中）

- `ON`：在**生成**连接结果时过滤右表
- `WHERE`：在连接**完成之后**再过滤整个结果集

```sql
-- A：先过滤部门，再连接 —— 王五（无部门）依然会出现，dept_name 为 NULL
SELECT u.name, d.dept_name
FROM users u
LEFT JOIN depts d ON u.dept_id = d.id AND d.dept_name = '研发部';

-- B：连接完再过滤 —— 王五被 WHERE 直接筛掉，LEFT JOIN 退化成 INNER JOIN
SELECT u.name, d.dept_name
FROM users u
LEFT JOIN depts d ON u.dept_id = d.id
WHERE d.dept_name = '研发部';
```

> 经验法则：想保留主表全部行，就把条件放在 `ON`；想真正过滤结果，才放 `WHERE`。

### 坑 2：一对多导致"行数放大"（Fan-out）

`depts` 里研发部有两条记录，任何按部门聚合后再 JOIN 的查询都可能把左表行数放大，导致 `SUM` 算多。

**解法**：先聚合再连接（用子查询/CTE 把右表压成一对一）。

```sql
WITH order_agg AS (
  SELECT user_id, SUM(amount) AS total
  FROM orders
  GROUP BY user_id      -- 先压成每个用户一行
)
SELECT u.name, COALESCE(o.total, 0) AS total
FROM users u
LEFT JOIN order_agg o ON o.user_id = u.id;
```

### 坑 3：`NULL` 参与比较永远不是 `TRUE`

`NULL = NULL` 的结果是 `UNKNOWN`，不会被 JOIN 匹配上。判断缺失请用 `IS NULL` / `IS NOT NULL`，或用 `COALESCE` 兜底。

### 坑 4：多表 JOIN 的顺序与括号

```sql
FROM a
LEFT JOIN b ON b.a_id = a.id
JOIN       c ON c.b_id = b.id   -- ⚠️ 这里 c 用 INNER JOIN 会把 a 中无 b 的行一并干掉
```

外连接后面跟内连接，很可能意外地把外连接"降级"。如果要保持 `a` 全量，后续的 `c` 通常也应该用 `LEFT JOIN`。

---

## 五、性能与可读性建议

1. **JOIN 条件列必须有索引**，尤其是被驱动表（通常是右表）的连接键；类型也要一致（`INT` 对 `VARCHAR` 会导致索引失效或隐式转换）
2. **小表驱动大表**：让结果集小的表做驱动表，减少外层循环次数
3. **不要 `SELECT *`**：只取需要的列，能显著减少网络传输，还可能命中覆盖索引
4. **优先用 `ON` 显式写条件**，不用 `NATURAL JOIN`，少用老式逗号连接
5. **用 `EXPLAIN` 看执行计划**，确认 JOIN 类型（`eq_ref` / `ref` / `ALL`）和驱动顺序是否符合预期
6. **先过滤再 JOIN**：能在子查询里 `WHERE` 掉的，不要等 JOIN 完再过滤，减少中间结果集

---

## 六、练习（附答案）

用本文的两张表，写出以下查询：

1. 查出所有用户及其部门名，没有部门的显示为「未分配」
```sql
SELECT u.name, COALESCE(d.dept_name, '未分配') AS dept_name
FROM users u
LEFT JOIN depts d ON u.dept_id = d.id;
```

2. 查出没有任何用户的部门
```sql
SELECT d.dept_name
FROM depts d
LEFT JOIN users u ON u.dept_id = d.id
WHERE u.id IS NULL;
```

3. 查出不属于任何部门的用户
```sql
SELECT u.name
FROM users u
LEFT JOIN depts d ON u.dept_id = d.id
WHERE d.id IS NULL;
```

4. 统计每个部门的**去重**人数（含 0 人的部门）
```sql
SELECT d.dept_name, COUNT(DISTINCT u.id) AS user_cnt
FROM depts d
LEFT JOIN users u ON u.dept_id = d.id
GROUP BY d.id, d.dept_name;
```

---

## 七、一句话总结

> **INNER 取交集，LEFT 保左表，RIGHT 保右表，FULL 两边都保，CROSS 全组合，SELF 是同表自连。**
> 记住一句口诀就够了：**先想清楚"哪些行必须留下"，JOIN 类型就自然确定了。**
