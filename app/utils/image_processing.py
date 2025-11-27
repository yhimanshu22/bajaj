from PIL import Image, ImageEnhance
import io

def enhance_image(image_bytes: bytes) -> bytes:
    """
    Enhance image quality for better OCR/Extraction.
    Applies contrast enhancement and sharpening.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Enhance Contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)  # Increase contrast by 50%
        
        # Enhance Sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)  # Increase sharpness by 50%
        
        # Save back to bytes
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=95)
        return output.getvalue()
        
    except Exception as e:
        # If enhancement fails (e.g. not an image), return original bytes
        return image_bytes
