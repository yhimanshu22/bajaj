from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from app.models.schemas import BillExtractionResponse, BillExtractionRequest
from app.services.preprocessing import preprocess_image
from app.services.ocr import extract_text
from app.services.extraction import extract_information
from app.services.llm import extract_with_llm
from app.utils.download import download_file
from dotenv import load_dotenv
import uuid

load_dotenv()

app = FastAPI(title="Bill Extraction API", version="0.1.0")

@app.get("/")
def read_root():
    return {"message": "Bill Extraction API is running"}

@app.post("/extract", response_model=BillExtractionResponse)
async def extract_bill(request: BillExtractionRequest):
    try:
        # Download file from URL
        contents = await download_file(request.document)
        
        # 1. Pre-processing
        processed_images = preprocess_image(contents)
        
        # 2. OCR
        ocr_results = extract_text(processed_images)
        
        # Combine text for LLM
        full_text = "\n".join([res["text"] for res in ocr_results])
        
        # 3. Extraction (LLM First, Fallback to Regex)
        extraction_data = None
        method = "Regex"
        
        # Try LLM
        try:
            llm_result = extract_with_llm(full_text)
            if llm_result:
                extraction_data = llm_result
                method = "LLM"
        except Exception:
            pass
            
        # Fallback to Regex if LLM failed or returned None
        if not extraction_data:
            extraction_data = extract_information(ocr_results)
        
        return BillExtractionResponse(
            is_success=True,
            data=extraction_data,
            flags={"extraction_method": method}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
