"""
系统监控服务
负责定期获取模型状态、API状态等信息
"""
import httpx
import asyncio
from datetime import datetime
from app.config import MODEL_STATUS_CHECK_INTERVAL
from app.state import state_manager


class SystemMonitor:
    """系统监控服务"""
    
    def __init__(self):
        self.running = False
        self._task = None
    
    async def start(self):
        """启动监控服务"""
        if self.running:
            print("⚠️  SystemMonitor已在运行")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._monitor_loop())
        print("✅ SystemMonitor启动成功")
    
    async def stop(self):
        """停止监控服务"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("🛑 SystemMonitor已停止")
    
    async def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                await self._check_model_status()
            except Exception as e:
                print(f"❌ 模型状态检查失败: {e}")
            
            # 等待下一次检查
            await asyncio.sleep(MODEL_STATUS_CHECK_INTERVAL)
    
    async def _check_model_status(self):
        """检查模型状态"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # 获取当前加载的模型
                response = await client.get(f"http://{state_manager.config.MODEL_HOST}:{state_manager.config.MODEL_PORT}/v1/models")
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", [])
                    
                    if models:
                        current_model = models[0].get("id", "unknown")
                        state_manager.update_model_status(
                            model_name=current_model,
                            status={
                                "available": True,
                                "models": models,
                                "last_check": datetime.now().isoformat()
                            }
                        )
                        print(f"✅ 模型状态更新: {current_model}")
                    else:
                        state_manager.update_model_status(
                            model_name="无模型",
                            status={
                                "available": False,
                                "last_check": datetime.now().isoformat()
                            }
                        )
                else:
                    print(f"⚠️  模型API返回错误: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ 无法连接到模型服务({state_manager.config.MODEL_HOST}:{state_manager.config.MODEL_PORT}): {e}")
            state_manager.update_model_status(
                model_name="连接失败",
                status={
                    "available": False,
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }
            )


# 创建全局实例
system_monitor = SystemMonitor()
