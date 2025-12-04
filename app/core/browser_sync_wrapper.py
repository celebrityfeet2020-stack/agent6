"""
M3 Agent v5.2 - Synchronous Wrapper for Async Browser Pool
Allows sync tools to use async browser pool
"""

import asyncio
from playwright.async_api import Page
from app.core.browser_pool import BrowserPool
import logging

logger = logging.getLogger(__name__)


def get_page_sync(browser_pool: BrowserPool) -> Page:
    """
    Synchronous wrapper to get a page from async browser pool.
    
    Args:
        browser_pool: The async BrowserPool instance
        
    Returns:
        Page: A new browser page
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, create a new one in a thread
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(browser_pool.get_page())
        else:
            # If no loop is running, use asyncio.run()
            return asyncio.run(browser_pool.get_page())
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(browser_pool.get_page())


async def close_page_async(page: Page):
    """
    Async helper to close a page.
    
    Args:
        page: Page to close
    """
    try:
        await page.close()
    except Exception as e:
        logger.warning(f"Error closing page: {e}")


def close_page_sync(page: Page):
    """
    Synchronous wrapper to close a page.
    
    Args:
        page: Page to close
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            loop.run_until_complete(close_page_async(page))
        else:
            asyncio.run(close_page_async(page))
    except RuntimeError:
        asyncio.run(close_page_async(page))
