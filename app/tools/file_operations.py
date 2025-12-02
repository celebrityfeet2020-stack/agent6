"""File Operations Tool"""
from langchain_core.tools import BaseTool
import os
from pathlib import Path

class FileOperationsTool(BaseTool):
    name: str = "file_operations"
    description: str = """Perform file operations (read, write, list).
    Input format: operation|path|content (content only for write)
    Operations: read, write, list, delete
    Example: read|/tmp/file.txt or write|/tmp/file.txt|Hello World"""
    
    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split('|')
            operation = parts[0].strip()
            path = parts[1].strip() if len(parts) > 1 else None
            content = parts[2] if len(parts) > 2 else None
            
            if operation == "read":
                with open(path, 'r') as f:
                    return f.read()
            elif operation == "write":
                with open(path, 'w') as f:
                    f.write(content)
                return f"File written to {path}"
            elif operation == "list":
                files = os.listdir(path)
                return "\n".join(files)
            elif operation == "delete":
                os.remove(path)
                return f"File deleted: {path}"
            else:
                return f"Unknown operation: {operation}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
