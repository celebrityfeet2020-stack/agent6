# M3 Agent v6.0 - assistant-ui前端开发指南

**作者**: Manus AI
**日期**: 2025-12-05

---

## 1. 技术栈

- **框架**: React 18
- **构建工具**: Vite
- **语言**: TypeScript
- **UI库**: assistant-ui, Radix UI, Lucide Icons
- **样式**: Tailwind CSS
- **状态管理**: Zustand (轻量级)
- **部署方式**: **静态文件** (编译为HTML/JS/CSS,由FastAPI提供服务)

> **重要**: v6.0采用静态文件部署方案。前端通过Vite编译为静态文件后,由FastAPI的`StaticFiles`中间件提供服务,实现单端口访问。这不会失去assistant-ui的任何核心功能,因为SSR、API路由等Next.js特性在我们的场景中并不需要。

---

## 2. 项目结构

```
/chatroom_ui
├── /dist               # 编译输出目录
├── /src
│   ├── /components     # React组件
│   │   ├── ChatHeader.tsx
│   │   ├── ChatInput.tsx
│   │   ├── ChatMessage.tsx
│   │   ├── FileUpload.tsx
│   │   ├── Resizer.tsx
│   │   └── ThoughtChain.tsx
│   ├── /hooks          # 自定义Hooks
│   │   └── useChat.ts
│   ├── /lib            # 辅助函数
│   │   └── runtime.ts
│   ├── /styles         # CSS样式
│   │   └── index.css
│   ├── App.tsx         # 主应用组件
│   └── main.tsx        # 入口文件
├── index.html          # HTML模板
├── package.json        # 项目配置
├── tsconfig.json       # TypeScript配置
└── vite.config.ts      # Vite配置
```

---

## 3. 核心组件设计

### 3.1. `App.tsx` (主应用)

负责整体布局和状态管理。

- **布局**: 三层布局 (思维链 / 对话框 / 输入框)
- **状态**: 使用Zustand管理聊天记录、连接状态、输入内容
- **逻辑**: 
  - 初始化SSE连接
  - 处理用户输入
  - 调用`useChat` hook发送消息

### 3.2. `useChat.ts` (自定义Hook)

封装所有聊天相关的逻辑。

- **功能**:
  - 发送消息到后端API (`/api/chat/stream`)
  - 监听SSE事件 (message/thought/tool/system)
  - 更新Zustand中的聊天记录
  - 处理文件上传

### 3.3. `ChatMessage.tsx`

渲染单条消息。

- **功能**:
  - 根据`source`字段显示不同角色的消息 (user/agent/api/livestream/fleet)
  - 显示头像、角色名、时间戳
  - 渲染Markdown内容
  - 显示思维链和工具调用

### 3.4. `ThoughtChain.tsx`

渲染思维链和工具调用。

- **功能**:
  - 显示思维链步骤 (understanding/tool_selection/executing...)
  - 显示工具调用 (名称、参数、状态、结果)
  - 可折叠的详细信息

### 3.5. `Resizer.tsx`

可拖动分割线。

- **功能**: 允许用户拖动分割线,调整思维链和对话框的比例。

### 3.6. `FileUpload.tsx`

文件上传组件。

- **功能**:
  - 支持拖拽、点击、粘贴上传
  - 支持全格式文件
  - 显示文件预览和上传进度

---

## 4. 开发流程

### 4.1. 环境准备

```bash
# 1. 安装Node.js和pnpm
# (推荐使用nvm)

# 2. 进入chatroom_ui目录
cd /path/to/m3-agent-v6.0/chatroom_ui

# 3. 安装依赖
pnpm install
```

### 4.2. 开发模式

```bash
# 启动Vite开发服务器 (端口5173)
pnpm run dev
```

在开发模式下,Vite会自动代理API请求到后端的8889端口。

**`vite.config.ts` 配置**:

```typescript
export default defineConfig({
  // ...
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8889',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    // 确保静态文件正确输出
    rollupOptions: {
      output: {
        manualChunks: undefined,
      },
    },
  },
});
```

### 4.3. 生产编译

```bash
# 编译为静态文件
pnpm run build

# 编译后的文件输出到 dist/ 目录
# 包含: index.html, assets/*.js, assets/*.css
```

编译完成后,FastAPI将通过以下方式提供这些静态文件:

```python
# admin_app.py
from fastapi.staticfiles import StaticFiles

app.mount("/chat", StaticFiles(directory="chatroom_ui/dist", html=True), name="chat")
```

### 4.3. 核心代码框架

#### `useChat.ts`

```typescript
import { create } from 'zustand';

// ... (类型定义)

const useChatStore = create<ChatState>((set) => ({ ... }));

export const useChat = () => {
  const { messages, setMessages } = useChatStore();
  
  const sendMessage = async (text: string, files: File[]) => {
    // 1. 构造请求体
    const body = {
      message: text,
      thread_id: 'default_session',
      source: 'user',
      metadata: { ... }
    };
    
    // 2. (如果需要)上传文件,获取URL
    
    // 3. 发送POST请求到 /api/chat/stream
    const response = await fetch('/api/chat/stream', { ... });
    
    // 4. 处理SSE流
    const reader = response.body?.getReader();
    // ...
  };
  
  return { messages, sendMessage };
};
```

#### `App.tsx`

```tsx
import { Resizer } from './components/Resizer';
import { FileUpload } from './components/FileUpload';
// ...

const App = () => {
  const [topPanelHeight, setTopPanelHeight] = useState(200);
  
  const handleResize = (delta: number) => {
    setTopPanelHeight(prev => Math.max(100, prev + delta));
  };
  
  return (
    <div className="layout-container">
      {/* 上层: 思维链 */}
      <div style={{ height: topPanelHeight }} className="top-panel">
        <ThoughtChainPanel />
      </div>
      
      {/* 分割线 */}
      <Resizer onResize={handleResize} />
      
      {/* 中层: 对话框 */}
      <div className="middle-panel">
        <MessageList />
      </div>
      
      {/* 下层: 输入框 */}
      <div className="bottom-panel">
        <FileUpload onFilesChange={...} />
        <ChatInput onSend={...} />
      </div>
    </div>
  );
};
```

---

## 5. 总结

基于assistant-ui的前端架构清晰、功能强大,通过模块化的组件和自定义Hook,可以高效地实现您要求的所有功能。这个框架也为未来的Generative UI和舰队模式提供了良好的基础。
