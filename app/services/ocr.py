import pytesseract
import numpy as np
from typing import List, Dict

def extract_text(images: List[np.ndarray]) -> List[Dict[str, str]]:
    """
    Extract text from a list of images using Tesseract.
    Returns a list of dictionaries containing raw text and HOCR data per page.
    """
    results = []
    
    for i, img in enumerate(images):
        # Extract raw text
        text = pytesseract.image_to_string(img, config='--psm 6')
        
        # Extract HOCR (layout info) - useful for table detection later
        hocr = pytesseract.image_to_pdf_or_hocr(img, extension='hocr')
        
        results.append({
            "page": i + 1,
            "text": text,
            "hocr": hocr.decode('utf-8')
        })
        
    return results
