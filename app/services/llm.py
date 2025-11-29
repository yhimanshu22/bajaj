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
            "temperature": 0.0  # deterministic output
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
9. FRAUD DETECTION: 
   - Compare the "Total" printed on the bill with the sum of the line items. If they don't match, this is a MAJOR FRAUD SIGNAL.
   - Look for inconsistent fonts, different ink colors, or signs of digital tampering/whitener.

OUTPUT FORMAT:

{
  "pagewise_line_items": [
    {
      "page_no": "1",
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
  "total_item_count": 0,
  "reconciled_amount": 0.00,
  "declared_total": 0.00,
  "fraud_signals": {
    "is_suspicious": false,
    "warnings": []
  }
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
        calculated_total = 0.0
        calculated_count = 0
        
        if "pagewise_line_items" in data:
            for page in data["pagewise_line_items"]:
                if "bill_items" in page:
                    for item in page["bill_items"]:
                        amount = item.get("item_amount", 0.0)
                        calculated_total += amount
                        calculated_count += 1
                        
        # Fraud Check: Total Mismatch
        declared_total = data.get("declared_total", 0.0)
        
        # Ensure fraud_signals dict exists
        if "fraud_signals" not in data or data["fraud_signals"] is None:
            data["fraud_signals"] = {"is_suspicious": False, "warnings": []}
            
        # Check for mismatch (tolerance of 1.0 for rounding differences)
        if declared_total > 0 and abs(declared_total - calculated_total) > 1.0:
            data["fraud_signals"]["is_suspicious"] = True
            data["fraud_signals"]["warnings"].append(
                f"Total Amount Mismatch: Bill says {declared_total}, but items sum to {round(calculated_total, 2)}"
            )
            
        # Overwrite reconciled_amount with the CORRECT calculated sum
        data["reconciled_amount"] = round(calculated_total, 2)
        data["total_item_count"] = calculated_count
        
        # Remove declared_total to match strict schema if needed (optional, but safer)
        data.pop("declared_total", None)
        
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
