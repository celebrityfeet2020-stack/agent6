"""
M3 Agent v5.7.1 - Synchronous Wrapper for Browser Pool
Simplified wrapper for thread-pool-based browser pool

v5.7.1: Much simpler now that browser pool uses thread pool
- No need for nest_asyncio
- No need for complex async/sync conversion
- Browser pool returns sync Page objects directly
"""

import asyncio
from playwright.sync_api import Page
from app.core.browser_pool import BrowserPool
import logging

logger = logging.getLogger(__name__)


async def get_page_async(browser_pool: BrowserPool) -> Page:
    """
    Async wrapper to get a page from browser pool.
    
    Args:
        browser_pool: The BrowserPool instance
        
    Returns:
        Page: A new browser page (sync API)
    """
    try:
        # Browser pool's get_page() is already async and returns sync Page
        page = await browser_pool.get_page()
        return page
    except Exception as e:
        logger.error(f"Failed to get page: {e}")
        raise


def get_page_sync(browser_pool: BrowserPool) -> Page:
    """
    Synchronous wrapper to get a page from browser pool.
    
    Args:
        browser_pool: The BrowserPool instance
        
    Returns:
        Page: A new browser page (sync API)
    
    Note:
        v5.7.1: This is now much simpler because browser pool uses thread pool.
        The returned Page is a sync API object, can be used directly in sync code.
    """
    try:
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run async get_page in the loop
        if loop.is_running():
            # If loop is already running, we're in an async context
            # This shouldn't happen in sync tools, but handle it anyway
            logger.warning("get_page_sync called from async context, use get_page_async instead")
            # Create a new loop in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(lambda: asyncio.run(browser_pool.get_page()))
                return future.result()
        else:
            # Normal case: run in current loop
            return loop.run_until_complete(browser_pool.get_page())
            
    except Exception as e:
        logger.error(f"Failed to get page (sync): {e}")
        raise


def close_page_sync(page: Page):
    """
    Synchronous wrapper to close a page.
    
    Args:
        page: Page to close (sync API)
    
    Note:
        v5.7.1: Page is now a sync API object, can be closed directly.
    """
    try:
        page.close()
        logger.debug("Page closed")
    except Exception as e:
        logger.warning(f"Error closing page: {e}")


async def close_page_async(page: Page):
    """
    Async wrapper to close a page.
    
    Args:
        page: Page to close (sync API)
    
    Note:
        v5.7.1: Page is a sync API object, but we run close in thread pool
        to avoid blocking the async event loop.
    """
    try:
        # Run sync close in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, page.close)
        logger.debug("Page closed (async)")
    except Exception as e:
        logger.warning(f"Error closing page: {e}")


__all__ = ['get_page_sync', 'get_page_async', 'close_page_sync', 'close_page_async']
