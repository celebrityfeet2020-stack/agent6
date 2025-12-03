# Agent System v3.6.0-beta 发布说明

**发布日期**: 2025年12月03日  
**版本号**: v3.6.0-beta  
**基于版本**: v3.5.0  
**发布类型**: Beta测试版（关键修复）

---

## 📋 概述

v3.6.0-beta 是一个**关键修复版本**，主要解决了 v3.5 中管理面板无法访问的问题，并为后续的 v3.6.0-rc（SSE流式改造）做好准备。本版本遵循**最小改动原则**，仅修复必要问题，确保不影响现有稳定功能。

---

## 🎯 核心更新

### 1. 修复管理面板端口映射 ✅

**问题描述**：
- v3.5 文档中的 Docker 启动命令错误地将宿主机 `8889` 端口映射到容器内的 `8080` 端口
- 但管理面板实际监听的是容器内的 `8002` 端口
- 导致访问 `http://<host>:8889` 时无法打开管理面板

**修复方案**：
- 修改 Docker Compose 配置，将端口映射改为 `8889:8002`
- 更新所有文档中的示例命令

**影响范围**：
- ✅ 管理面板现在可以正常访问
- ✅ 不影响 Agent API（端口 8888）的正常工作

### 2. 系统更名 ✅

**更名原因**：
- 原名"M3 Agent System"特指M3 Mac Studio设备
- 为了支持多设备部署（如A3090ti-3、D5母舰等），需要更通用的命名
- 便于在D5记忆航母中区分不同设备上的Agent实例

**更名内容**：
- Docker镜像名：`m3-agent-system` → `agent-system`
- 容器名：`m3-agent-api` → `agent-system-api`
- 文档标题和注释中的"M3 Agent System" → "Agent System"

**向后兼容**：
- ✅ 所有API接口保持不变
- ✅ 环境变量保持不变
- ✅ 工具模块保持不变

### 3. AGENT_ID 环境变量增强 ⭐

**新增功能**：
- 新增 `AGENT_ID` 环境变量，用于唯一标识Agent实例
- 在多Agent场景下，D5记忆航母可以通过`AGENT_ID`区分不同Agent的记忆

**配置示例**：
```bash
# M3 Mac Studio上的Agent
-e AGENT_ID="agent-m3-coo"

# A3090ti-3上的数字人内核Agent
-e AGENT_ID="agent-3090ti-kernel"

# D5母舰上的管理Agent
-e AGENT_ID="agent-d5-ceo"
```

**默认值**：
- 如果不配置，默认为 `agent-unknown`
- **强烈建议**在生产环境中配置有意义的`AGENT_ID`

---

## 📦 部署更新

### Docker Run 命令（ARM64 - M3 Mac Studio）

```bash
docker run -d --name agent-system-v3.6 \
  -p 8888:8000 \
  -p 8889:8002 \
  -e LLM_BASE_URL="http://192.168.9.125:8000/v1" \
  -e LLM_MODEL="Qwen/Qwen3-30B" \
  -e AGENT_ID="agent-m3-coo" \
  -e RPA_HOST_STRING="kori@192.168.9.125" \
  -e RPA_HOST_PASSWORD="225678" \
  -v ~/Desktop:/host_desktop \
  -v ~/Downloads:/host_downloads \
  -v ~/Documents:/host_documents \
  -v ~/.ssh:/root/.ssh:ro \
  junpeng999/agent-system:v3.6.0-beta-arm64
```

### Docker Run 命令（AMD64 - Linux服务器）

```bash
docker run -d --name agent-system-v3.6 \
  -p 8888:8000 \
  -p 8889:8002 \
  -e LLM_BASE_URL="http://localhost:8080/v1" \
  -e LLM_MODEL="qwen3-30b" \
  -e AGENT_ID="agent-3090ti-kernel" \
  -e RPA_HOST_STRING="a3090ti-3@localhost" \
  -e RPA_HOST_PASSWORD="225678" \
  -v /home/a3090ti-3/Desktop:/host_desktop \
  -v /home/a3090ti-3/Downloads:/host_downloads \
  -v /home/a3090ti-3/Documents:/host_documents \
  -v /home/a3090ti-3/.ssh:/root/.ssh:ro \
  junpeng999/agent-system:v3.6.0-beta-amd64
```

### Docker Compose 配置

```yaml
version: '3.8'

services:
  agent-system-api:
    image: agent-system:v3.6.0-beta
    container_name: agent-system-api
    ports:
      - "8888:8000"  # Agent API
      - "8889:8002"  # Admin Panel
    environment:
      LLM_BASE_URL: "http://192.168.9.125:8000/v1"
      LLM_MODEL: "Qwen/Qwen3-30B"
      AGENT_ID: "agent-m3-coo"
      # ... 其他环境变量
```

---

## 🧪 测试验证

### 验证步骤

1. **部署容器**：
   ```bash
   docker run -d --name agent-system-v3.6 ...
   ```

2. **验证Agent API**：
   ```bash
   curl http://localhost:8888/health
   # 预期输出：{"status":"healthy"}
   ```

3. **验证管理面板**：
   - 浏览器访问：`http://localhost:8889`
   - 预期：能够正常打开管理面板Web界面

4. **验证工具加载**：
   ```bash
   curl http://localhost:8888/api/tools | jq '.tools | length'
   # 预期输出：15
   ```

5. **验证AGENT_ID**：
   ```bash
   docker logs agent-system-v3.6 2>&1 | grep "AGENT_ID"
   # 预期输出：包含您配置的AGENT_ID
   ```

---

## 📊 性能指标

| 指标 | v3.5.0 | v3.6.0-beta | 变化 |
| :--- | :--- | :--- | :--- |
| Docker镜像大小 | ~2.6GB | ~2.6GB | 无变化 |
| 容器启动时间 | ~15秒 | ~15秒 | 无变化 |
| 工具加载数量 | 15个 | 15个 | 无变化 |
| 内存占用 | ~500MB | ~500MB | 无变化 |
| 管理面板可访问性 | ❌ | ✅ | **修复** |

---

## 🔄 从 v3.5 升级

### 升级步骤

1. **停止旧容器**：
   ```bash
   docker stop m3-agent-v3.5
   docker rm m3-agent-v3.5
   ```

2. **拉取新镜像**：
   ```bash
   # ARM64
   docker pull junpeng999/agent-system:v3.6.0-beta-arm64
   
   # AMD64
   docker pull junpeng999/agent-system:v3.6.0-beta-amd64
   ```

3. **启动新容器**（使用上文的Docker Run命令）

4. **验证功能**（使用上文的验证步骤）

### 数据迁移

- ✅ **无需数据迁移**：v3.6.0-beta 与 v3.5 完全兼容
- ✅ **记忆数据**：如果挂载了数据卷，记忆数据会自动保留

---

## ⚠️ 已知问题

- 无

---

## 🚀 下一步计划

### v3.6.0-rc（计划中）

1. **SSE流式改造**：
   - 新增 `/stream/chat/{thread_id}` 和 `/stream/logs` 接口
   - 支持实时打字机效果和日志推送
   - 完全向后兼容，不影响现有API

2. **记忆同步增强**：
   - 在记忆的`metadata`中增加`source`, `interface`, `client_id`等字段
   - 支持区分用户、API、Agent三方对话
   - 支持并发场景下的记忆完整性

3. **前端对接**：
   - 实现前端SSE事件流接收
   - 点亮实时监控面板（`thought / tool / system` 事件）

---

## 📞 支持与反馈

如果您在使用过程中遇到任何问题，请通过以下方式联系我们：

- GitHub Issues: [https://github.com/your-org/agent-system/issues](https://github.com/your-org/agent-system/issues)
- Email: support@your-org.com

---

**Agent System Team**  
*Building the Future of AI Automation*
