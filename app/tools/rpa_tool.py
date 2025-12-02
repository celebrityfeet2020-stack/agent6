"""
RPA Tool for M3 Agent
Supports cross-platform automation (Windows, macOS, Linux)
"""

import subprocess
import platform
import json
from typing import Dict, Any, Optional

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


class RPATool:
    """
    Cross-platform RPA tool for controlling physical devices
    """
    
    def __init__(self):
        self.platform = platform.system()  # 'Windows', 'Darwin' (macOS), 'Linux'
        
    def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information"""
        return {
            "name": "rpa_tool",
            "description": "Control physical device (mouse, keyboard, applications). Supports Windows, macOS, Linux.",
            "parameters": {
                "action": {
                    "type": "string",
                    "description": "Action to perform: move_mouse, click, double_click, right_click, type_text, press_key, screenshot, run_app, run_script",
                    "required": True
                },
                "x": {
                    "type": "integer",
                    "description": "X coordinate for mouse actions",
                    "required": False
                },
                "y": {
                    "type": "integer",
                    "description": "Y coordinate for mouse actions",
                    "required": False
                },
                "text": {
                    "type": "string",
                    "description": "Text to type or script to run",
                    "required": False
                },
                "key": {
                    "type": "string",
                    "description": "Key to press (e.g., 'enter', 'ctrl+c')",
                    "required": False
                },
                "app_path": {
                    "type": "string",
                    "description": "Path to application to run",
                    "required": False
                }
            }
        }
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Execute RPA action
        
        Args:
            action: Action to perform
            **kwargs: Additional parameters
            
        Returns:
            Result dictionary
        """
        if not PYAUTOGUI_AVAILABLE:
            return {
                "success": False,
                "error": "PyAutoGUI not installed. Please install it with: pip install pyautogui"
            }
        
        try:
            if action == "move_mouse":
                return self._move_mouse(kwargs.get("x"), kwargs.get("y"))
            elif action == "click":
                return self._click(kwargs.get("x"), kwargs.get("y"))
            elif action == "double_click":
                return self._double_click(kwargs.get("x"), kwargs.get("y"))
            elif action == "right_click":
                return self._right_click(kwargs.get("x"), kwargs.get("y"))
            elif action == "type_text":
                return self._type_text(kwargs.get("text"))
            elif action == "press_key":
                return self._press_key(kwargs.get("key"))
            elif action == "screenshot":
                return self._screenshot()
            elif action == "run_app":
                return self._run_app(kwargs.get("app_path"))
            elif action == "run_script":
                return self._run_script(kwargs.get("text"))
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _move_mouse(self, x: Optional[int], y: Optional[int]) -> Dict[str, Any]:
        """Move mouse to (x, y)"""
        if x is None or y is None:
            return {"success": False, "error": "x and y coordinates are required"}
        
        pyautogui.moveTo(x, y)
        return {
            "success": True,
            "message": f"Mouse moved to ({x}, {y})"
        }
    
    def _click(self, x: Optional[int], y: Optional[int]) -> Dict[str, Any]:
        """Click at (x, y)"""
        if x is not None and y is not None:
            pyautogui.click(x, y)
            return {"success": True, "message": f"Clicked at ({x}, {y})"}
        else:
            pyautogui.click()
            return {"success": True, "message": "Clicked at current position"}
    
    def _double_click(self, x: Optional[int], y: Optional[int]) -> Dict[str, Any]:
        """Double click at (x, y)"""
        if x is not None and y is not None:
            pyautogui.doubleClick(x, y)
            return {"success": True, "message": f"Double clicked at ({x}, {y})"}
        else:
            pyautogui.doubleClick()
            return {"success": True, "message": "Double clicked at current position"}
    
    def _right_click(self, x: Optional[int], y: Optional[int]) -> Dict[str, Any]:
        """Right click at (x, y)"""
        if x is not None and y is not None:
            pyautogui.rightClick(x, y)
            return {"success": True, "message": f"Right clicked at ({x}, {y})"}
        else:
            pyautogui.rightClick()
            return {"success": True, "message": "Right clicked at current position"}
    
    def _type_text(self, text: Optional[str]) -> Dict[str, Any]:
        """Type text"""
        if not text:
            return {"success": False, "error": "text parameter is required"}
        
        pyautogui.write(text)
        return {
            "success": True,
            "message": f"Typed: {text[:50]}..." if len(text) > 50 else f"Typed: {text}"
        }
    
    def _press_key(self, key: Optional[str]) -> Dict[str, Any]:
        """Press key or key combination"""
        if not key:
            return {"success": False, "error": "key parameter is required"}
        
        # Handle key combinations (e.g., 'ctrl+c')
        if '+' in key:
            keys = key.split('+')
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(key)
        
        return {
            "success": True,
            "message": f"Pressed key: {key}"
        }
    
    def _screenshot(self) -> Dict[str, Any]:
        """Take screenshot"""
        screenshot_path = "/tmp/rpa_screenshot.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)
        
        return {
            "success": True,
            "message": f"Screenshot saved to {screenshot_path}",
            "screenshot_path": screenshot_path
        }
    
    def _run_app(self, app_path: Optional[str]) -> Dict[str, Any]:
        """Run application"""
        if not app_path:
            return {"success": False, "error": "app_path parameter is required"}
        
        try:
            if self.platform == "Darwin":  # macOS
                subprocess.Popen(["open", app_path])
            elif self.platform == "Windows":
                subprocess.Popen([app_path])
            else:  # Linux
                subprocess.Popen([app_path])
            
            return {
                "success": True,
                "message": f"Launched application: {app_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to launch application: {str(e)}"
            }
    
    def _run_script(self, script: Optional[str]) -> Dict[str, Any]:
        """Run platform-specific script"""
        if not script:
            return {"success": False, "error": "script parameter is required"}
        
        try:
            if self.platform == "Darwin":  # macOS - AppleScript
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else None
                }
            elif self.platform == "Windows":  # PowerShell
                result = subprocess.run(
                    ["powershell", "-Command", script],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else None
                }
            else:  # Linux - Bash
                result = subprocess.run(
                    ["bash", "-c", script],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else None
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Script execution timed out (30s limit)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to run script: {str(e)}"
            }


# Tool instance
rpa_tool = RPATool()


def get_tool_info():
    """Get tool information for LangGraph"""
    return rpa_tool.get_tool_info()


def execute(**kwargs):
    """Execute RPA action"""
    action = kwargs.get("action")
    if not action:
        return {
            "success": False,
            "error": "action parameter is required"
        }
    
    return rpa_tool.execute(action, **kwargs)
