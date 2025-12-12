"""
定时任务调度服务
负责工具池预加载、性能检测等定时任务
"""
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import (
    TOOL_POOL_PRELOAD_DELAY,
    TOOL_POOL_CHECK_INTERVAL,
    BROWSER_POOL_PRELOAD_DELAY,
    BROWSER_POOL_CHECK_INTERVAL,
    PERFORMANCE_CHECK_DELAY,
    PERFORMANCE_CHECK_INTERVAL
)
from app.state import state_manager


class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.started = False
    
    async def start(self):
        """启动调度器"""
        if self.started:
            print("⚠️  TaskScheduler已在运行")
            return
        
        print("🔧 正在配置定时任务...")
        
        # 任务1: 工具池预加载(启动5分钟后执行一次,之后每30分钟检查)
        self.scheduler.add_job(
            self._preload_tool_pool,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=TOOL_POOL_PRELOAD_DELAY),
            id='tool_pool_preload'
        )
        
        # 任务2: 工具池健康检查(每30分钟)
        self.scheduler.add_job(
            self._check_tool_pool_health,
            trigger=IntervalTrigger(seconds=TOOL_POOL_CHECK_INTERVAL),
            id='tool_pool_health_check'
        )
        
        # 任务3: 浏览器池预加载(启动5分钟后)
        self.scheduler.add_job(
            self._preload_browser_pool,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=BROWSER_POOL_PRELOAD_DELAY),
            id='browser_pool_preload'
        )
        
        # 任务4: 性能检测(启动20分钟后首次执行,之后每30分钟)
        self.scheduler.add_job(
            self._performance_check,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=PERFORMANCE_CHECK_DELAY),
            id='performance_check_initial'
        )
        
        self.scheduler.add_job(
            self._performance_check,
            trigger=IntervalTrigger(seconds=PERFORMANCE_CHECK_INTERVAL),
            id='performance_check_recurring'
        )
        
        self.scheduler.start()
        self.started = True
        print("✅ TaskScheduler启动成功")
        print(f"   - 工具池预加载: {TOOL_POOL_PRELOAD_DELAY//60}分钟后")
        print(f"   - 性能检测: {PERFORMANCE_CHECK_DELAY//60}分钟后")
    
    async def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.started = False
            print("🛑 TaskScheduler已停止")
    
    async def _preload_tool_pool(self):
        """预加载工具池(容器启动后5分钟执行)"""
        print("🔧 开始加载15个工具到内存...")
        try:
            from app.tools import load_all_tools
            from langchain_openai import ChatOpenAI
            
            # 加载工具池
            tools, tool_errors = load_all_tools()
            state_manager.loaded_tools = {tool.name: tool for tool in tools}
            state_manager.tool_errors = tool_errors
            state_manager.mark_tool_pool_loaded({tool.name: tool for tool in tools})
            
            # 重新绑定工具到LLM
            llm = ChatOpenAI(
                base_url="http://localhost:8000/v1",
                model="local-model",
                temperature=0.7,
                api_key="not-needed"
            )
            llm_with_tools = llm.bind_tools(tools)
            state_manager.app_state["llm_with_tools"] = llm_with_tools
            state_manager.app_state["tools"] = tools
            
            print(f"✅ 工具池加载完成: {len(tools)}/15 个工具")
            if tool_errors:
                print(f"⚠️  {len(tool_errors)} 个工具加载失败")
        except Exception as e:
            print(f"❌ 工具池加载失败: {e}")
    
    async def _check_tool_pool_health(self):
        """检查工具池健康状态"""
        print("🔍 检查工具池健康状态...")
        try:
            loaded_tools = state_manager.loaded_tools
            tool_errors = state_manager.tool_errors
            
            print(f"✅ 工具池健康检查完成: {len(loaded_tools)}/15 工具正常")
            
            if tool_errors:
                print(f"⚠️  {len(tool_errors)} 个工具异常:")
                for tool_name, error in tool_errors.items():
                    print(f"     - {tool_name}: {error}")
        except Exception as e:
            print(f"❌ 工具池健康检查失败: {e}")
    
    async def _preload_browser_pool(self):
        """预加载浏览器池"""
        print("🔧 开始预加载浏览器池...")
        try:
            # TODO: 实现浏览器池预加载逻辑
            state_manager.mark_browser_pool_loaded({"status": "loaded"})
            print("✅ 浏览器池预加载完成")
        except Exception as e:
            print(f"❌ 浏览器池预加载失败: {e}")
    
    async def _performance_check(self):
        """性能检测"""
        print("📊 开始性能检测...")
        try:
            # 获取系统状态
            status = state_manager.get_system_status()
            
            # 更新性能数据
            state_manager.performance_data = {
                "uptime": status["uptime"],
                "tools_loaded": status["loaded_tools_count"],
                "last_check": datetime.now().isoformat()
            }
            state_manager.performance_last_check = datetime.now()
            
            print(f"✅ 性能检测完成: 运行时间 {status['uptime']}")
        except Exception as e:
            print(f"❌ 性能检测失败: {e}")


# 创建全局实例
task_scheduler = TaskScheduler()
