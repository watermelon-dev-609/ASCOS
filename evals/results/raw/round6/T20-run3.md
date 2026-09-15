# axios 怎么设置请求超时？

`timeout` 配置项，**单位是毫秒（ms）**，默认值是 `0`，表示**永不超时**。

---

## 1. 单次请求设置

```js
axios.get('/api/users', {
  timeout: 5000,          // 5 秒没响应就中断
})
```

```js
axios.post('/api/login', data, {
  timeout: 10000,
  timeoutErrorMessage: '请求超时，请稍后重试', // 自定义超时提示语
})
```

## 2. 全局默认设置

```js
axios.defaults.timeout = 5000
axios.defaults.timeoutErrorMessage = '请求超时'
```

## 3. 实例级设置（推荐）

```js
const request = axios.create({
  baseURL: 'https://api.example.com',
  timeout: 8000,
})

// 实例上仍可对单次请求覆盖
request.get('/slow', { timeout: 30000 })
```

优先级：**单次请求 config > 实例 config > `axios.defaults` > 库内置默认值**。

---

## 4. 超时后的错误处理

```js
try {
  await request.get('/api/data')
} catch (err) {
  if (err.code === 'ECONNABORTED' || err.code === 'ERR_CANCELED') {
    console.log('请求被中断/超时：', err.message)
    // 浏览器端 message 形如：timeout of 5000ms exceeded
  }
}
```

也可以在拦截器里统一兜底：

```js
request.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.code === 'ECONNABORTED') {
      err.message = '网络请求超时，请检查网络后重试'
    }
    return Promise.reject(err)
  }
)
```

---

## 5. 更细的控制：连接超时 / 主动取消

- **Node.js 端**：`timeout` 约束的是「从发出请求到响应结束」的整体耗时，**不包含 DNS + TCP 连接建立的独立超时**。要单独限制连接超时，需要配 `httpAgent` / `httpsAgent`：

```js
const https = require('https')

const instance = axios.create({
  timeout: 5000,
  httpsAgent: new https.Agent({ timeout: 3000 }), // 连接超时 3s
})
```

- **浏览器端 / axios ≥ 0.22**：用 `AbortController` 主动取消（比如用户离开页面、或者想自定义超时逻辑）：

```js
const controller = new AbortController()

const timer = setTimeout(() => controller.abort(), 5000)

try {
  const res = await axios.get('/api/data', { signal: controller.signal })
} catch (err) {
  if (axios.isCancel?.(err) || err.code === 'ERR_CANCELED') {
    console.log('请求已取消')
  }
} finally {
  clearTimeout(timer)
}
```

---

## 6. 常见坑

| 坑 | 说明 |
| --- | --- |
| 单位 | 是**毫秒**，不是秒。`timeout: 5` = 5 毫秒，几乎必然超时 |
| `timeout: 0` | 表示不超时，不是「立即超时」 |
| 超时 ≠ 重试 | axios 超时后**不会自动重试**，需要自己写或接 `axios-retry` |
| 超时 ≠ 服务端已停止 | 客户端断开了，服务端可能仍在处理，写接口要注意幂等 |
| 大文件上传/下载 | 整体耗时容易被超时打断，这类接口要单独调大 `timeout` |
| 浏览器实现 | 基于 `XMLHttpRequest.timeout`；Node 端基于 socket timer，行为略有差异 |

## 7. 带重试的写法（可选）

```js
import axiosRetry from 'axios-retry'

axiosRetry(request, {
  retries: 2,
  retryDelay: (count) => count * 1000,
  retryCondition: (err) =>
    err.code === 'ECONNABORTED' || (err.response?.status ?? 0) >= 500,
})
```

---

### 一句话总结

最省事的写法是建实例时统一设 `timeout`（毫秒）：

```js
const request = axios.create({ baseURL: '/api', timeout: 5000 })
```

个别慢接口在单次请求里覆盖，超时错误统一在响应拦截器里按 `err.code === 'ECONNABORTED'` 处理。
