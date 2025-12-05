"""
调试脚本:通过API检查app_state的实际状态
"""
import requests
import json

API_BASE = "http://192.168.9.125:8888"

print("=" * 60)
print("调试Agent6 app_state")
print("=" * 60)

# 1. 检查健康状态
print("\n1. 健康检查:")
resp = requests.get(f"{API_BASE}/health")
health = resp.json()
print(json.dumps(health, indent=2, ensure_ascii=False))

# 2. 检查工具列表
print("\n2. 工具列表:")
resp = requests.get(f"{API_BASE}/api/tools")
tools = resp.json()
print(json.dumps(tools, indent=2, ensure_ascii=False))

# 3. 测试工具调用
print("\n3. 测试工具调用:")
resp = requests.post(
    f"{API_BASE}/api/chat",
    json={
        "message": "搜索Python",
        "user_id": "debug"
    },
    timeout=30
)
chat_result = resp.json()
print(f"Response length: {len(chat_result.get('response', ''))}")
print(f"Tool calls: {chat_result.get('tool_calls')}")

# 4. 分析
print("\n" + "=" * 60)
print("分析:")
print("=" * 60)

tools_count = health.get("tools_count", 0)
tools_list_count = len(tools.get("tools", []))
has_tool_calls = chat_result.get("tool_calls") is not None

print(f"Health API报告工具数: {tools_count}")
print(f"Tools API返回工具数: {tools_list_count}")
print(f"Chat API有工具调用: {has_tool_calls}")

if tools_count == 0 and tools_list_count == 0:
    print("\n❌ 问题确认: app_state['tools']确实是空的")
    print("   可能原因:")
    print("   1. Background task没有成功更新app_state")
    print("   2. 更新的是不同的app_state对象")
    print("   3. 导入时机问题")
elif tools_count > 0 and tools_list_count == 0:
    print("\n⚠️  矛盾: Health显示有工具,但Tools API返回空")
    print("   说明list_tools函数有问题")
elif tools_count == 0 and tools_list_count > 0:
    print("\n⚠️  矛盾: Tools API有工具,但Health显示0")
    print("   说明health函数有问题")
else:
    print("\n✅ 工具系统正常")
