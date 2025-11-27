import requests
import json
import logging
import sys
import os
from deepdiff import DeepDiff

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.schemas import BillExtractionResponse  # optional schema reference

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API_URL = "http://127.0.0.1:8000/extract-bill-data"
API_URL = "https://medbill-g3hr.onrender.com/extract-bill-data"

def pretty(item):
    """Pretty JSON helper."""
    return json.dumps(item, indent=2, ensure_ascii=False)


def compare_items(extracted_items, expected_items):
    """
    Compare lists of extracted items vs expected items.
    Returns diff object.
    """
    return DeepDiff(expected_items, extracted_items, ignore_order=True, significant_digits=2)


def validate_response_structure(data):
    """
    Validate required keys exist for schema correctness.
    """
    required_keys = ["pagewise_line_items", "total_item_count", "reconciled_amount"]
    for key in required_keys:
        if key not in data:
            return False, f"Missing key: {key}"
    return True, ""


def test_extraction(name, url, expected_data):
    logger.info(f"\n🔍 Testing {name}...\n")

    payload = {"document": url}

    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        result = response.json()

        # Check success field
        if not result.get("is_success"):
            logger.error(f"{name} FAILED ❌ : API returned is_success = False")
            return

        data = result.get("data", {})

        # 1️⃣ Schema validation
        valid, msg = validate_response_structure(data)
        if not valid:
            logger.error(f"{name} ❌ INVALID SCHEMA: {msg}")
            return

        # 2️⃣ Extracted values
        extracted_count = data.get("total_item_count")
        expected_count = expected_data["data"]["total_item_count"]

        extracted_total = round(data.get("reconciled_amount"), 2)
        expected_total = round(expected_data["data"]["reconciled_amount"], 2)

        logger.info(f"📌 Count     → Expected: {expected_count} | Got: {extracted_count}")
        logger.info(f"📌 Total Amt → Expected: {expected_total} | Got: {extracted_total}")

        # 3️⃣ Per-page items
        page_items = data.get("pagewise_line_items", [])

        if not page_items:
            logger.error(f"{name} ❌ No pagewise_line_items found.")
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
            else:
                logger.info("✅ All extracted items match expected list EXACTLY!")

        # 4️⃣ Final Pass/Fail
        count_match = extracted_count == expected_count
        total_match = abs(extracted_total - expected_total) < 0.01

        if count_match and total_match:
            logger.info(f"\n{name} PASSED ✅\n")
        else:
            logger.warning(f"\n{name} FAILED ❌ : Mismatch in count or total\n")

    except Exception as e:
        logger.error(f"{name} Error: {e}")


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
            "total_item_count": 4,
            "reconciled_amount": 1699.84
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
            "total_item_count": 30,
            "reconciled_amount": 21800.00
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
            "total_item_count": 12,
            "reconciled_amount": 16390.00
        }
    }

    # Run Tests
    test_extraction("Sample 3 (Pharmacy – 4 items)", sample_pharmacy_url, sample_pharmacy_expected)
    print("-" * 80)

    test_extraction("Sample 1 (Hospital – 30 items)", sample_hospital_large_url, sample_hospital_large_expected)
    print("-" * 80)

    test_extraction("Sample 2 (Consultation + Ward – 12 items)", sample_consultation_url, sample_consultation_expected)
    print("-" * 80)
