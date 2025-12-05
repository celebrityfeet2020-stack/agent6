# M3 Agent System v5.9.0 部署文档

## 🚀 快速部署

### 1. 停止旧容器
```bash
docker stop m3-agent-backend
docker rm m3-agent-backend
```

### 2. 启动v5.9容器（**重要：挂载Docker socket**）
```bash
docker run -d \
  --name m3-agent-backend \
  -p 8888:8000 \
  -p 8889:8002 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e LLM_BASE_URL="https://api.siliconflow.cn/v1" \
  -e LLM_API_KEY="sk-your-api-key" \
  -e LLM_MODEL="Qwen/Qwen2.5-7B-Instruct" \
  --restart unless-stopped \
  junpeng999/agent-system:v5.9.0-local
```

**关键参数**：
- `-v /var/run/docker.sock:/var/run/docker.sock` - **挂载Docker socket**，允许code_executor使用Docker执行代码
- `-p 8888:8000` - 主API端口
- `-p 8889:8002` - 管理面板端口

---

## 🆕 v5.9新特性

### 1. 后台任务管理器（错开执行）
- **Wave 1**（每30分钟）：工具池预加载 + 性能测试
- **Wave 2**（每30分钟，延迟15分钟）：模型API检测 + 全面体检

**时间线**：
- 0分：启动
- 30分：Wave 1
- 45分：Wave 2
- 60分：Wave 1
- 75分：Wave 2
- ...

### 2. 工具池延迟加载
- 启动时不加载工具池（避免依赖冲突）
- 30分钟后由后台任务自动加载
- OCR + Whisper + Docker预加载到内存

### 3. Docker支持
- 挂载Docker socket后，code_executor可以使用Docker执行代码
- 未挂载时自动fallback到subprocess

---

## 📊 验证部署

### 1. 检查容器状态
```bash
docker ps | grep m3-agent-backend
```

应显示：`Up X seconds (healthy)`

### 2. 检查API版本
```bash
curl http://localhost:8888/ | jq
```

应返回：`"status": "M3 Agent System v5.9.0 Running"`

### 3. 检查后台任务日志
```bash
docker logs m3-agent-backend | grep "Background tasks started"
```

应显示：
```
✅ Background tasks started
   - Wave 1: every 30 minutes (tool pool + performance test)
   - Wave 2: every 30 minutes, 15 min offset (API check + health check)
```

---

## 🔧 常见问题

### Q: 为什么启动时没有加载工具池？
A: v5.9改为延迟加载，30分钟后由后台任务自动加载，避免启动时的依赖冲突。

### Q: code_executor为什么不能使用Docker？
A: 需要挂载Docker socket：`-v /var/run/docker.sock:/var/run/docker.sock`

### Q: 如何查看后台任务执行情况？
A: 查看容器日志：`docker logs -f m3-agent-backend | grep "Wave"`

---

## 📝 更新日志

### v5.9.0 (2025-12-XX)
- ✅ 后台任务管理器（两波错开执行）
- ✅ 工具池延迟加载（30分钟后）
- ✅ Docker socket挂载支持
- ✅ API版本号修复
- ✅ 性能测试和API检测定期执行

### v5.8.0 (2025-12-XX)
- ✅ 思维链 + 工具链
- ✅ 三角聊天室
- ✅ 工具池v5.8（OCR + Whisper预加载）
- ✅ 浏览器池优化
- ✅ Whisper模型配置修复

---

## 🎯 下一步

1. 等待30分钟，观察Wave 1执行
2. 等待45分钟，观察Wave 2执行
3. 验证工具池预加载成功
4. 测试code_executor的Docker功能
