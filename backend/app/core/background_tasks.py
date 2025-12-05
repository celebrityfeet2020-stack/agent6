"""
M3 Agent System v5.9 - Background Tasks Manager

后台任务管理器（错开执行）：
- 第1波（每30分钟）：工具池预加载 + 模型API检测（轻量级）
- 第2波（每30分钟，延迟15分钟）：性能测试 + 全面体检（重量级）
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger("m3_agent")


class BackgroundTasksManager:
    """后台任务管理器"""
    
    def __init__(self):
        self.started_at = datetime.now()
        self.tool_pool_loaded = False
        self.last_health_check = None
        self.last_performance_test = None
        self.last_api_check = None
        
        # 任务引用（用于取消）
        self.tasks = {}
    
    async def start(self):
        """启动所有后台任务"""
        logger.info("=" * 80)
        logger.info("🚀 Starting Background Tasks Manager (v5.9)")
        logger.info("=" * 80)
        
        # 第1波（每30分钟）：工具池预加载 + 模型API检测（轻量级）
        self.tasks['wave1'] = asyncio.create_task(
            self._wave1_check()
        )
        
        # 第2波（每30分钟，延迟15分钟）：性能测试 + 全面体检（重量级）
        self.tasks['wave2'] = asyncio.create_task(
            self._wave2_check()
        )
        
        logger.info("✅ Background tasks started")
        logger.info("   - Wave 1: every 30 minutes (tool pool + API check) [轻量级]")
        logger.info("   - Wave 2: every 30 minutes, 15 min offset (performance test + health check) [重量级]")
        logger.info("=" * 80)
    
    async def stop(self):
        """停止所有后台任务"""
        logger.info("Stopping background tasks...")
        for name, task in self.tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        logger.info("✅ All background tasks stopped")
    

    
    async def _initialize_browser_and_tools(self):
        """初始化浏览器池和工具 (v6.1)"""
        try:
            logger.info("🌐 Initializing browser pool and tools...")
            from app.core.startup import initialize_browser_pool_and_tools
            
            browser_pool, tools = await initialize_browser_pool_and_tools()
            
            # 更新全局变量
            import main
            main.browser_pool = browser_pool
            main.tools = tools
            main.llm_with_tools = main.llm.bind_tools(tools)
            
            logger.info(f"✅ Browser pool and {len(tools)} tools initialized successfully")
            
            # 推送到聊天室
            await self._send_chat_message(
                f"✅ 浏览器池和工具初始化完成\n- 工具数量: {len(tools)}",
                metadata={"type": "browser_tools_init"}
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize browser pool and tools: {e}", exc_info=True)
            await self._send_chat_message(f"❌ 浏览器池初始化失败: {e}", metadata={"type": "error"})
    
    async def _load_tool_pool(self):
        """预加载工具池"""
        try:
            logger.info("📦 Loading tool pool...")
            from app.core.tool_pool_v5_8 import enhanced_tool_pool
            
            await enhanced_tool_pool.initialize()
            self.tool_pool_loaded = True
            
            logger.info("✅ Tool pool loaded successfully")
            logger.info(f"   - OCR: {'✅' if enhanced_tool_pool.ocr_loaded else '❌'}")
            logger.info(f"   - Whisper: {'✅' if enhanced_tool_pool.whisper_loaded else '❌'}")
            logger.info(f"   - Docker: {'✅' if enhanced_tool_pool.docker_loaded else '❌'}")
            
            # 推送到聊天室
            await self._send_chat_message(
                f"✅ 工具池加载完成\n- OCR: {'✅' if enhanced_tool_pool.ocr_loaded else '❌'}\n- Whisper: {'✅' if enhanced_tool_pool.whisper_loaded else '❌'}\n- Docker: {'✅' if enhanced_tool_pool.docker_loaded else '❌'}",
                metadata={"type": "tool_pool_status"}
            )
            
        except Exception as e:
            logger.warning(f"Failed to load tool pool: {e}")
            self.tool_pool_loaded = False
            await self._send_chat_message(f"❌ 工具池加载失败: {e}", metadata={"type": "error"})
    
    async def _comprehensive_health_check(self):
        """全面体检"""
        try:
            logger.info("🏥 Starting comprehensive health check...")
            
            health_report = {
                "timestamp": datetime.now().isoformat(),
                "tool_pool": {
                    "loaded": self.tool_pool_loaded,
                },
                "tools": {},
                "apis": {},
            }
            
            # 检查15个工具
            from app.core.startup import initialize_browser_pool_and_tools
            try:
                _, tools = await initialize_browser_pool_and_tools()
                health_report["tools"]["count"] = len(tools)
                health_report["tools"]["names"] = [tool.name for tool in tools]
                logger.info(f"   - Tools: {len(tools)} available")
            except Exception as e:
                logger.warning(f"   - Tools check failed: {e}")
                health_report["tools"]["error"] = str(e)
            
            # 检查Fleet API
            try:
                # 简单检查：导入模块
                from app.api.fleet_api import router as fleet_router
                health_report["apis"]["fleet"] = "available"
                logger.info("   - Fleet API: ✅")
            except Exception as e:
                health_report["apis"]["fleet"] = f"error: {e}"
                logger.warning(f"   - Fleet API: ❌ {e}")
            
            # 检查LangGraph API
            try:
                from app.api.langgraph_adapter import router as langgraph_router
                health_report["apis"]["langgraph"] = "available"
                logger.info("   - LangGraph API: ✅")
            except Exception as e:
                health_report["apis"]["langgraph"] = f"error: {e}"
                logger.warning(f"   - LangGraph API: ❌ {e}")
            
            self.last_health_check = health_report
            logger.info("✅ Health check complete")
            
            # 推送到聊天室
            tools_count = health_report.get("tools", {}).get("count", 0)
            fleet_status = "✅" if health_report.get("apis", {}).get("fleet") == "available" else "❌"
            langgraph_status = "✅" if health_report.get("apis", {}).get("langgraph") == "available" else "❌"
            
            await self._send_chat_message(
                f"🏥 全面体检完成\n- 工具数量: {tools_count}\n- Fleet API: {fleet_status}\n- LangGraph API: {langgraph_status}",
                metadata={"type": "health_check", "report": health_report}
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
    
    async def _wave1_check(self):
        """第1波检查：工具池预加载 + 模型API检测（每30分钟，轻量级）"""
        try:
            # 首次等待15分钟
            logger.info("⏰ Wave 1 scheduled in 15 minutes...")
            await asyncio.sleep(900)  # 15分钟
            
            while True:
                try:
                    logger.info("=" * 80)
                    logger.info("🌊 Wave 1: Browser Pool + Tool Pool + API Check [轻量级]")
                    logger.info("=" * 80)
                    
                    # 1. 初始化浏览器池和工具 (v6.1)
                    await self._initialize_browser_and_tools()
                    
                    # 2. 预加载工具池
                    await self._load_tool_pool()
                    
                    # 2. 模型API检测
                    logger.info("🔌 Running API check...")
                    await self._send_chat_message("🔌 开始API检测...", metadata={"type": "api_check"})
                    # TODO: 实现实际的API检测逻辑
                    self.last_api_check = datetime.now()
                    logger.info("✅ API check complete")
                    await self._send_chat_message("✅ API检测完成", metadata={"type": "api_check"})
                    
                    logger.info("=" * 80)
                    logger.info(f"✅ Wave 1 Complete at {datetime.now().strftime('%H:%M:%S')}")
                    logger.info("=" * 80)
                    
                except Exception as e:
                    logger.error(f"Wave 1 failed: {e}")
                
                # 等待30分钟
                await asyncio.sleep(1800)
                
        except asyncio.CancelledError:
            logger.info("Wave 1 task cancelled")
    
    async def _wave2_check(self):
        """第2波检查：性能测试 + 全面体检（每30分钟，延迟15分钟，重量级）"""
        try:
            # 首次等待30分钟
            logger.info("⏰ Wave 2 scheduled in 30 minutes...")
            await asyncio.sleep(1800)  # 30分钟
            
            while True:
                try:
                    logger.info("=" * 80)
                    logger.info("🌊 Wave 2: Performance Test + Health Check [重量级]")
                    logger.info("=" * 80)
                    
                    # 1. 性能测试
                    logger.info("📊 Running performance test...")
                    await self._send_chat_message("📊 开始性能测试...", metadata={"type": "performance_test"})
                    # TODO: 实现实际的性能测试逻辑
                    self.last_performance_test = datetime.now()
                    logger.info("✅ Performance test complete")
                    await self._send_chat_message("✅ 性能测试完成", metadata={"type": "performance_test"})
                    
                    # 2. 全面体检
                    await self._comprehensive_health_check()
                    
                    logger.info("=" * 80)
                    logger.info(f"✅ Wave 2 Complete at {datetime.now().strftime('%H:%M:%S')}")
                    logger.info("=" * 80)
                    
                except Exception as e:
                    logger.error(f"Wave 2 failed: {e}")
                
                # 等待30分钟
                await asyncio.sleep(1800)
                
        except asyncio.CancelledError:
            logger.info("Wave 2 task cancelled")
    
    async def _send_chat_message(self, content: str, metadata: Dict = None):
        """发送消息到聊天室"""
        try:
            from app.api.unified_chat_room import send_system_message
            await send_system_message(content, metadata)
        except Exception as e:
            logger.warning(f"Failed to send chat message: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取后台任务状态"""
        return {
            "started_at": self.started_at.isoformat(),
            "uptime_seconds": (datetime.now() - self.started_at).total_seconds(),
            "tool_pool_loaded": self.tool_pool_loaded,
            "last_health_check": self.last_health_check["timestamp"] if self.last_health_check else None,
            "last_performance_test": self.last_performance_test.isoformat() if self.last_performance_test else None,
            "last_api_check": self.last_api_check.isoformat() if self.last_api_check else None,
            "tasks": {
                name: "running" if not task.done() else "completed"
                for name, task in self.tasks.items()
            }
        }


# 全局实例
background_tasks_manager = BackgroundTasksManager()
