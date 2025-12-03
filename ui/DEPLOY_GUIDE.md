# M3 Agent UI 前端部署指南

**版本**: v1.0  
**日期**: 2025-12-03  
**作者**: Manus AI

---

## 1. 部署架构

为了实现最佳性能与 SSE 流式传输的稳定性，我们推荐采用 **Nginx + Docker** 的部署方案：

*   **前端容器**: 运行 Nginx，负责托管静态资源 (React Build) 并反向代理 API 请求。
*   **后端容器**: 运行 Python FastAPI 服务 (Agent System)。

## 2. 快速开始

### 2.1 构建镜像

在项目根目录下执行以下命令构建前端镜像：

```bash
docker build -f Dockerfile.prod -t m3-agent-ui:latest .
```

### 2.2 启动容器

使用 Docker 运行前端容器，并将其连接到后端网络：

```bash
docker run -d \
  --name m3-agent-ui \
  -p 80:80 \
  --link backend_container_name:backend \
  m3-agent-ui:latest
```

> **注意**: 请将 `backend_container_name` 替换为您实际运行的后端容器名称。

## 3. Docker Compose 编排（推荐）

如果您希望一键启动前后端，可以使用以下 `docker-compose.yml` 配置：

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./m3-agent-ui
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
    depends_on:
      - backend

  backend:
    build:
      context: ./agent_system_v3.6
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=your_key_here
```

## 4. 关键配置说明

### 4.1 Nginx SSE 优化
在 `nginx.conf` 中，我们已经针对 SSE 做了特殊配置，确保流式数据不被缓存：

```nginx
location /api/ {
    proxy_pass http://backend:8000/api/;
    # 关键配置：关闭缓冲，支持长连接
    proxy_buffering off;
    proxy_read_timeout 24h;
    proxy_set_header Connection "upgrade";
}
```

### 4.2 环境变量
前端代码中的 API 地址默认为 `/api/v1/chat/stream`，通过 Nginx 转发，因此**无需在前端构建时注入后端 URL**，这使得镜像具有更好的可移植性。

---

**M3 Agent Team**  
*Deployment Engineering*
