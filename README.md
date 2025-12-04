# M3 Agent System - Triangle Chat Room Edition

**Version:** Backend v5.8.0 | Frontend v2.2

## 项目概述

M3 Agent System 是一个集成了 LangGraph、FastAPI 和 React 的智能代理系统，支持实时三角聊天室功能（Triangle Chat Room），实现用户、API 和助手之间的多源实时通信。

### 核心特性

- **三角聊天室（Triangle Chat Room）**：三个消息源（user/api/assistant）共享同一 thread_id，实现多方实时通信
- **混合消息传输**：WebSocket 实时推送 + SSE 流式响应的混合架构
- **消息持久化**：所有对话记录存储到 SQLite（memory_buffer.db），支持历史查询
- **双架构支持**：后端同时支持 ARM64 和 AMD64 架构
- **性能优化**：WebSocket 替代轮询，显著降低 CPU 和数据库负载
- **完整工具集**：集成 30+ 工具（浏览器自动化、代码执行、图像分析等）

## 技术栈

### 后端 (v5.8.0)
- **框架**：Python 3.11 + FastAPI + LangGraph
- **数据库**：SQLite (memory_buffer.db)
- **通信**：WebSocket + SSE streaming
- **LLM**：LM Studio (Qwen3-VL-235b) on port 8000
- **容器化**：Docker (ARM64 & AMD64)

### 前端 (v2.2)
- **框架**：React 18 + TypeScript + Vite
- **UI 库**：@assistant-ui/react + Tailwind CSS v4
- **通信**：WebSocket Client + SSE Adapter
- **样式**：15px 字体 + line-height 1.7（优化可读性）

## 仓库结构

```
m3-agent-system-repo/
├── backend/                    # 后端代码 (v5.8.0)
│   ├── app/
│   │   ├── main.py            # FastAPI 主应用
│   │   ├── websocket_manager.py  # WebSocket 连接管理
│   │   ├── memory/
│   │   │   └── memory_logger.py  # 对话日志记录
│   │   ├── tools/             # 30+ 工具集
│   │   └── api/               # API 适配器
│   ├── config/                # 配置文件
│   ├── Dockerfile             # Docker 构建文件
│   ├── requirements.txt       # Python 依赖
│   └── TECH_REPORT_v5.8.md   # 技术文档
├── frontend/                   # 前端代码 (v2.2)
│   ├── client/
│   │   └── src/
│   │       ├── lib/
│   │       │   ├── runtime.ts          # 运行时（集成 WebSocket）
│   │       │   └── websocket-client.ts # WebSocket 客户端
│   │       ├── components/
│   │       │   └── M3Thread.tsx        # 聊天界面
│   │       └── styles/
│   │           └── index.css           # 样式（字体优化）
│   ├── nginx.conf             # Nginx 配置（API/WS 代理）
│   ├── Dockerfile             # Docker 构建文件
│   ├── package.json           # Node.js 依赖
│   └── TECH_REPORT_v2.2.md   # 技术文档
└── .github/
    └── workflows/
        ├── build-backend-arm64.yml   # ARM64 构建流程
        ├── build-backend-amd64.yml   # AMD64 构建流程
        └── build-frontend.yml        # 前端构建流程
```

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/junpeng999/m3-agent-system.git
cd m3-agent-system
```

### 2. 部署后端 (v5.8.0)

```bash
# ARM64 架构（如 Apple Silicon、树莓派）
docker pull junpeng999/agent-system:v5.8.0-arm64
docker run -d -p 8888:8001 --name m3-backend junpeng999/agent-system:v5.8.0-arm64

# AMD64 架构（如 Intel/AMD 服务器）
docker pull junpeng999/agent-system:v5.5-amd64
docker run -d -p 8888:8001 --name m3-backend junpeng999/agent-system:v5.5-amd64
```

### 3. 部署前端 (v2.2)

```bash
docker pull junpeng999/m3-agent-ui:v2.2
docker run -d -p 8081:80 --name m3-frontend junpeng999/m3-agent-ui:v2.2
```

### 4. 访问系统

- **前端界面**：http://localhost:8081
- **后端 API**：http://localhost:8888/docs
- **WebSocket**：ws://localhost:8888/ws/chat/{thread_id}

## 三角聊天室使用指南

### 消息源类型

系统支持三种消息源，通过 `source` 参数区分：

1. **user**：用户通过前端 UI 发送的消息
2. **api**：外部系统通过 API 发送的消息
3. **assistant**：AI 助手生成的响应消息

### API 调用示例

```bash
# 用户消息
curl -X POST http://localhost:8888/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，请帮我分析一下数据",
    "thread_id": "thread_123",
    "source": "user"
  }'

# API 消息（外部系统推送）
curl -X POST http://localhost:8888/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "系统检测到异常事件",
    "thread_id": "thread_123",
    "source": "api"
  }'
```

### WebSocket 连接

```javascript
const ws = new WebSocket('ws://localhost:8888/ws/chat/thread_123');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(`[${message.source}] ${message.content}`);
};
```

### 查询历史记录

```bash
curl http://localhost:8888/api/threads/thread_123/history
```

## CI/CD 自动化构建

本项目使用 GitHub Actions 实现自动化构建和发布：

### 触发方式

1. **推送到 main 分支**：自动构建最新版本
2. **创建版本标签**：
   - `v5.5-arm64`：构建后端 ARM64 镜像
   - `v5.5-amd64`：构建后端 AMD64 镜像
   - `ui-v2.2`：构建前端镜像

### 手动触发构建

```bash
# 后端 ARM64
git tag v5.5-arm64
git push origin v5.5-arm64

# 后端 AMD64
git tag v5.5-amd64
git push origin v5.5-amd64

# 前端
git tag ui-v2.2
git push origin ui-v2.2
```

## 配置说明

### 后端配置

编辑 `backend/config/settings.py`：

```python
# LM Studio 配置
LM_STUDIO_BASE_URL = "http://localhost:8000/v1"
LM_STUDIO_MODEL = "qwen3-vl-235b"

# 数据库配置
DATABASE_PATH = "./memory_buffer.db"

# WebSocket 配置
WEBSOCKET_HEARTBEAT_INTERVAL = 30
```

### 前端配置

编辑 `frontend/client/.env`：

```bash
VITE_API_BASE_URL=http://192.168.9.125:8888
VITE_WS_BASE_URL=ws://192.168.9.125:8888
```

## 性能优化

### WebSocket vs 轮询

- **轮询方式**：每秒 1 次请求 = 86,400 次/天
- **WebSocket**：持久连接 + 事件驱动 = 接近 0 次轮询

**资源节省**：
- CPU 使用率降低 90%+
- 数据库查询减少 99%+
- 网络带宽节省 95%+

### 字体优化

前端采用 15px 字体 + 1.7 行高，优化长时间阅读体验：

```css
body {
  font-size: 15px;
  line-height: 1.7;
}
```

## 技术文档

- **后端技术报告**：[backend/TECH_REPORT_v5.5.md](backend/TECH_REPORT_v5.5.md)
- **前端技术报告**：[frontend/TECH_REPORT_v2.2.md](frontend/TECH_REPORT_v2.2.md)
- **CI/CD 管道文档**：[docs/GitHubActionsCI_CD管道深度报告.md](docs/GitHubActionsCI_CD管道深度报告.md)

## 版本历史

### v5.5 (Backend) - 2024-12-04
- ✅ 新增三角聊天室功能（Triangle Chat Room）
- ✅ 实现 WebSocket 实时消息推送
- ✅ 添加消息源（source）参数支持
- ✅ 集成 memory_buffer.db 对话日志
- ✅ 新增历史记录查询 API
- ✅ 修复 LM Studio 连接（端口 8000）

### v2.2 (Frontend) - 2024-12-04
- ✅ 集成 WebSocket 客户端
- ✅ 重写 runtime.ts 支持实时更新
- ✅ 优化字体样式（15px + line-height 1.7）
- ✅ 添加 Nginx API/WebSocket 代理
- ✅ 支持消息源差异化显示

## 许可证

MIT License

## 联系方式

- **项目维护者**：junpeng999
- **Docker Hub**：https://hub.docker.com/u/junpeng999
- **GitHub**：https://github.com/junpeng999

---

**注意**：本项目处于持续迭代开发中，v5.5 和 v2.2 并非最终版本。所有代码均为可编辑源代码，方便后续修改和扩展。
