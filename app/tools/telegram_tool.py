"""Telegram Tool - Bot API + Client API + Browser"""
from langchain_core.tools import BaseTool
from telethon import TelegramClient
from telegram import Bot
from playwright.sync_api import sync_playwright
import asyncio

class TelegramTool(BaseTool):
    name: str = "telegram_tool"
    description: str = """Interact with Telegram via Bot API, Client API, or Browser.
    Input format: method|params
    Methods: bot_send, client_send, browser_send
    Example: bot_send|chat_id:123456|message:Hello"""
    
    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split('|', 1)
            method = parts[0].strip()
            params_str = parts[1].strip() if len(parts) > 1 else ""
            
            # Parse params
            params = {}
            for param in params_str.split('|'):
                if ':' in param:
                    key, value = param.split(':', 1)
                    params[key.strip()] = value.strip()
            
            if method == "bot_send":
                # Bot API method
                bot_token = params.get('token', '')
                chat_id = params.get('chat_id', '')
                message = params.get('message', '')
                
                bot = Bot(token=bot_token)
                asyncio.run(bot.send_message(chat_id=chat_id, text=message))
                return f"Message sent via Bot API to {chat_id}"
            
            elif method == "client_send":
                # Client API method (Telethon)
                api_id = params.get('api_id', '')
                api_hash = params.get('api_hash', '')
                phone = params.get('phone', '')
                recipient = params.get('recipient', '')
                message = params.get('message', '')
                
                client = TelegramClient('session', api_id, api_hash)
                
                async def send():
                    await client.start(phone=phone)
                    await client.send_message(recipient, message)
                    await client.disconnect()
                
                asyncio.run(send())
                return f"Message sent via Client API to {recipient}"
            
            elif method == "browser_send":
                # Browser automation method
                message = params.get('message', '')
                recipient = params.get('recipient', '')
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=False)
                    page = browser.new_page()
                    page.goto('https://web.telegram.org/')
                    page.wait_for_load_state('networkidle')
                    
                    # Search for recipient
                    page.fill('[placeholder="Search"]', recipient)
                    page.click(f'text={recipient}')
                    
                    # Send message
                    page.fill('[contenteditable="true"]', message)
                    page.press('[contenteditable="true"]', 'Enter')
                    
                    browser.close()
                    return f"Message sent via Browser to {recipient}"
            
            else:
                return f"Unknown method: {method}"
                
        except Exception as e:
            return f"Telegram Error: {str(e)}"
    
    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
