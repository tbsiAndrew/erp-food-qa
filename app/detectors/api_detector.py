import requests
import numpy as np
import cv2
import base64
import urllib3
from ..labels import get_label

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class APIDetector:
    def __init__(self, api_endpoint: str):
        self.api_endpoint = api_endpoint.rstrip('/')
        self.model_name = "external_api"
        self.model_version = "1.0.0"
        # Test connection on initialization
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for self-signed certs
        
    def predict(self, bgr):
        """
        Send image to external API for quality inspection.
        
        Args:
            bgr: OpenCV BGR image array
            
        Returns:
            List of detection dictionaries with cls, label, conf, box
        """
        try:
            # Encode image as JPEG
            _, buffer = cv2.imencode('.jpg', bgr)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Prepare request payload
            payload = {
                "image": img_base64,
                "format": "base64"
            }
            
            # Send POST request to API
            response = self.session.post(
                f"{self.api_endpoint}/predict",
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                # Return default low confidence result on error
                return [{
                    "cls": "0",
                    "label": "unknown",
                    "conf": 0.0,
                    "box": [0, 0, bgr.shape[1], bgr.shape[0]],
                }]
            
            result = response.json()
            
            # Parse API response (adjust based on actual API format)
            # Expected format: {"class": int, "confidence": float, "label": str}
            cls = str(result.get("class", 0))
            conf = float(result.get("confidence", 0.0))
            label = result.get("label", get_label(int(cls)))
            
            return [{
                "cls": cls,
                "label": label,
                "conf": conf,
                "box": [0, 0, bgr.shape[1], bgr.shape[0]],
            }]
            
        except Exception as e:
            print(f"API prediction error: {e}")
            # Return default low confidence result on exception
            return [{
                "cls": "0",
                "label": "error",
                "conf": 0.0,
                "box": [0, 0, bgr.shape[1], bgr.shape[0]],
            }]
