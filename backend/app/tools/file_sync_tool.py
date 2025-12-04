"""
File Sync Tool for M3 Agent
Synchronize files between container and host machine
"""

import os
import shutil
import json
from typing import Dict, Any, Optional
from pathlib import Path
from langchain_core.tools import BaseTool
from pydantic import Field


class FileSyncTool(BaseTool):
    """
    File synchronization tool for container-host communication
    """
    
    name: str = "file_sync_tool"
    description: str = """Synchronize files between container and host machine (Desktop, Downloads, Documents).
    Input should be a JSON string with 'action' and parameters.
    Actions: copy_to_host, copy_from_host, list_host_files
    Example: {"action": "copy_to_host", "source_path": "/tmp/file.txt", "host_location": "desktop"}"""
    
    host_desktop: str = Field(default_factory=lambda: os.getenv("HOST_DESKTOP_PATH", "/host_desktop"))
    host_downloads: str = Field(default_factory=lambda: os.getenv("HOST_DOWNLOADS_PATH", "/host_downloads"))
    host_documents: str = Field(default_factory=lambda: os.getenv("HOST_DOCUMENTS_PATH", "/host_documents"))
    
    def _run(self, query: str) -> str:
        """
        Execute file sync action
        
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
            
            # Execute action
            if action == "copy_to_host":
                result = self._copy_to_host(
                    params.get("source_path"),
                    params.get("dest_path"),
                    params.get("host_location", "desktop")
                )
            elif action == "copy_from_host":
                result = self._copy_from_host(
                    params.get("source_path"),
                    params.get("dest_path"),
                    params.get("host_location", "desktop")
                )
            elif action == "list_host_files":
                result = self._list_host_files(params.get("host_location", "desktop"))
            else:
                result = {"success": False, "error": f"Unknown action: {action}"}
            
            return json.dumps(result)
            
        except json.JSONDecodeError as e:
            return json.dumps({"success": False, "error": f"Invalid JSON input: {str(e)}"})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    def _get_host_path(self, location: str) -> str:
        """Get host mount path by location"""
        location_map = {
            "desktop": self.host_desktop,
            "downloads": self.host_downloads,
            "documents": self.host_documents
        }
        return location_map.get(location.lower(), self.host_desktop)
    
    def _copy_to_host(self, source_path: Optional[str], dest_path: Optional[str], host_location: str) -> Dict[str, Any]:
        """Copy file from container to host"""
        if not source_path:
            return {"success": False, "error": "source_path is required"}
        
        if not os.path.exists(source_path):
            return {"success": False, "error": f"Source file not found: {source_path}"}
        
        host_base = self._get_host_path(host_location)
        
        if not os.path.exists(host_base):
            return {
                "success": False,
                "error": f"Host location not mounted: {host_location}. Please configure Docker volume."
            }
        
        # Determine destination path
        if dest_path:
            dest_full_path = os.path.join(host_base, dest_path)
        else:
            dest_full_path = os.path.join(host_base, os.path.basename(source_path))
        
        # Create destination directory if needed
        os.makedirs(os.path.dirname(dest_full_path), exist_ok=True)
        
        # Copy file
        shutil.copy2(source_path, dest_full_path)
        
        return {
            "success": True,
            "message": f"File copied to host {host_location}",
            "source": source_path,
            "destination": dest_full_path
        }
    
    def _copy_from_host(self, source_path: Optional[str], dest_path: Optional[str], host_location: str) -> Dict[str, Any]:
        """Copy file from host to container"""
        if not source_path:
            return {"success": False, "error": "source_path is required"}
        
        host_base = self._get_host_path(host_location)
        
        if not os.path.exists(host_base):
            return {
                "success": False,
                "error": f"Host location not mounted: {host_location}. Please configure Docker volume."
            }
        
        source_full_path = os.path.join(host_base, source_path)
        
        if not os.path.exists(source_full_path):
            return {"success": False, "error": f"Source file not found on host: {source_full_path}"}
        
        # Determine destination path
        if dest_path:
            dest_full_path = dest_path
        else:
            dest_full_path = os.path.join("/tmp", os.path.basename(source_path))
        
        # Create destination directory if needed
        os.makedirs(os.path.dirname(dest_full_path), exist_ok=True)
        
        # Copy file
        shutil.copy2(source_full_path, dest_full_path)
        
        return {
            "success": True,
            "message": f"File copied from host {host_location}",
            "source": source_full_path,
            "destination": dest_full_path
        }
    
    def _list_host_files(self, host_location: str) -> Dict[str, Any]:
        """List files on host"""
        host_base = self._get_host_path(host_location)
        
        if not os.path.exists(host_base):
            return {
                "success": False,
                "error": f"Host location not mounted: {host_location}. Please configure Docker volume."
            }
        
        files = []
        for item in os.listdir(host_base):
            item_path = os.path.join(host_base, item)
            files.append({
                "name": item,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
            })
        
        return {
            "success": True,
            "location": host_location,
            "files": files,
            "total_count": len(files)
        }
