"""Image OCR Tool - EasyOCR + Tesseract"""
from langchain_core.tools import BaseTool
import easyocr
import pytesseract
from PIL import Image
import os
# v5.8: Use enhanced tool pool
try:
    from app.core.tool_pool_v5_8 import enhanced_tool_pool as tool_pool
except ImportError:
    # Fallback to v5.7 tool pool
    from app.core.tool_pool import tool_pool

class ImageOCRTool(BaseTool):
    name: str = "image_ocr"
    description: str = """Extract text from images using OCR.
    Input should be a file path to an image.
    Returns extracted text."""
    
    reader: object = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # v5.8: Use global enhanced tool pool instead of creating new reader
        # self.reader = easyocr.Reader(['en', 'ch_sim'])  # Old: 10s loading time
        self.reader = None  # Will use enhanced_tool_pool.get_ocr_reader()
    
    def _run(self, image_path: str) -> str:
        try:
            if not os.path.exists(image_path):
                return f"Image file not found: {image_path}"
            
            # v5.7: Use pre-loaded OCR reader from tool pool
            reader = tool_pool.get_ocr_reader()
            if reader is None:
                return "Error: OCR reader not available"
            
            result = reader.readtext(image_path)
            text_easy = "\n".join([item[1] for item in result])
            
            # Also try Tesseract
            img = Image.open(image_path)
            text_tess = pytesseract.image_to_string(img)
            
            output = f"=== EasyOCR Results ===\n{text_easy}\n\n"
            output += f"=== Tesseract Results ===\n{text_tess}"
            
            return output
        except Exception as e:
            return f"Error performing OCR: {str(e)}"
    
    async def _arun(self, image_path: str) -> str:
        return self._run(image_path)
