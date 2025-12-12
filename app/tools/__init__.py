"""M3 Agent Tools - Complete Toolset"""
from .web_search import WebSearchTool
from .web_scraper import WebScraperTool
from .code_executor import CodeExecutorTool
from .file_operations import FileOperationsTool
from .image_ocr import ImageOCRTool
from .image_analysis import ImageAnalysisTool
from .ssh_tool import SSHTool
from .git_tool import GitTool
from .data_analysis import DataAnalysisTool
from .browser_automation import BrowserAutomationTool
from .api_caller import UniversalAPITool
from .telegram_tool import TelegramTool
from .speech_recognition_tool import SpeechRecognitionTool
from .rpa_tool import RPATool
from .file_sync_tool import FileSyncTool

def load_all_tools():
    """
    加载所有15个工具
    返回: (tools列表, errors字典)
    """
    print("🔧 正在加载工具池...")
    
    tools = []
    tool_classes = [
        UniversalAPITool,
        WebSearchTool,
        WebScraperTool,
        BrowserAutomationTool,
        CodeExecutorTool,
        FileOperationsTool,
        ImageOCRTool,
        ImageAnalysisTool,
        SpeechRecognitionTool,
        DataAnalysisTool,
        SSHTool,
        GitTool,
        TelegramTool,
        RPATool,
        FileSyncTool
    ]
    
    errors = {}
    for tool_class in tool_classes:
        try:
            tool = tool_class()
            tools.append(tool)
            print(f"  ✅ {tool.name}")
        except Exception as e:
            tool_name = tool_class.__name__
            errors[tool_name] = str(e)
            print(f"  ❌ {tool_name}: {e}")
    
    print(f"✅ 工具池加载完成: {len(tools)}/15 个工具")
    
    if errors:
        print(f"⚠️  {len(errors)} 个工具加载失败:")
        for tool_name, error in errors.items():
            print(f"     - {tool_name}: {error}")
    
    return tools, errors


__all__ = [
    "WebSearchTool",
    "WebScraperTool",
    "CodeExecutorTool",
    "FileOperationsTool",
    "ImageOCRTool",
    "ImageAnalysisTool",
    "SSHTool",
    "GitTool",
    "DataAnalysisTool",
    "BrowserAutomationTool",
    "UniversalAPITool",
    "TelegramTool",
    "SpeechRecognitionTool",
    "RPATool",
    "FileSyncTool",
    "load_all_tools",
]
