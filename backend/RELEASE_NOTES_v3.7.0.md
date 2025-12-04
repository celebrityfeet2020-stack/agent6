# 🚀 Agent System v3.7.0 正式版发布说明

**版本号**: `3.7.0`  
**发布日期**: 2025-12-03  
**Docker 镜像**: `junpeng999/agent-system:v3.7.0`

---

## ✨ 核心亮点

**v3.7.0 是一个里程碑式的版本**，我们一次性集成了所有规划的功能，并修复了历史遗留问题。现在，Agent 系统更加强大、稳定，并且为多 Agent、多前端的复杂场景做好了准备。

### 主要特性

1.  **SSE 流式输出**：全新的 `/stream/...` 接口，为前端提供实时的"打字机效果"和"思考过程"展示，用户体验大幅提升。
2.  **记忆同步增强**：每一条存入 D5 记忆航母的记忆，都增加了详细的 `metadata` 标签，包含 `source`, `interface`, `client_id` 等信息，实现了真正的"黑匣子"级全链路日志。
3.  **管理面板优化**：
    *   修复了端口映射问题（`8889:8002`）
    *   工具数量动态获取（不再硬编码）
    *   系统性能监控优化为**每小时更新一次**（降低资源消耗）
4.  **多 Agent 兼容**：通过 `AGENT_ID` 和 `client_id` 的设计，系统现在天生支持多个 Agent 实例同时运行，记忆互不干扰。

---

## ✅ 详细更新日志

### 新功能 (Features)

*   **[API]** 新增 `/stream/chat/{thread_id}` SSE 接口，用于流式传输 Agent 的思考过程和回复
*   **[Memory]** 增强 `add_memory` 函数，支持记录 `source`, `interface`, `client_id`, `agent_id` 等元数据
*   **[Memory]** 新增 `memory_logger.py` 模块，提供便捷的记忆记录函数
*   **[Admin]** 管理面板新增"系统性能"模块，实时显示 CPU、内存、磁盘使用率

### 修复 (Fixes)

*   **[Admin]** 修复了管理面板端口映射错误的问题（`8889:8080` → `8889:8002`）
*   **[Admin]** 修复了工具数量硬编码为 13 的问题，现在会动态从 Agent API 获取
*   **[Admin]** 修复了 `/api/status` 接口中 `api_port` 硬编码为 `8001` 的问题，修正为 `8000`

### 优化 (Improvements)

*   **[Admin]** 系统性能监控优化为**每小时执行一次**，降低资源消耗
*   **[System]** 系统正式更名为 "Agent System"，以适应多设备、多实例部署场景
*   **[Docs]** 全面更新文档，与 v3.7.0 功能保持一致
*   **[CI/CD]** 更新 GitHub Actions 工作流，自动构建和发布 v3.7.0 版本的 Docker 镜像
*   **[Repo]** 清理 git 仓库冗余文件

---

## 🛠️ 部署指南

### Docker 拉取命令

```bash
# ARM64 (M3 Mac Studio)
docker pull junpeng999/agent-system:v3.7.0-arm64

# AMD64 (Linux 服务器)
docker pull junpeng999/agent-system:v3.7.0-amd64
```

### 完整部署命令 (以 M3 Mac Studio 为例)

```bash
docker run -d --name agent-system-v3.7 \
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
  junpeng999/agent-system:v3.7.0-arm64
```

---

## 🧪 验证步骤

1.  **Agent API**: `curl http://localhost:8888/health`
2.  **管理面板**: 浏览器访问 `http://localhost:8889`，检查工具数量和系统性能是否正常显示
3.  **SSE 流式接口**: 使用前端或 curl 进行测试

---

## 📊 性能优化说明

### 系统性能监控优化

v3.7.0 对系统性能监控进行了重要优化：

*   **旧版本 (v3.6.0)**：每次访问管理面板都会实时采集系统性能数据（CPU、内存、磁盘），导致不必要的资源消耗。
*   **新版本 (v3.7.0)**：采用**缓存机制**，系统性能数据每小时更新一次，大幅降低资源消耗。

这一优化特别适合长期运行的 Agent 系统，可以减少对宿主机的性能影响。

---

感谢您的耐心和支持！v3.7.0 是一个更加成熟和强大的版本，期待它在您的数字人系统中发挥更大的作用！🚀
