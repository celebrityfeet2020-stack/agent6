"""
LangGraph工作流模块
从原main.py中剥离出来的核心Agent工作流逻辑
"""
import os
import json
from typing import Literal
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from app.config import LANGGRAPH_RECURSION_LIMIT
from app.state import state_manager


def load_system_prompt() -> str:
    """加载激活的元提示词"""
    try:
        prompts_file = "/app/data/system_prompts.json"
        if os.path.exists(prompts_file):
            with open(prompts_file, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
                for prompt in prompts:
                    if prompt.get("is_active", False):
                        return prompt["prompt"]
        
        # 默认提示词
        return """你是 Agent 6，一个功能强大的 AI Agent，拥有以下能力：

1. **网络搜索和抓取**：使用 web_search 搜索信息，使用 web_scraper 抓取网页内容
2. **浏览器自动化**：使用 browser_automation 进行复杂的网页交互
3. **代码执行**：使用 code_executor 在安全沙盒中执行 Python/JavaScript/Bash 代码
4. **文件操作**：使用 file_operations 读写文件
5. **图像处理**：使用 image_ocr 识别图片文字，使用 image_analysis 分析图像
6. **语音处理**：使用 speech_recognition_tool 转录音频
7. **数据分析**：使用 data_analysis 处理和可视化数据
8. **远程操作**：使用 ssh_tool 执行远程命令，使用 git_tool 管理代码仓库
9. **API 调用**：使用 universal_api 调用任意 RESTful API
10. **通讯**：使用 telegram_tool 发送 Telegram 消息
11. **RPA自动化**：使用 rpa_tool 进行复杂的自动化流程
12. **文件同步**：使用 file_sync_tool 同步文件到D5航母

**工作原则**：
- 根据用户需求，主动选择合适的工具来完成任务
- 如果一个工具不够，可以连续调用多个工具
- 始终向用户解释你在做什么以及为什么这样做
- 如果遇到错误，尝试其他方法或向用户寻求帮助

现在，请根据用户的请求，充分利用你的工具来完成任务！"""
    except Exception as e:
        print(f"Error loading system prompt: {e}")
        return "你是 Agent 6，一个功能强大的 AI 助手。"


def agent_node(state: MessagesState, config: dict) -> MessagesState:
    """Agent 节点：LLM 推理并决定是否调用工具"""
    messages = state["messages"]
    
    # 添加系统提示词（如果第一条消息不是 SystemMessage）
    if not messages or not isinstance(messages[0], SystemMessage):
        system_prompt = load_system_prompt()
        messages = [SystemMessage(content=system_prompt)] + messages
    
    # 从全局状态获取llm_with_tools
    llm_with_tools = state_manager.app_state.get("llm_with_tools")
    if not llm_with_tools:
        raise RuntimeError("LLM未初始化")
    
    # 调用 LLM（带重试机制）
    try:
        response = llm_with_tools.with_retry(stop_after_attempt=3).invoke(messages, config=config)
        return {"messages": [response]}
    except Exception as e:
        error_message = f"LLM 调用失败: {e}"
        print(f"ERROR: {error_message}")
        return {"messages": [AIMessage(content=error_message)]}


def should_continue(state: MessagesState) -> Literal["tools", END]:
    """条件边：判断是否需要继续调用工具"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # 如果 LLM 返回了 tool_calls，则继续调用工具
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    # 否则结束
    return END


def tool_node_with_error_handling(state: MessagesState) -> MessagesState:
    """工具节点（带错误处理）"""
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_invocations = []
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_invocations = last_message.tool_calls
    
    if not tool_invocations:
        return {"messages": [AIMessage(content="没有可用的工具调用")]}
    
    # 从全局状态获取tools
    tools = state_manager.app_state.get("tools", [])
    tool_node = ToolNode(tools)
    
    try:
        # 调用工具节点
        return tool_node.invoke(state)
    except Exception as e:
        error_message = f"工具调用失败: {e}"
        print(f"ERROR: {error_message}")
        # 返回错误信息给 LLM，让它决定下一步
        return {"messages": [ToolMessage(content=error_message, tool_call_id=tool_invocations[0]["id"])]}


def create_app_graph():
    """创建并编译LangGraph工作流"""
    print("🔧 正在创建LangGraph工作流...")
    
    # 创建工作流
    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node_with_error_handling)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    workflow.add_edge("tools", "agent")
    
    # 创建checkpointer
    checkpointer = MemorySaver()
    
    # 编译工作流
    app_graph = workflow.compile(checkpointer=checkpointer)
    
    print("✅ LangGraph工作流创建完成")
    return app_graph
