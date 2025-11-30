import google.generativeai as genai
import os
import json
import logging
from typing import Optional, Dict, Any, Tuple
import re

logger = logging.getLogger(__name__)

def sanitize_json(raw: str) -> str:
    """Clean LLM JSON output for safe parsing."""
    # 1. Remove markdown blocks
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
    
    raw = raw.strip()

    # 2. Fix the specific "Double Double-Quote" issue from your logs
    # Turns "COOMB""S" into "COOMB\"S"
    # Matches "" that is NOT at the start/end of a JSON key/value
    raw = raw.replace('""', '\\"')

    # 3. Remove trailing commas (Safe)
    raw = re.sub(r",\s*}", "}", raw)
    raw = re.sub(r",\s*]", "]", raw)

    # 4. Remove newlines/tabs for cleaner parsing
    raw = raw.replace("\n", " ").replace("\t", " ")
    
    return raw

def extract_with_llm(file_content: bytes, mime_type: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, int]]]:
    """Extract bill data using Gemini Vision model with strict JSON output."""

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not found. Skipping LLM extraction.")
        return None, None

    genai.configure(api_key=api_key)

    # FIXED: Correct model name
    model_name = 'gemini-2.5-pro' 
    logger.info(f"Using LLM model: {model_name}")

    model = genai.GenerativeModel(
        model_name,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.0,
            # "response_schema": ... # Optional: You can pass a typed schema here for even better results
        }
    )

    prompt = """
You are an extraction engine.

STRICT RULES:
1. Output ONLY valid JSON.
2. If the text contains double quotes, ESCAPE them with a backslash (e.g., \\").
3. DO NOT round numbers. Preserve exact values.
4. item_amount MUST equal (item_rate * item_quantity).
5. If quantity missing -> use 1.0
6. If rate missing -> use item_amount

OUTPUT FORMAT:
{
  "pagewise_line_items": [
    {
      "page_no": 1,
      "page_type": "Bill Detail | Final Bill | Pharmacy",
      "bill_items": [
        {
          "item_name": "string",
          "item_amount": 0.00,
          "item_rate": 0.00,
          "item_quantity": 0.00
        }
      ]
    }
  ],
  "total_item_count": 0
}
"""

    content = [
        {"mime_type": mime_type, "data": file_content},
        prompt
    ]

    try:
        response = model.generate_content(content)
        raw = response.text or ""
        
        # Clean the LLM output
        clean_raw = sanitize_json(raw)

        # Parse
        data = json.loads(clean_raw)
        
        # Post-processing: Recalculate totals
        calculated_count = 0
        if "pagewise_line_items" in data:
            for page in data["pagewise_line_items"]:
                if "bill_items" in page:
                    calculated_count += len(page["bill_items"])
                        
        data["total_item_count"] = calculated_count
        
        usage = {
            "total_tokens": response.usage_metadata.total_token_count,
            "input_tokens": response.usage_metadata.prompt_token_count,
            "output_tokens": response.usage_metadata.candidates_token_count
        }
        
        return data, usage

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON Parse Error: {e.msg}")
        logger.error(f"Error at line {e.lineno} column {e.colno}")
        logger.error("---- RAW OUTPUT ----")
        logger.error(raw) 
        logger.error("--------------------")
        raise e
    except Exception as e:
        logger.error(f"❌ General LLM Error: {str(e)}")
        raise e