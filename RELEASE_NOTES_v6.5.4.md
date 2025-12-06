# Agent6 v6.5.4 Release Notes

**发布日期**: 2025-12-07  
**版本**: v6.5.4  
**类型**: 重大修复版本

---

## 🎯 核心修复

### 1. ✅ 修复管理面板所有问题

#### 1.1 系统运行时间
- **问题**: 刷新网页就归零（前端计时器）
- **修复**: 改为从后端API获取容器启动时间
- **API**: `GET /api/dashboard/status` 返回 `uptime` 和 `started_at`

#### 1.2 LLM后端状态
- **问题**: 无法自动检测端口8000的模型
- **修复**: 实现自动检测逻辑，调用 `/v1/models` 端点
- **API**: `GET /api/models` 返回模型列表和当前模型
- **支持**: OpenAI兼容API（vLLM、Ollama、LM Studio等）

#### 1.3 Agent API状态
- **问题**: 没有定时更新机制
- **修复**: 实现定时任务系统
  - 启动后5分钟首次更新
  - 之后每30分钟定期更新
- **API**: `GET /api/agent-status` 返回工具数量、配置模型等

#### 1.4 模型性能测试
- **问题**: 没有定时测试机制
- **修复**: 实现定时性能测试
  - 启动后20分钟首次测试
  - 之后每15分钟定期测试
  - 与Agent API状态错开15分钟，减少性能损耗
- **API**: `GET /api/dashboard/performance` 返回性能数据

#### 1.5 内存预加载倒计时
- **问题**: 刷新网页就归零（前端计时器）
- **修复**: 改为从后端API获取实际预加载状态
- **API**: `GET /api/dashboard/preload-status` 返回状态和剩余时间

#### 1.6 元提示词
- **更新**: 使用A6通用系统提示词v2.0（终极版）
- **位置**: `/app/data/system_prompts.json`
- **特性**: 
  - 四大核心原则（诚实、联网、安全、结构化）
  - 15种工具详解
  - OODA循环工作流程

### 2. ✅ 修复Docker健康检查

- **问题**: 缺少 `/health` 端点，容器标记为unhealthy
- **修复**: 添加健康检查端点
- **端点**: `GET /health` 返回 `{"status": "healthy"}`

### 3. ✅ 优化模型预下载

- **EasyOCR**: 预下载英文和中文简体模型
- **Whisper**: 预下载small模型
- **效果**: 
  - 启动时间从20分钟缩短到2分钟（⬇️90%）
  - 容器立即标记为healthy

### 4. ✅ 修复聊天室白屏

- **问题**: 前端编译后文件路径不对
- **修复**: 
  - 优化Dockerfile多阶段构建
  - 确保前端dist目录正确复制到 `/app/chatroom_ui_dist`
  - 验证构建输出

---

## 📊 性能对比

| 指标 | v6.5.2 | v6.5.4 | 改进 |
|:---|:---:|:---:|:---:|
| **启动时间** | 20分钟 | 2分钟 | ⬇️ 90% |
| **容器健康** | unhealthy | healthy | ✅ |
| **API完整性** | 缺失2个端点 | 完整 | ✅ |
| **定时任务** | 无 | 有 | ✅ |
| **元提示词** | v1.0 | v2.0 | ✅ |
| **聊天室** | 白屏 | 正常 | ✅ |

---

## 🔧 技术细节

### 新增API端点

1. `GET /health` - Docker健康检查
2. `GET /api/models` - LLM模型检测
3. `GET /api/agent-status` - Agent API状态
4. `GET /api/dashboard/status` - 系统状态（包含运行时间）
5. `GET /api/dashboard/preload-status` - 预加载状态
6. `GET /api/dashboard/health` - 健康检测详情
7. `GET /api/dashboard/performance` - 性能数据

### 定时任务系统

```python
# Agent API状态更新
- 首次: 启动后5分钟
- 周期: 每30分钟

# 模型性能测试
- 首次: 启动后20分钟
- 周期: 每15分钟
```

### Dockerfile优化

```dockerfile
# Stage 1: 前端编译
FROM node:22-alpine AS frontend-builder
RUN pnpm run build

# Stage 2: 后端 + 模型预下载
FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy
RUN python3 -c "import easyocr; ..."
RUN python3 -c "import whisper; ..."
COPY --from=frontend-builder /build/dist /app/chatroom_ui_dist
```

---

## 🚀 部署说明

### 拉取镜像

```bash
# ARM64 (M3/Apple Silicon)
docker pull junpeng999/agent6:v6.5.4-arm64

# AMD64 (Intel/AMD)
docker pull junpeng999/agent6:v6.5.4-amd64
```

### 启动容器

```bash
docker run -d --name agent6 \
  -p 8888:8888 \
  -p 8889:8889 \
  --restart unless-stopped \
  junpeng999/agent6:v6.5.4-arm64
```

### 验证部署

```bash
# 等待60秒后验证
sleep 60

# 检查健康状态
curl http://localhost:8889/health

# 检查聊天室UI
curl -I http://localhost:8889/chatroom/

# 检查Agent API
curl http://localhost:8888/health
```

### 访问地址

- **聊天室UI**: http://localhost:8889/chatroom/
- **管理面板**: http://localhost:8889/admin
- **Agent API**: http://localhost:8888/
- **API文档**: http://localhost:8888/docs

---

## 📋 已知问题

### v6.5.5待修复

1. **Dockerfile优化**: 删除多余的 `playwright install chromium`（基础镜像已包含）
2. **日志优化**: 减少冗余日志输出
3. **多语言OCR**: 添加更多语言支持（日韩等）

---

## 🙏 致谢

感谢用户的详细反馈和耐心测试！

---

**下一版本**: v6.5.5（优化版本）  
**预计发布**: 2025-12-08
