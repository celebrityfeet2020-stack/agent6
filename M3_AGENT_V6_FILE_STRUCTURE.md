# M3 Agent v6.0 - 完整文件结构说明

**作者**: Manus AI
**日期**: 2025-12-05

---

## 1. 根目录结构

```
m3-agent-v6.0-COMPLETE/
├── admin_ui/              # 管理面板 (主应用使用)
├── app/                   # 核心应用代码 (主应用使用)
├── backend/               # 后端重构目录 (v5.9遗留,保留兼容)
├── chatroom_ui/           # (新增) assistant-ui前端聊天室
├── frontend/              # (v5.9遗留) 旧版前端,保留兼容
├── ui/                    # (v5.9遗留) 旧版三角聊天室UI,保留兼容
├── admin_app.py           # (新增) v6.0统一入口应用
├── main.py                # Agent后端主应用 (LangGraph)
├── Dockerfile             # Docker镜像构建文件
├── docker-compose.yml     # Docker Compose配置
├── requirements.txt       # Python依赖
└── README.md              # 项目说明
```

---

## 2. 核心目录详解

### 2.1. `admin_ui/` - 管理面板

```
admin_ui/
├── static/                # 静态资源 (CSS, JS, 图片)
└── templates/
    ├── dashboard.html     # (v6.0) 新版管理面板
    ├── dashboard_old_v3.9.html  # 旧版备份
    └── dashboard_v6_no_prompts.html  # 无元提示词版本(废弃)
```

**功能**: 系统监控、元提示词管理、健康检测、性能监控。

**访问**: `http://localhost:8889/admin`

### 2.2. `app/` - 核心应用代码

```
app/
├── api/                   # API模块
│   ├── chat_stream.py     # (新增) 统一流式聊天API
│   ├── dashboard_api.py   # (新增) Dashboard API
│   ├── fleet_api.py       # Fleet API (舰队模式预留)
│   ├── langgraph_adapter.py  # LangGraph适配器
│   └── streaming.py       # SSE流式输出工具
├── core/                  # 核心模块
│   ├── background_tasks.py  # (新增) 后台任务管理器
│   ├── browser_pool.py    # (修复) 同步浏览器池
│   └── startup.py         # (修改) 启动逻辑
├── memory/                # 记忆管理
│   ├── memory_logger.py   # 记忆日志
│   └── memory_sync.py     # 记忆同步
├── performance/           # 性能监控
│   └── performance_monitor.py  # 性能监控器
└── tools/                 # 15个工具
    ├── web_search.py
    ├── web_scraper.py
    ├── code_executor.py
    ├── file_operations.py
    ├── image_ocr.py
    ├── image_analysis.py
    ├── ssh_tool.py
    ├── git_tool.py
    ├── data_analysis.py
    ├── browser_automation.py
    ├── api_caller.py
    ├── telegram_tool.py
    ├── speech_recognition_tool.py
    ├── rpa_tool.py
    └── file_sync_tool.py
```

### 2.3. `chatroom_ui/` - assistant-ui前端聊天室 (新增)

```
chatroom_ui/
├── dist/                  # (编译后) 静态文件输出目录
├── src/
│   ├── components/        # React组件
│   │   ├── ChatHeader.tsx
│   │   ├── ChatInput.tsx
│   │   ├── ChatMessage.tsx
│   │   ├── FileUpload.tsx
│   │   ├── Resizer.tsx
│   │   └── ThoughtChain.tsx
│   ├── hooks/             # 自定义Hooks
│   │   └── useChat.ts
│   ├── lib/               # 辅助函数
│   │   └── runtime.ts
│   ├── styles/            # CSS样式
│   │   └── index.css
│   ├── App.tsx            # 主应用组件
│   └── main.tsx           # 入口文件
├── index.html             # HTML模板
├── package.json           # 项目配置
├── tsconfig.json          # TypeScript配置
└── vite.config.ts         # Vite配置
```

**功能**: 基于assistant-ui的现代聊天界面,支持三方可见、思维链可视化、文件上传。

**访问**: `http://localhost:8889/` 或 `http://localhost:8889/chat`

### 2.4. `backend/` - 后端重构目录 (v5.9遗留)

这是v5.9版本的后端重构目录,包含了三角聊天室、统一聊天室等功能。v6.0保留此目录以确保向后兼容,但主要使用`app/`和`admin_app.py`。

```
backend/
├── admin_ui/              # 管理面板 (与根目录admin_ui类似)
├── app/                   # 应用代码 (与根目录app类似)
│   ├── api/
│   │   ├── chat_room.py   # 三角聊天室API
│   │   ├── unified_chat_room.py  # 统一聊天室API
│   │   └── streaming.py
│   └── ...
├── ui/                    # 聊天室前端
└── admin_app.py           # 后端管理应用入口
```

### 2.5. `frontend/` 和 `ui/` - 旧版前端 (v5.9遗留)

这两个目录是v5.x版本的前端代码,保留以确保兼容性。v6.0推荐使用新的`chatroom_ui/`。

---

## 3. 关键文件说明

| 文件 | 作用 | 状态 |
|---|---|---|
| `admin_app.py` | **(新增)** v6.0统一入口,提供静态文件服务和路由分发 | ✅ 核心 |
| `main.py` | Agent后端主应用,集成LangGraph和工具 | ✅ 核心 |
| `app/api/chat_stream.py` | **(新增)** 统一流式聊天API | ✅ 核心 |
| `app/core/background_tasks.py` | **(新增)** 后台任务管理器 | ✅ 核心 |
| `app/core/browser_pool.py` | **(修复)** 同步浏览器池 | ✅ 核心 |
| `admin_ui/templates/dashboard.html` | **(v6.0)** 新版管理面板 | ✅ 核心 |
| `chatroom_ui/src/App.tsx` | **(新增)** 聊天室主组件 | ⏳ 待完成 |
| `chatroom_ui/src/hooks/useChat.ts` | **(新增)** 聊天逻辑Hook | ⏳ 待完成 |
| `Dockerfile` | Docker镜像构建文件 | ⏳ 待完成 |
| `requirements.txt` | Python依赖 | ✅ 已更新 |

---

## 4. 总结

v6.0的文件结构清晰、模块化,核心代码集中在`app/`和`chatroom_ui/`,通过`admin_app.py`统一对外提供服务。同时保留了v5.9的`backend/`、`frontend/`和`ui/`目录,确保向后兼容。

完整的文件树可参考 `M3_AGENT_V6_FILE_STRUCTURE.txt`。
