# M3 Agent v6.0 - 后端API完整文档

**作者**: Manus AI
**日期**: 2025-12-05

---

## 1. 核心API: 流式聊天

这是v6.0的核心API,用于所有聊天交互。

**端点**: `POST /api/chat/stream`

**请求体**:

```json
{
    "message": "你好,世界!",
    "thread_id": "default_session",
    "source": "user",
    "metadata": {
        "user_name": "张三",
        "device": "iPhone 15 Pro"
    }
}
```

| 字段 | 类型 | 必选 | 默认值 | 描述 |
|---|---|---|---|---|
| `message` | string | 是 | | 用户或API发送的消息内容 |
| `thread_id` | string | 否 | `default_session` | 会话ID。不传或传`default_session`表示共享会话 |
| `source` | string | 否 | `user` | 消息来源 (user/api/admin/livestream/fleet) |
| `metadata` | object | 否 | `null` | 额外元数据,用于前端显示或元提示词规则 |

**响应**: `text/event-stream` (SSE)

SSE事件包含以下类型:

- `message`: 消息事件 (用户/Agent)
- `thought`: 思维链事件
- `tool`: 工具调用事件
- `system`: 系统日志事件

**示例事件**:

```
event: message
data: {"id": "...", "timestamp": "...", "type": "message", "role": "user", "content": "你好", "source": "user", ...}


event: thought
data: {"id": "...", "timestamp": "...", "type": "thought", "content": "正在理解用户需求...", ...}


event: tool
data: {"id": "...", "timestamp": "...", "type": "tool", "tool_name": "web_search", "status": "calling", ...}
```

---

## 2. Dashboard API

用于管理面板的数据接口。

| 端点 | 方法 | 描述 |
|---|---|---|
| `/api/dashboard/status` | GET | 获取系统整体状态 (运行时间、预加载状态、健康状态) |
| `/api/dashboard/health` | GET | 获取最新的健康检测结果 |
| `/api/dashboard/performance` | GET | 获取最新的性能测试结果 |
| `/api/dashboard/preload-status` | GET | 获取内存预加载状态 |
| `/api/dashboard/trigger-health-check` | POST | 手动触发一次健康检测 |
| `/api/dashboard/trigger-performance-test` | POST | 手动触发一次性能测试 |

---

## 3. 元提示词API

用于管理元提示词。

| 端点 | 方法 | 描述 |
|---|---|---|
| `/api/prompts` | GET | 获取所有元提示词 |
| `/api/prompts` | POST | 创建新元提示词 |
| `/api/prompts/{id}` | GET | 获取单个元提示词 |
| `/api/prompts/{id}` | PUT | 更新元提示词 |
| `/api/prompts/{id}` | DELETE | 删除元提示词 |
| `/api/prompts/{id}/activate` | POST | 激活元提示词 |

---

## 4. 文件结构和代码清单

### 4.1. 目录结构

```
/app
├── /api
│   ├── chat_stream.py  # (新增) 流式聊天API
│   └── dashboard_api.py  # (新增) Dashboard API
├── /core
│   ├── background_tasks.py # (新增) 后台任务管理器
│   ├── browser_pool.py   # (修复) 同步浏览器池
│   └── startup.py        # (修改) 启动逻辑
├── /tools
│   └── ... (15个工具)
└── main.py             # (修改) 主应用,集成新API

/admin_ui
└── /templates
    └── dashboard.html    # (修改) 新版管理面板

/chatroom_ui
├── /dist               # (新增) 编译后的静态文件
├── /src
│   ├── /components     # (新增) React组件
│   └── App.tsx         # (新增) 主应用
└── package.json        # (新增) 前端项目配置
```

### 4.2. 关键代码清单

#### `app/api/chat_stream.py`

```python
# (完整代码见之前的文件写入)
class StreamChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = "default_session"
    source: Optional[str] = "user"
    metadata: Optional[Dict[str, Any]] = None

async def stream_agent_response(...) -> AsyncGenerator[str, None]:
    # ... (流式执行Agent并生成SSE事件)
```

#### `main.py`

```python
# 导入
from app.api.chat_stream import stream_agent_response, StreamChatRequest

# ...

# 注册API端点
@app.post("/api/chat/stream")
async def chat_stream(request: StreamChatRequest):
    return StreamingResponse(
        stream_agent_response(
            app_graph=app_graph,
            message=request.message,
            thread_id=request.thread_id,
            source=request.source,
            metadata=request.metadata
        ),
        media_type="text/event-stream"
    )
```

#### `admin_app.py`

```python
# 挂载静态文件
app.mount("/chat", StaticFiles(directory="../chatroom_ui/dist"), name="chat")
app.mount("/admin", StaticFiles(directory="../admin_ui/templates"), name="admin")

# 根路径重定向
@app.get("/")
async def root():
    return RedirectResponse(url="/chat")
```

---

## 5. 总结

v6.0的后端API设计清晰、功能强大,通过统一的`/api/chat/stream`端点,满足了三方可见、共享会话、灵活扩展等所有需求。同时,Dashboard和元提示词API也为系统管理提供了完整的支持。
