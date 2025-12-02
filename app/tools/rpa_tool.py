"""
RPA Tool for M3 Agent
Supports cross-platform automation (Windows, macOS, Linux)
"""

import subprocess
import platform
import json
from typing import Dict, Any, Optional
from langchain_core.tools import BaseTool
from pydantic import Field

# Lazy import pyautogui to avoid DISPLAY issues in Docker
# Will be imported only when actually needed
PYAUTOGUI_AVAILABLE = None  # Will be checked on first use


def _check_pyautogui():
    """Lazy import and check pyautogui availability"""
    global PYAUTOGUI_AVAILABLE
    if PYAUTOGUI_AVAILABLE is None:
        try:
            import pyautogui as _pg
            globals()['pyautogui'] = _pg
            PYAUTOGUI_AVAILABLE = True
        except (ImportError, KeyError) as e:
            PYAUTOGUI_AVAILABLE = False
    return PYAUTOGUI_AVAILABLE


class RPATool(BaseTool):
    """
    Cross-platform RPA tool for controlling physical devices
    """
    
    name: str = "rpa_tool"
    description: str = """Control physical device (mouse, keyboard, applications). 
    Input should be a JSON string with 'action' and optional parameters.
    Actions: move_mouse, click, double_click, right_click, type_text, press_key, screenshot, run_app, run_script
    Example: {"action": "click", "x": 100, "y": 200}"""
    
    platform_name: str = Field(default_factory=lambda: platform.system())
    
    def _run(self, query: str) -> str:
        """
        Execute RPA action
        
        Args:
            query: JSON string with action and parameters
            
        Returns:
            Result string
        """
        try:
            # Parse input
            params = json.loads(query) if isinstance(query, str) else query
            action = params.get("action")
            
            if not action:
                return json.dumps({"success": False, "error": "Missing 'action' parameter"})
            
            if not _check_pyautogui():
                return json.dumps({
                    "success": False,
                    "error": "PyAutoGUI not available. This may be because DISPLAY is not set (Docker environment) or pyautogui is not installed."
                })
            
            # Execute action
            if action == "move_mouse":
                result = self._move_mouse(params.get("x"), params.get("y"))
            elif action == "click":
                result = self._click(params.get("x"), params.get("y"))
            elif action == "double_click":
                result = self._double_click(params.get("x"), params.get("y"))
            elif action == "right_click":
                result = self._right_click(params.get("x"), params.get("y"))
            elif action == "type_text":
                result = self._type_text(params.get("text"))
            elif action == "press_key":
                result = self._press_key(params.get("key"))
            elif action == "screenshot":
                result = self._screenshot()
            elif action == "run_app":
                result = self._run_app(params.get("app_path"))
            elif action == "run_script":
                result = self._run_script(params.get("text"))
            else:
                result = {"success": False, "error": f"Unknown action: {action}"}
            
            return json.dumps(result)
            
        except json.JSONDecodeError as e:
            return json.dumps({"success": False, "error": f"Invalid JSON input: {str(e)}"})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
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
        
        pyautogui.typewrite(text, interval=0.05)
        return {
            "success": True,
            "message": f"Typed text: {text[:50]}..."
        }
    
    def _press_key(self, key: Optional[str]) -> Dict[str, Any]:
        """Press key"""
        if not key:
            return {"success": False, "error": "key parameter is required"}
        
        pyautogui.press(key)
        return {
            "success": True,
            "message": f"Pressed key: {key}"
        }
    
    def _screenshot(self) -> Dict[str, Any]:
        """Take screenshot"""
        import tempfile
        import os
        
        # Save to temp file
        temp_file = os.path.join(tempfile.gettempdir(), "rpa_screenshot.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(temp_file)
        
        return {
            "success": True,
            "message": f"Screenshot saved to {temp_file}",
            "file_path": temp_file
        }
    
    def _run_app(self, app_path: Optional[str]) -> Dict[str, Any]:
        """Run application"""
        if not app_path:
            return {"success": False, "error": "app_path parameter is required"}
        
        try:
            if self.platform_name == "Windows":
                subprocess.Popen(app_path, shell=True)
            else:  # macOS, Linux
                subprocess.Popen(["open" if self.platform_name == "Darwin" else "xdg-open", app_path])
            
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
        """Run script via SSH"""
        if not script:
            return {"success": False, "error": "script parameter is required"}
        
        try:
            # Get RPA_HOST_STRING from environment
            import os
            host_string = os.getenv("RPA_HOST_STRING")
            
            if not host_string:
                return {
                    "success": False,
                    "error": "RPA_HOST_STRING environment variable not set"
                }
            
            # Execute via SSH
            result = subprocess.run(
                ["ssh", host_string, script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Script execution timed out (30s)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to execute script: {str(e)}"
            }
