import google.generativeai as genai
import os
import json
import logging
from typing import Optional, Dict, Any, Tuple, List
import re
from app.utils.pdf import split_pdf

logger = logging.getLogger(__name__)


def sanitize_json(raw: str) -> str:
    """Clean LLM JSON output for safe parsing."""
    # 1. Remove markdown blocks
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
    
    raw = raw.strip()

    # 2. Fix the specific "Double Double-Quote" issue
    raw = raw.replace('""', '\\"')

    # 3. Remove trailing commas (Safe)
    raw = re.sub(r",\s*}", "}", raw)
    raw = re.sub(r",\s*]", "]", raw)

    # 4. Remove newlines/tabs for cleaner parsing
    raw = raw.replace("\n", " ").replace("\t", " ")
    
    return raw


def extract_page_1(content: bytes, mime_type: str) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """Extract summary and metadata from Page 1 using Pro model."""
    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        'gemini-2.5-pro',
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.0,
            "max_output_tokens": 8192 # Page 1 shouldn't be huge
        }
    )

    prompt = """
    You are an extraction engine. Extract the Bill Header info (Patient Name, Bill No, Dates) 
    AND the 'Summary Table' (the table showing Gross Amt per category).
    Ignore the footer.
    
    OUTPUT FORMAT:
    {
      "metadata": {
        "patient_name": "string",
        "bill_no": "string",
        "admission_date": "string",
        "discharge_date": "string",
        "net_amount": 0.00
      },
      "category_summary": [
        {
          "category": "string",
          "gross_amount": 0.00
        }
      ]
    }
    """
    
    response = model.generate_content([{'mime_type': mime_type, 'data': content}, prompt])
    raw = sanitize_json(response.text)
    data = json.loads(raw)
    
    usage = {
        "total_tokens": response.usage_metadata.total_token_count,
        "input_tokens": response.usage_metadata.prompt_token_count,
        "output_tokens": response.usage_metadata.candidates_token_count
    }
    return data, usage


def extract_line_items(content: bytes, mime_type: str, page_num: int) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Extract line items from Page 2+ using Flash model."""
    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        'gemini-2.0-flash',
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.0,
            "max_output_tokens": 8192
        }
    )

    prompt = f"""
    This is page {page_num} of a hospital bill. 
    Extract ONLY the tabular line items (medicines, services, charges).
    Ignore page headers repeated at the top.
    Ignore page footers.
    
    Return strict JSON list:
    [
      {{ "item_name": "...", "item_amount": 0.0, "item_rate": 0.0, "item_quantity": 0.0 }}
    ]
    """
    
    response = model.generate_content([{'mime_type': mime_type, 'data': content}, prompt])
    raw = sanitize_json(response.text)
    data = json.loads(raw)
    
    usage = {
        "total_tokens": response.usage_metadata.total_token_count,
        "input_tokens": response.usage_metadata.prompt_token_count,
        "output_tokens": response.usage_metadata.candidates_token_count
    }
    return data, usage


def extract_with_llm(file_content: bytes, mime_type: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, int]]]:
    """Extract bill data using Split & Merge strategy."""
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not found. Skipping LLM extraction.")
        return None, None

    try:
        # 1. Split PDF if applicable
        pages = []
        if mime_type == "application/pdf":
            pages = split_pdf(file_content)
        else:
            pages = [file_content] # Treat image as single page

        logger.info(f"Processing {len(pages)} pages...")
        
        total_usage = {"total_tokens": 0, "input_tokens": 0, "output_tokens": 0}
        
        # 2. Process Page 1 (Summary)
        logger.info("Processing Page 1 (Summary)...")
        # For single images, we treat it as Page 1 but might need to adjust prompt if it has line items too.
        # Assuming the robust logic: Page 1 always has metadata.
        summary_data, usage1 = extract_page_1(pages[0], mime_type if mime_type != "application/pdf" else "application/pdf")
        
        # Accumulate usage
        for k in total_usage: total_usage[k] += usage1.get(k, 0)
        
        all_line_items = []
        
        # 3. Process Pages 2+ (Line Items)
        if len(pages) > 1:
            for i, page_content in enumerate(pages[1:], start=2):
                logger.info(f"Processing Page {i}...")
                try:
                    # For PDF split pages, they are still PDFs
                    p_mime = "application/pdf" if mime_type == "application/pdf" else mime_type
                    items, usage_p = extract_line_items(page_content, p_mime, i)
                    
                    if isinstance(items, list):
                        all_line_items.extend(items)
                    
                    for k in total_usage: total_usage[k] += usage_p.get(k, 0)
                    
                except Exception as e:
                    logger.error(f"Error processing page {i}: {e}")
                    # Continue to next page
                    continue
        else:
            # If single page, try to extract line items from it as well if not present in summary
            # Or maybe the single page contains everything. 
            # For now, let's assume single page might have line items too.
            # But extract_page_1 prompt only asked for summary.
            # Let's call extract_line_items on page 1 too if it's a single page?
            # Or update extract_page_1 to get everything if it's single page.
            # To keep it simple and robust for the "Large Bill" use case, let's just try to get line items from Page 1 too if it's the only page.
            if len(pages) == 1:
                 logger.info("Single page document. Extracting line items from Page 1...")
                 try:
                    items, usage_p = extract_line_items(pages[0], mime_type if mime_type != "application/pdf" else "application/pdf", 1)
                    if isinstance(items, list):
                        all_line_items.extend(items)
                    for k in total_usage: total_usage[k] += usage_p.get(k, 0)
                 except Exception as e:
                     logger.error(f"Error extracting line items from single page: {e}")

        # 4. Merge
        final_output = {
            "pagewise_line_items": [
                {
                    "page_no": "All",
                    "page_type": "Merged",
                    "bill_items": all_line_items
                }
            ],
            "total_item_count": len(all_line_items),
            "metadata": summary_data.get("metadata", {}),
            "category_summary": summary_data.get("category_summary", [])
        }
        
        # 5. Validation (Optional logging)
        net_amount = summary_data.get("metadata", {}).get("net_amount", 0.0)
        total_extracted = sum(item.get("item_amount", 0) for item in all_line_items)
        logger.info(f"Validation: Net Amount ({net_amount}) vs Extracted Total ({total_extracted})")
        
        return final_output, total_usage

    except Exception as e:
        logger.error(f"❌ Extraction failed: {str(e)}")
        raise e