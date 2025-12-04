# M3 Agent UI v2.2 技术报告

**版本**: 2.2
**发布日期**: 2025-12-04
**基于**: v1.9稳定版本
**核心特性**: 三角聊天室（WebSocket实时推送）+ 字体优化

---

## 1. 版本概述

v2.2是基于v1.9稳定版本的重大功能升级，实现了**精简三角聊天室**，支持User/API/Agent三方实时对话，并修复了字体样式呈现问题。

### 1.1 核心改进

| 功能 | v1.9 | v2.2 |
|------|------|------|
| **WebSocket连接** | ❌ 无 | ✅ 实时推送 |
| **历史消息加载** | ❌ 无 | ✅ 启动时加载 |
| **source区分** | ✅ 已支持 | ✅ 保持 |
| **字体样式** | ✅ 已优化 | ✅ 强制覆盖Tailwind |
| **版本号** | 1.9 | 2.2 |

### 1.2 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 v2.2                               │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  ChatPage.tsx                                       │    │
│  │  ┌──────────────────────────────────────────┐     │    │
│  │  │  runtime.ts                               │     │    │
│  │  │  ┌────────────────────────────────┐      │     │    │
│  │  │  │  WebSocketClient               │      │     │    │
│  │  │  │  - 连接 /ws/chat/{thread_id}   │      │     │    │
│  │  │  │  - 接收实时消息                │      │     │    │
│  │  │  │  - 发送心跳包                  │      │     │    │
│  │  │  └────────────────────────────────┘      │     │    │
│  │  │                                           │     │    │
│  │  │  ┌────────────────────────────────┐      │     │    │
│  │  │  │  加载历史消息                  │      │     │    │
│  │  │  │  GET /api/threads/{id}/history │      │     │    │
│  │  │  └────────────────────────────────┘      │     │    │
│  │  └──────────────────────────────────────────┘     │    │
│  │                                                     │    │
│  │  ┌──────────────────────────────────────────┐     │    │
│  │  │  M3Thread.tsx                             │     │    │
│  │  │  - 根据source显示不同样式                │     │    │
│  │  │  - user: 右侧蓝色                        │     │    │
│  │  │  - api: 左侧绿色                         │     │    │
│  │  │  - assistant: 左侧灰色                   │     │    │
│  │  └──────────────────────────────────────────┘     │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  index.css                                          │    │
│  │  - 字体优化：15px, line-height 1.7                 │    │
│  │  - 强制覆盖Tailwind工具类                          │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 核心修改详解

### 2.1 websocket-client.ts（新增）

**位置**: `/client/src/lib/websocket-client.ts`

完整代码（115行）：

```typescript
/**
 * WebSocket客户端
 * 用于连接后端的三角聊天室
 */

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private threadId: string;
  private onMessageCallback: ((message: any) => void) | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private heartbeatInterval: NodeJS.Timeout | null = null;

  constructor(threadId: string) {
    this.threadId = threadId;
    // 使用相对路径，nginx会代理到后端
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    this.url = `${protocol}//${host}/ws/chat/${threadId}`;
  }

  /**
   * 连接到WebSocket服务器
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('[WebSocket] Connected to', this.url);
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('[WebSocket] Received:', data);

            // 处理pong消息（心跳包响应）
            if (data.type === 'pong') {
              return;
            }

            // 调用回调函数
            if (this.onMessageCallback) {
              this.onMessageCallback(data);
            }
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WebSocket] Error:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('[WebSocket] Disconnected');
          this.stopHeartbeat();
          this.attemptReconnect();
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 断开连接
   */
  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * 设置消息回调函数
   */
  onMessage(callback: (message: any) => void) {
    this.onMessageCallback = callback;
  }

  /**
   * 启动心跳包
   */
  private startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 30000); // 每30秒发送一次
  }

  /**
   * 停止心跳包
   */
  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * 尝试重新连接
   */
  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`[WebSocket] Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect().catch((error) => {
          console.error('[WebSocket] Reconnect failed:', error);
        });
      }, 2000 * this.reconnectAttempts); // 指数退避
    } else {
      console.error('[WebSocket] Max reconnect attempts reached');
    }
  }
}
```

**核心功能**:

1. **自动重连**: 
   - 最多尝试5次
   - 指数退避（2秒、4秒、6秒...）

2. **心跳包**:
   - 每30秒发送`"ping"`
   - 保持连接活跃

3. **消息回调**:
   - 通过`onMessage()`注册回调
   - 接收到消息时自动调用

---

### 2.2 runtime.ts（重写）

**位置**: `/client/src/lib/runtime.ts`

完整代码（115行）：

```typescript
/**
 * M3 Agent Runtime v2.2
 * 使用WebSocket实现三角聊天室
 */

import { AssistantRuntimeCore } from "@assistant-ui/react";
import { WebSocketClient } from "./websocket-client";

const THREAD_ID = "default"; // 固定使用default线程

/**
 * 创建M3 Agent Runtime
 */
export function createM3Runtime(): AssistantRuntimeCore {
  let wsClient: WebSocketClient | null = null;
  const messages: any[] = [];

  // 创建runtime
  const runtime = new AssistantRuntimeCore({
    async *streamText({ messages: inputMessages }) {
      const lastMessage = inputMessages[inputMessages.length - 1];
      
      if (lastMessage.role !== "user") {
        return;
      }

      try {
        // 发送消息到后端
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: lastMessage.content,
            thread_id: THREAD_ID,
            source: "user"
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        
        // 流式输出响应
        const text = data.response || "";
        for (const char of text) {
          yield { type: "text-delta", textDelta: char };
          await new Promise(resolve => setTimeout(resolve, 20));
        }

      } catch (error) {
        console.error("Failed to send message:", error);
        yield { type: "text-delta", textDelta: "抱歉，发送消息失败。" };
      }
    }
  });

  // 初始化：加载历史消息 + 连接WebSocket
  (async () => {
    try {
      // 1. 加载历史消息
      console.log("[Runtime] Loading history...");
      const response = await fetch(`/api/threads/${THREAD_ID}/history?limit=50`);
      const data = await response.json();
      
      if (data.messages && data.messages.length > 0) {
        // 将历史消息添加到runtime
        for (const msg of data.messages) {
          messages.push({
            role: msg.source === "assistant" ? "assistant" : "user",
            content: msg.content,
            metadata: { source: msg.source }
          });
        }
        console.log(`[Runtime] Loaded ${data.messages.length} history messages`);
      }

      // 2. 连接WebSocket
      console.log("[Runtime] Connecting to WebSocket...");
      wsClient = new WebSocketClient(THREAD_ID);
      
      wsClient.onMessage((message) => {
        // 接收到新消息时，添加到runtime
        if (message.type === "new_message") {
          const newMsg = {
            role: message.source === "assistant" ? "assistant" : "user",
            content: message.content,
            metadata: { source: message.source }
          };
          
          messages.push(newMsg);
          
          // 通知runtime更新
          runtime.switchToThread(THREAD_ID);
          console.log("[Runtime] New message received:", message.source, message.content);
        }
      });

      await wsClient.connect();
      console.log("[Runtime] WebSocket connected");

    } catch (error) {
      console.error("[Runtime] Initialization failed:", error);
    }
  })();

  // 清理函数
  window.addEventListener("beforeunload", () => {
    if (wsClient) {
      wsClient.disconnect();
    }
  });

  return runtime;
}
```

**核心流程**:

1. **加载历史消息**:
   ```typescript
   const response = await fetch(`/api/threads/${THREAD_ID}/history?limit=50`);
   ```
   - 启动时加载最近50条消息
   - 填充到runtime的messages数组

2. **连接WebSocket**:
   ```typescript
   wsClient = new WebSocketClient(THREAD_ID);
   wsClient.onMessage((message) => { ... });
   await wsClient.connect();
   ```
   - 连接到`/ws/chat/default`
   - 注册消息回调

3. **接收实时消息**:
   ```typescript
   wsClient.onMessage((message) => {
     if (message.type === "new_message") {
       messages.push(newMsg);
       runtime.switchToThread(THREAD_ID);
     }
   });
   ```
   - 接收到新消息时添加到runtime
   - 自动更新UI

---

### 2.3 index.css（字体修复）

**位置**: `/client/src/index.css`

**新增部分**（第80-95行）：

```css
/* ========================================
   Tailwind工具类覆盖（确保字体样式生效）
   ======================================== */

/* 强制覆盖Tailwind的text-sm和text-base */
.text-sm {
  font-size: 15px !important;
  line-height: 1.7 !important;
}

.text-base {
  font-size: 15px !important;
  line-height: 1.7 !important;
}

/* 小标签保持13px */
.text-xs {
  font-size: 13px !important;
  line-height: 1.5 !important;
}
```

**说明**:
- v1.9已经优化了body的字体（15px, line-height 1.7）
- 但是Tailwind的工具类（如`text-sm`）会覆盖body样式
- 使用`!important`强制覆盖Tailwind的默认值

**效果对比**:

| 元素 | v1.9 | v2.2 |
|------|------|------|
| **body** | 15px ✅ | 15px ✅ |
| **带text-sm的div** | 14px ❌ | 15px ✅ |
| **带text-base的p** | 16px ❌ | 15px ✅ |

---

### 2.4 package.json（版本号）

**位置**: `/package.json`

```json
{
  "name": "m3-agent-ui",
  "version": "2.2",
  "description": "M3 Agent System UI with WebSocket Triangle Chat Room"
}
```

---

### 2.5 M3Thread.tsx（已有，无需修改）

**位置**: `/client/src/components/chat/M3Thread.tsx`

**关键代码**（第48-60行）：

```typescript
// 根据source显示不同样式
const isUser = message.role === "user" && message.metadata?.source === "user";
const isApi = message.role === "user" && message.metadata?.source === "api";
const isAssistant = message.role === "assistant";

return (
  <div className={cn(
    "flex gap-3 p-4",
    isUser && "flex-row-reverse bg-blue-50",
    isApi && "bg-green-50",
    isAssistant && "bg-gray-50"
  )}>
    {/* ... */}
  </div>
);
```

**说明**: v1.9已经实现了根据`metadata.source`区分显示，v2.2保持不变。

---

## 3. 数据流分析

### 3.1 启动流程

```
1. 用户打开页面
   ↓
2. runtime.ts初始化
   ↓
3. 加载历史消息
   GET /api/threads/default/history
   ↓
4. 连接WebSocket
   WS /ws/chat/default
   ↓
5. 显示聊天界面
```

### 3.2 发送消息流程

```
1. 用户输入消息
   ↓
2. runtime.streamText()
   ↓
3. POST /api/chat
   { message: "你好", thread_id: "default", source: "user" }
   ↓
4. 后端处理
   - 记录到数据库
   - 调用Agent
   - 广播到WebSocket
   ↓
5. 前端接收WebSocket消息
   ↓
6. 更新UI显示
```

### 3.3 接收API消息流程

```
1. 外部API调用后端
   POST /api/chat
   { message: "主播你好", thread_id: "default", source: "api" }
   ↓
2. 后端处理
   - 记录到数据库
   - 调用Agent
   - 广播到WebSocket
   ↓
3. 前端接收WebSocket消息
   { type: "new_message", source: "api", content: "主播你好" }
   ↓
4. M3Thread.tsx显示为绿色气泡（左侧）
```

---

## 4. 样式规范

### 4.1 消息气泡样式

| 角色 | 位置 | 背景色 | 文字颜色 |
|------|------|--------|----------|
| **user** | 右侧 | `bg-blue-50` | 默认 |
| **api** | 左侧 | `bg-green-50` | 默认 |
| **assistant** | 左侧 | `bg-gray-50` | 默认 |

### 4.2 字体规范

| 元素 | 字体大小 | 行高 | 字重 |
|------|----------|------|------|
| **正文** | 15px | 1.7 | 400 |
| **标题h1** | 22px | 1.4 | 600 |
| **标题h2** | 20px | 1.4 | 600 |
| **标题h3** | 18px | 1.4 | 600 |
| **标题h4** | 16px | 1.4 | 600 |
| **小标签** | 13px | 1.5 | 400 |

---

## 5. 开发指南

### 5.1 本地开发

```bash
# 安装依赖
cd ui
pnpm install

# 启动开发服务器
pnpm dev

# 访问
open http://localhost:5173
```

### 5.2 环境配置

**开发环境**:
```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:8888',
      '/ws': {
        target: 'ws://localhost:8888',
        ws: true
      }
    }
  }
});
```

**生产环境**:
```nginx
# nginx.conf
location /api/ {
    proxy_pass http://192.168.9.125:8888/;
}

location /ws/ {
    proxy_pass http://192.168.9.125:8888/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

---

### 5.3 添加新的消息来源

**步骤**:

1. **后端**: 在`ChatRequest`中添加新的source值
```python
source: str = "user"  # user/api/assistant/newSource
```

2. **前端**: 在`M3Thread.tsx`中添加新的样式
```typescript
const isNewSource = message.metadata?.source === "newSource";

<div className={cn(
  "flex gap-3 p-4",
  isNewSource && "bg-purple-50"  // 新来源用紫色
)}>
```

3. **测试**:
```bash
curl -X POST http://localhost:8888/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "测试", "thread_id": "default", "source": "newSource"}'
```

---

## 6. 故障排查

### 6.1 WebSocket连接失败

**症状**: Console显示"WebSocket disconnected"

**排查**:
1. 检查nginx配置：
```bash
docker exec m3-agent-ui cat /etc/nginx/conf.d/default.conf | grep -A 5 "location /ws"
```

2. 测试WebSocket端点：
```bash
wscat -c ws://192.168.9.125:8081/ws/chat/default
```

3. 检查后端日志：
```bash
docker logs m3-agent-backend | grep WebSocket
```

---

### 6.2 历史消息不显示

**症状**: 打开页面后看不到历史消息

**排查**:
1. 检查API响应：
```bash
curl http://192.168.9.125:8081/api/threads/default/history
```

2. 检查Console：
```javascript
// 打开浏览器Console，查看是否有错误
[Runtime] Loading history...
[Runtime] Loaded 10 history messages
```

3. 检查数据库：
```bash
docker exec m3-agent-backend sqlite3 /app/data/memory_buffer.db \
  "SELECT COUNT(*) FROM dialogue WHERE thread_id='default';"
```

---

### 6.3 字体样式不生效

**症状**: 字体显示为13px或14px，而不是15px

**排查**:
1. 检查Computed样式：
   - 打开DevTools → Elements
   - 选中消息文字
   - 查看Computed标签中的font-size

2. 检查CSS加载：
```bash
curl http://192.168.9.125:8081/assets/index.css | grep "text-sm"
```

3. 清除浏览器缓存：
   - Ctrl+Shift+R (Windows)
   - Cmd+Shift+R (Mac)

---

## 7. 性能优化

### 7.1 消息加载优化

**当前**: 启动时加载50条历史消息

**优化方案**:
- 使用虚拟滚动（react-window）
- 分页加载（每次20条）
- 懒加载图片和附件

### 7.2 WebSocket优化

**当前**: 每个tab页一个连接

**优化方案**:
- 使用SharedWorker共享连接
- 减少心跳包频率（60秒）
- 压缩消息（gzip）

---

## 8. 未来规划

### 8.1 短期（v2.3）
- [ ] 添加消息搜索功能
- [ ] 支持Markdown渲染
- [ ] 添加代码高亮

### 8.2 中期（v2.4-v2.5）
- [ ] 支持文件上传
- [ ] 添加语音消息
- [ ] 实现消息引用

### 8.3 长期（v3.0）
- [ ] 多线程支持（切换不同对话）
- [ ] 用户系统（登录/注册）
- [ ] 主题切换（暗色模式）

---

## 9. 附录

### 9.1 技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| **React** | 18.3.1 | UI框架 |
| **TypeScript** | 5.6.2 | 类型系统 |
| **Vite** | 5.4.2 | 构建工具 |
| **Tailwind CSS** | 4.0.0 | 样式框架 |
| **@assistant-ui/react** | 0.5.76 | 聊天UI组件 |

### 9.2 相关文档
- [后端v5.5技术报告](../m3-agent-v5.2.0/TECH_REPORT_v5.5.md)
- [v1.9交付文档](./M3AgentUIv1.9.0最终交付文档.md)
- [部署指南](./DEPLOYMENT_GUIDE.md)

### 9.3 联系方式
- GitHub: https://github.com/celebrityfeet2020-stack/m3-agent-system
- Docker Hub: https://hub.docker.com/r/junpeng999/m3-agent-ui

---

**文档版本**: 1.0
**最后更新**: 2025-12-04
**作者**: Manus AI
