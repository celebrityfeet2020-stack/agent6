"""
M3 Agent System v6.0 - Background Tasks Manager

后台任务管理器（优化时间安排，避免启动冲突）：
- 启动后15分钟：内存预加载（工具池+模型）
- 预加载后立即：API和工具内部检测 → 汇报到控制面板
- 之后每30分钟：API和工具检测
- 启动后30分钟：性能检测（模型性能测试）
- 之后每30分钟：性能检测

时间线：
T+0:    系统启动（轻量级，无预加载）
T+15:   内存预加载 + API/工具检测
T+30:   性能检测
T+45:   API/工具检测
T+60:   性能检测
T+75:   API/工具检测
...
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
import os

logger = logging.getLogger("m3_agent")


class BackgroundTasksManager:
    """后台任务管理器 v6.0"""
    
    def __init__(self):
        self.started_at = datetime.now()
        self.startup_time = time.time()
        
        # 状态标志
        self.preload_completed = False
        self.preload_time = None
        
        # 检测结果缓存
        self.last_api_check = None
        self.last_performance_test = None
        self.health_status = {
            "tools": {},
            "apis": {},
            "models": {},
            "browser_pool": {}
        }
        
        # 任务引用
        self.tasks = {}
    
    async def start(self):
        """启动所有后台任务"""
        logger.info("=" * 80)
        logger.info("🚀 Starting Background Tasks Manager v6.0")
        logger.info("=" * 80)
        logger.info("📅 Schedule:")
        logger.info("   T+15min: Memory Preload + API/Tool Check")
        logger.info("   T+30min: Performance Test")
        logger.info("   Then every 30min alternating (15min offset)")
        logger.info("=" * 80)
        
        # 启动预加载任务（15分钟后）
        self.tasks['preload'] = asyncio.create_task(
            self._delayed_preload_task()
        )
        
        # 启动API/工具检测任务（15分钟后首次，之后每30分钟）
        self.tasks['api_check'] = asyncio.create_task(
            self._api_tool_check_task()
        )
        
        # 启动性能检测任务（30分钟后首次，之后每30分钟）
        self.tasks['performance'] = asyncio.create_task(
            self._performance_test_task()
        )
        
        logger.info("✅ Background tasks scheduled")
    
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
    
    # ============================================
    # 内存预加载
    # ============================================
    
    async def _delayed_preload_task(self):
        """延迟预加载任务（启动后15分钟执行一次）"""
        try:
            logger.info("⏰ Memory preload scheduled in 15 minutes...")
            await asyncio.sleep(900)  # 15分钟
            
            logger.info("=" * 80)
            logger.info("📦 Starting Memory Preload (T+15min)")
            logger.info("=" * 80)
            
            await self._preload_memory()
            
            self.preload_completed = True
            self.preload_time = datetime.now()
            
            logger.info("=" * 80)
            logger.info(f"✅ Memory Preload Complete at {self.preload_time.strftime('%H:%M:%S')}")
            logger.info("=" * 80)
            
        except asyncio.CancelledError:
            logger.info("Preload task cancelled")
        except Exception as e:
            logger.error(f"Preload task failed: {e}", exc_info=True)
    
    async def _preload_memory(self):
        """预加载内存（工具池+模型）"""
        try:
            # 1. 预加载浏览器池（已在startup时加载，这里检查状态）
            logger.info("🌐 Checking browser pool...")
            from app.core.browser_pool import get_browser_pool
            browser_pool = get_browser_pool()
            if browser_pool and browser_pool._started:
                logger.info("   ✅ Browser pool already loaded")
                self.health_status["browser_pool"]["status"] = "loaded"
            else:
                logger.warning("   ⚠️ Browser pool not started")
                self.health_status["browser_pool"]["status"] = "not_started"
            
            # 2. 预加载Whisper模型
            logger.info("🎤 Preloading Whisper model...")
            try:
                from app.tools.speech_recognition_tool import SpeechRecognitionTool
                # 创建实例会触发预加载
                whisper_tool = SpeechRecognitionTool(preload_model=True, model_size="small")
                logger.info("   ✅ Whisper model loaded (small)")
                self.health_status["models"]["whisper"] = "loaded"
            except Exception as e:
                logger.warning(f"   ⚠️ Whisper preload failed: {e}")
                self.health_status["models"]["whisper"] = f"failed: {e}"
            
            # 3. 预加载OCR模型
            logger.info("🔍 Preloading OCR models...")
            try:
                from app.tools.image_ocr import ImageOCRTool
                ocr_tool = ImageOCRTool()
                logger.info("   ✅ OCR models loaded (EasyOCR)")
                self.health_status["models"]["ocr"] = "loaded"
            except Exception as e:
                logger.warning(f"   ⚠️ OCR preload failed: {e}")
                self.health_status["models"]["ocr"] = f"failed: {e}"
            
            # 4. 预加载图像分析模型
            logger.info("🖼️ Preloading image analysis models...")
            try:
                from app.tools.image_analysis import ImageAnalysisTool
                image_tool = ImageAnalysisTool()
                logger.info("   ✅ Image analysis models loaded (Haar Cascade)")
                self.health_status["models"]["image_analysis"] = "loaded"
            except Exception as e:
                logger.warning(f"   ⚠️ Image analysis preload failed: {e}")
                self.health_status["models"]["image_analysis"] = f"failed: {e}"
            
            # 推送到聊天室
            await self._send_system_message(
                "✅ 内存预加载完成\n" +
                f"- 浏览器池: {self.health_status['browser_pool'].get('status', 'unknown')}\n" +
                f"- Whisper: {self.health_status['models'].get('whisper', 'unknown')}\n" +
                f"- OCR: {self.health_status['models'].get('ocr', 'unknown')}\n" +
                f"- 图像分析: {self.health_status['models'].get('image_analysis', 'unknown')}",
                metadata={"type": "memory_preload", "status": self.health_status}
            )
            
        except Exception as e:
            logger.error(f"Memory preload failed: {e}", exc_info=True)
            await self._send_system_message(
                f"❌ 内存预加载失败: {e}",
                metadata={"type": "error"}
            )
    
    # ============================================
    # API和工具检测
    # ============================================
    
    async def _api_tool_check_task(self):
        """API和工具检测任务（15分钟后首次，之后每30分钟）"""
        try:
            # 首次等待15分钟（与预加载同时）
            logger.info("⏰ API/Tool check scheduled in 15 minutes...")
            await asyncio.sleep(900)  # 15分钟
            
            # 等待预加载完成
            await asyncio.sleep(10)  # 预加载后10秒执行检测
            
            while True:
                try:
                    logger.info("=" * 80)
                    logger.info("🔌 API/Tool Health Check")
                    logger.info("=" * 80)
                    
                    await self._check_api_and_tools()
                    
                    logger.info("=" * 80)
                    logger.info(f"✅ API/Tool Check Complete at {datetime.now().strftime('%H:%M:%S')}")
                    logger.info("=" * 80)
                    
                except Exception as e:
                    logger.error(f"API/Tool check failed: {e}")
                
                # 等待30分钟
                await asyncio.sleep(1800)
                
        except asyncio.CancelledError:
            logger.info("API/Tool check task cancelled")
    
    async def _check_api_and_tools(self):
        """检查API和工具状态"""
        check_result = {
            "timestamp": datetime.now().isoformat(),
            "tools": {},
            "apis": {},
            "summary": {}
        }
        
        try:
            # 1. 检查15个工具
            logger.info("🔧 Checking tools...")
            from app.core.startup import initialize_browser_pool_and_tools
            try:
                _, tools = initialize_browser_pool_and_tools()
                check_result["tools"]["count"] = len(tools)
                check_result["tools"]["names"] = [tool.name for tool in tools]
                check_result["tools"]["status"] = "available"
                logger.info(f"   ✅ {len(tools)} tools available")
                
                # 测试关键工具
                tool_tests = {}
                for tool in tools[:3]:  # 测试前3个工具
                    try:
                        # 简单测试：检查工具是否有必要的方法
                        if hasattr(tool, '_run') and hasattr(tool, 'name'):
                            tool_tests[tool.name] = "ok"
                        else:
                            tool_tests[tool.name] = "missing_methods"
                    except Exception as e:
                        tool_tests[tool.name] = f"error: {e}"
                
                check_result["tools"]["tests"] = tool_tests
                
            except Exception as e:
                logger.warning(f"   ❌ Tools check failed: {e}")
                check_result["tools"]["status"] = "error"
                check_result["tools"]["error"] = str(e)
            
            # 2. 检查Fleet API
            logger.info("🚢 Checking Fleet API...")
            try:
                from app.api.fleet_api import router as fleet_router
                check_result["apis"]["fleet"] = "available"
                logger.info("   ✅ Fleet API available")
            except Exception as e:
                check_result["apis"]["fleet"] = f"error: {e}"
                logger.warning(f"   ❌ Fleet API: {e}")
            
            # 3. 检查LangGraph API
            logger.info("🔗 Checking LangGraph API...")
            try:
                from app.api.langgraph_adapter import router as langgraph_router
                check_result["apis"]["langgraph"] = "available"
                logger.info("   ✅ LangGraph API available")
            except Exception as e:
                check_result["apis"]["langgraph"] = f"error: {e}"
                logger.warning(f"   ❌ LangGraph API: {e}")
            
            # 4. 检查LLM连接
            logger.info("🤖 Checking LLM connection...")
            llm_base_url = os.getenv("LLM_BASE_URL", "http://192.168.9.125:8000/v1")
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{llm_base_url}/models")
                    if response.status_code == 200:
                        data = response.json()
                        models = data.get("data", [])
                        check_result["apis"]["llm"] = {
                            "status": "connected",
                            "models_count": len(models),
                            "models": [m.get("id") for m in models[:3]]
                        }
                        logger.info(f"   ✅ LLM connected ({len(models)} models)")
                    else:
                        check_result["apis"]["llm"] = {"status": "error", "code": response.status_code}
                        logger.warning(f"   ⚠️ LLM returned {response.status_code}")
            except Exception as e:
                check_result["apis"]["llm"] = {"status": "error", "error": str(e)}
                logger.warning(f"   ❌ LLM connection failed: {e}")
            
            # 5. 生成摘要
            tools_ok = check_result["tools"].get("status") == "available"
            fleet_ok = check_result["apis"].get("fleet") == "available"
            langgraph_ok = check_result["apis"].get("langgraph") == "available"
            llm_ok = check_result["apis"].get("llm", {}).get("status") == "connected"
            
            check_result["summary"] = {
                "tools": "✅" if tools_ok else "❌",
                "fleet_api": "✅" if fleet_ok else "❌",
                "langgraph_api": "✅" if langgraph_ok else "❌",
                "llm": "✅" if llm_ok else "❌",
                "overall": "healthy" if all([tools_ok, fleet_ok, langgraph_ok, llm_ok]) else "degraded"
            }
            
            self.last_api_check = check_result
            self.health_status["tools"] = check_result["tools"]
            self.health_status["apis"] = check_result["apis"]
            
            # 推送到聊天室和控制面板
            await self._send_system_message(
                "🔌 API/工具检测完成\n" +
                f"- 工具: {check_result['summary']['tools']} ({check_result['tools'].get('count', 0)}个)\n" +
                f"- Fleet API: {check_result['summary']['fleet_api']}\n" +
                f"- LangGraph API: {check_result['summary']['langgraph_api']}\n" +
                f"- LLM: {check_result['summary']['llm']}\n" +
                f"- 整体状态: {check_result['summary']['overall']}",
                metadata={"type": "api_tool_check", "result": check_result}
            )
            
        except Exception as e:
            logger.error(f"API/Tool check failed: {e}", exc_info=True)
    
    # ============================================
    # 性能检测
    # ============================================
    
    async def _performance_test_task(self):
        """性能检测任务（30分钟后首次，之后每30分钟）"""
        try:
            # 首次等待30分钟
            logger.info("⏰ Performance test scheduled in 30 minutes...")
            await asyncio.sleep(1800)  # 30分钟
            
            while True:
                try:
                    logger.info("=" * 80)
                    logger.info("📊 Performance Test")
                    logger.info("=" * 80)
                    
                    await self._run_performance_test()
                    
                    logger.info("=" * 80)
                    logger.info(f"✅ Performance Test Complete at {datetime.now().strftime('%H:%M:%S')}")
                    logger.info("=" * 80)
                    
                except Exception as e:
                    logger.error(f"Performance test failed: {e}")
                
                # 等待30分钟
                await asyncio.sleep(1800)
                
        except asyncio.CancelledError:
            logger.info("Performance test task cancelled")
    
    async def _run_performance_test(self):
        """运行性能测试"""
        test_result = {
            "timestamp": datetime.now().isoformat(),
            "model_performance": {},
            "memory_status": {}
        }
        
        try:
            # 1. 测试LLM性能
            logger.info("🤖 Testing LLM performance...")
            llm_base_url = os.getenv("LLM_BASE_URL", "http://192.168.9.125:8000/v1")
            
            try:
                # 获取当前模型
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{llm_base_url}/models")
                    data = response.json()
                    models = data.get("data", [])
                    current_model = models[0].get("id") if models else None
                
                if current_model:
                    # 测试TTFT和吞吐量
                    test_prompt = "你好"
                    start_time = time.time()
                    ttft = None
                    
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        async with client.stream(
                            "POST",
                            f"{llm_base_url}/chat/completions",
                            json={
                                "model": current_model,
                                "messages": [{"role": "user", "content": test_prompt}],
                                "max_tokens": 50,
                                "stream": True
                            }
                        ) as response:
                            first_chunk = True
                            async for line in response.aiter_lines():
                                if first_chunk and line.strip():
                                    ttft = (time.time() - start_time) * 1000
                                    first_chunk = False
                    
                    end_time = time.time()
                    total_latency = (end_time - start_time) * 1000
                    
                    # 获取token统计
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(
                            f"{llm_base_url}/chat/completions",
                            json={
                                "model": current_model,
                                "messages": [{"role": "user", "content": test_prompt}],
                                "max_tokens": 50
                            }
                        )
                        data = response.json()
                        usage = data.get("usage", {})
                        completion_tokens = usage.get("completion_tokens", 0)
                    
                    tokens_per_second = round(completion_tokens / (total_latency / 1000), 2) if total_latency > 0 else 0
                    
                    test_result["model_performance"] = {
                        "model": current_model,
                        "tokens_per_second": tokens_per_second,
                        "ttft_ms": round(ttft, 2) if ttft else 0,
                        "total_latency_ms": round(total_latency, 2),
                        "status": "ok"
                    }
                    
                    logger.info(f"   ✅ {current_model}: {tokens_per_second} tok/s, TTFT: {ttft:.2f}ms")
                else:
                    test_result["model_performance"] = {"status": "no_model"}
                    logger.warning("   ⚠️ No model loaded")
                    
            except Exception as e:
                test_result["model_performance"] = {"status": "error", "error": str(e)}
                logger.warning(f"   ❌ LLM performance test failed: {e}")
            
            # 2. 检查内存状态
            logger.info("💾 Checking memory status...")
            try:
                import psutil
                process = psutil.Process()
                memory_info = process.memory_info()
                
                test_result["memory_status"] = {
                    "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                    "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                    "percent": round(process.memory_percent(), 2)
                }
                
                logger.info(f"   ✅ Memory: {test_result['memory_status']['rss_mb']} MB RSS")
            except Exception as e:
                test_result["memory_status"] = {"error": str(e)}
                logger.warning(f"   ⚠️ Memory check failed: {e}")
            
            self.last_performance_test = test_result
            
            # 推送到聊天室和控制面板
            perf = test_result.get("model_performance", {})
            mem = test_result.get("memory_status", {})
            
            await self._send_system_message(
                "📊 性能测试完成\n" +
                f"- 模型: {perf.get('model', 'N/A')}\n" +
                f"- 吞吐量: {perf.get('tokens_per_second', 0)} tok/s\n" +
                f"- TTFT: {perf.get('ttft_ms', 0)} ms\n" +
                f"- 内存: {mem.get('rss_mb', 0)} MB",
                metadata={"type": "performance_test", "result": test_result}
            )
            
        except Exception as e:
            logger.error(f"Performance test failed: {e}", exc_info=True)
    
    # ============================================
    # 辅助方法
    # ============================================
    
    async def _send_system_message(self, content: str, metadata: Dict = None):
        """发送系统消息到聊天室"""
        try:
            from backend.app.api.unified_chat_room import send_system_message
            await send_system_message(content, metadata)
        except Exception as e:
            logger.debug(f"Failed to send system message: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取后台任务状态"""
        uptime = time.time() - self.startup_time
        
        return {
            "started_at": self.started_at.isoformat(),
            "uptime_seconds": round(uptime, 2),
            "uptime_formatted": self._format_uptime(uptime),
            "preload_completed": self.preload_completed,
            "preload_time": self.preload_time.isoformat() if self.preload_time else None,
            "last_api_check": self.last_api_check["timestamp"] if self.last_api_check else None,
            "last_performance_test": self.last_performance_test["timestamp"] if self.last_performance_test else None,
            "health_status": self.health_status,
            "tasks": {
                name: "running" if not task.done() else "completed"
                for name, task in self.tasks.items()
            }
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """格式化运行时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"


# 全局实例
background_tasks_manager = BackgroundTasksManager()
