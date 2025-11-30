import io
from typing import List
from pypdf import PdfReader, PdfWriter

def split_pdf(file_content: bytes) -> List[bytes]:
    """
    Splits a PDF file content into a list of bytes, where each element 
    is a single page PDF.
    """
    try:
        reader = PdfReader(io.BytesIO(file_content))
        pages = []
        
        for i in range(len(reader.pages)):
            writer = PdfWriter()
            writer.add_page(reader.pages[i])
            
            output_stream = io.BytesIO()
            writer.write(output_stream)
            pages.append(output_stream.getvalue())
            
        return pages
    except Exception as e:
        print(f"Error splitting PDF: {e}")
        # If splitting fails, return the original content as a single item list
        # This acts as a fallback for non-PDFs or corrupted PDFs
        return [file_content]
