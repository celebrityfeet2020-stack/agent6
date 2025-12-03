"""Browser Automation Tool - Full Playwright automation with Browser Pool (v5.0)"""
from langchain_core.tools import BaseTool
from playwright.sync_api import Page
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BrowserAutomationTool(BaseTool):
    name: str = "browser_automation"
    description: str = """Automate browser actions like clicking, filling forms, posting tweets.
    Input format: action|url|params
    Actions: click, fill, submit, screenshot, tweet
    Example: tweet|https://twitter.com|Hello World"""
    
    browser_pool: Optional[object] = None  # Will be injected from main.py
    
    def _run(self, input_str: str) -> str:
        page: Optional[Page] = None
        try:
            parts = input_str.split('|', 2)
            action = parts[0].strip()
            url = parts[1].strip()
            params = parts[2].strip() if len(parts) > 2 else ""
            
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
            
            # Navigate to URL
            page.goto(url, timeout=30000)
            page.wait_for_load_state('networkidle')
            
            # Execute action
            if action == "click":
                page.click(params)
                result = f"Clicked element: {params}"
            
            elif action == "fill":
                selector, text = params.split(':', 1)
                page.fill(selector, text)
                result = f"Filled {selector} with text"
            
            elif action == "submit":
                page.click(params)
                page.wait_for_load_state('networkidle')
                result = "Form submitted"
            
            elif action == "screenshot":
                page.screenshot(path=params or '/tmp/screenshot.png')
                result = f"Screenshot saved to {params or '/tmp/screenshot.png'}"
            
            elif action == "tweet":
                # Twitter posting automation
                # Note: Requires login session
                page.fill('[data-testid="tweetTextarea_0"]', params)
                page.click('[data-testid="tweetButtonInline"]')
                time.sleep(2)
                result = "Tweet posted successfully"
            
            else:
                result = f"Unknown action: {action}"
            
            return result
            
        except Exception as e:
            return f"Browser automation error: {str(e)}"
        
        finally:
            # Clean up page (v5.0: close context but keep browser running)
            if page and self.browser_pool:
                try:
                    self.browser_pool.close_context(page)
                except Exception as e:
                    logger.warning(f"Error closing page context: {e}")
    
    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
