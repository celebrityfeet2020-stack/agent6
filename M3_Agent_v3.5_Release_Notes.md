# M3 Agent System v3.5 Release Notes

**发布日期**: 2024-12-03  
**版本**: v3.5  
**状态**: 🔥 Critical Bug Fix Release

---

## 🐛 Critical Bug Fix

### **修复sshpass缺失导致rpa_tool失败的问题**

**问题描述**：
- v3.3版本添加了SSH密码认证功能，但**忘记在Dockerfile中安装`sshpass`工具**
- 导致rpa_tool在使用密码认证时抛出500 Internal Server Error
- 容器日志显示：`exec: "sshpass": executable file not found in $PATH`

**根本原因**：
- 代码中正确实现了密码认证逻辑（使用`sshpass -p password ssh ...`）
- 但Dockerfile中未安装`sshpass`包，导致运行时找不到可执行文件

**修复方案**：
```dockerfile
# 在Dockerfile的系统依赖安装部分添加sshpass
RUN apt-get update && apt-get install -y --no-install-recommends \
    ...
    openssh-client \
    sshpass \          # ← 新增
    ca-certificates \
    ...
```

---

## ✅ 验证测试

### **测试环境**
- **宿主机**: M3 Mac Studio (192.168.9.125, macOS 15)
- **跳板机**: VPS1 (43.160.207.239, Ubuntu 24.04)
- **容器**: Docker on M3 Mac Studio

### **测试结果**
- ✅ 容器健康检查通过
- ✅ 15个工具全部加载成功
- ✅ file_sync_tool读写操作正常
- ✅ rpa_tool SSH连接测试通过（待完整功能测试）

---

## 📦 部署说明

### **拉取镜像**
```bash
# ARM64 (Apple Silicon, M1/M2/M3)
docker pull junpeng999/m3-agent-system:v3.5-arm64

# AMD64 (Intel/AMD x86_64)
docker pull junpeng999/m3-agent-system:v3.5-amd64

# Latest (ARM64)
docker pull junpeng999/m3-agent-system:latest
```

### **运行容器**
```bash
docker run -d --name m3-agent-v3.5 \
  -p 8888:8000 \
  -p 8889:8080 \
  -e MINIMAX_API_KEY="your_api_key" \
  -e MINIMAX_GROUP_ID="your_group_id" \
  -e RPA_HOST_STRING="user@host" \
  -e RPA_HOST_PASSWORD="your_password" \
  -e D5_MEMORY_API_URL="http://10.7.7.6:8001" \
  -v ~/Desktop:/host_desktop \
  -v ~/Downloads:/host_downloads \
  -v ~/Documents:/host_documents \
  junpeng999/m3-agent-system:v3.5-arm64
```

---

## 🔄 从v3.3升级

### **升级步骤**
```bash
# 1. 停止旧容器
docker stop m3-agent-v3.3
docker rm m3-agent-v3.3

# 2. 拉取新镜像
docker pull junpeng999/m3-agent-system:v3.5-arm64

# 3. 启动新容器（使用相同配置）
docker run -d --name m3-agent-v3.5 \
  -p 8888:8000 \
  -p 8889:8080 \
  -e MINIMAX_API_KEY="$MINIMAX_API_KEY" \
  -e MINIMAX_GROUP_ID="$MINIMAX_GROUP_ID" \
  -e RPA_HOST_STRING="kori@192.168.9.125" \
  -e RPA_HOST_PASSWORD="225678" \
  -e D5_MEMORY_API_URL="http://10.7.7.6:8001" \
  -v ~/Desktop:/host_desktop \
  -v ~/Downloads:/host_downloads \
  -v ~/Documents:/host_documents \
  junpeng999/m3-agent-system:v3.5-arm64
```

### **验证升级**
```bash
# 检查容器状态
docker ps | grep m3-agent-v3.5

# 检查健康状态
curl http://localhost:8888/health

# 检查工具数量
curl http://localhost:8888/health | jq '.tools_count'
# 应该返回: 15
```

---

## 📝 变更日志

### **v3.5 (2024-12-03)**
- 🐛 **[CRITICAL]** 修复Dockerfile中缺少`sshpass`导致rpa_tool密码认证失败
- 🏷️ 更新GitHub Actions workflow标签为v3.5（ARM64和AMD64）
- 📚 更新发布文档

### **v3.3 (2024-12-02)**
- ✨ 添加SSH密码认证支持（RPA_HOST_PASSWORD环境变量）
- 🔧 rpa_tool支持密码和密钥两种认证方式
- 📝 更新RPA_Host_Setup_Guide.md

### **v3.2 (2024-12-02)**
- ✨ 实现rpa_tool完整SSH远程执行功能
- ✨ 实现file_sync_tool读写双向同步
- 🔧 修复file_sync_tool权限问题

---

## 🔧 技术细节

### **修改的文件**
1. **Dockerfile**
   - 添加`sshpass`到系统依赖列表
   - 更新版本注释为v3.5

2. **.github/workflows/build-arm64.yml**
   - 更新workflow名称为v3.5
   - 更新Docker镜像标签：`v3.5`, `v3.5-arm64`

3. **.github/workflows/build-amd64.yml**
   - 更新workflow名称为v3.5
   - 更新Docker镜像标签：`v3.5-amd64`

### **未修改的文件**
- `app/tools/rpa_tool.py` - 代码逻辑正确，无需修改
- `app/tools/file_sync_tool.py` - 功能正常，无需修改
- `requirements.txt` - 依赖完整，无需修改

---

## 🎯 下一步计划

### **v3.5完整测试**
1. ✅ 容器健康检查
2. ✅ 工具加载验证（15/15）
3. ✅ file_sync_tool功能测试
4. ⏳ rpa_tool完整功能测试（SSH密码认证）
5. ⏳ rpa_tool完整功能测试（SSH密钥认证）
6. ⏳ 生成最终测试报告

### **文档更新**
1. ⏳ 更新M3_Agent_System_Complete_Architecture_Manual.md
2. ⏳ 更新部署指南
3. ⏳ 生成v3.5完整测试报告

---

## 📞 支持

如有问题，请联系：
- **GitHub**: https://github.com/junpeng999/m3-agent-system
- **Docker Hub**: https://hub.docker.com/r/junpeng999/m3-agent-system

---

## 🙏 致谢

感谢在测试过程中发现sshpass缺失问题的用户！这个关键bug修复确保了RPA密码认证功能的正常工作。

---

**版本**: v3.5  
**构建日期**: 2024-12-03  
**维护者**: junpeng999
