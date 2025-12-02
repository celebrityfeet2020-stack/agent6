"""
File Sync Tool for M3 Agent
Synchronize files between container and host machine
"""

import os
import shutil
from typing import Dict, Any, Optional
from pathlib import Path


class FileSyncTool:
    """
    File synchronization tool for container-host communication
    """
    
    def __init__(self):
        # Default host mount points (configured via Docker volumes)
        self.host_desktop = os.getenv("HOST_DESKTOP_PATH", "/host_desktop")
        self.host_downloads = os.getenv("HOST_DOWNLOADS_PATH", "/host_downloads")
        self.host_documents = os.getenv("HOST_DOCUMENTS_PATH", "/host_documents")
        
    def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information"""
        return {
            "name": "file_sync_tool",
            "description": "Synchronize files between container and host machine (Desktop, Downloads, Documents)",
            "parameters": {
                "action": {
                    "type": "string",
                    "description": "Action to perform: copy_to_host, copy_from_host, list_host_files",
                    "required": True
                },
                "source_path": {
                    "type": "string",
                    "description": "Source file path (for copy operations)",
                    "required": False
                },
                "dest_path": {
                    "type": "string",
                    "description": "Destination file path (for copy operations)",
                    "required": False
                },
                "host_location": {
                    "type": "string",
                    "description": "Host location: desktop, downloads, documents",
                    "required": False
                }
            }
        }
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Execute file sync action
        
        Args:
            action: Action to perform
            **kwargs: Additional parameters
            
        Returns:
            Result dictionary
        """
        try:
            if action == "copy_to_host":
                return self._copy_to_host(
                    kwargs.get("source_path"),
                    kwargs.get("dest_path"),
                    kwargs.get("host_location", "desktop")
                )
            elif action == "copy_from_host":
                return self._copy_from_host(
                    kwargs.get("source_path"),
                    kwargs.get("dest_path"),
                    kwargs.get("host_location", "desktop")
                )
            elif action == "list_host_files":
                return self._list_host_files(kwargs.get("host_location", "desktop"))
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


# Tool instance
file_sync_tool = FileSyncTool()


def get_tool_info():
    """Get tool information for LangGraph"""
    return file_sync_tool.get_tool_info()


def execute(**kwargs):
    """Execute file sync action"""
    action = kwargs.get("action")
    if not action:
        return {
            "success": False,
            "error": "action parameter is required"
        }
    
    return file_sync_tool.execute(action, **kwargs)
