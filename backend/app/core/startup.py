"""
M3 Agent v5.1 - Startup Event Handler
Initializes browser pool and tools in FastAPI startup event
"""

from app.core.browser_pool import get_browser_pool
from app.tools import *
import logging

logger = logging.getLogger(__name__)


async def initialize_browser_pool_and_tools():
    """
    Initialize browser pool and tools in FastAPI startup event.
    
    v5.1: Moved from module-level to startup event to avoid event loop conflicts.
    This ensures browser pool is pre-loaded into memory but doesn't conflict with
    admin_app's event loop.
    
    Returns:
        tuple: (browser_pool, tools list)
    """
    logger.info("[Startup] Initializing browser pool...")
    
    # v6.1: Get browser pool instance but don't start it yet
    # Browser will be started lazily on first use to avoid asyncio conflicts
    browser_pool = get_browser_pool(headless=True)
    logger.info("✅ Browser pool instance created (lazy initialization)")
    
    # Initialize all 15 tools with browser pool
    tools = [
        WebSearchTool(),
        WebScraperTool(browser_pool=browser_pool),
        CodeExecutorTool(),
        FileOperationsTool(),
        ImageOCRTool(),
        ImageAnalysisTool(),  # Pre-loaded Haar Cascade
        SSHTool(),
        GitTool(),
        DataAnalysisTool(),
        BrowserAutomationTool(browser_pool=browser_pool),
        UniversalAPITool(),
        TelegramTool(browser_pool=browser_pool),
        SpeechRecognitionTool(preload_model=True, model_size="small"),  # Pre-loaded Whisper
        RPATool(),
        FileSyncTool(),
    ]
    
    logger.info(f"✅ {len(tools)} tools initialized with browser pool (v6.1 - lazy init)")
    
    return browser_pool, tools
