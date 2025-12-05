# M3 Agent v6.0 - 部署和集成指南

**作者**: Manus AI
**日期**: 2025-12-05

---

## 1. 部署方案: 混合部署

v6.0采用**混合部署**方案,将React前端编译为静态文件,由FastAPI后端统一提供服务,实现单端口访问。

**优势**:
- ✅ **单一端口**: 简化部署、网络配置和反向代理
- ✅ **无需Node.js运行时**: 生产环境只需Python
- ✅ **部署简单**: 只需一个Docker容器
- ✅ **高性能**: 静态文件由FastAPI高效提供

---

## 2. 部署步骤

### 2.1. 编译前端 (本地或CI/CD)

```bash
# 1. 进入chatroom_ui目录
cd /path/to/m3-agent-v6.0/chatroom_ui

# 2. 安装依赖
pnpm install

# 3. 编译为静态文件
pnpm run build

# 4. 静态文件输出到 dist/ 目录
# 确保 dist/ 目录已生成
```

### 2.2. 构建Docker镜像

Dockerfile会自动处理前端编译和后端集成。

```bash
# 1. 进入项目根目录
cd /path/to/m3-agent-v6.0

# 2. 构建Docker镜像
docker build -t m3-agent:v6.0 .
```

**Dockerfile (关键部分)**:

```dockerfile
# --- 1. 前端编译 ---
FROM node:20-alpine AS builder
WORKDIR /app/chatroom_ui
COPY chatroom_ui/package*.json ./
RUN npm install -g pnpm
RUN pnpm install
COPY chatroom_ui/ .
RUN pnpm run build

# --- 2. 后端 ---
FROM python:3.11-slim
WORKDIR /app

# 复制编译好的前端
COPY --from=builder /app/chatroom_ui/dist ./chatroom_ui/dist

# 复制后端代码
COPY . .

# 安装Python依赖
RUN pip install -r requirements.txt

# 暴露端口
EXPOSE 8889

# 启动
CMD ["uvicorn", "admin_app:app", "--host", "0.0.0.0", "--port", "8889"]
```

### 2.3. 运行容器

```bash
# 使用docker run
docker run -d -p 8889:8889 --name m3-agent-v6 m3-agent:v6.0

# 或使用docker-compose.yml
services:
  m3-agent:
    image: m3-agent:v6.0
    ports:
      - "8889:8889"
    restart: always
```

---

## 3. 访问和验证

- **聊天室**: `http://localhost:8889/chat`
- **管理面板**: `http://localhost:8889/admin`
- **根路径**: `http://localhost:8889/` (自动重定向到聊天室)

### 验证步骤:

1. ✅ 打开 `http://localhost:8889/chat`, 确认聊天室UI加载正常。
2. ✅ 发送一条消息,确认SSE流式响应正常。
3. ✅ 打开 `http://localhost:8889/admin`, 确认管理面板加载正常。
4. ✅ 检查元提示词管理功能是否可用。
5. ✅ 检查Dashboard的系统状态是否实时更新。

---

## 4. Nginx反向代理 (可选)

如果需要使用域名访问,可以配置Nginx反向代理。

```nginx
server {
    listen 80;
    server_name your-agent-domain.com;

    location / {
        proxy_pass http://localhost:8889;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 支持WebSocket
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 支持SSE流
        proxy_buffering off;
        proxy_cache off;
    }
}
```

---

## 5. 总结

v6.0的部署流程清晰、简单,通过Docker和混合部署方案,实现了单容器、单端口的极简部署。这大大降低了维护成本,并为未来的水平扩展提供了便利。
