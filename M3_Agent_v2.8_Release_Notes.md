# M3 Agent v2.8 Release Notes

## 🎯 版本概述

**M3 Agent v2.8** 是一个重要的功能增强版本，主要实现了跨平台RPA功能，让Agent能够控制物理设备，并修复了v2.7的已知问题。

**发布日期**: 2025-12-03  
**版本号**: v2.8  
**基于**: v2.7

---

## 🚀 新功能

### 1. **跨平台RPA工具**（核心功能）

**功能描述**：Agent现在可以通过SSH连接到物理设备，控制鼠标、键盘和应用程序。

**支持的平台**：
- ✅ Windows（通过PowerShell）
- ✅ macOS（通过AppleScript）
- ✅ Linux（通过Bash）

**支持的操作**：
- 鼠标控制：移动、点击、双击、右键
- 键盘控制：输入文本、按键、快捷键
- 屏幕截图
- 运行应用程序
- 执行平台特定脚本

**技术实现**：
- 核心库：PyAutoGUI
- macOS：AppleScript
- Windows：PowerShell
- Linux：Bash

**使用示例**：
```python
# Agent通过SSH连接到Mac Studio
ssh_tool.execute("kori@192.168.9.125", "python3 /path/to/rpa_tool.py --action move_mouse --x 100 --y 200")

# Agent通过SSH连接到Windows
ssh_tool.execute("admin@192.168.9.29", "powershell C:\\path\\to\\rpa_tool.ps1 -Action Click -X 100 -Y 200")
```

### 2. **文件同步工具** (需要Docker卷挂载)

**功能描述**：在容器和宿主机之间同步文件。

**支持的位置**：
- Desktop（桌面）
- Downloads（下载）
- Documents（文档）

**支持的操作**：
- 从容器复制文件到宿主机
- 从宿主机复制文件到容器
- 列出宿主机文件

**Docker配置**：
```bash
docker run -d \
  -v /Users/kori/Desktop:/host_desktop \
  -v /Users/kori/Downloads:/host_downloads \
  -v /Users/kori/Documents:/host_documents \
  junpeng999/m3-agent-system:v2.8-arm64

### 3. **SSH自连接** (可选，用于RPA)

**功能描述**：让M3 Agent能够通过SSH连接到自己的宿主机（例如Mac Studio），从而控制物理桌面。

**配置步骤**：

1. **在宿主机上开启SSH服务**：
   - **macOS**: 系统设置 -> 共享 -> 远程登录 -> 开启
   - **Linux**: `sudo systemctl start ssh`
   - **Windows**: 设置 -> 应用 -> 可选功能 -> 添加功能 -> OpenSSH服务器

2. **在M3容器中配置SSH密钥** (推荐，免密登录)：
   ```bash
   # 在容器内生成SSH密钥
   docker exec m3-agent ssh-keygen -t rsa -b 4096 -N '' -f ~/.ssh/id_rsa

   # 将公钥添加到宿主机
   docker exec m3-agent ssh-copy-id -i ~/.ssh/id_rsa.pub kori@192.168.9.125
   ```

3. **或者在M3容器中配置SSH密码** (不推荐)：
   ```bash
   docker run -d \
     -e HOST_SSH_PASSWORD="your_host_ssh_password" \
     junpeng999/m3-agent-system:v2.8-arm64
   ```

**使用示例**：
```python
# Agent通过SSH连接到自己的宿主机
ssh_tool.execute(
    host="kori@192.168.9.125",
    command="osascript -e 'tell application "Safari" to activate'"
)
```
```

---

## 🔧 问题修复

### 1. **修复Fleet API的psutil问题**

**问题描述**：v2.7的Fleet API在获取CPU/内存使用情况时会抛出`ModuleNotFoundError: No module named 'psutil'`错误。

**修复方案**：
- 在`requirements.txt`中添加`psutil==6.1.0`
- 在`fleet_api.py`中将`psutil`导入移到文件顶部

**影响的端点**：
- `GET /api/fleet/agent/status`

### 2. **完善Browser Automation测试**

**改进内容**：
- 在GitHub Actions的AMD64构建中添加了Browser Automation测试
- 测试headless模式下的浏览器自动化功能
- 确保Chromium在CI环境中正常工作

---

## 📦 依赖更新

### 新增依赖

| 包名 | 版本 | 用途 |
| :--- | :--- | :--- |
| `psutil` | 6.1.0 | 系统资源监控 |
| `pyautogui` | 0.9.54 | RPA自动化 |

### 系统依赖

| 包名 | 用途 |
| :--- | :--- |
| `x11-utils` | X11工具 |
| `xdotool` | X11自动化 |
| `scrot` | 屏幕截图 |
| `python3-tk` | Tkinter支持 |
| `python3-dev` | Python开发头文件 |

---

## 🎯 升级指南

### 从v2.7升级到v2.8

1. **拉取v2.8镜像**：
   ```bash
   docker pull junpeng999/m3-agent-system:v2.8-arm64

### 3. **SSH自连接** (可选，用于RPA)

**功能描述**：让M3 Agent能够通过SSH连接到自己的宿主机（例如Mac Studio），从而控制物理桌面。

**配置步骤**：

1. **在宿主机上开启SSH服务**：
   - **macOS**: 系统设置 -> 共享 -> 远程登录 -> 开启
   - **Linux**: `sudo systemctl start ssh`
   - **Windows**: 设置 -> 应用 -> 可选功能 -> 添加功能 -> OpenSSH服务器

2. **在M3容器中配置SSH密钥** (推荐，免密登录)：
   ```bash
   # 在容器内生成SSH密钥
   docker exec m3-agent ssh-keygen -t rsa -b 4096 -N '' -f ~/.ssh/id_rsa

   # 将公钥添加到宿主机
   docker exec m3-agent ssh-copy-id -i ~/.ssh/id_rsa.pub kori@192.168.9.125
   ```

3. **或者在M3容器中配置SSH密码** (不推荐)：
   ```bash
   docker run -d \
     -e HOST_SSH_PASSWORD="your_host_ssh_password" \
     junpeng999/m3-agent-system:v2.8-arm64
   ```

**使用示例**：
```python
# Agent通过SSH连接到自己的宿主机
ssh_tool.execute(
    host="kori@192.168.9.125",
    command="osascript -e 'tell application "Safari" to activate'"
)
```
   ```

2. **停止旧容器**：
   ```bash
   docker stop m3-agent
   docker rm m3-agent
   ```

3. **启动v2.8容器**（完整配置）：
   ```bash
   docker run -d \
     --name m3-agent \
     --restart unless-stopped \
     -p 8888:8000 \
     -p 8889:8001 \
     -v m3-agent-data:/data \
     -v /Users/kori/Desktop:/host_desktop \
     -v /Users/kori/Downloads:/host_downloads \
     -v /Users/kori/Documents:/host_documents \
     -e OPENAI_API_KEY="your_key" \
     -e TAVILY_API_KEY="your_key" \
     -e D5_API_URL="http://10.7.7.6:8000" \
     -e AGENT_ID="m3-mac-studio-001" \
     junpeng999/m3-agent-system:v2.8-arm64

### 3. **SSH自连接** (可选，用于RPA)

**功能描述**：让M3 Agent能够通过SSH连接到自己的宿主机（例如Mac Studio），从而控制物理桌面。

**配置步骤**：

1. **在宿主机上开启SSH服务**：
   - **macOS**: 系统设置 -> 共享 -> 远程登录 -> 开启
   - **Linux**: `sudo systemctl start ssh`
   - **Windows**: 设置 -> 应用 -> 可选功能 -> 添加功能 -> OpenSSH服务器

2. **在M3容器中配置SSH密钥** (推荐，免密登录)：
   ```bash
   # 在容器内生成SSH密钥
   docker exec m3-agent ssh-keygen -t rsa -b 4096 -N '' -f ~/.ssh/id_rsa

   # 将公钥添加到宿主机
   docker exec m3-agent ssh-copy-id -i ~/.ssh/id_rsa.pub kori@192.168.9.125
   ```

3. **或者在M3容器中配置SSH密码** (不推荐)：
   ```bash
   docker run -d \
     -e HOST_SSH_PASSWORD="your_host_ssh_password" \
     junpeng999/m3-agent-system:v2.8-arm64
   ```

**使用示例**：
```python
# Agent通过SSH连接到自己的宿主机
ssh_tool.execute(
    host="kori@192.168.9.125",
    command="osascript -e 'tell application "Safari" to activate'"
)
```
   ```

4. **验证部署**：
   ```bash
   curl http://localhost:8888/health
   ```

---

## 📊 性能指标

| 指标 | v2.7 | v2.8 | 变化 |
| :--- | :--- | :--- | :--- |
| **镜像大小** | ~2.5GB | ~2.6GB | +100MB |
| **启动时间** | ~15秒 | ~15秒 | 无变化 |
| **工具数量** | 13个 | 15个 | +2个 |
| **Fleet API端点** | 9个 | 9个 | 无变化 |

---

## 🔮 未来计划（v2.9）

1. **Faster-Whisper**：提升语音识别速度4-5倍
2. **多Agent协同**：M3之间的任务分配和协作
3. **更多RPA功能**：图像识别、OCR集成
4. **性能优化**：减少镜像大小，提升启动速度

---

## 📝 已知问题

1. **RPA工具在容器内无法直接使用**：需要通过SSH连接到物理设备
2. **文件同步需要Docker卷挂载**：需要在`docker run`命令中通过`-v`参数配置，否则文件同步工具无法工作。
3. **RPA工具需要SSH连接**：RPA工具必须通过SSH连接到物理设备才能使用，无法直接在容器内控制宿主机桌面。

---

## 👥 贡献者

- **Manus AI** - 核心开发

---

## 📄 许可证

MIT License
