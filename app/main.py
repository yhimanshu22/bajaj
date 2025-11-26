from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from app.models.schemas import BillExtractionResponse, BillExtractionRequest
from app.services.llm import extract_with_llm
from app.utils.download import download_file
from dotenv import load_dotenv
import uuid

load_dotenv()

app = FastAPI(title="Bill Extraction API", version="0.1.0", debug=True)

@app.get("/")
def read_root():
    return {"message": "Bill Extraction API is running"}

@app.post("/extract-bill-data", response_model=BillExtractionResponse)
async def extract_bill(request: BillExtractionRequest):
    try:
        # Download file from URL
        file_content, mime_type = await download_file(request.document)
        
        # Extraction using Gemini Vision
        extraction_data = extract_with_llm(file_content, mime_type)
        
        if not extraction_data:
            raise HTTPException(status_code=500, detail="Failed to extract data using Gemini")
        
        return BillExtractionResponse(
            is_success=True,
            data=extraction_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
