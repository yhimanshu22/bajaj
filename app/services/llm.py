import google.generativeai as genai
import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def extract_with_llm(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract bill information using Google Gemini.
    Returns a dictionary matching the API response schema or None if failed.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not found. Skipping LLM extraction.")
        return None

    try:
        genai.configure(api_key=api_key)
        model_name = 'gemini-2.0-flash'
        logger.info(f"Using LLM model: {model_name}")
        model = genai.GenerativeModel(model_name)

        prompt = f"""
        You are an expert data extraction assistant. Extract the following information from the provided OCR text of a bill/invoice.
        
        Output strictly valid JSON with this structure:
        {{
            "pagewise_line_items": [
                {{
                    "page_no": "1",
                    "bill_items": [
                        {{
                            "item_name": "Description of item",
                            "item_amount": 0.00,
                            "item_rate": 0.00,
                            "item_quantity": 0.00
                        }}
                    ]
                }}
            ],
            "total_item_count": 0,
            "reconciled_amount": 0.00
        }}

        Rules:
        1. Extract all line items accurately.
        2. If quantity is missing, infer it (usually 1).
        3. If rate is missing, infer it from amount/quantity.
        4. "reconciled_amount" should be the sum of all item_amounts.
        5. Do not include markdown formatting (```json ... ```). Just the raw JSON string.
        
        OCR Text:
        {text}
        """

        response = model.generate_content(prompt)
        
        # Clean response (remove markdown if present)
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        data = json.loads(raw_text.strip())
        return data

    except Exception as e:
        logger.error(f"LLM Extraction failed: {e}")
        return None
