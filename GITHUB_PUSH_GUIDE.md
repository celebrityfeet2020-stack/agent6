# GitHub 推送指南

## 前置准备

### 1. 创建GitHub仓库

访问 https://github.com/new 创建新仓库：

- **仓库名称**：`m3-agent-system`
- **描述**：M3 Agent System - Triangle Chat Room Edition (Backend v5.5 + Frontend v2.2)
- **可见性**：Public 或 Private（根据需求选择）
- **不要**勾选 "Initialize this repository with a README"（我们已经有了）

### 2. 配置GitHub Personal Access Token

1. 访问：https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 勾选权限：
   - `repo`（完整仓库访问权限）
   - `workflow`（GitHub Actions权限）
4. 生成并保存Token（只显示一次）

### 3. 配置Docker Hub Secrets

为了让GitHub Actions能够推送Docker镜像，需要在GitHub仓库中配置Secrets：

1. 进入仓库页面：`https://github.com/junpeng999/m3-agent-system`
2. 点击 `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret`，添加以下两个Secrets：

   **Secret 1:**
   - Name: `DOCKERHUB_USERNAME`
   - Value: `junpeng999`

   **Secret 2:**
   - Name: `DOCKERHUB_TOKEN`
   - Value: [您的Docker Hub Access Token]

**获取Docker Hub Token：**
1. 登录 https://hub.docker.com
2. 点击右上角头像 → Account Settings
3. 点击 Security → New Access Token
4. 输入Token名称（如 `github-actions`）
5. 选择权限：Read & Write
6. 生成并复制Token

## 推送代码到GitHub

### 方法1：使用HTTPS（推荐）

```bash
cd /home/ubuntu/m3-agent-system-repo

# 添加远程仓库
git remote add origin https://github.com/junpeng999/m3-agent-system.git

# 推送代码和标签
git push -u origin main
git push origin --tags

# 验证推送
git remote -v
```

**注意**：首次推送时会要求输入GitHub用户名和Personal Access Token（作为密码）。

### 方法2：使用SSH（需要配置SSH密钥）

```bash
cd /home/ubuntu/m3-agent-system-repo

# 添加远程仓库（SSH方式）
git remote add origin git@github.com:junpeng999/m3-agent-system.git

# 推送代码和标签
git push -u origin main
git push origin --tags
```

## 验证推送成功

### 1. 检查代码

访问：`https://github.com/junpeng999/m3-agent-system`

应该能看到：
- ✅ backend/ 目录（34个Python文件）
- ✅ frontend/ 目录（80个TS/TSX文件）
- ✅ .github/workflows/ 目录（3个workflow文件）
- ✅ README.md 文档
- ✅ 3个版本标签（v5.5-arm64, v5.5-amd64, ui-v2.2）

### 2. 检查GitHub Actions

访问：`https://github.com/junpeng999/m3-agent-system/actions`

应该能看到3个自动触发的工作流：
- ✅ Build Backend ARM64
- ✅ Build Backend AMD64
- ✅ Build Frontend

### 3. 监控构建进度

点击每个工作流查看构建日志：
- 构建时间：约10-20分钟（取决于网络和GitHub Actions资源）
- 成功标志：绿色✓图标
- 失败标志：红色✗图标（需要查看日志排查）

### 4. 验证Docker镜像

构建完成后，访问Docker Hub验证镜像：

- ARM64后端：https://hub.docker.com/r/junpeng999/agent-system/tags
  - 应该有标签：`v5.5-arm64`, `latest-arm64`
- AMD64后端：https://hub.docker.com/r/junpeng999/agent-system/tags
  - 应该有标签：`v5.5-amd64`, `latest-amd64`
- 前端：https://hub.docker.com/r/junpeng999/m3-agent-ui/tags
  - 应该有标签：`v2.2`, `latest`

## 常见问题

### Q1: 推送失败 - Authentication failed

**原因**：GitHub用户名或Token错误

**解决**：
```bash
# 重新配置凭据
git config --global credential.helper store
git push -u origin main
# 输入正确的用户名和Token
```

### Q2: GitHub Actions构建失败

**原因**：Docker Hub Secrets未配置或配置错误

**解决**：
1. 检查仓库Settings → Secrets → Actions
2. 确认 `DOCKERHUB_USERNAME` 和 `DOCKERHUB_TOKEN` 已正确配置
3. 重新触发构建：
   ```bash
   git commit --allow-empty -m "Trigger rebuild"
   git push origin main
   ```

### Q3: Docker镜像推送失败

**原因**：Docker Hub Token权限不足或已过期

**解决**：
1. 重新生成Docker Hub Token（Read & Write权限）
2. 更新GitHub Secrets中的 `DOCKERHUB_TOKEN`
3. 重新触发构建

### Q4: 构建速度慢

**原因**：GitHub Actions免费版资源有限

**优化方案**：
- 使用缓存（已配置 `cache-from: type=gha`）
- 避免频繁推送触发构建
- 考虑升级到GitHub Pro（更多并发资源）

## 后续更新流程

### 更新代码并重新构建

```bash
cd /home/ubuntu/m3-agent-system-repo

# 修改代码后提交
git add .
git commit -m "Update: 描述修改内容"
git push origin main

# 如果需要更新版本号，创建新标签
git tag v5.6-arm64
git tag v5.6-amd64
git tag ui-v2.3
git push origin --tags
```

### 仅构建特定架构

```bash
# 仅触发ARM64构建
git tag v5.5-arm64-rebuild
git push origin v5.5-arm64-rebuild

# 仅触发AMD64构建
git tag v5.5-amd64-rebuild
git push origin v5.5-amd64-rebuild

# 仅触发前端构建
git tag ui-v2.2-rebuild
git push origin ui-v2.2-rebuild
```

## 部署到M3服务器

构建完成后，在M3服务器上部署：

```bash
# SSH连接到M3服务器
ssh root@192.168.9.125

# 拉取最新镜像（ARM64架构）
docker pull junpeng999/agent-system:v5.5-arm64
docker pull junpeng999/m3-agent-ui:v2.2

# 停止旧容器
docker stop m3-backend m3-frontend
docker rm m3-backend m3-frontend

# 启动新容器
docker run -d -p 8888:8001 --name m3-backend \
  --restart unless-stopped \
  junpeng999/agent-system:v5.5-arm64

docker run -d -p 8081:80 --name m3-frontend \
  --restart unless-stopped \
  junpeng999/m3-agent-ui:v2.2

# 验证运行状态
docker ps
curl http://localhost:8888/health
curl http://localhost:8081/health
```

## 技术支持

如遇到问题，请检查：
1. GitHub Actions构建日志
2. Docker Hub镜像标签
3. M3服务器容器日志：`docker logs m3-backend`

---

**准备就绪！** 现在可以开始推送代码到GitHub了。
