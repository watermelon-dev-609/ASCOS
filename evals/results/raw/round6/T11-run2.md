# SQL 教程：讲清楚 JOIN 的几种类型

> 这是一份面向初学者的知识性教程，不涉及本仓库任何代码改动。

## 一、为什么需要 JOIN

关系型数据库的设计原则是「一件事只存一份」。比如：

- `users` 表存用户（id, name）
- `orders` 表存订单（id, user_id, amount）

订单表只存 `user_id`，不重复存用户名。当我们需要「列出订单并带上用户姓名」时，就必须把两张表按 `users.id = orders.user_id` 这条关系**横向拼接**起来 —— 这就是 JOIN。

## 二、准备示例数据

```sql
-- 左表：用户
CREATE TABLE users (
  id   INT PRIMARY KEY,
  name VARCHAR(20)
);

-- 右表：订单
CREATE TABLE orders (
  id      INT PRIMARY KEY,
  user_id INT,
  amount  INT
);

INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob'), (3, 'Carol');
INSERT INTO orders VALUES (101, 1, 200), (102, 1, 150), (103, 2, 300), (104, 99, 50);
```

注意两个「坑」数据，后面所有 JOIN 的差异都靠它们体现：

- `Carol`（id=3）**没有订单**
- 订单 104 的 `user_id=99`，**没有对应的用户**

## 三、七种 JOIN 全景图

用集合的视角（左表 A = users，右表 B = orders）：

| 类型 | 含义 | 口语说法 |
|------|------|----------|
| INNER JOIN | 两边都能匹配上的行 | 交集 A∩B |
| LEFT JOIN | 左表全保留，右表匹配不上补 NULL | 左表全部 + 交集 |
| RIGHT JOIN | 右表全保留，左表匹配不上补 NULL | 右表全部 + 交集 |
| FULL OUTER JOIN | 两边都保留，谁缺谁补 NULL | 并集 A∪B |
| CROSS JOIN | 笛卡尔积，每一行两两组合 | N × M |
| SELF JOIN | 自己和自己连接 | 不是新语法，是一种用法 |
| NATURAL JOIN | 自动按同名列连接 | 强烈不推荐 |

## 四、逐个拆解

### 1. INNER JOIN（内连接）

只返回**两边都能匹配**的行。

```sql
SELECT u.name, o.id AS order_id, o.amount
FROM users u
INNER JOIN orders o ON u.id = o.user_id;
```

结果：

| name | order_id | amount |
|------|----------|--------|
| Alice | 101 | 200 |
| Alice | 102 | 150 |
| Bob   | 103 | 300 |

- Carol 被丢掉（没有订单）
- 订单 104 被丢掉（没有对应用户）
- Alice 出现两次（她有两笔订单），这是**一对多关系**的正常表现

> `INNER` 可省略，直接写 `JOIN` 等价于 `INNER JOIN`。

### 2. LEFT JOIN（左外连接）

左表（`FROM` 后面那张）**一行不少**；右表匹配不上则填 NULL。

```sql
SELECT u.name, o.id AS order_id, o.amount
FROM users u
LEFT JOIN orders o ON u.id = o.user_id;
```

结果：

| name | order_id | amount |
|------|----------|--------|
| Alice | 101 | 200 |
| Alice | 102 | 150 |
| Bob   | 103 | 300 |
| Carol | NULL | NULL |

**经典用法：找「没有订单的用户」**——加一个 `WHERE 右表主键 IS NULL`：

```sql
SELECT u.name
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.id IS NULL;   -- 结果：Carol
```

这个模式叫 **anti-join（反连接）**，是 LEFT JOIN 最高频的实战场景。

### 3. RIGHT JOIN（右外连接）

与 LEFT JOIN 完全对称，保留右表全部行。

```sql
SELECT u.name, o.id AS order_id, o.amount
FROM users u
RIGHT JOIN orders o ON u.id = o.user_id;
```

结果：

| name | order_id | amount |
|------|----------|--------|
| Alice | 101 | 200 |
| Alice | 102 | 150 |
| Bob   | 103 | 300 |
| NULL  | 104 | 50   |

> 实践建议：**几乎不用 RIGHT JOIN**。任何 `A RIGHT JOIN B` 都能改写为 `B LEFT JOIN A`，只调整表的书写顺序即可。统一用 LEFT JOIN 能显著降低多人协作时的阅读成本。

### 4. FULL OUTER JOIN（全外连接）

两边都保留，缺的一侧补 NULL。

```sql
SELECT u.name, o.id AS order_id, o.amount
FROM users u
FULL OUTER JOIN orders o ON u.id = o.user_id;
```

结果：

| name | order_id | amount |
|------|----------|--------|
| Alice | 101 | 200 |
| Alice | 102 | 150 |
| Bob   | 103 | 300 |
| Carol | NULL | NULL |
| NULL  | 104 | 50   |

注意：**MySQL 不支持 FULL OUTER JOIN**。需要用 `LEFT JOIN` + `RIGHT JOIN` + `UNION` 模拟：

```sql
SELECT u.name, o.id AS order_id
FROM users u LEFT JOIN orders o ON u.id = o.user_id
UNION                                   -- UNION 去重，UNION ALL 不去重
SELECT u.name, o.id
FROM users u RIGHT JOIN orders o ON u.id = o.user_id;
```

### 5. CROSS JOIN（交叉连接 / 笛卡尔积）

不加任何条件，左表每行 × 右表每行。

```sql
SELECT u.name, o.id AS order_id
FROM users u
CROSS JOIN orders o;                    -- 3 用户 × 4 订单 = 12 行
```

**危险**：1000 × 1000 = 100 万行，10 万 × 10 万 = 100 亿行。生产环境绝大多数 CROSS JOIN 都是忘了写 `ON` 条件的事故。

少数正当用途：生成日期序列、生成「用户 × 商品」的推荐候选集、造测试数据。

### 6. SELF JOIN（自连接）

不是新语法，是「同一张表起两个别名再连接」。典型场景：员工表里查「某员工及其经理」。

```sql
SELECT e.name AS employee, m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;
```

因为同一张表出现两次，**必须起别名**，否则无法区分左右两侧。

### 7. NATURAL JOIN（自然连接）

自动按「同名列」连接，省略 `ON`：

```sql
SELECT * FROM users NATURAL JOIN orders;  -- 会尝试按 id 连接（users.id vs orders.id）——语义错误
```

**强烈不推荐**：它依赖列名而非显式关系，一旦有人给表新增一个同名的无关列，查询语义会静默改变，是典型的线上事故来源。始终显式写 `ON` 或 `USING(col)`。

## 五、容易踩的五个坑

### 坑 1：ON 与 WHERE 的语义差别（外连接时）

```sql
-- A：先过滤右表再连接 → Alice 只会剩下一行订单，但 Carol 依然保留
SELECT u.name, o.amount
FROM users u
LEFT JOIN orders o ON u.id = o.user_id AND o.amount > 100;

-- B：先连接再过滤 → o.amount > 100 会把 amount 为 NULL 的 Carol 一并筛掉，
--    结果等价于 INNER JOIN，LEFT JOIN 白写了
SELECT u.name, o.amount
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.amount > 100;
```

结论：**对外连接，右表的过滤条件写在 `ON` 里；要「排除」匹配行时才写 `WHERE ... IS NULL`。**

### 坑 2：LEFT JOIN 后行数变多，聚合被放大

```sql
-- 错误：先 JOIN 再 COUNT，会把用户按订单数重复计数
SELECT u.id, COUNT(*) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id;

-- 正确：用 COUNT(右表列) 只数非 NULL
SELECT u.id, COUNT(o.id) AS order_cnt
FROM users u LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id;
```

先 JOIN 再 `SUM(amount)` 同样会把金额按行数放大。**先聚合子查询再 JOIN** 是最稳妥的写法：

```sql
SELECT u.name, COALESCE(t.total, 0) AS total
FROM users u
LEFT JOIN (
  SELECT user_id, SUM(amount) AS total FROM orders GROUP BY user_id
) t ON u.id = t.user_id;
```

### 坑 3：笛卡尔积（忘了 ON）

`SELECT ... FROM a, b` 这种老式写法等价于 CROSS JOIN。改成显式 `JOIN ... ON` 后，如果漏写 ON 会直接语法报错，更快暴露问题。

### 坑 4：ON 两侧类型不一致导致匹配失败

`users.id` 是 `BIGINT`，`orders.user_id` 是 `VARCHAR` 时，部分数据库会做隐式转换（导致索引失效、全表扫描），部分数据库会静默匹配不上。建外键时保持类型完全一致。

### 坑 5：NULL 永远匹配不上

`NULL = NULL` 的结果是 `UNKNOWN`，不是 `TRUE`。所以任何 `ON a.x = b.x` 在 `x` 为 NULL 时都不会匹配，JOIN 时需要注意空值处理（如 `ON COALESCE(a.x, '') = COALESCE(b.x, '')`）。

## 六、性能要点

1. **给连接键建索引**：`ON` 条件里的列（通常是右表的外键列）必须有索引。
2. **小表驱动大表**：优化器通常会选小表做驱动表；MySQL 的 NLJ 算法下驱动表行数决定了循环次数。
3. **减少 JOIN 后的数据量**：能用子查询/CTE 提前过滤和聚合，就不要让大表先 JOIN 再过滤。
4. **用 `EXPLAIN` 验证**：重点看 `type`（避免 `ALL` 全表扫描）和 `rows`（预估扫描行数）。
5. **MySQL 8.0+ 支持 Hash Join**：对大表等值连接、且连接键无索引的场景有明显提升。

## 七、速查结论

- 只要交集 → `INNER JOIN`
- 要保留左表全部 → `LEFT JOIN`
- 要找「左表有、右表没有」 → `LEFT JOIN ... WHERE 右表列 IS NULL`
- 要保留两张表全部 → `FULL OUTER JOIN`（MySQL 用 UNION 模拟）
- 需要左右都保留但数据库不支持 FULL JOIN → `LEFT JOIN` UNION `RIGHT JOIN`
- 见到 `RIGHT JOIN` → 改写成 `LEFT JOIN`
- 见到 `NATURAL JOIN` → 改写成显式 `ON`
- 见到没有 `ON` 的多表连接 → 十有八九是 bug

## 八、一图流记忆

```
   A        B
 ┌───┐   ┌───┐
 │ █████████ │  INNER  → 中间重叠部分
 │███┼───┼███│  LEFT   → 整个左边圆
 │ █████████ │  RIGHT  → 整个右边圆
 └───┘   └───┘  FULL   → 两个圆的并集
```
