"""
核心模块
"""
from app.core.browser_pool import BrowserPool, get_browser_pool, shutdown_browser_pool

__all__ = ["BrowserPool", "get_browser_pool", "shutdown_browser_pool"]
