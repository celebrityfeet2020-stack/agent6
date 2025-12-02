"""
M3 Agent System v2.2.0 - Logging Configuration
统一的日志配置，支持文件轮转和结构化日志
"""

import logging
import logging.handlers
import os
from datetime import datetime

# 日志目录
LOG_DIR = os.getenv("LOG_DIR", "/var/log/m3_agent")
os.makedirs(LOG_DIR, exist_ok=True)

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(name: str = "m3_agent", level: str = "INFO"):
    """
    配置日志系统
    
    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 控制台 Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件 Handler（带轮转）
    log_file = os.path.join(LOG_DIR, f"{name}.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 错误日志单独记录
    error_log_file = os.path.join(LOG_DIR, f"{name}_error.log")
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    return logger

# 创建默认日志记录器
main_logger = setup_logging("m3_agent", "INFO")
admin_logger = setup_logging("m3_admin", "INFO")
tool_logger = setup_logging("m3_tools", "DEBUG")
