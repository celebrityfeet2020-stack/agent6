"""
添加临时调试端点到main.py
"""

debug_endpoint = '''

# ============================================
# 临时调试端点 (v6.3.2 debug)
# ============================================

@app.get("/debug/app_state")
async def debug_app_state():
    """调试: 检查app_state的实际内容"""
    return {
        "app_state_id": id(app_state),
        "browser_pool": app_state["browser_pool"] is not None,
        "tools_count": len(app_state["tools"]),
        "tools_sample": [
            {"name": t.name, "description": t.description[:50]}
            for t in app_state["tools"][:3]
        ] if app_state["tools"] else [],
        "llm_with_tools": app_state["llm_with_tools"] is not None,
        "app_graph": app_state["app_graph"] is not None,
    }
'''

# 读取main.py
with open("/home/ubuntu/m3_agent_analysis/agent6/backend/main.py", "r") as f:
    content = f.read()

# 检查是否已经添加
if "/debug/app_state" in content:
    print("调试端点已存在")
else:
    # 在文件末尾添加
    content += debug_endpoint
    
    # 写回
    with open("/home/ubuntu/m3_agent_analysis/agent6/backend/main.py", "w") as f:
        f.write(content)
    
    print("✅ 调试端点已添加到main.py")
    print("   端点: GET /debug/app_state")
