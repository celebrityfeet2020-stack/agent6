# M3 Agent System v5.1.0 Release Notes

**发布日期**: 2025-12-03  
**版本类型**: Bug Fix Release  
**基于版本**: v5.0.0

---

## 🐛 Bug修复

### 1. 修复Event Loop冲突 (Critical)

**问题描述**:  
v5.0.0在启动时报错：
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**根本原因**:  
浏览器池在模块导入时就调用`sync_playwright().start()`，与Admin Panel的event loop冲突。

**解决方案**:  
- 将浏览器池初始化移到FastAPI的`startup`事件
- 将workflow编译也移到`startup`事件
- 新增`app/core/startup.py`统一管理启动流程

**影响范围**: 后端启动流程

---

### 2. 修复前端Nginx配置 (Critical)

**问题描述**:  
前端容器启动失败：
```
nginx: [emerg] host not found in upstream "backend" in /etc/nginx/conf.d/default.conf:26
```

**根本原因**:  
nginx配置中有`proxy_pass http://backend:8000/api/;`，但Docker容器中不存在名为"backend"的主机。

**解决方案**:  
- 删除nginx中的backend代理配置
- 前端直接使用环境变量`VITE_API_BASE_URL`访问后端

**影响范围**: 前端nginx配置

---

## ✅ 保留的v5.0性能优化

v5.1.0**完全保留**了v5.0的所有性能优化：

### 1. 全局浏览器池 (90%性能提升)
- ✅ 浏览器在startup事件中**预加载到内存**
- ✅ 3个Playwright工具共享浏览器实例
- ✅ 性能提升：5-10秒 → 0.5-1秒

### 2. 模型预加载 (60%性能提升)
- ✅ ImageAnalysisTool: Haar Cascade预加载
- ✅ SpeechRecognitionTool: Whisper模型预加载

---

## 📦 部署升级

### Docker部署 (推荐)

#### 后端v5.1.0
```bash
# 拉取镜像
docker pull junpeng999/agent-system:v5.1.0-arm64

# 停止旧容器
docker stop agent-system-v5.0
docker rm agent-system-v5.0

# 启动v5.1.0
docker run -d --name agent-system-v5.1 \
  -p 8888:8000 \
  -p 8889:8002 \
  -e LLM_BASE_URL="http://192.168.9.125:8000/v1" \
  -e LLM_MODEL="qwen3-next-80b-a3b-thinking-mlx" \
  -e ADMIN_PORT=8002 \
  junpeng999/agent-system:v5.1.0-arm64
```

#### 前端UI v1.8.0 (已修复)
```bash
# 拉取镜像
docker pull junpeng999/m3-agent-ui:1.8.0

# 停止旧容器
docker stop m3-ui
docker rm m3-ui

# 启动v1.8.0
docker run -d -p 80:80 \
  -e VITE_API_BASE_URL="http://192.168.9.125:8888" \
  --name m3-ui \
  junpeng999/m3-agent-ui:1.8.0
```

---

## 🧪 验证测试

### 1. 验证后端启动
```bash
# 查看日志
docker logs agent-system-v5.1

# 应该看到：
# ✅ Browser pool pre-loaded into memory (v5.1)
# ✅ 15 tools initialized with browser pool (v5.1)
# ✅ Startup complete: browser pool, tools, and workflow ready
```

### 2. 验证前端启动
```bash
# 查看日志
docker logs m3-ui

# 应该看到nginx正常启动，没有backend错误
```

### 3. 验证API
```bash
# 测试后端
curl http://192.168.9.125:8888/

# 应该返回：
# {"status":"M3 Agent System v5.1.0 Running","tools":15,...}

# 测试前端
curl http://192.168.9.125/

# 应该返回HTML页面
```

---

## 📊 版本对比

| 版本 | 状态 | 主要问题 |
|------|------|----------|
| v3.9.0 | ✅ 稳定 | 性能未优化 |
| v5.0.0 | ❌ 失败 | Event loop冲突 + nginx配置错误 |
| v5.1.0 | ✅ 稳定 | 修复所有问题，保留性能优化 |

---

## 🔗 相关文档

- [v5.0性能优化技术报告](TECH_REPORT_v5.0.0.md)
- [工具加载机制分析](TOOL_LOADING_ANALYSIS.md)
- [v3.9技术报告](TECH_REPORT_v3.9.0.md)

---

## 👥 贡献者

- Manus AI Agent - 代码实现与测试
- M3 Team - 需求与反馈
