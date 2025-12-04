"""Image Analysis Tool - OpenCV (v5.0: Pre-loaded models)"""
from langchain_core.tools import BaseTool
import cv2
import numpy as np
import logging

# v5.8: Use enhanced tool pool
try:
    from app.core.tool_pool_v5_8 import enhanced_tool_pool
    USE_TOOL_POOL = True
except ImportError:
    USE_TOOL_POOL = False

logger = logging.getLogger(__name__)

class ImageAnalysisTool(BaseTool):
    name: str = "image_analysis"
    description: str = """Analyze images for faces, edges, objects.
    Input format: operation|image_path
    Operations: detect_faces, detect_edges, get_info
    Example: detect_faces|/tmp/image.jpg"""
    
    face_cascade: object = None  # Pre-loaded in __init__ (v5.0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # v5.8: Use global enhanced tool pool for CV models
        if USE_TOOL_POOL:
            self.face_cascade = None  # Will use enhanced_tool_pool.get_cv_model()
            logger.info("✅ ImageAnalysisTool initialized (will use global tool pool)")
        else:
            # Fallback: Pre-load Haar Cascade classifier (v5.0 optimization)
            try:
                self.face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
                logger.info("✅ Haar Cascade face detector pre-loaded (v5.0)")
            except Exception as e:
                logger.warning(f"Failed to pre-load face detector: {e}")
    
    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split('|')
            operation = parts[0].strip()
            image_path = parts[1].strip()
            
            img = cv2.imread(image_path)
            if img is None:
                return f"Cannot read image: {image_path}"
            
            if operation == "detect_faces":
                # v5.8: Use pre-loaded classifier from tool pool
                if USE_TOOL_POOL:
                    face_cascade = enhanced_tool_pool.get_cv_model("face")
                    if face_cascade is None:
                        return "Error: Face detector not loaded"
                else:
                    face_cascade = self.face_cascade
                    if face_cascade is None:
                        return "Error: Face detector not loaded"
                
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                return f"Detected {len(faces)} faces in the image"
            
            elif operation == "detect_edges":
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 100, 200)
                edge_count = np.count_nonzero(edges)
                return f"Edge detection completed. Edge pixels: {edge_count}"
            
            elif operation == "get_info":
                height, width, channels = img.shape
                return f"Image info: {width}x{height}, {channels} channels"
            
            else:
                return f"Unknown operation: {operation}"
        except Exception as e:
            return f"Error analyzing image: {str(e)}"
    
    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
