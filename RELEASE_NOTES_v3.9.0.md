# 🐛 M3 Agent System v3.9.0 - Bug修复版

**发布日期**: 2025-12-04  
**版本类型**: Bug修复  
**基于版本**: v3.8.0

---

## 📋 修复内容

### 🔧 Bug修复

#### 1. 后端检测逻辑错误 ❌ → ✅
**问题**：
- v3.8.0只检查第一个模型ID是否带斜杠来判断是否为LM Studio
- 当第一个模型是不带斜杠的模型（如`qwen3-next-80b-a3b-thinking-mlx`）时，无法正确识别为LM Studio
- 导致管理面板显示"OpenAI Compatible"而不是"LM Studio"

**修复**：
```python
# 修复前
if "/" in first_model_id:
    return "LM Studio", data["data"]

# 修复后
has_slash_model = any("/" in model.get("id", "") for model in data["data"])
if has_slash_model:
    return "LM Studio", data["data"]
```

**影响**：
- ✅ 现在可以正确识别LM Studio，即使第一个模型不带斜杠
- ✅ 管理面板显示正确的后端类型

---

#### 2. 性能监控切换模型 ❌ → ✅
**问题**：
- v3.8.0的性能监控使用环境变量`LLM_MODEL`指定的模型进行测试
- 当LM Studio当前运行的模型与环境变量不同时，会触发模型切换
- 导致用户正在使用的模型被意外卸载和重新加载

**修复**：
```python
# 新增函数：获取当前运行的模型
async def get_current_model(llm_base_url: str) -> Optional[str]:
    """获取当前运行的模型"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{llm_base_url}/models")
            data = response.json()
            models = data.get("data", [])
            if models:
                return models[0].get("id")  # 返回第一个模型
    except Exception as e:
        print(f"[Performance Monitor] Failed to get current model: {e}")
    return None

# 修复后的性能测试
async def measure_model_performance() -> Dict:
    # 获取当前运行的模型
    current_model = await get_current_model(llm_base_url)
    
    # 使用当前模型进行测试，而不是环境变量指定的模型
    response = await client.post(
        f"{llm_base_url}/chat/completions",
        json={
            "model": current_model,  # ✅ 使用当前模型
            "messages": [{"role": "user", "content": test_prompt}],
            "max_tokens": 50,
            "stream": True
        }
    )
```

**影响**：
- ✅ 性能监控不再切换模型
- ✅ 用户可以安全地使用任意模型，不会被性能监控干扰
- ✅ 性能数据反映的是当前实际运行的模型

---

### ℹ️ DELETE接口422错误
**状态**: 非bug，API文档显示问题

经过测试，DELETE线程接口实际工作正常：
- ✅ 删除存在的线程 → 返回200
- ✅ 删除不存在的线程 → 返回404

API文档中显示的422错误只是Swagger UI的示例，不影响实际使用。

---

## 📊 版本对比

| 功能 | v3.8.0 | v3.9.0 |
|------|--------|--------|
| 后端检测（LM Studio） | ❌ 只检查第一个模型 | ✅ 检查所有模型 |
| 性能监控 | ❌ 使用环境变量模型 | ✅ 使用当前运行模型 |
| 模型切换问题 | ❌ 会意外切换模型 | ✅ 不切换模型 |
| 其他功能 | ✅ 完全兼容 | ✅ 完全兼容 |

---

## 🚀 升级指南

### Docker部署
```bash
# 停止旧容器
docker stop agent-system-v3.8
docker rm agent-system-v3.8

# 拉取v3.9.0镜像
docker pull junpeng999/agent-system:v3.9.0-arm64

# 启动v3.9.0容器
docker run -d --name agent-system-v3.9 \
  -p 8888:8000 \
  -p 8889:8002 \
  -e LLM_BASE_URL="http://192.168.9.125:8000/v1" \
  -e LLM_MODEL="minimax/minimax-m2" \
  -e AGENT_ID="agent-m3-coo" \
  -e RPA_HOST_STRING="kori@192.168.9.125" \
  -e RPA_HOST_PASSWORD="225678" \
  -v ~/Desktop:/host_desktop \
  -v ~/Downloads:/host_downloads \
  -v ~/Documents:/host_documents \
  -v ~/.ssh:/root/.ssh:ro \
  junpeng999/agent-system:v3.9.0-arm64
```

### 兼容性
- ✅ 完全向后兼容v3.8.0
- ✅ 所有API接口保持不变
- ✅ 所有功能保持不变
- ✅ 零破坏性变更

---

## 🎯 推荐升级理由

1. **修复关键bug** - 后端检测和性能监控的bug会影响用户体验
2. **无风险升级** - 完全向后兼容，零破坏性变更
3. **提升稳定性** - 不再意外切换模型，避免工作中断

---

## 📝 已知问题

无

---

## 🔗 相关链接

- **GitHub仓库**: https://github.com/celebrityfeet2020-stack/m3-agent-system
- **Docker Hub**: https://hub.docker.com/r/junpeng999/agent-system
- **v3.8.0发布说明**: RELEASE_NOTES_v3.8.0.md
- **v3.7.0发布说明**: RELEASE_NOTES_v3.7.0.md
