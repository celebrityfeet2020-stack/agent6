# M3 Agent System v3.2 部署指南

## 快速部署

```bash
# 1. 停止旧版本
docker stop m3-agent-v3.1 2>/dev/null || true
docker rm m3-agent-v3.1 2>/dev/null || true

# 2. 拉取v3.2镜像
docker pull junpeng999/m3-agent-system:v3.2-arm64

# 3. 启动v3.2容器（注意：宿主机目录改为读写模式）
docker run -d \
  --name m3-agent-v3.2 \
  --restart always \
  -p 8888:8000 \
  -p 8889:8001 \
  -v m3-agent-data:/data \
  -v /Users/kori/Desktop:/host_desktop:rw \
  -v /Users/kori/Downloads:/host_downloads:rw \
  -v /Users/kori/Documents:/host_documents:rw \
  -v /Users/kori/.ssh:/root/.ssh:ro \
  -e MINIMAX_API_KEY="${MINIMAX_API_KEY}" \
  -e MINIMAX_GROUP_ID="${MINIMAX_GROUP_ID}" \
  -e RPA_HOST_STRING="kori@192.168.9.125" \
  -e D5_MEMORY_API_URL="http://10.7.7.6:8000/api/memory/receive" \
  junpeng999/m3-agent-system:v3.2-arm64

# 4. 验证部署
sleep 15
curl http://localhost:8888/health
```

## v3.2 重要变更

### 1. 宿主机目录挂载模式变更

**旧版本（v3.0, v3.1）**：
```bash
-v /Users/kori/Desktop:/host_desktop:ro   # 只读
-v /Users/kori/Downloads:/host_downloads:ro
-v /Users/kori/Documents:/host_documents:ro
```

**v3.2**：
```bash
-v /Users/kori/Desktop:/host_desktop:rw    # 读写
-v /Users/kori/Downloads:/host_downloads:rw
-v /Users/kori/Documents:/host_documents:rw
```

**原因**：file_sync_tool需要写入权限才能将容器中的文件复制到宿主机。

### 2. rpa_tool SSH远程执行

v3.2的rpa_tool通过SSH连接到宿主机执行RPA操作，需要：

1. **SSH免密登录**：确保容器可以通过SSH免密登录到宿主机
   ```bash
   # 在宿主机上测试
   ssh kori@192.168.9.125 "echo 'SSH连接正常'"
   ```

2. **宿主机安装pyautogui**：
   ```bash
   # macOS
   pip3 install pyautogui
   
   # Linux (Debian/Ubuntu)
   sudo apt-get install python3-tk python3-dev scrot
   pip3 install pyautogui
   
   # Windows
   pip install pyautogui
   ```

3. **环境变量RPA_HOST_STRING**：已在docker run命令中设置

## 功能测试

### 测试file_sync_tool

```bash
curl -X POST http://localhost:8888/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "请在容器中创建一个测试文件/tmp/test.txt，内容为'Hello M3'，然后使用file_sync_tool将它复制到宿主机Desktop",
    "thread_id": "test_file_sync"
  }'
```

预期结果：Desktop目录中出现test.txt文件。

### 测试rpa_tool

```bash
curl -X POST http://localhost:8888/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "请使用rpa_tool获取宿主机的屏幕截图",
    "thread_id": "test_rpa"
  }'
```

预期结果：返回截图文件路径。

## 故障排查

### file_sync_tool无法写入

**症状**：`[Errno 30] Read-only file system`

**解决**：
1. 检查docker run命令中的挂载模式是否为`:rw`
2. 重新创建容器

### rpa_tool SSH连接失败

**症状**：`SSH connection failed`

**解决**：
1. 检查SSH免密登录：
   ```bash
   docker exec m3-agent-v3.2 ssh -o StrictHostKeyChecking=no kori@192.168.9.125 "echo test"
   ```

2. 检查宿主机pyautogui：
   ```bash
   ssh kori@192.168.9.125 "python3 -c 'import pyautogui; print(pyautogui.__version__)'"
   ```

3. 检查RPA_HOST_STRING环境变量：
   ```bash
   docker exec m3-agent-v3.2 env | grep RPA_HOST_STRING
   ```

## 版本对比

| 特性 | v3.0/v3.1 | v3.2 |
|:---|:---:|:---:|
| file_sync_tool读取 | ✅ | ✅ |
| file_sync_tool写入 | ❌ 只读 | ✅ 读写 |
| rpa_tool | ❌ 无SSH | ✅ SSH远程执行 |
| 宿主机目录挂载 | 只读 | 读写 |

## 安全建议

由于宿主机目录改为读写模式，建议：

1. **限制Agent权限**：不要给Agent执行危险操作的权限
2. **监控文件操作**：定期检查Desktop/Downloads/Documents目录的变化
3. **备份重要文件**：在升级前备份重要数据
4. **使用专用账户**：考虑为M3 Agent创建专用的macOS账户，限制其访问范围

## 回滚方案

如果v3.2出现问题，可以回滚到v3.1：

```bash
docker stop m3-agent-v3.2
docker rm m3-agent-v3.2

docker run -d \
  --name m3-agent-v3.1 \
  --restart always \
  -p 8888:8000 \
  -p 8889:8001 \
  -v m3-agent-data:/data \
  -v /Users/kori/Desktop:/host_desktop:ro \
  -v /Users/kori/Downloads:/host_downloads:ro \
  -v /Users/kori/Documents:/host_documents:ro \
  -v /Users/kori/.ssh:/root/.ssh:ro \
  -e MINIMAX_API_KEY="${MINIMAX_API_KEY}" \
  -e MINIMAX_GROUP_ID="${MINIMAX_GROUP_ID}" \
  -e RPA_HOST_STRING="kori@192.168.9.125" \
  -e D5_MEMORY_API_URL="http://10.7.7.6:8000/api/memory/receive" \
  junpeng999/m3-agent-system:v3.1-arm64
```
