# M3 Agent v6.0 - 开发路线图和待办事项

**作者**: Manus AI
**日期**: 2025-12-05

---

## 1. 当前v6.0状态

**v6.0已完成**: 完整的设计文档和核心代码框架。

**待完成**: 基于此框架,完成所有功能的代码实现。

---

## 2. 开发路线图 (Roadmap)

### Phase 1: v6.0代码实现 (预计1-2天)

**目标**: 完成v6.0所有功能的代码实现,达到可部署状态。

- **后端**:
  - [x] 修复v5.9的bug
  - [x] 实现延迟预加载和定时监控
  - [x] 优化Dashboard和元提示词API
  - [x] **实现`/api/chat/stream`流式API**

- **前端**:
  - [ ] **实现三层布局 (思维链/对话框/输入框)**
  - [ ] **实现可拖动分割线**
  - [ ] **实现全格式文件上传**
  - [ ] **实现思维链和工具调用可视化**
  - [ ] **集成SSE流,实现实时更新**
  - [ ] **应用优化的视觉设计**

- **部署**:
  - [ ] 编写完整的Dockerfile
  - [ ] 编写docker-compose.yml
  - [ ] 完成端到端测试

### Phase 2: v6.1功能增强 (预计1周)

**目标**: 增加Generative UI和多会话管理。

- **Generative UI**:
  - [ ] Agent可以动态生成React组件 (例如:表格、图表)
  - [ ] 定义Generative UI的schema
  - [ ] 在前端实现动态组件渲染

- **多会话管理**:
  - [ ] 在UI上增加新建/切换/删除会话的功能
  - [ ] 后端支持多`thread_id`的持久化存储
  - [ ] 在管理面板增加会话监控

### Phase 3: v7.0舰队战略聊天室 (长期)

**目标**: 实现多Agent协同的舰队战略聊天室。

- **多Agent协同**:
  - [ ] 定义Agent间通信协议
  - [ ] 实现Agent注册和发现机制
  - [ ] 在UI上显示多个Agent的状态

- **三位一体聊天室**:
  - [ ] 实现用户/Agent/Admin在同一个UI中的无缝交互
  - [ ] 实现权限控制和角色管理
  - [ ] 实现跨Agent的思维链追踪

---

## 3. v6.0详细待办事项 (TODO List)

### 后端 (已完成80%)

- [x] `app/api/chat_stream.py`: 流式API模块
- [x] `main.py`: 集成流式API端点
- [x] `admin_app.py`: 配置静态文件路由
- [ ] **测试**: 编写单元测试和集成测试

### 前端 (已完成40% - 核心组件框架)

- [x] `src/styles/index.css`: 优化的视觉设计
- [x] `src/components/Resizer.tsx`: 可拖动分割线
- [x] `src/components/FileUpload.tsx`: 文件上传
- [ ] `src/hooks/useChat.ts`: **(核心)** 实现SSE连接和消息处理
- [ ] `src/components/ThoughtChain.tsx`: **(核心)** 渲染思维链和工具调用
- [ ] `src/components/ChatMessage.tsx`: **(核心)** 渲染不同角色的消息
- [ ] `src/App.tsx`: **(核心)** 集成所有组件,完成三层布局
- [ ] **文件上传逻辑**: 将上传的文件发送到后端 (需要后端API支持)

### 部署 (已完成50% - 设计)

- [x] `Dockerfile`: 设计完成
- [ ] `docker-compose.yml`: 编写
- [ ] **CI/CD**: 配置GitHub Actions,实现自动化编译和部署

---

## 4. 给您的建议

您可以按照以下顺序继续开发:

1. **`useChat.ts`**: 这是前端的核心,负责与后端通信。
2. **`ChatMessage.tsx`**: 渲染从`useChat`获取的消息。
3. **`ThoughtChain.tsx`**: 渲染思维链和工具调用。
4. **`App.tsx`**: 将所有组件组合起来,完成UI。
5. **Dockerfile**: 编写完整的Dockerfile,实现自动化构建。

**我已经为您搭建了坚实的基础,剩下的主要是UI的组装和逻辑的串联。**

祝您开发顺利! 🎉
