# M3 Agent System v3.8.0 发布说明

**发布日期**: 2025-01-XX（待定）  
**版本**: v3.8.0  
**状态**: 开发中（等待v3.7测试完成后推送）

---

## 🎯 核心改进

### 1. 多LLM框架兼容性增强
- ✅ **LM Studio**: 通过模型ID格式识别（如 `Qwen/Qwen3-30B`）
- ✅ **Ollama**: 通过API响应格式识别
- ✅ **llama.cpp**: 通过HTTP响应头识别
- ✅ **MLX**: 通过HTTP响应头识别
- ✅ **OpenAI Compatible**: 通用兼容模式

### 2. 管理面板重构（2-2-2布局）
**新布局设计**：
- 第一行（2列）：LLM后端状态 + Agent API状态
- 第二行（2列）：模型性能 + API性能
- 第三行（1列）：元提示词管理
- 第四行（1列）：可用工具

**移除模块**：
- ❌ 系统性能监控（CPU/内存/磁盘）- 已移除
- ❌ 性能基准测试模块 - 已集成到"刷新状态"按钮

### 3. 模型性能监控
**新增指标**：
- **Tokens/s（吞吐量）**: 模型生成速度
- **TTFT（首token延迟）**: 首个token响应时间（ms）
- **平均延迟**: 完整响应时间（ms）

**更新机制**：
- 每小时自动更新一次
- 点击"刷新状态"按钮立即更新
- 只测试当前运行的模型（使用`LLM_MODEL`环境变量）

### 4. API性能监控
**新增指标**：
- **平均响应时间**: API请求平均耗时（ms）
- **请求总数**: 累计处理的请求数
- **成功率**: 成功请求占比（%）
- **每小时请求数**: 当前小时的请求量

**数据收集**：
- 自动记录每次API调用
- 保留最近24小时的统计数据
- 每小时自动更新缓存

---

## 🔧 技术改进

### 后端（admin_app.py）
1. **增强`detect_llm_backend()`函数**
   - 支持检测LM Studio、Ollama、llama.cpp、MLX
   - 通过HTTP响应头和模型ID格式识别

2. **修复`/api/benchmark`接口**
   - 只测试当前运行的模型（不再遍历所有模型）
   - 避免使用错误的模型名触发测试

3. **新增性能监控模块**
   - `app/performance/performance_monitor.py`
   - 独立的性能数据采集和缓存机制
   - 后台定时任务每小时更新

4. **更新`/api/status`接口**
   - 返回模型性能数据（`model_performance`）
   - 返回API性能数据（`api_performance`）

### 前端（dashboard.html）
1. **重构为2-2-2布局**
   - 使用CSS Grid实现响应式布局
   - 前4个卡片2x2排列，后2个占满宽度

2. **新增性能指标显示**
   - 模型性能卡片：Tokens/s、TTFT、平均延迟
   - API性能卡片：响应时间、请求总数、成功率、每小时请求数
   - 显示最后更新时间

3. **移除硬件性能模块**
   - 不再显示CPU/内存/磁盘使用率
   - 专注于模型和API性能

4. **优化用户体验**
   - 每30秒自动刷新状态
   - 性能指标颜色编码（绿色=良好，黄色=警告，红色=错误）

---

## 📦 文件变更

### 新增文件
- `app/performance/performance_monitor.py` - 性能监控模块

### 修改文件
- `admin_app.py` - 集成性能监控，增强框架检测
- `admin_ui/templates/dashboard.html` - 重构为2-2-2布局
- `main.py` - 更新版本号为3.8.0
- `config/logging_config.py` - 更新版本号

---

## 🚀 部署说明

### 环境变量
确保以下环境变量正确配置：
```bash
LLM_BASE_URL=http://192.168.9.125:8000/v1  # LLM后端地址
LLM_MODEL=minimax/minimax-m2                # 当前运行的模型
ADMIN_PORT=8002                             # 管理面板端口
```

### Docker部署
```bash
# 构建镜像
docker build -t m3-agent:v3.8.0 .

# 运行容器
docker run -d \
  -p 8000:8000 \
  -p 8002:8002 \
  -e LLM_BASE_URL=http://192.168.9.125:8000/v1 \
  -e LLM_MODEL=minimax/minimax-m2 \
  --name m3-agent-v3.8 \
  m3-agent:v3.8.0
```

### 访问管理面板
```
http://<服务器IP>:8002
```

---

## 🔄 从v3.7升级

### 兼容性
- ✅ 完全向后兼容v3.7
- ✅ 无需修改环境变量
- ✅ 自动迁移现有数据

### 升级步骤
1. 停止v3.7容器
2. 拉取v3.8镜像
3. 启动v3.8容器
4. 访问管理面板验证

---

## 📝 已知问题

### 待修复
- 无

### 计划改进
- [ ] 添加性能趋势图表（v3.9）
- [ ] 支持自定义性能监控间隔（v3.9）
- [ ] 导出性能报告功能（v3.9）

---

## 🙏 致谢

感谢所有测试v3.7版本并提供反馈的用户！

---

## 📞 支持

如有问题，请通过以下方式联系：
- GitHub Issues: https://github.com/celebrityfeet2020-stack/m3-agent-system/issues
- 邮箱: support@m3agent.com

---

**注意**: 本版本尚未推送到GitHub，等待v3.7测试完成后再发布。
