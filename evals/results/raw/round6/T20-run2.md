# axios 怎么设置请求超时？

`timeout` 的单位是**毫秒**，默认值是 `0`（表示永不超时）。有三种粒度可以设置。

## 1. 全局默认（影响所有请求）

```js
import axios from 'axios'

axios.defaults.timeout = 5000 // 5 秒
```

## 2. 实例级别（推荐，项目里最常用）

```js
const http = axios.create({
  baseURL: '/api',
  timeout: 10000, // 10 秒
})

http.get('/users')
```

## 3. 单次请求（优先级最高，会覆盖实例/全局配置）

```js
axios.get('/api/slow', { timeout: 30000 })
axios.post('/api/upload', data, { timeout: 0 }) // 0 = 不限制，适合大文件上传
```

优先级：**单次请求配置 > 实例配置 > 全局 defaults**。

## 如何捕获超时错误

超时后 axios 会 reject，错误对象的 `code` 是 `ECONNABORTED`（浏览器端 `message` 里带 `timeout of xxx ms exceeded`）：

```js
try {
  await http.get('/api/data')
} catch (err) {
  if (err.code === 'ECONNABORTED') {
    console.log('请求超时')
  } else {
    console.log('其他错误', err)
  }
}
```

统一处理可以放在响应拦截器里：

```js
http.interceptors.response.use(
  res => res,
  err => {
    if (err.code === 'ECONNABORTED') {
      err.message = '请求超时，请稍后重试'
    }
    return Promise.reject(err)
  }
)
```

## 注意点

1. **浏览器端**底层是 `XMLHttpRequest.timeout`，超时后会触发 `ontimeout` 并中断请求。
2. **Node 端**底层是 `http` 模块，`timeout` 表示「socket 建立后到收到响应」的时间，不包括 DNS 和连接建立阶段。
3. 想单独控制**连接超时**，Node 端可以配合自定义 agent：

   ```js
   const https = require('https')
   const http = axios.create({
     timeout: 10000, // 响应超时
     httpsAgent: new https.Agent({ timeout: 3000 }), // 连接超时
   })
   ```

4. 需要「连接超时 + 读取超时 + 自动重试」这种更细的控制时，axios 原生 `timeout` 不够用，可以用 `AbortController` 手动中断，或引入 `axios-retry`：

   ```js
   import axiosRetry from 'axios-retry'
   axiosRetry(http, { retries: 3, retryDelay: axiosRetry.exponentialDelay })
   ```

5. 超时本身不会自动取消服务端处理，只是客户端放弃等待；对非幂等接口（如创建订单）重试要谨慎。

## 常见配置示例

```js
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE,
  timeout: 15000,
})

http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.code === 'ECONNABORTED'
      ? '请求超时，请检查网络后重试'
      : err.response?.data?.message || '请求失败'
    return Promise.reject(new Error(msg))
  }
)

export default http
```
