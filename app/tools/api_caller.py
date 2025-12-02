"""Universal API Tool - Call any REST API"""
from langchain_core.tools import BaseTool
import requests
import json

class UniversalAPITool(BaseTool):
    name: str = "universal_api"
    description: str = """Call any REST API endpoint.
    Input format: method|url|headers|body
    Methods: GET, POST, PUT, DELETE
    Example: POST|https://api.example.com/data|{"Authorization":"Bearer token"}|{"key":"value"}"""
    
    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split('|')
            method = parts[0].strip().upper()
            url = parts[1].strip()
            headers = json.loads(parts[2]) if len(parts) > 2 and parts[2].strip() else {}
            body = json.loads(parts[3]) if len(parts) > 3 and parts[3].strip() else None
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=body, timeout=30)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=body, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return f"Unsupported HTTP method: {method}"
            
            result = f"Status: {response.status_code}\n"
            result += f"Headers: {dict(response.headers)}\n"
            result += f"Body: {response.text[:1000]}"
            
            return result
            
        except Exception as e:
            return f"API Call Error: {str(e)}"
    
    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
