"""Git Tool - Version control operations"""
from langchain_core.tools import BaseTool
import git
import os

class GitTool(BaseTool):
    name: str = "git_tool"
    description: str = """Perform Git operations.
    Input format: operation|repo_path|args
    Operations: clone, status, commit, push, pull
    Example: status|/tmp/repo or clone|/tmp/repo|https://github.com/user/repo.git"""
    
    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split('|')
            operation = parts[0].strip()
            repo_path = parts[1].strip()
            args = parts[2].strip() if len(parts) > 2 else None
            
            if operation == "clone":
                git.Repo.clone_from(args, repo_path)
                return f"Repository cloned to {repo_path}"
            
            repo = git.Repo(repo_path)
            
            if operation == "status":
                return str(repo.git.status())
            elif operation == "commit":
                repo.git.add(A=True)
                repo.index.commit(args or "Auto commit")
                return "Changes committed"
            elif operation == "push":
                origin = repo.remote(name='origin')
                origin.push()
                return "Changes pushed"
            elif operation == "pull":
                origin = repo.remote(name='origin')
                origin.pull()
                return "Changes pulled"
            else:
                return f"Unknown operation: {operation}"
        except Exception as e:
            return f"Git Error: {str(e)}"
    
    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
