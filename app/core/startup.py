"""
M3 Agent v5.9.1 - Startup Event Handler (FIXED)
Initializes browser pool and tools - synchronous version
"""

from app.core.browser_pool import get_browser_pool
from app.tools import *
import logging

logger = logging.getLogger(__name__)


def initialize_browser_pool_and_tools():
    """
    Initialize browser pool and tools.
    
    v5.9.1 FIX: Changed to synchronous to avoid event loop conflicts.
    Browser pool is pre-loaded into memory using sync API.
    
    Returns:
        tuple: (browser_pool, tools list)
    """
    logger.info("[Startup] Initializing browser pool...")
    
    # Initialize browser pool (sync)
    browser_pool = get_browser_pool(headless=True)
    browser_pool.start()  # Explicitly start to pre-load into memory
    logger.info("✅ Browser pool pre-loaded into memory (v5.9.1 FIXED - sync mode)")
    
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
    
    logger.info(f"✅ {len(tools)} tools initialized with browser pool (v5.9.1 FIXED)")
    
    return browser_pool, tools
