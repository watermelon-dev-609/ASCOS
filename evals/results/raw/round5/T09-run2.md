# 生产白屏问题 — 排查结论（首轮）

> 编排器路由：Bug / 上线部署问题 → `debugging` → `code-review` → `verification`（并需加载 `references/release.md` + `references/observability.md`）
> 本轮实际停留阶段：**debugging 的证据采集前置**。原因见「二、为什么我现在不给根因」。

---

## 一、任务判定

| 项 | 结论 |
|---|---|
| 任务类型 | 生产缺陷（P0 级，首屏完全不可用）+ 上线/部署问题 |
| 规模级别 | **中**（单页面入口，但发生在生产、影响全部首屏流量；若涉及多层路由/灰度/多端则上调为「大」） |
| 调用链 | `debugging` → `code-review` → `verification` |
| 强制前置 | 已有代码库 → 应先读 `references/repository-awareness.md` 并消费 `CONTEXT.md` |
| **本轮状态** | **未完成**。未产出根因与修复，按 debugging 契约触发「证据不足 → 停止并索取产物」 |

---

## 二、为什么我现在不给根因

按 `debugging` 的契约与证据阶梯，给根因必须有证据，不能靠猜：

| 级别 | 含义 | 本轮状态 |
|---|---|---|
| L0 红环 | 可稳定复现 + 拿到控制台源码级堆栈（sourcemap 已还原） | ❌ 无 |
| L1 | 可复现，但只有压缩后堆栈 / 无 sourcemap | ❌ 无 |
| L2 | 不能复现，只有现象描述、用户截图、监控聚合 | ❌ 无 |

**当前证据等级 = 无。** 合同规定：仅当连 L2 都没有时，停止分析、请求环境/产物——而不是输出一份「可能是 A 也可能是 B」的伪结论。白屏是**同一个现象、至少八类不同根因**，凭现象猜根因的修复成功率极低，且每一次错误尝试都在消耗线上时间。

所以下面给的是：**止血动作（现在就能做）+ 自助定位路径（5 分钟出证据）+ 我需要的产物清单**。证据到位后我直接进根因与最小修复。

---

## 三、先止血（按优先级，需你确认后我再执行）

> 回滚属于影响共享状态的操作，按「必须询问/人工介入边界」，**我不擅自执行**，请确认。

1. **回滚到上一个稳定版本**——白屏且刚上线，回滚是恢复最快、风险最低的路径。多数情况下 5 分钟内恢复，优先于任何诊断。
2. **若暂不能回滚**，按顺序尝试：
   - 刷 CDN 缓存（重点：确认 `index.html` 不被强缓存；`index.html` 指向旧 hash 而旧 chunk 已被清理 → 必然白屏）；
   - 停掉/降级 Service Worker（SW 缓存了旧 `index.html` 是高频根因）；
   - 核对线上 `index.html` 引用的资源 hash 与实际部署的 assets 是否一致。
3. **不要**在此期间继续发布新版本叠加变更——会让归因范围变脏。

---

## 四、自助定位：先看这三个点，10 秒内把八类根因砍到两三类

请让反馈用户（或你自己在无痕窗口）打开 DevTools，按顺序看：

**第 1 刀：Elements 面板看挂载点**
- 看 `#root` / `#app` 内**有没有子节点**
  - **空** → JS 根本没挂载：资源加载失败 / 运行时崩溃 / CSP 拦截 / SW 缓存 → 走第 2 刀
  - **有 DOM 但看不见** → 不是白屏 bug，是 CSS/渲染问题（字体色与背景同色、`z-index` 遮挡、`opacity:0`、容器高度为 0）

**第 2 刀：Console 看第一条红错**（勾选 Preserve log + 硬刷新 Ctrl+Shift+R）
- `ChunkLoadError / Loading chunk N failed / Unexpected token '<'` → **资源/缓存类**：hash 不匹配、CDN 未刷新、SPA fallback 缺失（`<'` 说明本该返回 JS 却返回了 index.html）
- `xxx is not defined / Cannot read properties of undefined` → **运行时崩溃**：多为环境变量缺失（如 `import.meta.env.VITE_API_BASE` 在新环境未注入）
- `SyntaxError / Unexpected token '?'` → **浏览器兼容**：构建产物语法过新，无 polyfill，`browserslist` 配错
- `Refused to execute inline script ... CSP` → **安全策略拦截**
- Console 干净但页面白 → 看 Network 与路由守卫（可能死循环重定向）

**第 3 刀：Network 面板（过滤 JS）**
- 首个入口 JS 是 404/403/502？→ 部署产物不完整或 CDN 路径/base 配置错
- 全部 200 但仍白屏？→ 运行时/CSP/路由问题
- 对比 `index.html` 里的 hash 与 Network 实际请求到的 hash

**常用验证命令**（有服务器/部署权限时）：
```bash
# 1. 线上 index.html 实际引用了哪些资源
curl -s https://<domain>/ | grep -oE '(src|href)="[^"]*"'

# 2. 这些资源是否真的存在（拿上一步的真实路径逐个打）
curl -I https://<domain>/assets/index-<hash>.js

# 3. index.html 是否被 CDN 强缓存（看 Cache-Control / Age / X-Cache）
curl -I https://<domain>/ | grep -iE 'cache-control|age|x-cache|etag'

# 4. SPA fallback 是否生效：深路由应返回 index.html 且 200
curl -s -o /dev/null -w '%{http_code}\n' https://<domain>/some/deep/route

# 5. 本地复现生产产物（dev 正常、prod 白屏 → 构建/环境变量问题）
npm ci && npm run build && npx vite preview   # 或 npx serve dist

# 6. 圈定变更范围（与上一个稳定 tag 对比）
git log --oneline <last-good-tag>..HEAD
git diff --stat <last-good-tag>..HEAD -- package-lock.json vite.config.* webpack.config.* src/main.* src/router .env*
```

**判据**：dev 正常 + prod 白屏 → 构建/产物/环境变量；本地 prod 也白 → 代码/依赖；仅线上白 → 部署/CDN/缓存/SW；仅部分用户白 → 浏览器兼容 / 灰度批次 / CDN 节点未刷新。

---

## 五、我需要你提供的产物（补齐这些，我立刻进根因 + 最小修复）

**必须（缺一我无法定位）：**
1. 浏览器 Console **第一条报错原文 + 完整堆栈**（无痕窗口 + 硬刷新，不要截图压缩）
2. Network 面板截图，或逐个资源的状态码（尤其首个入口 JS）
3. `#root` / `#app` 内容：**为空** 还是 **有 DOM**
4. 影响范围：全部用户还是部分？比例？集中在哪类浏览器/系统/地区？
5. 本次上线变更清单：`git log` / `git diff --stat` 相对上一个稳定版本；依赖、构建配置、`.env`、路由、入口文件是否动过
6. 部署方式：静态托管 / 容器 / CDN？`index.html` 缓存策略？是否上了 Service Worker？
7. 错误监控（Sentry 等）里**按版本分组**的聚合错误 Top 几条

**能大幅加速：**
8. sourcemap 是否已上传到监控平台（决定 L0 还是 L1）
9. `package.json` 的 build 脚本、`vite.config.*` / `webpack.config.*`、`browserslist`
10. 构建产物 hash、部署时间、灰度批次

---

## 六、事实 / 假设 / 建议（严格分开）

**事实**
- 刚上线的版本，用户打开即白屏。
- 我当前对代码库、构建产物、线上环境、监控数据**均无访问权限**，未执行任何命令，未读到任何日志。
- 按证据阶梯，当前证据等级为「无」。

**假设（未经证实，仅用于指导采集，不作为结论）**
- 白屏高频根因排序（概率非均匀，仅供排查顺序参考）：① `index.html` 与 assets hash 不匹配 / CDN 缓存 ② SW 缓存旧 `index.html` ③ 生产环境变量未注入 ④ SPA fallback 缺失导致深路由 404 ⑤ 运行时未捕获异常且无 ErrorBoundary 兜底 ⑥ 浏览器兼容缺 polyfill ⑦ CSP 拦截 ⑧ 首屏强依赖接口失败无兜底。
- 若「dev 正常、prod 白屏」，最可能是构建产物或环境变量问题。

**建议**
- 立即按第三节止血，优先回滚（需你确认）。
- 按第四节三刀流程补证据后发我，我直接给根因 + 最小修复 + 回归测试。
- **长期必补**（本次暴露的真问题）：框架层 ErrorBoundary + `window.onerror`/`unhandledrejection` 全局兜底与上报——白屏不应是静默失败；上线后自动冒烟（访问首页断言挂载点有子节点）+ 前端错误率告警；`index.html` 强制 `no-cache`，assets 长缓存 + hash；sourcemap 上传监控平台且不外发。

---

## 七、验收（DoD）——逐项结论，不虚构分数

| 项 | 结论 |
|---|---|
| 根因定位 | ❌ 未完成（无证据，未猜测） |
| 最小修复 | ❌ 未产出 |
| 回归测试 | ❌ 未产出 |
| Build / Test / Lint / Type Check 证据 | ❌ 无（未执行任何验证） |
| 白屏恢复（线上可用） | ⬜ 待你确认回滚后确认 |
| 风险清单 | ✅ 已附（见下） |

**判定：本轮未完成。** 按 `verification` 契约，「无真实验证证据 → 判定未完成，禁止声称通过」。

---

## 八、剩余风险清单

1. **线上持续不可用**：在拿到证据前，每多一分钟都是全量首屏流量损失。风险等级：高。缓解：优先回滚，而非先诊断。
2. **证据缺失导致误判**：在没有 Console 堆栈的情况下修复，改错方向的概率高，且可能引入二次故障。缓解：严格执行第四节三刀流程再动代码。
3. **静默失败未被观测**：如果线上根本没有错误上报 / ErrorBoundary，说明同类问题过去也可能发生过而无人知晓，且本次根因可能长期无法定位。风险等级：高（架构性）。
4. **回滚本身的风险**：若本次上线伴随数据库迁移或接口契约变更，回滚前端可能造成前后端版本不匹配。缓解：回滚前确认本次发布是否含后端/数据变更——**这一点请明确告知我**。
5. **缓存污染残留**：即使修好根因，已缓存旧 `index.html` 的客户端与 CDN 节点可能持续白屏一段时间。缓解：修复后强制刷 CDN + 评估 SW 版本回收策略。
6. **本轮交付的已知缺口**：本次执行范围被限定为只读编排器 `SKILL.md`，未加载 `skills/debugging` / `skills/verification` 的执行细则，也未加载 `references/release.md`、`references/observability.md`、`references/repository-awareness.md` 与 `CONTEXT.md`。因此本轮**未做代码库感知、未做变更影响分析**，第四节为通用排查路径而非针对本仓库的定向分析。证据到位后需补做这些步骤。
