# Fleet API 完整文档

**版本**: v2.5  
**更新日期**: 2025-12-03  
**状态**: 接口完整，核心功能为mock实现  

---

## 📋 概述

Fleet API是M3 Agent System与D5管理航母和Temporal调度系统对接的标准接口。通过Fleet API，D5可以：

- 向M3分配任务
- 接收M3的任务状态更新
- 获取任务执行结果
- 管理M3的记忆系统

---

## 🔗 基础信息

**Base URL**: `http://your-m3-host:8888/api/fleet`

**认证方式**: 暂无（内网调用，后续版本可能添加Token认证）

**Content-Type**: `application/json`

---

## 📡 接口列表

### 1. 任务接收 - POST /task/receive

**描述**: Temporal向M3分配新任务。

**请求体**:
```json
{
  "task_id": "task-12345",
  "task_type": "research",
  "message": "研究人工智能的最新进展",
  "task_content": "详细研究2024年AI领域的突破性进展...",
  "priority": "high",
  "deadline": "2025-12-10T18:00:00Z",
  "metadata": {
    "source": "D5",
    "user_id": "user-001"
  }
}
```

**参数说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | ✅ | 任务唯一标识 |
| task_type | string | ✅ | 任务类型（research/code_generation/writing/analysis） |
| message | string | ✅ | 任务描述消息 |
| task_content | string | ❌ | 详细任务内容（可选，默认使用message） |
| priority | string/int | ❌ | 优先级（low/normal/high/urgent 或 1/2/3/4，默认normal） |
| deadline | datetime | ❌ | 截止时间（ISO 8601格式） |
| metadata | object | ❌ | 任务元数据 |

**响应**:
```json
{
  "status": "accepted",
  "task_id": "task-12345",
  "estimated_time": 300,
  "message": "Task queued successfully (mock)"
}
```

**状态码**:
- `200 OK`: 任务接收成功
- `422 Unprocessable Entity`: 参数验证失败

---

### 2. 状态上报 - POST /task/status

**描述**: M3向Temporal上报任务执行状态。

**请求体**:
```json
{
  "task_id": "task-12345",
  "status": "running",
  "progress": 50,
  "current_step": "正在搜索相关资料",
  "error": null
}
```

**参数说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | ✅ | 任务ID |
| status | string | ✅ | 任务状态（queued/running/completed/failed） |
| progress | int | ❌ | 进度百分比（0-100，默认0） |
| current_step | string | ❌ | 当前执行步骤描述 |
| error | string | ❌ | 错误信息（如有） |

**响应**:
```json
{
  "status": "reported",
  "message": "Status reported successfully (mock)"
}
```

**状态码**:
- `200 OK`: 状态上报成功
- `422 Unprocessable Entity`: 参数验证失败

---

### 3. 任务完成 - POST /task/complete

**描述**: M3向Temporal上报任务完成结果。

**请求体**:
```json
{
  "task_id": "task-12345",
  "result": {
    "summary": "研究报告已完成",
    "data": {
      "report_url": "https://...",
      "key_findings": ["发现1", "发现2"]
    }
  },
  "execution_time": 285.5
}
```

**参数说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | ✅ | 任务ID |
| result | object | ✅ | 任务结果（自定义结构） |
| execution_time | float | ✅ | 执行时间（秒） |

**响应**:
```json
{
  "task_id": "task-12345",
  "status": "completed",
  "message": "Task completion recorded (mock)"
}
```

**状态码**:
- `200 OK`: 任务完成记录成功
- `422 Unprocessable Entity`: 参数验证失败

---

### 4. 错误上报 - POST /task/error

**描述**: M3向Temporal上报任务执行错误。

**请求体**:
```json
{
  "task_id": "task-12345",
  "error_message": "网络连接超时",
  "error_type": "NetworkError",
  "stack_trace": "Traceback (most recent call last):\n  File ..."
}
```

**参数说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | ✅ | 任务ID |
| error_message | string | ✅ | 错误消息 |
| error_type | string | ✅ | 错误类型 |
| stack_trace | string | ❌ | 堆栈跟踪 |

**响应**:
```json
{
  "task_id": "task-12345",
  "status": "error_recorded",
  "message": "Task error recorded (mock)"
}
```

**状态码**:
- `200 OK`: 错误记录成功
- `422 Unprocessable Entity`: 参数验证失败

---

### 5. 查询任务状态 - GET /task/{task_id}

**描述**: 查询指定任务的当前状态。

**路径参数**:
- `task_id`: 任务ID

**响应**:
```json
{
  "task_id": "task-12345",
  "status": "unknown",
  "message": "Task status query not implemented yet (mock)"
}
```

**状态码**:
- `200 OK`: 查询成功

---

### 6. 搜索记忆 - POST /memory/search

**描述**: 在M3的记忆系统中搜索相关信息。

**请求体**:
```json
{
  "query": "人工智能的最新进展",
  "search_type": "hybrid",
  "limit": 10,
  "filters": {
    "date_range": "2024-01-01 to 2024-12-31"
  }
}
```

**参数说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | ✅ | 搜索查询 |
| search_type | string | ❌ | 搜索类型（vector/graph/hybrid，默认hybrid） |
| limit | int | ❌ | 返回结果数量（默认10） |
| filters | object | ❌ | 过滤条件 |

**响应**:
```json
{
  "memories": [],
  "total": 0,
  "message": "Memory search not implemented yet (mock)"
}
```

**状态码**:
- `200 OK`: 搜索成功

---

### 7. 存储记忆 - POST /memory/store

**描述**: 向M3的记忆系统存储新信息。

**请求体**:
```json
{
  "content": "2024年AI领域取得了重大突破...",
  "source": "M3_task_12345",
  "entities": ["AI", "机器学习", "深度学习"],
  "importance": 8.5,
  "metadata": {
    "category": "research",
    "tags": ["AI", "2024"]
  }
}
```

**参数说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | ✅ | 记忆内容 |
| source | string | ✅ | 来源标识（如"M3_task_12345"） |
| entities | array | ❌ | 实体列表 |
| importance | float | ❌ | 重要性（1-10，默认5.0） |
| metadata | object | ❌ | 元数据 |

**响应**:
```json
{
  "memory_id": "mem_mock_1234567890",
  "status": "stored",
  "message": "Memory storage not implemented yet (mock)"
}
```

**状态码**:
- `200 OK`: 存储成功
- `422 Unprocessable Entity`: 参数验证失败

---

### 8. 获取任务上下文 - GET /memory/context/{task_id}

**描述**: 获取指定任务的相关上下文记忆。

**路径参数**:
- `task_id`: 任务ID

**响应**:
```json
{
  "task_id": "task-12345",
  "context": [],
  "message": "Context retrieval not implemented yet (mock)"
}
```

**状态码**:
- `200 OK`: 查询成功

---

### 9. 健康检查 - GET /health

**描述**: 检查Fleet API模块的健康状态。

**响应**:
```json
{
  "status": "healthy",
  "module": "fleet_integration",
  "version": "2.5",
  "features": {
    "temporal_integration": "mock",
    "memory_integration": "mock"
  },
  "message": "Fleet API endpoints are ready (mock implementation)"
}
```

**状态码**:
- `200 OK`: 服务健康

---

## 🔄 典型工作流程

### 任务执行流程

```
1. D5/Temporal → M3: POST /task/receive
   ↓
2. M3接收任务，加入队列
   ↓
3. M3 → D5/Temporal: POST /task/status (status: "queued")
   ↓
4. M3开始执行任务
   ↓
5. M3 → D5/Temporal: POST /task/status (status: "running", progress: 30)
   ↓
6. M3继续执行...
   ↓
7. M3 → D5/Temporal: POST /task/status (status: "running", progress: 70)
   ↓
8. 任务完成
   ↓
9. M3 → D5/Temporal: POST /task/complete
```

### 错误处理流程

```
1. D5/Temporal → M3: POST /task/receive
   ↓
2. M3执行任务时发生错误
   ↓
3. M3 → D5/Temporal: POST /task/error
```

---

## ⚠️ 注意事项

### 当前版本限制

1. **Mock实现**: 除了`/task/receive`和`/health`，其他接口都是mock实现，不会真正处理数据。
2. **无持久化**: 任务状态和记忆不会持久化存储。
3. **无认证**: 当前版本没有认证机制，仅适用于内网环境。

### 未来版本计划

1. **v2.6**: 实现真实的任务状态管理（使用Redis）
2. **v2.7**: 集成记忆系统
3. **v2.8**: 添加Token认证

---

## 🔧 集成示例

### Python示例

```python
import requests

# 1. 分配任务
response = requests.post(
    "http://m3-host:8888/api/fleet/task/receive",
    json={
        "task_id": "task-001",
        "task_type": "research",
        "message": "研究AI最新进展",
        "priority": "high"
    }
)
print(response.json())

# 2. 查询任务状态
response = requests.get(
    "http://m3-host:8888/api/fleet/task/task-001"
)
print(response.json())

# 3. 健康检查
response = requests.get(
    "http://m3-host:8888/api/fleet/health"
)
print(response.json())
```

### cURL示例

```bash
# 分配任务
curl -X POST http://m3-host:8888/api/fleet/task/receive \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "task-001",
    "task_type": "research",
    "message": "研究AI最新进展",
    "priority": 3
  }'

# 上报状态
curl -X POST http://m3-host:8888/api/fleet/task/status \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "task-001",
    "status": "running",
    "progress": 50
  }'

# 完成任务
curl -X POST http://m3-host:8888/api/fleet/task/complete \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "task-001",
    "result": {"summary": "完成"},
    "execution_time": 120.5
  }'
```

---

## 📞 技术支持

如有问题或建议，请访问：https://help.manus.im

---

**文档版本**: v1.0  
**维护者**: M3 Agent Team
