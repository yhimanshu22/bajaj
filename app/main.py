from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from app.models.schemas import BillExtractionResponse, BillExtractionRequest
from app.services.llm import extract_with_llm
from app.utils.download import download_file
from app.utils.image_processing import enhance_image
from app.services.cache import response_cache
from dotenv import load_dotenv
import uuid

load_dotenv()

app = FastAPI(title="Bill Extraction API", version="0.1.0", debug=True)

@app.get("/")
def read_root():
    return {"message": "Bill Extraction API is running"}

import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/extract-bill-data", response_model=BillExtractionResponse)
async def extract_bill(request: BillExtractionRequest):
    try:
        logger.info(f"Received extraction request for document: {request.document}")
        
        # 1. Check Cache
        cached_result = response_cache.get(request.document)
        if cached_result:
            logger.info("Cache hit")
            return BillExtractionResponse(
                is_success=True,
                token_usage=cached_result.get("token_usage"),
                data=cached_result["data"]
            )

        # Download file from URL
        logger.info("Downloading file...")
        file_content, mime_type = await download_file(request.document)
        logger.info(f"File downloaded. Mime type: {mime_type}")
        
        # Pre-processing: Enhance image if it's an image type
        if mime_type.startswith("image/"):
            file_content = enhance_image(file_content)
        
        # Extraction using Gemini Vision
        logger.info("Calling Gemini Vision...")
        extraction_data, token_usage = extract_with_llm(file_content, mime_type)
        
        if not extraction_data:
            raise HTTPException(status_code=500, detail="Failed to extract data using Gemini")
        
        # 2. Store in Cache
        cache_payload = {
            "data": extraction_data,
            "token_usage": token_usage
        }
        response_cache.set(request.document, cache_payload)

        return BillExtractionResponse(
            is_success=True,
            token_usage=token_usage,
            data=extraction_data
        )
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-from-file", response_model=BillExtractionResponse)
async def extract_bill_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        mime_type = file.content_type
        
        # Pre-processing: Enhance image
        if mime_type.startswith("image/"):
            content = enhance_image(content)
        
        extraction_data, token_usage = extract_with_llm(content, mime_type)
        
        if not extraction_data:
             raise HTTPException(status_code=500, detail="Failed to extract data using Gemini")
             
        return BillExtractionResponse(
            is_success=True,
            token_usage=token_usage,
            data=extraction_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
