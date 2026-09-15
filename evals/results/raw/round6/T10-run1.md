# 交付：商品（Product）增删改查接口

> 编排器：`ai-software-company-skill`（ASCOS）。本文按「判断 → 路由 → 执行 → 验收」四阶段输出，末尾附**剩余风险清单**。

---

## 0. 前置声明（事实，非推断）

本次会话的执行约束为：**仅加载编排器 SKILL.md，未读取仓库任何其他文件**。因此：

- 未完成 `references/repository-awareness.md` 要求的「先感知代码库」与 `CONTEXT.md` 消费；
- 技术栈、既有分层、ORM/迁移方式、鉴权中间件、是否已有 Product 模型 —— 全部**未知**；

按 ASCOS 契约，这属于 `implementation` 的失败状态（无法在确认的 seam 上落地），**不静默降级**。故本文交付的是：**已补全的需求 + 接口/数据设计 + 校验与错误契约 + 测试与验证清单 + 风险清单**，代码落地需先确认下方第 3.4 节的 5 个待确认项（其中第 1、2 项阻断）。

---

## 1. 判断（任务分级）

| 判定项 | 结论 |
|---|---|
| 级别 | **中** |
| 依据 | 「单功能 / 单 API，影响范围清晰 → 中」（单资源 CRUD，边界可在需求阶段定清） |
| 升级信号 | 命中「对外接口」→ **至少中，强制安全审查**（写操作 + 鉴权 + 输入校验 + 越权风险） |
| 未升级为「大」的理由 | 单资源、不跨层、不引入新基础设施；**若确认涉及多租户 / SKU-价格-库存联动 / 与订单域耦合，则升级为大并插入 `architecture` 阶段** |

## 2. 路由

```
requirements → implementation → code-review → verification
                                            ↘ security（强制，因含对外接口）
```

- 未走 `architecture`：单资源 CRUD，无架构分叉点（无新中间件、无跨服务契约）。
- 强制读 `references/security.md`：命中对外接口/写操作。
- `code-review` 当前**无法执行**（无 diff、无基点）→ 按契约**显式报错**，不伪造报告，改为给出 pre-CR 检查清单（第 6 节）。

---

## 3. 阶段一：`requirements` 产出

### 3.1 事实（来自用户原话）

- 需要一个「商品」的增、删、改、查接口。

### 3.2 假设（我主动补全的，标注为**假设**而非事实）

| # | 假设项 | 取值 | 若假设错误的代价 |
|---|---|---|---|
| A1 | 协议与风格 | REST + JSON，资源名 `/api/products` | 中：需改路由与序列化层 |
| A2 | 数据归属 | 商品为**主数据**，不含 SKU/价格/库存明细 | **高**：字段设计返工 |
| A3 | 删除语义 | **软删除**（`deleted_at`），列表默认过滤 | **高**：误硬删会破坏订单/库存引用完整性 |
| A4 | 权限 | 读：登录用户；写（增/改/删）：管理员角色 | **高**：越权写库 |
| A5 | 多租户 | 单租户，暂不做租户隔离 | 高：后续补隔离成本大 |
| A6 | 幂等 | 创建接口需支持 `Idempotency-Key` | 中：重复下单/重复建品 |
| A7 | 并发控制 | 更新使用乐观锁（`version` 字段 / `If-Match`） | 中：更新丢失 |
| A8 | 分页 | 游标或 `page+pageSize`，上限 100 | 低 |

### 3.3 建议（非事实，供你拍板）

1. **先做「商品主数据」最小闭合**：`name / status / category_id / description / images / attrs`。价格与库存拆到独立资源，避免商品表随业务膨胀成宽表（反过度设计）。
2. **删除必须是软删除**，并提供 `POST /api/products/{id}:restore` 而非硬删。
3. **列表接口默认不返回已删除**，用 `include_deleted=true` 显式开启，避免误读。
4. 写操作统一走**审计字段**（`created_by / updated_by / created_at / updated_at`），成本极低、事后无法补。

### 3.4 待确认项（阻断项已标注）

| # | 问题 | 阻断? | 不确认的后果 |
|---|---|---|---|
| Q1 | 技术栈与既有分层（框架、ORM、目录约定、是否已有 Product 模型） | **是** | 代码无法落地 / 重复造轮子 |
| Q2 | 鉴权与授权方式（Session / JWT？角色枚举？谁可写） | **是** | 越权漏洞 |
| Q3 | 删除语义：软删 or 硬删 | 是 | 数据完整性事故 |
| Q4 | 商品是否含 SKU / 价格 / 库存 | 否（但强烈建议先定） | 字段返工 |
| Q5 | 是否多租户 | 否（但影响面大） | 后续补隔离成本高 |

> 按「主动补全，而非狂问」原则：仅 Q1–Q3 阻断，其余我已用假设 A2/A5 兜底并在风险清单中标注。

### 3.5 验收标准（可测）

- [ ] 创建：合法入参返回 `201` + `Location` + 资源体；重复 `Idempotency-Key` 返回首次结果，不产生第二条记录。
- [ ] 查询单条：存在返回 `200`；不存在返回 `404`；已软删默认 `404`。
- [ ] 列表：支持分页与 `name` 模糊、`status` 过滤；`pageSize>100` 返回 `400`。
- [ ] 更新：全量/局部更新成功返回 `200`；`version` 冲突返回 `409`。
- [ ] 删除：软删成功返回 `204`；再次查询返回 `404`；`restore` 后恢复可见。
- [ ] 越权：非管理员调用写接口返回 `403`；未登录返回 `401`。
- [ ] 校验：非法入参返回 `422` 且错误体含 `field / code / message`。

---

## 4. 阶段二：`implementation` 设计产出（栈无关）

### 4.1 接口契约

| 方法 | 路径 | 语义 | 成功 | 主要错误 |
|---|---|---|---|---|
| POST | `/api/products` | 创建 | `201` | `400` `401` `403` `409`(幂等冲突) `422` |
| GET | `/api/products/{id}` | 详情 | `200` | `401` `404` |
| GET | `/api/products` | 列表（分页/过滤/排序） | `200` | `401` `422` |
| PATCH | `/api/products/{id}` | 局部更新（乐观锁） | `200` | `401` `403` `404` `409` `422` |
| DELETE | `/api/products/{id}` | 软删除 | `204` | `401` `403` `404` |
| POST | `/api/products/{id}:restore` | 恢复 | `200` | `401` `403` `404` `409`(已存在同名) |

### 4.2 数据模型（SQL，按实际 ORM 转写）

```sql
CREATE TABLE products (
  id           BIGSERIAL PRIMARY KEY,
  name         VARCHAR(120)  NOT NULL,
  category_id  BIGINT        NULL,
  description  TEXT          NULL,
  status       VARCHAR(16)   NOT NULL DEFAULT 'draft',  -- draft|active|archived
  version      INT           NOT NULL DEFAULT 0,        -- 乐观锁
  deleted_at   TIMESTAMPTZ   NULL,
  created_by   BIGINT        NOT NULL,
  updated_by   BIGINT        NOT NULL,
  created_at   TIMESTAMPTZ   NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE INDEX idx_products_list ON products (status, created_at DESC, id DESC)
  WHERE deleted_at IS NULL;                              -- 列表主查询
CREATE INDEX idx_products_name  ON products (name);      -- 若模糊查询走前缀匹配
-- 若业务要求同名唯一：CREATE UNIQUE INDEX ... WHERE deleted_at IS NULL;
```

### 4.3 校验规则（服务端强制，不信任客户端）

- `name`：必填，`1..120`，去空白后非空；
- `status`：枚举白名单 `draft|active|archived`；
- `description`：`<= 5000`；
- `category_id`：存在性校验（防悬垂引用）；
- 列表：`pageSize` 默认 20、上限 100；`page >= 1`；排序字段白名单（防 SQL 注入 / 防索引失效）；
- 所有路径参数 `id` 做类型与存在性校验（防 IDOR 前置）。

### 4.4 分层职责（落地时按此分 seam，便于单测）

```
router/controller  → 只做参数绑定与 HTTP 语义，不含业务
service            → 业务规则、权限判定、事务边界（唯一允许写库的地方）
repository         → 数据访问，屏蔽 ORM
dto/schema         → 入参校验 schema（单一来源，前后端共用）
```

关键实现要点：
1. **授权判定必须传 `actor` 到 service**，不在 controller 里散落 `if (user.role)`。
2. 写操作在**同一事务**内更新 `version` 与审计字段。
3. 软删与恢复都走 service，禁止 controller 直接改 `deleted_at`。
4. 列表查询默认带 `deleted_at IS NULL`。

### 4.5 测试清单（红绿循环）

单元（service 层，无需 HTTP）：
- [ ] 非法 `name` 抛校验错误
- [ ] 非管理员写操作抛 `Forbidden`
- [ ] `version` 不匹配抛 `Conflict`
- [ ] 软删后列表/详情不可见；restore 后可见

集成（打真实 DB，每个用例独立事务回滚）：
- [ ] POST → GET 往返一致
- [ ] 幂等 Key 重复提交只创建一条
- [ ] 分页边界：`pageSize=100` 通过，`101` 返回 `422`
- [ ] 并发两次 PATCH，第二次 `409`

契约/E2E（冒烟）：
- [ ] 全 5 个端点按 3.5 的状态码表返回

### 4.6 验证命令（**占位**，需 Q1 确认后替换为真实命令）

```
# 待补：依据 package.json / pom.xml / pyproject.toml 的既有脚本
<build> && <test> && <lint> && <typecheck>
```

---

## 5. 阶段三：`code-review` —— **本轮无法执行（按契约显式上报）**

`code-review` 的失败状态定义：「基点不可解析或 diff 为空 → 立即报错」。当前**既无代码也无 diff**，因此不伪造审查结论。改为给出**提交前自检清单**，落地后逐项过：

**Standards 轴（工程规范）**
- [ ] 所有外部输入在边界处校验（含 query/path/header）
- [ ] 无 SQL 字符串拼接；排序/过滤字段白名单
- [ ] 错误信息不泄露内部细节（堆栈、SQL）
- [ ] 审计字段完整；事务边界正确
- [ ] 无 N+1 查询；列表走 `idx_products_list`
- [ ] 敏感操作有日志（who/when/what），无敏感字段入日志

**Spec 轴（是否符合需求）**
- [ ] 覆盖 3.5 全部验收标准
- [ ] 状态码与 4.1 契约表一致
- [ ] 软删语义与 A3 一致
- [ ] 权限矩阵与 A4 一致

---

## 6. 阶段四：`verification` —— DoD 逐项判定

| DoD 项 | 结论 | 说明 |
|---|---|---|
| 需求已补全并标注事实/假设/建议 | ✅ 完成 | 第 3 节 |
| 接口契约与数据模型已定 | ✅ 完成 | 4.1 / 4.2 |
| 安全审查项已列出 | ⚠️ 部分 | 清单已给，未对真实代码执行 |
| 代码已落地 | ❌ **未完成** | Q1/Q2/Q3 未确认，无法在真实 seam 上实现 |
| 测试已编写并通过 | ❌ **未完成** | 仅有测试清单，无运行证据 |
| Build / Lint / Type Check 真实通过 | ❌ **未完成** | 无证据 → 按契约**判定未完成，不声称通过** |
| 风险清单已附 | ✅ 完成 | 见下 |

**结论：本轮交付为「设计就绪（Design-Ready）」，非「可发布（Shippable）」。** 按 ASCOS 第 6 条「写完 ≠ 完成」与 non-negotiables，不得声称完成。

---

## 7. 剩余风险清单

| # | 风险 | 等级 | 触发条件 | 缓解建议 |
|---|---|---|---|---|
| R1 | **未感知代码库**导致重复造轮子或与既有 Product 模型冲突 | 高 | 仓库已有商品域代码 | Q1 确认后先 `grep` 既有模型；以复用优先 |
| R2 | **越权写入（IDOR / 缺失角色校验）** | 高 | 授权未落到 service 层 | 统一中间件 + service 二次判定；补 `403` 用例 |
| R3 | **删除语义错误**破坏订单/库存引用完整性 | 高 | A3 假设不成立 | 强制软删 + 恢复接口；硬删仅走离线任务 |
| R4 | 字段边界过宽/过窄（SKU、价格、库存归属未定） | 中 | A2 假设不成立 | Q4 确认；先做主数据，价格库存拆独立资源 |
| R5 | 并发更新丢失 | 中 | 无乐观锁 | `version` + `409` 重试语义 |
| R6 | 重复创建（表单重提 / 网络重试） | 中 | 无幂等 | `Idempotency-Key` + 唯一索引兜底 |
| R7 | 列表性能劣化（深分页 / 无索引 / N+1） | 中 | 数据量增长 | 覆盖索引；深分页改游标 |
| R8 | 多租户隔离缺失 | 中 | A5 假设不成立 | Q5 确认；若多租户，表加 `tenant_id` 并全查询强制注入 |
| R9 | 审计与可观测性缺失（无法追溯谁改了什么） | 中 | 上线后追责 | 审计字段 + 写操作结构化日志 |
| R10 | 注入 / 排序字段滥用 | 低-中 | 动态 ORDER BY | 白名单映射，禁止拼接 |
| R11 | 迁移风险（DDL 上线锁表） | 低 | 大表加索引/加列 | 在线 DDL；索引用 `CONCURRENTLY`（PG） |
| R12 | **本轮无 Build/Test/Lint 真实证据** | — | 已发生 | 禁止视为完成；Q1 确认后立即补跑并回贴真实输出 |

---

## 8. 下一步（等你一句话）

回我 **Q1（技术栈/目录）**、**Q2（鉴权与角色）**、**Q3（软删 or 硬删）** 三项，我即刻按 4.4 分层落到具体文件、补测试并跑真实的 build/test/lint 输出给你。（Q4/Q5 可顺带确认，不阻断。）
