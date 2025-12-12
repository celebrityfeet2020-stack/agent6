"""
Agent6 统一配置模块
负责管理所有系统配置,包括版本号、时区、上下文长度等
"""
import os
from pathlib import Path

# ==================== 系统基础配置 ====================
AGENT_VERSION = "Agent 6"
TIMEZONE = "Asia/Shanghai"  # 北京时间

# 设置环境变量时区
os.environ["TZ"] = TIMEZONE

# ==================== 路径配置 ====================
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ==================== 端口配置 ====================
API_PORT = 8888  # 主API端口
DASHBOARD_PORT = 8889  # 管理面板端口(将合并到8888)
MODEL_PORT = 8000  # LM Studio模型端口

# ==================== 上下文管理配置 ====================
# 可配置的上下文长度参数
MAX_CONTEXT_LENGTH = 200000  # 最大上下文长度(tokens)
COMPRESSION_THRESHOLD = 0.85  # 压缩阈值(当使用率达到85%时触发压缩)

# 计算具体的压缩触发点
COMPRESSION_TRIGGER_TOKENS = int(MAX_CONTEXT_LENGTH * COMPRESSION_THRESHOLD)  # 170,000 tokens

# ==================== 工具池配置 ====================
# 工具池预加载时间(容器启动后5分钟)
TOOL_POOL_PRELOAD_DELAY = 300  # 秒
# 工具池健康检查间隔(每30分钟)
TOOL_POOL_CHECK_INTERVAL = 1800  # 秒

# ==================== 浏览器池配置 ====================
# 浏览器池预加载时间(容器启动后5分钟)
BROWSER_POOL_PRELOAD_DELAY = 300  # 秒
# 浏览器池健康检查间隔(每30分钟)
BROWSER_POOL_CHECK_INTERVAL = 1800  # 秒

# ==================== 性能检测配置 ====================
# 性能检测首次执行延迟(容器启动后20分钟)
PERFORMANCE_CHECK_DELAY = 1200  # 秒
# 性能检测间隔(每30分钟)
PERFORMANCE_CHECK_INTERVAL = 1800  # 秒

# ==================== 模型监控配置 ====================
# 模型状态获取间隔(每1分钟)
MODEL_STATUS_CHECK_INTERVAL = 60  # 秒

# ==================== LangGraph配置 ====================
LANGGRAPH_RECURSION_LIMIT = 50

# ==================== 日志配置 ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ==================== API配置 ====================
# 是否启用CORS
ENABLE_CORS = True
# 允许的源
CORS_ORIGINS = ["*"]

# ==================== 配置验证 ====================
def validate_config():
    """验证配置的有效性"""
    assert MAX_CONTEXT_LENGTH > 0, "MAX_CONTEXT_LENGTH必须大于0"
    assert 0 < COMPRESSION_THRESHOLD < 1, "COMPRESSION_THRESHOLD必须在0-1之间"
    assert TOOL_POOL_PRELOAD_DELAY >= 0, "TOOL_POOL_PRELOAD_DELAY不能为负数"
    assert PERFORMANCE_CHECK_DELAY >= 0, "PERFORMANCE_CHECK_DELAY不能为负数"
    print(f"✅ 配置验证通过 - {AGENT_VERSION}")
    print(f"   时区: {TIMEZONE}")
    print(f"   上下文长度: {MAX_CONTEXT_LENGTH:,} tokens")
    print(f"   压缩阈值: {COMPRESSION_THRESHOLD*100}% ({COMPRESSION_TRIGGER_TOKENS:,} tokens)")

# 模块加载时自动验证
validate_config()
