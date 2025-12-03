"""Web Scraper Tool - Playwright-based web scraping with Browser Pool (v5.0)"""
from langchain_core.tools import BaseTool
from playwright.sync_api import Page
from typing import Optional
import logging

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
            # Get page from browser pool (v5.0 optimization)
            if self.browser_pool:
                page = self.browser_pool.get_page()
                logger.debug("Using browser pool (v5.0)")
            else:
                # Fallback to old method if pool not available
                from playwright.sync_api import sync_playwright
                logger.warning("Browser pool not available, using fallback method")
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context()
                    page = context.new_page()
            
            # Scrape page
            page.goto(url, timeout=30000)
            page.wait_for_load_state('networkidle', timeout=10000)
            text = page.evaluate('() => document.body.innerText')
            
            return f"Content from {url}:\n\n{text[:5000]}"
            
        except Exception as e:
            return f"Error scraping {url}: {str(e)}"
        
        finally:
            # Clean up page (v5.0: close context but keep browser running)
            if page and self.browser_pool:
                try:
                    self.browser_pool.close_context(page)
                except Exception as e:
                    logger.warning(f"Error closing page context: {e}")
    
    async def _arun(self, url: str) -> str:
        return self._run(url)
