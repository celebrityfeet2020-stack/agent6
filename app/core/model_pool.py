"""
模型池管理模块
负责在容器启动后将OCR和Whisper模型热加载到内存(显存)中
确保首次调用时无需等待加载，实现毫秒级响应
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ModelPool:
    """模型池管理器"""
    
    def __init__(self):
        self.ocr_model = None
        self.whisper_model = None
        self.loaded = False
        self.load_time: Optional[datetime] = None
        self.errors: Dict[str, str] = {}
        
    def preload_models(self) -> bool:
        """
        预加载所有模型到内存
        
        Returns:
            bool: 是否成功加载所有模型
        """
        logger.info("🔧 开始预加载模型到内存...")
        success = True
        
        # 1. 加载EasyOCR模型
        if not self._load_ocr_model():
            success = False
        
        # 2. 加载Whisper模型
        if not self._load_whisper_model():
            success = False
        
        if success:
            self.loaded = True
            self.load_time = datetime.now()
            logger.info(f"✅ 模型池加载完成！加载时间: {self.load_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            logger.error(f"❌ 模型池加载失败！错误: {self.errors}")
        
        return success
    
    def _load_ocr_model(self) -> bool:
        """加载EasyOCR模型"""
        try:
            logger.info("  📦 正在加载EasyOCR模型...")
            import easyocr
            
            # 创建Reader对象会自动加载模型到内存
            self.ocr_model = easyocr.Reader(['en', 'ch_sim'], gpu=False)
            
            logger.info("  ✅ EasyOCR模型加载成功")
            return True
            
        except Exception as e:
            error_msg = f"EasyOCR模型加载失败: {str(e)}"
            logger.error(f"  ❌ {error_msg}")
            self.errors["ocr"] = error_msg
            return False
    
    def _load_whisper_model(self) -> bool:
        """加载Whisper模型"""
        try:
            logger.info("  📦 正在加载Whisper模型...")
            import whisper
            
            # 加载模型到内存
            self.whisper_model = whisper.load_model("small")
            
            logger.info("  ✅ Whisper模型加载成功")
            return True
            
        except Exception as e:
            error_msg = f"Whisper模型加载失败: {str(e)}"
            logger.error(f"  ❌ {error_msg}")
            self.errors["whisper"] = error_msg
            return False
    
    def get_ocr_model(self):
        """获取OCR模型实例"""
        if not self.loaded or self.ocr_model is None:
            logger.warning("⚠️ OCR模型未加载，尝试即时加载...")
            self._load_ocr_model()
        return self.ocr_model
    
    def get_whisper_model(self):
        """获取Whisper模型实例"""
        if not self.loaded or self.whisper_model is None:
            logger.warning("⚠️ Whisper模型未加载，尝试即时加载...")
            self._load_whisper_model()
        return self.whisper_model
    
    def get_status(self) -> Dict[str, Any]:
        """获取模型池状态"""
        return {
            "loaded": self.loaded,
            "load_time": self.load_time.strftime("%Y-%m-%d %H:%M:%S") if self.load_time else None,
            "models": {
                "ocr": self.ocr_model is not None,
                "whisper": self.whisper_model is not None
            },
            "errors": self.errors
        }
    
    def reload_failed_models(self) -> bool:
        """重新加载失败的模型"""
        logger.info("🔄 检查并重新加载失败的模型...")
        reloaded = False
        
        # 重新加载OCR模型（如果失败）
        if self.ocr_model is None:
            logger.info("  🔄 重新加载OCR模型...")
            if self._load_ocr_model():
                reloaded = True
                if "ocr" in self.errors:
                    del self.errors["ocr"]
        
        # 重新加载Whisper模型（如果失败）
        if self.whisper_model is None:
            logger.info("  🔄 重新加载Whisper模型...")
            if self._load_whisper_model():
                reloaded = True
                if "whisper" in self.errors:
                    del self.errors["whisper"]
        
        # 更新加载状态
        if self.ocr_model is not None and self.whisper_model is not None:
            self.loaded = True
            if not self.load_time:
                self.load_time = datetime.now()
        
        if reloaded:
            logger.info("✅ 失败模型重新加载完成")
        else:
            logger.info("ℹ️ 没有需要重新加载的模型")
        
        return reloaded


# 全局模型池实例
model_pool = ModelPool()
