# axios 怎么设置请求超时？

`timeout` 单位是**毫秒**，默认是 `0`（永不超时）。可以按「全局 → 实例 → 单次请求」三个层级设置，优先级从低到高。

## 1. 全局默认值

```js
import axios from 'axios';

axios.defaults.timeout = 5000;              // 5 秒
axios.defaults.timeoutErrorMessage = '请求超时，请稍后重试'; // 自定义超时提示
```

## 2. 实例级（推荐）

```js
const http = axios.create({
  baseURL: '/api',
  timeout: 8000,
  timeoutErrorMessage: '网络超时'
});

export default http;
```

## 3. 单次请求

```js
axios.get('/user', { timeout: 3000 });

axios.post('/save', data, { timeout: 10000 });
```

单次配置会覆盖实例/全局配置。

## 4. 需要区分「连接超时」和「响应超时」

axios 的 `timeout` 只控制**整体响应耗时**（Node 环境下不含 DNS、TLS 之外的细粒度阶段）。如果想单独限制建连时间，要在 Node 端用 Agent：

```js
const http = require('http');
const https = require('https');

const instance = axios.create({
  timeout: 10000,                 // 响应超时
  httpAgent: new http.Agent({ timeout: 3000 }),   // 连接超时
  httpsAgent: new https.Agent({ timeout: 3000 })
});
```

浏览器环境下没有连接超时的概念，`timeout` 就是唯一手段。

## 5. 手动取消 / 更灵活的超时控制

用 `AbortController` 配合 `signal`，可以随时中断请求（axios v0.22+ 支持）：

```js
const controller = new AbortController();

const timer = setTimeout(() => controller.abort(), 5000);

axios.get('/data', { signal: controller.signal })
  .finally(() => clearTimeout(timer));
```

## 6. 超时后的错误处理

```js
try {
  await http.get('/list');
} catch (err) {
  if (err.code === 'ECONNABORTED' || axios.isCancel(err)) {
    // 超时或被取消
  } else if (err.response) {
    // 服务端返回了 4xx / 5xx
  } else {
    // 网络错误
  }
}
```

常见坑：

- 超时错误码是 `ECONNABORTED`，`err.message` 默认是 `timeout of 5000ms exceeded`（可用 `timeoutErrorMessage` 改写），`err.response` 为 `undefined`。
- `timeout: 0` 表示不限制，生产环境不建议。
- 上传/下载大文件时用统一的短超时容易误伤，建议给这类接口单独配置更长的 `timeout`。
- 需要重试的话，在响应拦截器里对 `ECONNABORTED` 做退避重试，而不是简单把超时时间调大。
