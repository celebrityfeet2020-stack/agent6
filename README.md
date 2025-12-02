# M3 Agent System v2.5

**M3 Agent System** 是一个基于LangGraph的智能Agent系统，支持13种工具调用和OpenAI兼容接口。

**版本**: v2.5  
**发布日期**: 2025-12-03  
**更新类型**: Bug修复 + 功能补全  

---

## 🎯 v2.5 更新内容

### 关键修复
- ✅ 修复Healthcheck端口错误（8001→8888）
- ✅ 修复Admin端口环境变量不生效
- ✅ 修复Fleet API `report_status`函数bug
- ✅ 添加Fleet API `/task/complete`和`/task/error`接口
- ✅ **新增Speech Recognition工具**（完整实现）

### 功能优化
- ✅ Fleet API参数验证更灵活（支持整数priority）
- ✅ 完整的Fleet API文档

### 代码质量
- ✅ 清理PostgreSQL遗留代码和依赖
- ✅ 标准化部署配置

---

## 🛠️ 功能特性

### 13个工具模块
1. **Web Search** - 网页搜索
2. **Web Scraper** - 网页抓取
3. **Browser Automation** - 浏览器自动化
4. **Code Executor** - 代码执行
5. **File Operations** - 文件操作
6. **Image OCR** - 图像文字识别
7. **Image Analysis** - 图像分析
8. **SSH Tool** - SSH远程操作
9. **Git Tool** - Git版本控制
10. **Data Analysis** - 数据分析
11. **Universal API** - 通用API调用
12. **Telegram Tool** - Telegram机器人
13. **Speech Recognition** - 语音识别 ⭐ 新增

### Fleet API
- 完整的D5集成接口
- 支持任务分配、状态上报、结果回传
- 记忆系统集成接口
- 详细文档见 `docs/fleet_api.md`

---

## 🚀 快速开始

### 前置要求
- Docker 20.10+
- LM Studio或其他OpenAI兼容的LLM服务

### 标准部署

```bash
docker run -d \
  --name m3-agent-api \
  --restart unless-stopped \
  -p 8888:8888 \
  -p 8889:8889 \
  -e API_PORT=8888 \
  -e ADMIN_PORT=8889 \
  -e LLM_BASE_URL=http://host.docker.internal:8000/v1 \
  -e OPENAI_API_KEY=your-api-key \
  --add-host host.docker.internal:host-gateway \
  -v /path/to/data:/app/data \
  -v /path/to/logs:/app/logs \
  junpeng999/m3-agent-system:v2.5-arm64
```

### 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| API_PORT | API服务端口 | 8888 |
| ADMIN_PORT | 管理面板端口 | 8889 |
| LLM_BASE_URL | LLM服务地址 | http://host.docker.internal:8000/v1 |
| OPENAI_API_KEY | OpenAI API密钥（用于Speech Recognition） | - |
| LLM_MODEL | LLM模型名称 | minimax/minimax-m2 |
| LLM_TEMPERATURE | 温度参数 | 0.7 |
| LLM_MAX_TOKENS | 最大token数 | 4096 |

---

## 📡 API接口

### 主要接口

1. **聊天接口**: `POST /api/agent/chat`
2. **健康检查**: `GET /health`
3. **工具列表**: `GET /api/tools`
4. **Fleet API**: `/api/fleet/*` (详见文档)

### OpenAI兼容接口

- `POST /v1/chat/completions`
- `POST /v1/completions`
- `POST /v1/embeddings`
- `GET /v1/models`

### 管理面板

访问 `http://your-host:8889` 查看管理面板。

---

## 🔧 工具使用示例

### Speech Recognition（新增）

```python
import requests

response = requests.post(
    "http://localhost:8888/api/agent/chat",
    json={
        "message": "请转录这个音频文件：/path/to/audio.m4a",
        "thread_id": "test-001"
    }
)
print(response.json())
```

**支持的音频格式**: mp3, mp4, mpeg, mpga, m4a, wav, webm  
**文件大小限制**: 25MB  
**需要配置**: `OPENAI_API_KEY` 环境变量

### Fleet API

详细文档见 `docs/fleet_api.md`

```python
import requests

# 分配任务
response = requests.post(
    "http://localhost:8888/api/fleet/task/receive",
    json={
        "task_id": "task-001",
        "task_type": "research",
        "message": "研究AI最新进展",
        "priority": "high"
    }
)
```

---

## 📦 Docker镜像

### 可用镜像

- `junpeng999/m3-agent-system:v2.5-arm64` (Apple Silicon)
- `junpeng999/m3-agent-system:v2.5-amd64` (x86_64)

### 构建镜像

```bash
# ARM64 (Apple Silicon)
docker build -t m3-agent-system:v2.5-arm64 --platform linux/arm64 .

# AMD64 (x86_64)
docker build -t m3-agent-system:v2.5-amd64 --platform linux/amd64 .
```

---

## 🔄 从v2.3.0升级

### 升级步骤

1. **停止旧容器**:
```bash
docker stop m3-agent-api
docker rm m3-agent-api
```

2. **拉取新镜像**:
```bash
docker pull junpeng999/m3-agent-system:v2.5-arm64
```

3. **启动新容器**（使用上面的标准部署命令）

4. **验证**:
```bash
curl http://localhost:8888/health
curl http://localhost:8888/api/fleet/health
```

### 重要变更

- ✅ 端口映射方式（不再使用`--network host`）
- ✅ 所有端口通过环境变量配置
- ✅ 移除PostgreSQL依赖
- ✅ 新增Speech Recognition工具（需要OPENAI_API_KEY）

---

## ⚠️ 注意事项

### 部署注意事项

1. **不要挂载config目录**（避免配置冲突）
2. **使用端口映射**，不要使用`--network host`
3. **所有端口通过环境变量配置**
4. **Speech Recognition需要配置OPENAI_API_KEY**

### 已知限制

1. **Fleet API**: 除了`/task/receive`和`/health`，其他接口为mock实现
2. **记忆系统**: 使用内存checkpointer，重启后丢失
3. **未来计划**: 通过D5记忆航母实现集中式记忆管理

---

## 📚 文档

- [Fleet API完整文档](docs/fleet_api.md)
- [v2.5改进方案总结](docs/v2.5_improvements.md)

---

## 🐛 问题反馈

如有问题或建议，请访问：https://help.manus.im

---

## 📝 更新日志

### v2.5 (2025-12-03)

**新增**:
- Speech Recognition工具完整实现
- Fleet API `/task/complete`接口
- Fleet API `/task/error`接口
- Fleet API完整文档

**修复**:
- Healthcheck端口错误（8001→8888）
- Admin端口环境变量不生效
- Fleet API `report_status`函数NameError
- Fleet API参数验证过于严格

**优化**:
- 清理PostgreSQL遗留代码
- 标准化部署配置
- 更新README文档

**测试**:
- 完成5个核心工具测试
- 完成Fleet API全接口测试
- 验证Speech Recognition工具功能

### v2.3.0 (2025-12-01)

- 初始发布版本
- 12个工具模块
- Fleet API预留框架

---

**维护者**: M3 Agent Team  
**许可证**: MIT
