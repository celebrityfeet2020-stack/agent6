"""
RPA Tool for M3 Agent
Supports cross-platform automation (Windows, macOS, Linux)
Executes commands on host machine via SSH
"""

import subprocess
import platform
import json
import os
import tempfile
from typing import Dict, Any, Optional
from langchain_core.tools import BaseTool
from pydantic import Field


class RPATool(BaseTool):
    """
    Cross-platform RPA tool for controlling physical devices via SSH
    """
    
    name: str = "rpa_tool"
    description: str = """Control physical device (mouse, keyboard, applications) on host machine via SSH. 
    Input should be a JSON string with 'action' and optional parameters.
    Actions: move_mouse, click, double_click, right_click, type_text, press_key, screenshot, run_app, run_script
    Example: {"action": "click", "x": 100, "y": 200}"""
    
    platform_name: str = Field(default_factory=lambda: platform.system())
    
    def _run(self, query: str) -> str:
        """
        Execute RPA action on host machine via SSH
        
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
            
            # Get RPA_HOST_STRING from environment
            host_string = os.getenv("RPA_HOST_STRING")
            
            if not host_string:
                return json.dumps({
                    "success": False,
                    "error": "RPA_HOST_STRING environment variable not set. Please set it to 'user@host' format."
                })
            
            # Execute action
            if action == "move_mouse":
                result = self._move_mouse_remote(host_string, params.get("x"), params.get("y"))
            elif action == "click":
                result = self._click_remote(host_string, params.get("x"), params.get("y"))
            elif action == "double_click":
                result = self._double_click_remote(host_string, params.get("x"), params.get("y"))
            elif action == "right_click":
                result = self._right_click_remote(host_string, params.get("x"), params.get("y"))
            elif action == "type_text":
                result = self._type_text_remote(host_string, params.get("text"))
            elif action == "press_key":
                result = self._press_key_remote(host_string, params.get("key"))
            elif action == "screenshot":
                result = self._screenshot_remote(host_string)
            elif action == "run_app":
                result = self._run_app_remote(host_string, params.get("app_path"))
            elif action == "run_script":
                result = self._run_script_remote(host_string, params.get("script"))
            else:
                result = {"success": False, "error": f"Unknown action: {action}"}
            
            return json.dumps(result)
            
        except json.JSONDecodeError as e:
            return json.dumps({"success": False, "error": f"Invalid JSON input: {str(e)}"})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    def _execute_remote_python(self, host_string: str, python_code: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute Python code on remote host via SSH"""
        try:
            # Escape quotes in Python code
            escaped_code = python_code.replace('"', '\\"').replace("'", "\\'")
            
            # Execute via SSH
            result = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", host_string, f'python3 -c "{escaped_code}"'],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout.strip()
                }
            else:
                return {
                    "success": False,
                    "error": f"Remote execution failed: {result.stderr}"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Remote execution timed out ({timeout}s)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"SSH connection failed: {str(e)}"
            }
    
    def _move_mouse_remote(self, host_string: str, x: Optional[int], y: Optional[int]) -> Dict[str, Any]:
        """Move mouse to (x, y) on remote host"""
        if x is None or y is None:
            return {"success": False, "error": "x and y coordinates are required"}
        
        python_code = f"import pyautogui; pyautogui.moveTo({x}, {y}); print('Mouse moved to ({x}, {y})')"
        result = self._execute_remote_python(host_string, python_code)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Mouse moved to ({x}, {y})"
            }
        return result
    
    def _click_remote(self, host_string: str, x: Optional[int], y: Optional[int]) -> Dict[str, Any]:
        """Click at (x, y) on remote host"""
        if x is not None and y is not None:
            python_code = f"import pyautogui; pyautogui.click({x}, {y}); print('Clicked at ({x}, {y})')"
            message = f"Clicked at ({x}, {y})"
        else:
            python_code = "import pyautogui; pyautogui.click(); print('Clicked at current position')"
            message = "Clicked at current position"
        
        result = self._execute_remote_python(host_string, python_code)
        
        if result["success"]:
            return {
                "success": True,
                "message": message
            }
        return result
    
    def _double_click_remote(self, host_string: str, x: Optional[int], y: Optional[int]) -> Dict[str, Any]:
        """Double click at (x, y) on remote host"""
        if x is not None and y is not None:
            python_code = f"import pyautogui; pyautogui.doubleClick({x}, {y}); print('Double clicked at ({x}, {y})')"
            message = f"Double clicked at ({x}, {y})"
        else:
            python_code = "import pyautogui; pyautogui.doubleClick(); print('Double clicked at current position')"
            message = "Double clicked at current position"
        
        result = self._execute_remote_python(host_string, python_code)
        
        if result["success"]:
            return {
                "success": True,
                "message": message
            }
        return result
    
    def _right_click_remote(self, host_string: str, x: Optional[int], y: Optional[int]) -> Dict[str, Any]:
        """Right click at (x, y) on remote host"""
        if x is not None and y is not None:
            python_code = f"import pyautogui; pyautogui.rightClick({x}, {y}); print('Right clicked at ({x}, {y})')"
            message = f"Right clicked at ({x}, {y})"
        else:
            python_code = "import pyautogui; pyautogui.rightClick(); print('Right clicked at current position')"
            message = "Right clicked at current position"
        
        result = self._execute_remote_python(host_string, python_code)
        
        if result["success"]:
            return {
                "success": True,
                "message": message
            }
        return result
    
    def _type_text_remote(self, host_string: str, text: Optional[str]) -> Dict[str, Any]:
        """Type text on remote host"""
        if not text:
            return {"success": False, "error": "text parameter is required"}
        
        # Escape special characters
        escaped_text = text.replace("\\", "\\\\").replace("'", "\\'")
        python_code = f"import pyautogui; pyautogui.typewrite('{escaped_text}', interval=0.05); print('Typed text')"
        result = self._execute_remote_python(host_string, python_code)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Typed text: {text[:50]}..."
            }
        return result
    
    def _press_key_remote(self, host_string: str, key: Optional[str]) -> Dict[str, Any]:
        """Press key on remote host"""
        if not key:
            return {"success": False, "error": "key parameter is required"}
        
        python_code = f"import pyautogui; pyautogui.press('{key}'); print('Pressed key: {key}')"
        result = self._execute_remote_python(host_string, python_code)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Pressed key: {key}"
            }
        return result
    
    def _screenshot_remote(self, host_string: str) -> Dict[str, Any]:
        """Take screenshot on remote host and transfer to container"""
        try:
            # Generate remote temp file path
            remote_temp = f"/tmp/rpa_screenshot_{os.getpid()}.png"
            
            # Take screenshot on remote host
            python_code = f"import pyautogui; screenshot = pyautogui.screenshot(); screenshot.save('{remote_temp}'); print('{remote_temp}')"
            result = self._execute_remote_python(host_string, python_code, timeout=60)
            
            if not result["success"]:
                return result
            
            # Transfer file to container via scp
            local_temp = os.path.join(tempfile.gettempdir(), f"rpa_screenshot_{os.getpid()}.png")
            scp_result = subprocess.run(
                ["scp", "-o", "StrictHostKeyChecking=no", f"{host_string}:{remote_temp}", local_temp],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if scp_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to transfer screenshot: {scp_result.stderr}"
                }
            
            # Clean up remote file
            subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", host_string, f"rm -f {remote_temp}"],
                capture_output=True,
                timeout=10
            )
            
            return {
                "success": True,
                "message": f"Screenshot saved to {local_temp}",
                "file_path": local_temp
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Screenshot failed: {str(e)}"
            }
    
    def _run_app_remote(self, host_string: str, app_path: Optional[str]) -> Dict[str, Any]:
        """Run application on remote host"""
        if not app_path:
            return {"success": False, "error": "app_path parameter is required"}
        
        try:
            # Detect platform and use appropriate command
            # For macOS: open
            # For Linux: xdg-open
            # For Windows: start
            python_code = f"""
import subprocess
import platform
app_path = '{app_path}'
system = platform.system()
if system == 'Darwin':
    subprocess.Popen(['open', app_path])
elif system == 'Linux':
    subprocess.Popen(['xdg-open', app_path])
elif system == 'Windows':
    subprocess.Popen(['start', app_path], shell=True)
print(f'Launched application: {{app_path}}')
"""
            result = self._execute_remote_python(host_string, python_code)
            
            if result["success"]:
                return {
                    "success": True,
                    "message": f"Launched application: {app_path}"
                }
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to launch application: {str(e)}"
            }
    
    def _run_script_remote(self, host_string: str, script: Optional[str]) -> Dict[str, Any]:
        """Run shell script on remote host"""
        if not script:
            return {"success": False, "error": "script parameter is required"}
        
        try:
            # Execute via SSH
            result = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", host_string, script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "message": "Script executed successfully" if result.returncode == 0 else "Script execution failed"
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
