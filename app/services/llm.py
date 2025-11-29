import google.generativeai as genai
import os
import json
import logging
from typing import Optional, Dict, Any, Tuple
import re

logger = logging.getLogger(__name__)


def sanitize_json(raw: str) -> str:
    """Clean LLM JSON output for safe parsing."""

    # Remove markdown blocks like ```json ... ```
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json", "", 1)

    raw = raw.strip()

    # Remove trailing commas in dicts/lists
    raw = re.sub(r",\s*}", "}", raw)
    raw = re.sub(r",\s*]", "]", raw)

    # Remove commas from numbers (e.g. 1,200.00 -> 1200.00)
    # Look for digits, comma, digits
    raw = re.sub(r'(\d),(\d)', r'\1\2', raw)

    # Replace single quotes with double quotes
    raw = re.sub(r"(?<!\\)'", "\"", raw)

    # Remove stray line breaks / tabs
    raw = raw.replace("\n", " ").replace("\t", " ")

    # Collapse multiple spaces
    raw = re.sub(r"\s+", " ", raw)

    return raw


def extract_with_llm(file_content: bytes, mime_type: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, int]]]:
    """Extract bill data using Gemini Vision model with strict JSON output."""

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not found. Skipping LLM extraction.")
        return None, None

    genai.configure(api_key=api_key)

    model_name = 'gemini-2.0-flash'
    logger.info(f"Using LLM model: {model_name}")

    model = genai.GenerativeModel(
        model_name,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.0,  # deterministic output
            "max_output_tokens": 8192
        }
    )

    prompt = """
You are an extraction engine.

STRICT RULES:
1. Output ONLY valid JSON. No text before or after. No markdown. No backticks.
2. ALL JSON keys MUST use double quotes.
3. DO NOT round numbers. Preserve the exact numeric values detected.
4. item_amount MUST equal (item_rate × item_quantity) without rounding.
5. If quantity missing → use 1.00
6. If rate missing → use item_amount
7. DO NOT modify values. DO NOT approximate.
8. No comments. No explanations.
7. DO NOT modify values. DO NOT approximate.
8. No comments. No explanations.

OUTPUT FORMAT:

{
  "pagewise_line_items": [
    {
      "page_no": "1",
      "page_type": "Bill Detail | Final Bill | Pharmacy",
      "bill_items": [
        {
          "item_name": "",
          "item_amount": 0.00,
          "item_rate": 0.00,
          "item_quantity": 0.00
        }
      ]
    }
  ],
  "total_item_count": 0
}

Return only the JSON object.
"""

    content = [
        {"mime_type": mime_type, "data": file_content},
        prompt
    ]

    response = model.generate_content(content)

    raw = response.text or ""
    raw = raw.strip()

    # Clean the LLM output
    raw = sanitize_json(raw)

    # Final JSON parsing block
    try:
        data = json.loads(raw)
        
        # Post-processing: Recalculate totals to ensure accuracy
        calculated_count = 0
        
        if "pagewise_line_items" in data:
            for page in data["pagewise_line_items"]:
                if "bill_items" in page:
                    for item in page["bill_items"]:
                        calculated_count += 1
                        
        data["total_item_count"] = calculated_count
        
        # Extract token usage
        usage = {
            "total_tokens": response.usage_metadata.total_token_count,
            "input_tokens": response.usage_metadata.prompt_token_count,
            "output_tokens": response.usage_metadata.candidates_token_count
        }
        
        return data, usage

    except Exception as e:
        logger.error("❌ LLM JSON parse failed.")
        logger.error("---- RAW OUTPUT ----")
        logger.error(raw)
        logger.error("--------------------")
        raise e
