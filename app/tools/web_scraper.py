"""Web Scraper Tool - Playwright-based web scraping"""
from langchain_core.tools import BaseTool
from playwright.sync_api import sync_playwright
import time

class WebScraperTool(BaseTool):
    name: str = "web_scraper"
    description: str = """Scrape content from a web page.
    Input should be a URL.
    Returns the text content of the page."""
    
    def _run(self, url: str) -> str:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=30000)
                page.wait_for_load_state('networkidle', timeout=10000)
                content = page.content()
                text = page.evaluate('() => document.body.innerText')
                browser.close()
                return f"Content from {url}:\n\n{text[:5000]}"
        except Exception as e:
            return f"Error scraping {url}: {str(e)}"
    
    async def _arun(self, url: str) -> str:
        return self._run(url)
