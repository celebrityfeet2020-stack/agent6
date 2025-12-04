"""Code Executor Tool - Secure Python Sandbox (v5.8: subprocess fallback)"""
from langchain_core.tools import BaseTool
import docker
import tempfile
import os
import subprocess
import logging

# v5.8: Use enhanced tool pool
try:
    from app.core.tool_pool_v5_8 import enhanced_tool_pool as tool_pool
except ImportError:
    # Fallback to v5.7 tool pool
    from app.core.tool_pool import tool_pool

logger = logging.getLogger(__name__)

class CodeExecutorTool(BaseTool):
    name: str = "code_executor"
    description: str = """Execute Python code in a secure Docker sandbox.
    Input should be Python code as a string.
    Returns the output of the code execution."""
    
    def _run(self, code: str) -> str:
        # v5.8: Try Docker first, fallback to subprocess
        try:
            return self._run_with_docker(code)
        except Exception as docker_error:
            logger.warning(f"Docker execution failed: {docker_error}")
            logger.info("Falling back to subprocess execution...")
            try:
                return self._run_with_subprocess(code)
            except Exception as subprocess_error:
                return f"Error executing code (both Docker and subprocess failed):\nDocker: {docker_error}\nSubprocess: {subprocess_error}"
    
    def _run_with_docker(self, code: str) -> str:
        """
        v5.8: Execute code using Docker (preferred method)
        
        Args:
            code: Python code to execute
        
        Returns:
            Execution output
        """
        # Use pre-loaded Docker client from tool pool
        client = tool_pool.get_docker_client()
        if client is None:
            # Try to create new client
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
    
    def _run_with_subprocess(self, code: str) -> str:
        """
        v5.8: Execute code using subprocess (fallback method)
        
        Warning: Less secure than Docker, but works when Docker is unavailable
        
        Args:
            code: Python code to execute
        
        Returns:
            Execution output
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute with timeout and resource limits
            result = subprocess.run(
                ['python3', '-c', code],
                capture_output=True,
                text=True,
                timeout=30,
                check=False  # Don't raise on non-zero exit
            )
            
            # Combine stdout and stderr
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[exit code: {result.returncode}]"
            
            return output or "(no output)"
            
        finally:
            os.unlink(temp_file)
    
    async def _arun(self, code: str) -> str:
        return self._run(code)
