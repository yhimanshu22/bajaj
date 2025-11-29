import requests
import json
import logging
import sys
import os
try:
    from deepdiff import DeepDiff
except ImportError:
    DeepDiff = None

import time

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.schemas import BillExtractionResponse  # optional schema reference

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# API_URL = "http://127.0.0.1:8000/extract-bill-data"
base_url = os.getenv("API_BASE_URL")
if not base_url:
    logger.warning("API_BASE_URL not found in .env, defaulting to localhost")
    base_url = "http://127.0.0.1:8000"

API_URL = f"{base_url}/extract-bill-data"

def pretty(item):
    """Pretty JSON helper."""
    return json.dumps(item, indent=2, ensure_ascii=False)


def compare_items(extracted_items, expected_items):
    """
    Compare lists of extracted items vs expected items.
    Returns diff object.
    """
    if DeepDiff:
        return DeepDiff(expected_items, extracted_items, ignore_order=True, significant_digits=2)
    else:
        logger.warning("DeepDiff not installed. Skipping deep comparison.")
        return {}


def validate_response_structure(data):
    """
    Validate required keys exist for schema correctness.
    """
    required_keys = ["pagewise_line_items", "total_item_count"]
    for key in required_keys:
        if key not in data:
            return False, f"Missing key: {key}"
    return True, ""


def test_extraction(name, url, expected_data):
    logger.info(f"\n🔍 Testing {name}...\n")

    payload = {"document": url}

    start_time = time.time()
    try:
        response = requests.post(API_URL, json=payload)
        elapsed = time.time() - start_time
        logger.info(f"⏱️ Time taken: {elapsed:.2f}s")
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"{name} ❌ HTTP Error: {e}")
            logger.error(f"Response Status Code: {response.status_code}")
            logger.error(f"Response Body: {response.text}")
            return

        result = response.json()

        # Check success field
        if not result.get("is_success"):
            logger.error(f"{name} FAILED ❌ : API returned is_success = False")
            logger.error(f"Full Response: {pretty(result)}")
            return

        data = result.get("data", {})

        # 1️⃣ Schema validation
        valid, msg = validate_response_structure(data)
        if not valid:
            logger.error(f"{name} ❌ INVALID SCHEMA: {msg}")
            logger.error(f"Received Data Keys: {list(data.keys())}")
            return

        # 2️⃣ Extracted values
        extracted_count = data.get("total_item_count")
        expected_count = expected_data["data"]["total_item_count"]

        logger.info(f"📌 Count     → Expected: {expected_count} | Got: {extracted_count}")

        # 3️⃣ Per-page items
        page_items = data.get("pagewise_line_items", [])

        if not page_items:
            logger.error(f"{name} ❌ No pagewise_line_items found.")
            logger.error(f"Full Data: {pretty(data)}")
            return

        extracted_bill_items = page_items[0]["bill_items"]
        logger.info(f"🧾 First 3 Extracted Items:\n{pretty(extracted_bill_items[:3])}")

        # Optional: Full expected items for deep comparison (if provided)
        expected_items = expected_data["data"].get("full_items_list")

        if expected_items:
            logger.info("🔎 Running FULL item comparison...")
            diff = compare_items(extracted_bill_items, expected_items)

            if diff:
                logger.warning(f"❌ Item Mismatch Found:\n{pretty(diff)}")
                # Log full extracted items for debugging
                logger.info(f"Full Extracted Items:\n{pretty(extracted_bill_items)}")
            else:
                logger.info("✅ All extracted items match expected list EXACTLY!")

        # 4️⃣ Final Pass/Fail
        count_match = extracted_count == expected_count

        if count_match:
            logger.info(f"\n{name} PASSED ✅\n")
        else:
            logger.warning(f"\n{name} FAILED ❌ : Mismatch in count or total\n")
            logger.warning(f"Expected Count: {expected_count}, Got: {extracted_count}")

    except Exception as e:
        logger.error(f"{name} ❌ Unexpected Error: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":

    # -----------------------------
    # Sample 3: Pharmacy (4 items)
    # -----------------------------
    sample_pharmacy_url = (
        "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png"
        "?sv=2025-07-05&spr=https&st=2025-11-24T14%3A13%3A22Z&se=2026-11-25T14%3A13%3A00Z"
        "&sr=b&sp=r&sig=WFJYfNw0PJdZOpOYlsoAW0XujYGG1x2HSbcDREiFXSU%3D"
    )

    sample_pharmacy_expected = {
        "data": {
            "total_item_count": 4
        }
    }

    # -------------------------------------------
    # Sample 1: Full Hospital Bill (30 items)
    # -------------------------------------------
    sample_hospital_large_url = (
        "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_1.png"
        "?sv=2025-07-05&spr=https&st=2025-11-24T14%3A21%3A03Z&se=2026-11-25T14%3A21%3A00Z"
        "&sr=b&sp=r&sig=2szJobwLVzcVSmg5IPWjRT9k7pHq2Tvifd6seRa2xRI%3D"
    )

    sample_hospital_large_expected = {
        "data": {
            "total_item_count": 30
        }
    }

    # ---------------------------------------------------
    # Sample 2: Consultation + Ward + Lab (12 items)
    # ---------------------------------------------------
    sample_consultation_url = (
        "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_3.png"
        "?sv=2025-07-05&spr=https&st=2025-11-24T14%3A24%3A39Z&se=2026-11-25T14%3A24%3A00Z"
        "&sr=b&sp=r&sig=egKAmIUms8H5f3kgrGXKvcfuBVlQp0Qc2tsfxdvRgUY%3D"
    )

    sample_consultation_expected = {
        "data": {
            "total_item_count": 12
        }
    }

    # Run Tests
    test_extraction("Sample 3 (Pharmacy – 4 items)", sample_pharmacy_url, sample_pharmacy_expected)
    print("-" * 80)

    test_extraction("Sample 1 (Hospital – 30 items)", sample_hospital_large_url, sample_hospital_large_expected)
    print("-" * 80)

    test_extraction("Sample 2 (Consultation + Ward – 12 items)", sample_consultation_url, sample_consultation_expected)
    print("-" * 80)

    # ---------------------------------------------------
    # Complex Case: Large PDF that caused JSON truncation
    # ---------------------------------------------------
    complex_pdf_url = (
        "https://hackrx.blob.core.windows.net/files/Final%20Data/complex/images/"
        "HOS_INW_KONATHAMTANUJASRIKIRAN_3603_22112025163607.pdf"
        "?se=2025-12-05T05%3A33%3A00Z&sp=r&sv=2025-11-05&sr=b&sig=ahyeUJ9KrNh96pTPzusU2RP4vEFdxcynObbXWOjnuQs%3D"
    )
    
    # We don't know the exact count, but we want to ensure it doesn't crash with JSON error.
    # We'll set a dummy expectation and check logs for "INVALID SCHEMA" or "Unexpected Error".
    # If it parses successfully, it will likely fail the count check but pass the schema check.
    complex_pdf_expected = {
        "data": {
            "total_item_count": 999 # Dummy value
        }
    }

    test_extraction("Complex PDF (Truncation Check)", complex_pdf_url, complex_pdf_expected)
    print("-" * 80)
