import cv2
import numpy as np
from typing import List
from pdf2image import convert_from_bytes

def preprocess_image(image_bytes: bytes) -> List[np.ndarray]:
    """
    Convert bytes (PDF or Image) to a list of preprocessed numpy arrays (one per page).
    """
    images = []
    
    # Try to detect if it's a PDF
    if image_bytes.startswith(b'%PDF'):
        try:
            pil_images = convert_from_bytes(image_bytes)
            for pil_img in pil_images:
                images.append(np.array(pil_img))
        except Exception as e:
            # Likely poppler not installed
            raise ValueError(f"Failed to process PDF. Ensure poppler-utils is installed. Error: {str(e)}")
    else:
        # Assume it's an image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is not None:
            images.append(img)
            
    processed_images = []
    for img in images:
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Thresholding (Otsu's) - optional, might be too aggressive for some bills
        # _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        processed_images.append(denoised)
        
    return processed_images
