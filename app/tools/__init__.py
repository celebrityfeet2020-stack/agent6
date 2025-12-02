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
]
