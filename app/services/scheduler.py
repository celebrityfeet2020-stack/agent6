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
from app.core.model_pool import model_pool
from app.services.model_monitor import model_monitor


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
        
        # 任务1.5: 模型池预加载(启动5分钟后执行,与工具池同时)
        self.scheduler.add_job(
            self._preload_model_pool,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=TOOL_POOL_PRELOAD_DELAY),
            id='model_pool_preload'
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
        
        # 任务5: 模型信息监控(启动1分钟后首次执行,之后每5分钟)
        self.scheduler.add_job(
            self._update_model_info,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=60),
            id='model_info_initial'
        )
        
        self.scheduler.add_job(
            self._update_model_info,
            trigger=IntervalTrigger(seconds=300),
            id='model_info_recurring'
        )
        
        self.scheduler.start()
        self.started = True
        print("✅ TaskScheduler启动成功")
        print(f"   - 工具池预加载: {TOOL_POOL_PRELOAD_DELAY//60}分钟后")
        print(f"   - 模型池预加载: {TOOL_POOL_PRELOAD_DELAY//60}分钟后")
        print(f"   - 性能检测: {PERFORMANCE_CHECK_DELAY//60}分钟后")
        print(f"   - 模型信息监控: 1分钟后首次执行,之后每5分钟")
    
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
                base_url=f"http://{state_manager.config.MODEL_HOST}:{state_manager.config.MODEL_PORT}/v1",
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
    
    async def _preload_model_pool(self):
        """预加载模型池(容器启动5分钟后执行)"""
        print("🧠 开始加载OCR和Whisper模型到内存...")
        try:
            success = model_pool.preload_models()
            
            if success:
                state_manager.model_pool_loaded = True
                state_manager.model_pool_load_time = model_pool.load_time
                print("✅ 模型池加载完成")
            else:
                print("❌ 模型池加载部分失败")
        except Exception as e:
            print(f"❌ 模型池加载失败: {e}")
    
    async def _check_tool_pool_health(self):
        """检查工具池健康状态并自动重载失败的工具"""
        print("🔍 检查工具池健康状态...")
        try:
            loaded_tools = state_manager.loaded_tools
            tool_errors = state_manager.tool_errors
            
            print(f"✅ 工具池健康检查完成: {len(loaded_tools)}/16 工具正常")
            
            # 如果有工具异常，尝试重新加载
            if tool_errors:
                print(f"⚠️  {len(tool_errors)} 个工具异常，尝试重新加载...")
                for tool_name, error in tool_errors.items():
                    print(f"     - {tool_name}: {error}")
                
                # 重新加载失败的工具
                await self._reload_failed_tools()
                    
            # 检查模型池健康状态
            model_status = model_pool.get_status()
            if not model_status["loaded"]:
                print("⚠️  模型池未加载，尝试重新加载...")
                model_pool.reload_failed_models()
        except Exception as e:
            print(f"❌ 工具池健康检查失败: {e}")
    
    async def _reload_failed_tools(self):
        """重新加载失败的工具"""
        try:
            from app.tools import load_all_tools
            from langchain_openai import ChatOpenAI
            
            # 重新加载所有工具
            print("🔄 重新加载工具池...")
            tools, tool_errors = load_all_tools()
            
            # 更新状态管理器
            state_manager.loaded_tools = {tool.name: tool for tool in tools}
            state_manager.tool_errors = tool_errors
            
            # 重新绑定工具到LLM
            llm = ChatOpenAI(
                base_url=f"http://{state_manager.config.MODEL_HOST}:{state_manager.config.MODEL_PORT}/v1",
                model="local-model",
                temperature=0.7,
                api_key="not-needed"
            )
            llm_with_tools = llm.bind_tools(tools)
            state_manager.app_state["llm_with_tools"] = llm_with_tools
            state_manager.app_state["tools"] = tools
            
            # 统计重载结果
            success_count = len(tools)
            failed_count = len(tool_errors)
            
            if failed_count == 0:
                print(f"✅ 工具池重载成功: {success_count}/16 个工具全部正常")
            else:
                print(f"⚠️  工具池重载完成: {success_count}/16 个工具正常, {failed_count} 个仍然失败")
                for tool_name, error in tool_errors.items():
                    print(f"     - {tool_name}: {error}")
                    
        except Exception as e:
            print(f"❌ 工具池重载失败: {e}")
    
    async def _preload_browser_pool(self):
        """预加载浏览器池"""
        print("🔧 开始预加载浏览器池...")
        try:
            from app.core.browser_pool import get_browser_pool
            
            # 初始化浏览器池
            browser_pool = get_browser_pool(headless=True)
            browser_pool.start()
            
            # 更新状态
            state_manager.app_state["browser_pool"] = browser_pool
            state_manager.mark_browser_pool_loaded({
                "status": "loaded",
                "pool_size": browser_pool.pool_size,
                "headless": browser_pool.headless
            })
            
            print(f"✅ 浏览器池预加载完成 - 池大小: {browser_pool.pool_size}")
        except Exception as e:
            print(f"❌ 浏览器池预加载失败: {e}")
            import traceback
            traceback.print_exc()
    
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
    
    async def _update_model_info(self):
        """更新模型信息"""
        try:
            await model_monitor.update_model_info()
        except Exception as e:
            print(f"❌ 模型信息更新失败: {e}")


# 创建全局实例
task_scheduler = TaskScheduler()
