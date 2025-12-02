"""Image Analysis Tool - OpenCV"""
from langchain_core.tools import BaseTool
import cv2
import numpy as np

class ImageAnalysisTool(BaseTool):
    name: str = "image_analysis"
    description: str = """Analyze images for faces, edges, objects.
    Input format: operation|image_path
    Operations: detect_faces, detect_edges, get_info
    Example: detect_faces|/tmp/image.jpg"""
    
    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split('|')
            operation = parts[0].strip()
            image_path = parts[1].strip()
            
            img = cv2.imread(image_path)
            if img is None:
                return f"Cannot read image: {image_path}"
            
            if operation == "detect_faces":
                face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
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
