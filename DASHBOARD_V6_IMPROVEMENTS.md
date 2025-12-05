# Dashboard v6.0 改进说明

## 核心修复

### 1. 时间显示问题 ✅ 已修复

**问题描述**:
- 旧版使用`new Date().toLocaleString('zh-CN')`显示时间
- 虽然指定了中文区域,但实际显示的是浏览器本地时区
- 如果服务器返回UTC时间,会导致时间显示错误

**修复方案**:
创建专用的`toBeijingTime()`函数,统一处理时间转换:

```javascript
function toBeijingTime(isoString) {
    if (!isoString) return '--';
    
    try {
        const date = new Date(isoString);
        
        // 转换为北京时间 (UTC+8)
        const beijingTime = new Date(date.getTime() + (8 * 60 * 60 * 1000));
        
        // 格式化为: 2024-12-05 12:30:45
        const year = beijingTime.getUTCFullYear();
        const month = String(beijingTime.getUTCMonth() + 1).padStart(2, '0');
        const day = String(beijingTime.getUTCDate()).padStart(2, '0');
        const hours = String(beijingTime.getUTCHours()).padStart(2, '0');
        const minutes = String(beijingTime.getUTCMinutes()).padStart(2, '0');
        const seconds = String(beijingTime.getUTCSeconds()).padStart(2, '0');
        
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    } catch (e) {
        console.error('时间转换失败:', e);
        return isoString;
    }
}
```

**修复效果**:
- ✅ 所有时间统一显示为北京时间(UTC+8)
- ✅ 格式统一: `2024-12-05 12:30:45` (24小时制)
- ✅ 精确到秒
- ✅ 容错处理: 转换失败时返回原始字符串

---

## v6.0 新增功能

### 1. 系统状态概览卡片

**新增3个大数字卡片**:

#### 1.1 系统运行时间
- 显示格式化的运行时间 (例如: "2小时 15分钟")
- 显示启动时间 (北京时间)
- 数据来源: `/api/dashboard/status`

#### 1.2 内存预加载状态
- 显示图标: ⏳ (等待中) / ✅ (已完成)
- 显示预加载完成时间
- 数据来源: `/api/dashboard/preload-status`

#### 1.3 整体健康状态
- 显示图标: 🟢 (健康) / 🟡 (降级) / 🔴 (异常)
- 显示状态文字
- 数据来源: `/api/dashboard/status`

### 2. 健康检测详情卡片

**新增健康检测详情展示**:

#### 2.1 工具状态
- 可用工具数量
- 工具整体状态 (✅ 可用 / ❌ 不可用)

#### 2.2 API状态
- Fleet API状态
- LangGraph API状态
- LLM连接状态

**数据来源**: `/api/dashboard/health`

### 3. 内存状态卡片

**新增内存监控**:
- RSS内存 (常驻内存)
- VMS内存 (虚拟内存)
- 内存占用率

**数据来源**: `/api/dashboard/performance`

### 4. 手动触发按钮

**新增2个手动触发按钮**:

#### 4.1 立即检测按钮
- 位置: Agent API状态卡片
- 功能: 手动触发健康检测
- API: `POST /api/dashboard/trigger-health-check`
- 效果: 5秒后自动刷新结果

#### 4.2 立即测试按钮
- 位置: 模型性能卡片
- 功能: 手动触发性能测试
- API: `POST /api/dashboard/trigger-performance-test`
- 效果: 10秒后自动刷新结果

---

## UI布局优化

### 布局变化

**旧版布局** (v3.9):
```
[LLM后端状态] [Agent API状态]
[模型性能]    [API性能]
[元提示词管理 - 全宽]
[可用工具 - 全宽]
```

**新版布局** (v6.0):
```
[运行时间] [预加载状态] [整体健康]
[LLM后端状态] [Agent API状态]
[模型性能] [API性能] [内存状态]
[健康检测详情 - 全宽]
[可用工具 - 全宽]
```

### 响应式设计

**桌面端** (>1024px):
- 3列布局: 运行时间、预加载、健康状态
- 2列布局: LLM后端、Agent API
- 3列布局: 模型性能、API性能、内存状态

**平板端** (768px-1024px):
- 3列 → 2列
- 其他保持2列

**手机端** (<768px):
- 所有卡片改为单列布局

---

## API集成

### v6.0 新增API端点

#### 1. `/api/dashboard/status`
获取系统整体状态

**响应示例**:
```json
{
  "timestamp": "2024-12-05T12:00:00",
  "summary": {
    "overall": "healthy",
    "uptime": "2h 15m 30s",
    "preload_completed": true,
    "last_check": "2024-12-05T11:45:00",
    "last_performance": "2024-12-05T11:30:00"
  },
  "details": {
    "started_at": "2024-12-05T09:44:30",
    "uptime_seconds": 8130,
    "uptime_formatted": "2h 15m 30s",
    "preload_completed": true,
    "preload_time": "2024-12-05T09:59:30"
  }
}
```

#### 2. `/api/dashboard/preload-status`
获取内存预加载状态

**响应示例**:
```json
{
  "completed": true,
  "preload_time": "2024-12-05T09:59:30",
  "health_status": {
    "browser_pool": {"status": "loaded"},
    "models": {
      "whisper": "loaded",
      "ocr": "loaded",
      "image_analysis": "loaded"
    }
  }
}
```

#### 3. `/api/dashboard/health`
获取健康检测结果

**响应示例**:
```json
{
  "status": "ok",
  "data": {
    "timestamp": "2024-12-05T11:45:00",
    "tools": {
      "count": 15,
      "status": "available",
      "names": ["web_search", "web_scraper", ...]
    },
    "apis": {
      "fleet": "available",
      "langgraph": "available",
      "llm": {
        "status": "connected",
        "models_count": 3
      }
    },
    "summary": {
      "tools": "✅",
      "fleet_api": "✅",
      "langgraph_api": "✅",
      "llm": "✅",
      "overall": "healthy"
    }
  }
}
```

#### 4. `/api/dashboard/performance`
获取性能测试结果

**响应示例**:
```json
{
  "status": "ok",
  "data": {
    "timestamp": "2024-12-05T11:30:00",
    "model_performance": {
      "model": "qwen2.5-7b-instruct",
      "tokens_per_second": 45.2,
      "ttft_ms": 120.5,
      "total_latency_ms": 850.3,
      "status": "ok"
    },
    "memory_status": {
      "rss_mb": 2048.5,
      "vms_mb": 4096.2,
      "percent": 12.5
    }
  }
}
```

#### 5. `POST /api/dashboard/trigger-health-check`
手动触发健康检测

**响应示例**:
```json
{
  "status": "triggered",
  "message": "Health check started in background"
}
```

#### 6. `POST /api/dashboard/trigger-performance-test`
手动触发性能测试

**响应示例**:
```json
{
  "status": "triggered",
  "message": "Performance test started in background"
}
```

### 兼容旧API

**保留的旧API**:
- `/api/status` - LLM后端和Agent API状态
- `/api/prompts` - 元提示词管理 (已移除,v6.0不再显示)

---

## 自动刷新机制

### 刷新策略

**页面加载时**:
- 立即加载所有数据
- 并行请求6个API端点

**定时刷新**:
- 每30秒自动刷新所有数据
- 使用`setInterval(loadAllData, 30000)`

**手动刷新**:
- "🔄 刷新状态" 按钮: 刷新LLM后端状态
- "🔍 立即检测" 按钮: 触发健康检测,5秒后刷新
- "🚀 立即测试" 按钮: 触发性能测试,10秒后刷新

---

## 代码改进

### 1. 时间处理函数

**新增2个工具函数**:

```javascript
// 转换为北京时间
function toBeijingTime(isoString) { ... }

// 格式化运行时间
function formatUptime(seconds) { ... }
```

### 2. 数据加载函数

**重构为模块化函数**:

```javascript
// v6.0 新增
async function loadSystemStatus() { ... }
async function loadPreloadStatus() { ... }
async function loadHealthStatus() { ... }
async function loadPerformanceData() { ... }

// 兼容旧版
async function loadLLMStatus() { ... }

// 统一加载
async function loadAllData() {
    await Promise.all([
        loadSystemStatus(),
        loadPreloadStatus(),
        loadHealthStatus(),
        loadPerformanceData(),
        loadLLMStatus()
    ]);
}
```

### 3. 手动触发函数

**新增2个触发函数**:

```javascript
async function triggerHealthCheck() {
    const response = await fetch('/api/dashboard/trigger-health-check', { method: 'POST' });
    alert('✅ 健康检测已触发');
    setTimeout(async () => {
        await loadHealthStatus();
        await loadSystemStatus();
    }, 5000);
}

async function triggerPerformanceTest() {
    const response = await fetch('/api/dashboard/trigger-performance-test', { method: 'POST' });
    alert('✅ 性能测试已触发');
    setTimeout(async () => {
        await loadPerformanceData();
    }, 10000);
}
```

---

## 移除的功能

### 元提示词管理

**原因**: 
- v6.0专注于系统监控和性能管理
- 元提示词管理功能使用频率低
- 可通过API直接管理

**移除内容**:
- 元提示词列表展示
- 创建/编辑/删除提示词功能
- 激活提示词功能
- 模态框UI

**替代方案**:
- 使用API直接管理: `/api/prompts`
- 或在后续版本中作为独立页面

---

## 部署验证

### 验证步骤

#### 1. 检查Dashboard可访问
```bash
curl http://localhost:8888/admin/
# 应返回HTML页面
```

#### 2. 检查时间显示
- 打开Dashboard
- 查看"更新时间"字段
- 应显示北京时间格式: `2024-12-05 12:30:45`

#### 3. 检查v6.0新功能
- 查看"系统运行时间"卡片
- 查看"内存预加载"状态
- 查看"整体健康状态"
- 查看"健康检测详情"
- 查看"内存状态"

#### 4. 测试手动触发
- 点击"🔍 立即检测"按钮
- 等待5秒,查看健康检测结果是否更新
- 点击"🚀 立即测试"按钮
- 等待10秒,查看性能测试结果是否更新

#### 5. 测试自动刷新
- 打开浏览器开发者工具
- 查看Network标签
- 应每30秒自动请求API

---

## 文件变更

### 修改的文件

1. **admin_ui/templates/dashboard.html**
   - 旧版备份为: `dashboard_old_v3.9.html`
   - 新版: 完全重写,约600行

2. **backend/admin_ui/templates/dashboard.html**
   - 同步更新为v6.0版本

### 新增的文件

- 无 (仅修改现有文件)

---

## 总结

### 核心改进

1. ✅ **时间显示修复** - 统一使用北京时间,格式规范
2. ✅ **v6.0功能集成** - 完整集成6个新API端点
3. ✅ **UI布局优化** - 新增5个卡片,响应式设计
4. ✅ **手动触发功能** - 支持立即执行检测/测试
5. ✅ **代码重构** - 模块化函数,易于维护

### 用户体验提升

- 🎯 **一目了然** - 大数字卡片直观展示关键指标
- 🎯 **实时监控** - 30秒自动刷新,掌握系统状态
- 🎯 **主动控制** - 手动触发按钮,无需等待定时任务
- 🎯 **时间准确** - 北京时间显示,避免时区混淆
- 🎯 **响应式设计** - 支持桌面/平板/手机访问

---

**Dashboard v6.0是一个重大UI升级,强烈建议所有用户更新!** 🎉
