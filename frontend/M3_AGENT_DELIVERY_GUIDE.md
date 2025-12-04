# M3 Agent UI 完整交付指南

**版本**: v1.8 (Final Delivery)
**日期**: 2025-12-04
**作者**: Manus AI

---

## 1. 项目概述

M3 Agent UI 是一个专为 M3 Agent System 设计的高级战术指挥控制台（Cyber-Tactical Command Interface）。它不仅仅是一个聊天窗口，更是一个集成了实时监控、思维链可视化、多模态输入和系统控制的综合终端。

### 核心特性 (v1.8)

*   **垂直分屏指挥舱布局**：
    *   **顶部**: 实时系统日志与思维链 (CoT) 面板，支持折叠与高度调整。
    *   **中部**: 沉浸式对话窗口，支持 Markdown 高亮渲染。
    *   **底部**: 增强型指令舱，支持文件拖拽与粘贴。
*   **无缝流式同步**: 基于 SSE (Server-Sent Events) 实现毫秒级打字机效果，彻底消除页面闪烁。
*   **多模态交互**: 支持图片、音频、文档的拖拽上传与预览，配合机械音效反馈。
*   **移动端适配**: 响应式设计，在手机和平板上自动切换为折叠式日志面板。
*   **开发者友好**: 内置 cURL 生成器、健康检查端点 (/health) 及 i18n 国际化架构。

---

## 2. 项目结构

```text
m3-agent-ui/
├── client/                 # 前端源码 (React 19 + Vite)
│   ├── src/
│   │   ├── components/     # UI 组件
│   │   │   ├── chat/       # 核心聊天组件 (M3Thread, SystemLogPanel, etc.)
│   │   │   └── ui/         # 基础 UI 组件 (shadcn/ui)
│   │   ├── hooks/          # 自定义 Hooks (useSoundEffects, useMediaQuery)
│   │   ├── lib/            # 工具库 (runtime, i18n, sse-adapter)
│   │   └── pages/          # 页面组件 (ChatPage)
│   └── public/             # 静态资源
├── Dockerfile.prod         # 生产环境构建文件
├── nginx.conf              # Nginx 生产环境配置
├── DEPLOY_GUIDE.md         # 详细部署指南
├── M3_AGENT_MANUAL_CN.md   # 用户操作手册
└── package.json            # 项目依赖配置
```

---

## 3. 快速部署

详细步骤请参考项目根目录下的 `DEPLOY_GUIDE.md`。

### 简易步骤

1.  **构建镜像**:
    ```bash
    docker build -f Dockerfile.prod -t m3-agent-ui:v1.8 .
    ```

2.  **启动容器**:
    ```bash
    docker run -d -p 80:80 \
      -e VITE_API_BASE_URL="http://your-backend-api" \
      --name m3-ui \
      m3-agent-ui:v1.8
    ```

3.  **验证**:
    访问 `http://localhost` 即可看到界面。
    访问 `http://localhost/health` 可检查服务健康状态。

---

## 4. 功能指南

详细操作请参考 `M3_AGENT_MANUAL_CN.md`。

### 快捷键
*   **复制 cURL**: 在日志面板中点击任意 `[TOOL]` 条目旁的 `< >` 图标。
*   **代码复制**: 在对话框的代码块右上角点击 "Copy"。

### 移动端操作
*   在手机上访问时，日志面板默认隐藏。点击右上角的 **"展开日志"** 按钮可查看系统运行状态。

---

## 5. 二次开发指南

### 国际化 (i18n)
项目已预留国际化接口。如需添加新语言：
1.  打开 `client/src/lib/i18n.ts`。
2.  在 `translations` 对象中添加新的语言键值对（如 `jp`）。
3.  在 `useI18n` store 中切换 `language` 状态。

### 主题定制
样式文件位于 `client/src/index.css`。
*   修改 `:root` 下的 `--primary` 变量可更改主色调（默认：深海蓝）。
*   修改 `--font-mono` 可替换等宽字体（默认：JetBrains Mono）。

---

**M3 AGENT SYSTEM // END OF REPORT**
