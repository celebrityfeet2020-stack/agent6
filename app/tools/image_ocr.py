"""Image OCR Tool - EasyOCR + Tesseract"""
from langchain_core.tools import BaseTool
import easyocr
import pytesseract
from PIL import Image
import os

class ImageOCRTool(BaseTool):
    name: str = "image_ocr"
    description: str = """Extract text from images using OCR.
    Input should be a file path to an image.
    Returns extracted text."""
    
    reader: object = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reader = easyocr.Reader(['en', 'ch_sim'])
    
    def _run(self, image_path: str) -> str:
        try:
            if not os.path.exists(image_path):
                return f"Image file not found: {image_path}"
            
            # Try EasyOCR first
            result = self.reader.readtext(image_path)
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
