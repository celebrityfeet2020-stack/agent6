"""
Browser Sync Wrapper - Bridge between sync tools and async browser pool
A6 System v6.2.2 - Critical fix for missing module
"""
import asyncio
from playwright.async_api import Page
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_page_sync(browser_pool) -> Page:
    """
    Synchronous wrapper to get a page from async browser pool.
    Used by tools that run in sync context but need async browser operations.
    
    Args:
        browser_pool: The BrowserPool instance
        
    Returns:
        Page: A Playwright page instance
    """
    try:
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run async get_page in sync context
        page = loop.run_until_complete(browser_pool.get_page())
        logger.debug("Got page from browser pool (sync wrapper)")
        return page
    except Exception as e:
        logger.error(f"Error getting page from browser pool: {e}")
        raise


def close_page_sync(page: Optional[Page]) -> None:
    """
    Synchronous wrapper to close a page.
    
    Args:
        page: The Playwright page to close
    """
    if page:
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run async close in sync context
            loop.run_until_complete(page.close())
            logger.debug("Closed page (sync wrapper)")
        except Exception as e:
            logger.error(f"Error closing page: {e}")
