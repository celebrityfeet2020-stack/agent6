"""SSH Tool - Remote command execution"""
from langchain_core.tools import BaseTool
import paramiko

class SSHTool(BaseTool):
    name: str = "ssh_tool"
    description: str = """Execute commands on remote servers via SSH.
    Input format: host|username|password|command
    Example: 192.168.1.100|root|password|ls -la"""
    
    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split('|')
            host = parts[0].strip()
            username = parts[1].strip()
            password = parts[2].strip()
            command = parts[3].strip()
            
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, username=username, password=password, timeout=10)
            
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            client.close()
            
            # v5.8: 修复空响应问题
            if not output and not error:
                result = "(Command executed successfully, no output)"
            elif output and not error:
                result = f"=== Output ===\n{output}"
            elif error and not output:
                result = f"=== Error ===\n{error}"
            else:
                result = f"=== Output ===\n{output}\n=== Error ===\n{error}"
            
            return result
        except Exception as e:
            return f"SSH Error: {str(e)}"
    
    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
