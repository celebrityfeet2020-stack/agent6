"""Browser Automation Tool - Full Playwright automation with Browser Pool (v5.0)"""
from langchain_core.tools import BaseTool
from playwright.async_api import Page
import time
from typing import Optional
import logging
from app.core.browser_sync_wrapper import get_page_sync, close_page_sync

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
            
            # Get page from browser pool (v5.2 async optimization)
            if self.browser_pool:
                page = get_page_sync(self.browser_pool)
                logger.debug("Using browser pool (v5.2)")
            else:
                raise RuntimeError("Browser pool not initialized")
            
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
            
            # v5.8: 确保返回非空结果
            return result if result else "(Action completed, no output)"
            
        except Exception as e:
            logger.error(f"Browser automation error: {e}", exc_info=True)
            return f"Browser automation error: {str(e)}"
        
        finally:
            # Cleanup (v5.2)
            if page:
                try:
                    close_page_sync(page)
                except Exception as e:
                    logger.warning(f"Error closing page: {e}")
    
    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
