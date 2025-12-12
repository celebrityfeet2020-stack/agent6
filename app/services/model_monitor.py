"""
模型监控服务
定期从8000端口获取当前运行的模型信息
"""
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from app.state import state_manager
from app.config import MODEL_HOST, MODEL_PORT

logger = logging.getLogger(__name__)


class ModelMonitor:
    """模型监控器"""
    
    def __init__(self):
        self.last_check_time: Optional[datetime] = None
        self.check_interval = 300  # 5分钟检查一次
        
    async def fetch_model_info(self) -> Optional[Dict[str, Any]]:
        """
        从模型服务获取模型信息
        
        Returns:
            模型信息字典，失败返回None
        """
        try:
            # 请求模型列表API
            url = f"http://{MODEL_HOST}:{MODEL_PORT}/v1/models"
            logger.info(f"正在从 {url} 获取模型信息...")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # OpenAI API格式: {"object": "list", "data": [{"id": "model_name", ...}]}
                if "data" in data and len(data["data"]) > 0:
                    model_info = data["data"][0]  # 取第一个模型
                    model_name = model_info.get("id", "unknown")
                    
                    logger.info(f"✅ 成功获取模型信息: {model_name}")
                    
                    return {
                        "name": model_name,
                        "full_info": model_info,
                        "fetched_at": datetime.now().isoformat(),
                        "source": url
                    }
                else:
                    logger.warning(f"⚠️ 模型列表为空: {data}")
                    return None
            else:
                logger.error(f"❌ 获取模型信息失败: HTTP {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"❌ 请求模型服务失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ 获取模型信息时发生错误: {str(e)}")
            return None
    
    async def update_model_info(self):
        """
        更新模型信息到state_manager
        
        这个方法会被定时任务调用
        """
        logger.info("🔍 开始更新模型信息...")
        
        model_info = await self.fetch_model_info()
        
        if model_info:
            # 更新到state_manager
            state_manager.current_model = model_info["name"]
            state_manager.model_status = model_info
            state_manager.model_last_check = datetime.now()
            
            logger.info(f"✅ 模型信息已更新: {model_info['name']}")
        else:
            logger.warning("⚠️ 模型信息更新失败")
        
        self.last_check_time = datetime.now()


# 全局模型监控器实例
model_monitor = ModelMonitor()
