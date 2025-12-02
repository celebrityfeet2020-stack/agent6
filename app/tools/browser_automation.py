"""Browser Automation Tool - Full Playwright automation"""
from langchain_core.tools import BaseTool
from playwright.sync_api import sync_playwright
import time

class BrowserAutomationTool(BaseTool):
    name: str = "browser_automation"
    description: str = """Automate browser actions like clicking, filling forms, posting tweets.
    Input format: action|url|params
    Actions: click, fill, submit, screenshot, tweet
    Example: tweet|https://twitter.com|Hello World"""
    
    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split('|', 2)
            action = parts[0].strip()
            url = parts[1].strip()
            params = parts[2].strip() if len(parts) > 2 else ""
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)  # Docker容器中必须使用headless模式
                context = browser.new_context()
                page = context.new_page()
                page.goto(url, timeout=30000)
                page.wait_for_load_state('networkidle')
                
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
                    result = f"Tweet posted: {params}"
                
                else:
                    result = f"Unknown action: {action}"
                
                browser.close()
                return result
                
        except Exception as e:
            return f"Browser Automation Error: {str(e)}"
    
    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
