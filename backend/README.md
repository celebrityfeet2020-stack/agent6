# Agent System v3.6.0-beta

**Agent System** 是一个基于LangGraph的企业级智能Agent系统，支持15种工具调用、跨平台RPA、记忆同步和OpenAI兼容接口。

**版本**: v3.6.0-beta  
**发布日期**: 2025-12-03  
**更新类型**: 关键修复 + 系统更名  
**基于版本**: v3.5.0

---

## 🎯 v3.6.0-beta 更新内容

### 关键修复
- ✅ **修复管理面板端口映射**：将宿主机8889端口正确映射到容器内8002端口
- ✅ **系统更名**：从"M3 Agent System"更名为通用的"Agent System"
- ✅ **AGENT_ID增强**：新增`AGENT_ID`环境变量，支持多Agent场景下的唯一标识

### 配置优化
- ✅ 更新Docker Compose配置，端口映射更清晰
- ✅ 更新环境变量示例，添加AGENT_ID配置说明
- ✅ 优化文档和注释，提升可维护性

### 向后兼容
- ✅ **完全兼容v3.5**：所有现有功能保持不变
- ✅ **增量改造**：仅修复必要问题，不影响稳定性

---

## 🛠️ 功能特性

### 15个工具模块
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
13. **Speech Recognition** - 语音识别
14. **RPA Tool** - 跨平台RPA自动化 (v2.8+)
15. **File Sync** - 容器与宿主机文件同步 (v2.8+)

### Fleet API
- 完整的D5集成接口
- 支持任务分配、状态上报、结果回传
- 记忆系统集成接口
- Agent注册与心跳机制

### 记忆同步机制
- 本地SQLite暂存 + 后台批量同步
- 支持操作日志、思考链、对话历史、系统日志
- 异步处理，零性能损失
- 支持多Agent场景（通过AGENT_ID区分）

### RPA自动化
- 支持Windows/macOS/Linux
- 鼠标、键盘、屏幕截图、应用控制
- 通过SSH连接到物理设备
- v3.5修复sshpass缺失问题

---

## 🚀 快速开始

### 方式一：Docker Run（推荐）

```bash
# 适用于M3 Mac Studio (ARM64)
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

```bash
# 适用于Linux服务器 (AMD64)
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

### 方式二：Docker Compose

```bash
# 1. 克隆或下载源代码
git clone https://github.com/your-org/agent-system.git
cd agent-system

# 2. 复制环境变量配置
cp .env.example .env

# 3. 编辑.env文件，配置LLM和AGENT_ID
nano .env

# 4. 启动服务
docker-compose up -d

# 5. 查看日志
docker-compose logs -f agent-system-api
```

### 环境变量说明

| 变量名 | 必需 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `LLM_BASE_URL` | ✅ | - | LLM服务的API地址 |
| `LLM_MODEL` | ✅ | - | 使用的模型标识符 |
| `AGENT_ID` | ⭐ 推荐 | `agent-unknown` | Agent实例的唯一标识符 |
| `RPA_HOST_STRING` | 可选 | - | RPA目标主机（格式：`user@host`） |
| `RPA_HOST_PASSWORD` | 可选 | - | RPA目标主机密码 |
| `D5_MEMORY_API_URL` | 可选 | - | D5记忆航母API地址 |

---

## 📡 API接口

### Agent API (端口 8888)
- `GET /` - 系统信息
- `GET /health` - 健康检查
- `POST /api/chat` - 对话接口
- `GET /api/tools` - 工具列表
- 更多接口请参考完整文档

### 管理面板 (端口 8889)
- `http://<host>:8889` - Web管理界面
- 实时监控Agent状态
- 工具调用日志
- 系统性能指标

---

## 🔧 开发与贡献

### 本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
nano .env

# 3. 运行主程序
python main.py

# 4. 运行管理面板（另一个终端）
python admin_app.py
```

---

## 📚 文档

- [完整部署指南](docs/deployment.md)
- [API接口文档](docs/api.md)
- [工具开发指南](docs/tools.md)
- [RPA配置指南](RPA_Host_Setup_Guide.md)

---

## 🐛 已知问题

- 无

---

## 📝 版本历史

### v3.6.0-beta (2025-12-03)
- 修复管理面板端口映射
- 系统更名为"Agent System"
- 新增AGENT_ID环境变量

### v3.5.0 (2024-12-03)
- 修复sshpass缺失，RPA功能完整可用
- 100%工具加载率

### v2.8 (2024-12-03)
- 新增RPA工具和文件同步工具
- 修复psutil依赖问题

### v2.7 (2024-12-03)
- Whisper模型预装
- LangGraph API适配层
- 记忆同步机制

---

## 📄 许可证

MIT License

---

## 🙏 致谢

感谢所有贡献者和用户的支持！

**Agent System Team**  
*Building the Future of AI Automation*
