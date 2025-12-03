"""Web Scraper Tool - Playwright-based web scraping with Browser Pool (v5.0)"""
from langchain_core.tools import BaseTool
from playwright.async_api import Page
from typing import Optional
import logging
from app.core.browser_sync_wrapper import get_page_sync, close_page_sync

logger = logging.getLogger(__name__)


class WebScraperTool(BaseTool):
    name: str = "web_scraper"
    description: str = """Scrape content from a web page.
    Input should be a URL.
    Returns the text content of the page."""
    
    browser_pool: Optional[object] = None  # Will be injected from main.py
    
    def _run(self, url: str) -> str:
        page: Optional[Page] = None
        try:
            # Get page from browser pool (v5.2 async optimization)
            if self.browser_pool:
                page = get_page_sync(self.browser_pool)
                logger.debug("Using browser pool (v5.2)")
            else:
                raise RuntimeError("Browser pool not initialized")
            
            # Scrape page
            page.goto(url, timeout=30000)
            page.wait_for_load_state('networkidle', timeout=10000)
            text = page.evaluate('() => document.body.innerText')
            
            return f"Content from {url}:\n\n{text[:5000]}"
            
        except Exception as e:
            return f"Error scraping {url}: {str(e)}"
        
        finally:
            # Cleanup (v5.2)
            if page:
                try:
                    close_page_sync(page)
                except Exception as e:
                    logger.warning(f"Error closing page: {e}")
    
    async def _arun(self, url: str) -> str:
        return self._run(url)
