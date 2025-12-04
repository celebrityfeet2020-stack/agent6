"""Code Executor Tool - Execute code in Docker sandbox"""
from langchain_core.tools import BaseTool
import docker
import tempfile
import os

class CodeExecutorTool(BaseTool):
    name: str = "code_executor"
    description: str = """Execute Python code in a secure Docker sandbox.
    Input should be Python code as a string.
    Returns the output of the code execution."""
    
    def _run(self, code: str) -> str:
        try:
            client = docker.from_env()
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                result = client.containers.run(
                    "python:3.11-slim",
                    f"python -c '{code}'",
                    remove=True,
                    mem_limit="512m",
                    network_disabled=False,
                    timeout=30
                )
                return result.decode('utf-8')
            finally:
                os.unlink(temp_file)
        except Exception as e:
            return f"Error executing code: {str(e)}"
    
    async def _arun(self, code: str) -> str:
        return self._run(code)
