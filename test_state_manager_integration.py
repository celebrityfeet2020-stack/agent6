"""
验证StateManager集成是否正确
模拟main.py和background_tasks.py的交互
"""
import sys
sys.path.insert(0, "/home/ubuntu/m3_agent_analysis/agent6/backend")

print("=" * 60)
print("测试StateManager集成")
print("=" * 60)

# 1. 模拟main.py导入
print("\n1. 模拟main.py导入StateManager...")
from app.core.state_manager import StateManager

state_mgr_main = StateManager()
print(f"   Main StateManager ID: {id(state_mgr_main)}")
print(f"   初始状态: {state_mgr_main.get_all()}")

# 通过_state直接访问(模拟main.py中的app_state = state_mgr._state)
app_state = state_mgr_main._state
print(f"   app_state ID: {id(app_state)}")
print(f"   app_state内容: {app_state}")

# 2. 模拟background_tasks更新状态
print("\n2. 模拟background_tasks更新状态...")

def simulate_background_task():
    # 在background_tasks中重新获取StateManager
    from app.core.state_manager import StateManager
    
    state_mgr_bg = StateManager()
    print(f"   Background StateManager ID: {id(state_mgr_bg)}")
    print(f"   是否同一实例: {state_mgr_bg is state_mgr_main}")
    
    # 模拟加载工具
    mock_tools = [
        type('Tool', (), {'name': 'search', 'description': 'Search tool'}),
        type('Tool', (), {'name': 'calculator', 'description': 'Calculator tool'}),
        type('Tool', (), {'name': 'browser', 'description': 'Browser tool'}),
    ]
    
    state_mgr_bg.set("tools", mock_tools)
    state_mgr_bg.set("tools_loaded", True)
    state_mgr_bg.set("tools_load_time", "2025-12-06T01:30:00")
    
    print(f"   更新后状态: tools={len(state_mgr_bg.get('tools', []))} loaded={state_mgr_bg.get('tools_loaded')}")

simulate_background_task()

# 3. 模拟API端点读取
print("\n3. 模拟API端点读取...")

def simulate_list_tools_api():
    # 通过app_state访问(因为main.py中 app_state = state_mgr._state)
    tools = app_state.get("tools", [])
    print(f"   通过app_state读取: {len(tools)} tools")
    
    # 也可以通过StateManager访问
    state_mgr_api = StateManager()
    tools2 = state_mgr_api.get("tools", [])
    print(f"   通过StateManager读取: {len(tools2)} tools")
    
    return {
        "tools": [{"name": t.name, "description": t.description} for t in tools]
    }

result = simulate_list_tools_api()
print(f"   API返回: {result}")

# 4. 验证结果
print("\n" + "=" * 60)
print("验证结果:")
print("=" * 60)

if len(result["tools"]) > 0:
    print("✅ StateManager集成成功!")
    print("   - 跨模块状态共享正常")
    print("   - background_tasks更新可以被API访问")
    print("   - app_state引用正确")
else:
    print("❌ StateManager集成失败!")
    print("   需要检查代码")

# 5. 测试并发安全性
print("\n5. 测试并发安全性...")
import threading

def concurrent_update(thread_id):
    state_mgr = StateManager()
    state_mgr.set(f"thread_{thread_id}", f"value_{thread_id}")

threads = []
for i in range(10):
    t = threading.Thread(target=concurrent_update, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

state_mgr_final = StateManager()
thread_keys = [k for k in state_mgr_final.get_all().keys() if k.startswith("thread_")]
print(f"   并发更新成功: {len(thread_keys)}/10 keys")

if len(thread_keys) == 10:
    print("✅ 线程安全测试通过")
else:
    print("⚠️  线程安全测试失败")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
