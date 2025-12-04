"""
M3 Agent System v5.8 - Enhanced Global Tool Pool
增强版全局工具池：预加载所有工具到内存（512GB内存完全够用）

v5.8新增预加载：
- Whisper模型（语音识别）
- OpenCV模型（图像分析）
- 浏览器实例（Playwright）
- Docker客户端（代码执行）
- SSH连接池（远程执行）

总内存占用预估：~3-5GB（512GB内存占用不到1%）
"""

import logging
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class EnhancedToolPool:
    """
    增强版全局工具池：管理所有重量级工具资源
    
    v5.8设计原则：
    1. 启动时一次性加载所有重量级资源
    2. 保持资源在内存中，避免重复加载
    3. 提供统一的资源访问接口
    4. 支持资源健康检查和重启
    5. 尽可能预加载，512GB内存完全够用
    """
    
    def __init__(self):
        # OCR资源
        self.ocr_reader = None
        self.ocr_loaded = False
        self.ocr_load_time = 0.0
        
        # Whisper资源（v5.8新增预加载）
        self.whisper_model = None
        self.whisper_loaded = False
        self.whisper_load_time = 0.0
        
        # OpenCV资源（v5.8新增预加载）
        self.cv_models = {}
        self.cv_loaded = False
        self.cv_load_time = 0.0
        
        # Telegram资源
        self.telegram_client = None
        self.telegram_loaded = False
        
        # Docker资源
        self.docker_client = None
        self.docker_loaded = False
        self.docker_load_time = 0.0
        
        # SSH连接池
        self.ssh_connections: Dict[str, Any] = {}
        
        # 浏览器池（由browser_pool.py管理，这里只记录状态）
        self.browser_pool = None
        self.browser_pool_loaded = False
        
        # 初始化时间
        self.initialized_at: Optional[datetime] = None
        self.total_load_time = 0.0
        
        # 内存占用估算（MB）
        self.memory_usage = {
            "ocr": 0,
            "whisper": 0,
            "cv": 0,
            "docker": 0,
            "browser": 0,
            "total": 0
        }
    
    async def initialize(self):
        """
        初始化工具池：预加载所有重量级资源
        
        v5.8策略：
        - 尽可能预加载所有工具
        - 失败不中断启动（降级使用懒加载）
        - 记录详细的加载时间和内存占用
        """
        logger.info("=" * 80)
        logger.info("🚀 Initializing Enhanced Tool Pool (v5.8)")
        logger.info("   Target: Pre-load ALL tools into memory (512GB available)")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        
        # 1. 加载EasyOCR（高优先级，~500MB）
        await self._load_ocr()
        
        # 2. 加载Whisper模型（v5.8新增，~500MB）
        await self._load_whisper()
        
        # 3. 加载OpenCV模型（v5.8新增，~100MB）
        await self._load_cv()
        
        # 4. 加载Docker客户端（中优先级，~10MB）
        await self._load_docker()
        
        # 5. 加载Telegram客户端（可选）
        await self._load_telegram()
        
        # 6. 浏览器池（由browser_pool.py管理）
        logger.info("ℹ️  Browser pool: Managed by browser_pool.py")
        
        # 记录初始化完成
        self.initialized_at = datetime.now()
        self.total_load_time = (self.initialized_at - start_time).total_seconds()
        
        # 计算总内存占用
        self.memory_usage["total"] = sum([
            self.memory_usage["ocr"],
            self.memory_usage["whisper"],
            self.memory_usage["cv"],
            self.memory_usage["docker"],
            self.memory_usage["browser"]
        ])
        
        logger.info("=" * 80)
        logger.info(f"✅ Enhanced Tool Pool Initialized in {self.total_load_time:.2f}s")
        logger.info(f"   - OCR:      {'✅' if self.ocr_loaded else '❌'} ({self.ocr_load_time:.2f}s, ~{self.memory_usage['ocr']}MB)")
        logger.info(f"   - Whisper:  {'✅' if self.whisper_loaded else '❌'} ({self.whisper_load_time:.2f}s, ~{self.memory_usage['whisper']}MB)")
        logger.info(f"   - OpenCV:   {'✅' if self.cv_loaded else '❌'} ({self.cv_load_time:.2f}s, ~{self.memory_usage['cv']}MB)")
        logger.info(f"   - Docker:   {'✅' if self.docker_loaded else '❌'} ({self.docker_load_time:.2f}s, ~{self.memory_usage['docker']}MB)")
        logger.info(f"   - Telegram: {'✅' if self.telegram_loaded else '❌'}")
        logger.info(f"   Total Memory: ~{self.memory_usage['total']}MB / 512GB (< 1%)")
        logger.info("=" * 80)
    
    async def _load_ocr(self):
        """加载EasyOCR模型"""
        try:
            logger.info("📸 Loading EasyOCR model (en, ch_sim)...")
            start = datetime.now()
            
            import easyocr
            self.ocr_reader = easyocr.Reader(['en', 'ch_sim'], gpu=False)
            
            self.ocr_load_time = (datetime.now() - start).total_seconds()
            self.ocr_loaded = True
            self.memory_usage["ocr"] = 500  # 估算500MB
            logger.info(f"✅ EasyOCR loaded in {self.ocr_load_time:.2f}s (~500MB)")
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to load EasyOCR: {e}")
            logger.warning("   Will use lazy loading on first OCR request")
            self.ocr_loaded = False
    
    async def _load_whisper(self):
        """加载Whisper模型（v5.8新增）"""
        try:
            logger.info("🎤 Loading Whisper model (medium)...")
            start = datetime.now()
            
            import whisper
            # 使用medium模型（平衡速度和精度）
            self.whisper_model = whisper.load_model("medium")
            
            self.whisper_load_time = (datetime.now() - start).total_seconds()
            self.whisper_loaded = True
            self.memory_usage["whisper"] = 500  # 估算500MB
            logger.info(f"✅ Whisper model loaded in {self.whisper_load_time:.2f}s (~500MB)")
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to load Whisper model: {e}")
            logger.warning("   Will use lazy loading on first speech recognition request")
            self.whisper_loaded = False
    
    async def _load_cv(self):
        """加载OpenCV模型（v5.8新增）"""
        try:
            logger.info("👁️  Loading OpenCV models (Haar Cascade)...")
            start = datetime.now()
            
            import cv2
            
            # 加载Haar Cascade分类器
            cascade_path = cv2.data.haarcascades
            
            # 人脸检测
            self.cv_models["face"] = cv2.CascadeClassifier(
                os.path.join(cascade_path, 'haarcascade_frontalface_default.xml')
            )
            
            # 眼睛检测
            self.cv_models["eye"] = cv2.CascadeClassifier(
                os.path.join(cascade_path, 'haarcascade_eye.xml')
            )
            
            # 微笑检测
            self.cv_models["smile"] = cv2.CascadeClassifier(
                os.path.join(cascade_path, 'haarcascade_smile.xml')
            )
            
            self.cv_load_time = (datetime.now() - start).total_seconds()
            self.cv_loaded = True
            self.memory_usage["cv"] = 100  # 估算100MB
            logger.info(f"✅ OpenCV models loaded in {self.cv_load_time:.2f}s (~100MB)")
            logger.info(f"   Loaded: face, eye, smile detectors")
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to load OpenCV models: {e}")
            logger.warning("   Will use lazy loading on first image analysis request")
            self.cv_loaded = False
    
    async def _load_docker(self):
        """
        加载Docker客户端
        
        v5.8增强：
        - 检查Docker socket是否存在
        - 检查Docker daemon是否运行
        - 提供详细的错误提示
        """
        try:
            logger.info("🐳 Loading Docker client...")
            start = datetime.now()
            
            # v5.8: 检查Docker socket
            import os
            docker_socket = "/var/run/docker.sock"
            if not os.path.exists(docker_socket):
                logger.warning(f"⚠️  Docker socket not found: {docker_socket}")
                logger.warning("   To enable Docker support, run:")
                logger.warning("   docker run -v /var/run/docker.sock:/var/run/docker.sock ...")
                self.docker_loaded = False
                return
            
            # 加载Docker客户端
            import docker
            self.docker_client = docker.from_env()
            
            # v5.8: 测试连接和版本
            ping_result = self.docker_client.ping()
            version_info = self.docker_client.version()
            
            self.docker_load_time = (datetime.now() - start).total_seconds()
            self.docker_loaded = True
            self.memory_usage["docker"] = 10  # 估算10MB
            logger.info(f"✅ Docker client loaded in {self.docker_load_time:.2f}s (~10MB)")
            logger.info(f"   Docker version: {version_info.get('Version', 'unknown')}")
            logger.info(f"   API version: {version_info.get('ApiVersion', 'unknown')}")
            
        except ImportError as e:
            logger.warning(f"⚠️  Docker Python library not installed: {e}")
            logger.warning("   Install with: pip install docker")
            self.docker_loaded = False
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to load Docker client: {e}")
            logger.warning("   Code execution tool will use subprocess fallback")
            logger.warning("   Hint: Make sure Docker daemon is running")
            self.docker_loaded = False
    
    async def _load_telegram(self):
        """加载Telegram客户端（可选）"""
        try:
            # Telegram需要认证，暂时跳过预加载
            # 可以在有配置时再启用
            logger.info("📱 Telegram client: Skipped (requires authentication)")
            self.telegram_loaded = False
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to load Telegram client: {e}")
            self.telegram_loaded = False
    
    # ============================================
    # 资源访问接口
    # ============================================
    
    def get_ocr_reader(self):
        """
        获取OCR Reader
        
        Returns:
            EasyOCR Reader实例，如果未加载则尝试懒加载
        """
        if not self.ocr_loaded:
            logger.warning("OCR reader not pre-loaded, creating on demand...")
            try:
                import easyocr
                self.ocr_reader = easyocr.Reader(['en', 'ch_sim'], gpu=False)
                self.ocr_loaded = True
                logger.info("✅ EasyOCR loaded on demand")
            except Exception as e:
                logger.error(f"Failed to load EasyOCR: {e}")
                return None
        
        return self.ocr_reader
    
    def get_whisper_model(self):
        """
        获取Whisper模型（v5.8新增）
        
        Returns:
            Whisper模型实例，如果未加载则尝试懒加载
        """
        if not self.whisper_loaded:
            logger.warning("Whisper model not pre-loaded, creating on demand...")
            try:
                import whisper
                self.whisper_model = whisper.load_model("medium")
                self.whisper_loaded = True
                logger.info("✅ Whisper model loaded on demand")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                return None
        
        return self.whisper_model
    
    def get_cv_model(self, model_type: str = "face"):
        """
        获取OpenCV模型（v5.8新增）
        
        Args:
            model_type: 模型类型（face/eye/smile）
        
        Returns:
            OpenCV分类器实例，如果未加载则尝试懒加载
        """
        if not self.cv_loaded:
            logger.warning("OpenCV models not pre-loaded, creating on demand...")
            try:
                import cv2
                cascade_path = cv2.data.haarcascades
                
                if model_type == "face":
                    model = cv2.CascadeClassifier(
                        os.path.join(cascade_path, 'haarcascade_frontalface_default.xml')
                    )
                elif model_type == "eye":
                    model = cv2.CascadeClassifier(
                        os.path.join(cascade_path, 'haarcascade_eye.xml')
                    )
                elif model_type == "smile":
                    model = cv2.CascadeClassifier(
                        os.path.join(cascade_path, 'haarcascade_smile.xml')
                    )
                else:
                    logger.error(f"Unknown model type: {model_type}")
                    return None
                
                self.cv_models[model_type] = model
                logger.info(f"✅ OpenCV {model_type} model loaded on demand")
                return model
                
            except Exception as e:
                logger.error(f"Failed to load OpenCV model: {e}")
                return None
        
        return self.cv_models.get(model_type)
    
    def get_docker_client(self):
        """
        获取Docker客户端
        
        Returns:
            Docker client实例，如果未加载则尝试懒加载
        """
        if not self.docker_loaded:
            logger.warning("Docker client not pre-loaded, creating on demand...")
            try:
                import docker
                self.docker_client = docker.from_env()
                self.docker_client.ping()
                self.docker_loaded = True
                logger.info("✅ Docker client loaded on demand")
            except Exception as e:
                logger.error(f"Failed to load Docker client: {e}")
                return None
        
        return self.docker_client
    
    def get_ssh_connection(self, host: str, port: int = 22):
        """
        获取SSH连接（连接池）
        
        Args:
            host: SSH主机地址
            port: SSH端口
        
        Returns:
            SSH连接实例，如果不存在则返回None
        """
        key = f"{host}:{port}"
        return self.ssh_connections.get(key)
    
    def add_ssh_connection(self, host: str, connection: Any, port: int = 22):
        """
        添加SSH连接到连接池
        
        Args:
            host: SSH主机地址
            connection: SSH连接实例
            port: SSH端口
        """
        key = f"{host}:{port}"
        self.ssh_connections[key] = connection
        logger.info(f"✅ SSH connection added to pool: {key}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取工具池状态
        
        Returns:
            状态字典
        """
        return {
            "initialized": self.initialized_at is not None,
            "initialized_at": self.initialized_at.isoformat() if self.initialized_at else None,
            "total_load_time": self.total_load_time,
            "resources": {
                "ocr": {
                    "loaded": self.ocr_loaded,
                    "load_time": self.ocr_load_time,
                    "memory_mb": self.memory_usage["ocr"]
                },
                "whisper": {
                    "loaded": self.whisper_loaded,
                    "load_time": self.whisper_load_time,
                    "memory_mb": self.memory_usage["whisper"]
                },
                "opencv": {
                    "loaded": self.cv_loaded,
                    "load_time": self.cv_load_time,
                    "memory_mb": self.memory_usage["cv"],
                    "models": list(self.cv_models.keys())
                },
                "docker": {
                    "loaded": self.docker_loaded,
                    "load_time": self.docker_load_time,
                    "memory_mb": self.memory_usage["docker"]
                },
                "telegram": {
                    "loaded": self.telegram_loaded
                },
                "ssh_connections": len(self.ssh_connections),
            },
            "memory_usage": self.memory_usage
        }
    
    async def shutdown(self):
        """关闭工具池，释放资源"""
        logger.info("🛑 Shutting down Enhanced Tool Pool...")
        
        # 关闭Docker客户端
        if self.docker_client:
            try:
                self.docker_client.close()
                logger.info("✅ Docker client closed")
            except Exception as e:
                logger.warning(f"Failed to close Docker client: {e}")
        
        # 关闭Telegram客户端
        if self.telegram_client:
            try:
                await self.telegram_client.disconnect()
                logger.info("✅ Telegram client disconnected")
            except Exception as e:
                logger.warning(f"Failed to disconnect Telegram: {e}")
        
        # 关闭SSH连接
        for key, conn in self.ssh_connections.items():
            try:
                conn.close()
                logger.info(f"✅ SSH connection closed: {key}")
            except Exception as e:
                logger.warning(f"Failed to close SSH {key}: {e}")
        
        logger.info("✅ Enhanced Tool Pool shutdown complete")


# 全局工具池实例
enhanced_tool_pool = EnhancedToolPool()


# 导出
__all__ = ['enhanced_tool_pool', 'EnhancedToolPool']
