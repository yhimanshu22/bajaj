import requests
import json
import logging
import sys
import os

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.schemas import BillExtractionResponse
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "http://127.0.0.1:8000/extract"

def test_extraction(name, url, expected_data):
    logger.info(f"Testing {name}...")
    
    payload = {"document": url}
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Basic Validation
        if not result.get("is_success"):
            logger.error(f"{name} FAILED: API returned is_success=False")
            return
            
        data = result.get("data", {})
        extracted_count = data.get("total_item_count")
        expected_count = expected_data["data"]["total_item_count"]
        
        extracted_total = data.get("reconciled_amount")
        expected_total = expected_data["data"]["reconciled_amount"]
        
        logger.info(f"{name} Results:")
        logger.info(f"  Item Count: Expected {expected_count}, Got {extracted_count}")
        logger.info(f"  Total Amount: Expected {expected_total}, Got {extracted_total}")
        logger.info(f"  Method: {result.get('flags', {}).get('extraction_method', 'Unknown')}")
        
        # Detailed Item Comparison (Optional - printing first few)
        logger.info(f"  First 3 Extracted Items: {data.get('pagewise_line_items', [])[0].get('bill_items', [])[:3] if data.get('pagewise_line_items') else 'None'}")
        
        if extracted_count == expected_count and abs(extracted_total - expected_total) < 1.0:
            logger.info(f"{name} PASSED ✅")
        else:
            logger.warning(f"{name} FAILED / MISMATCH ❌")

    except Exception as e:
        logger.error(f"{name} Error: {e}")

if __name__ == "__main__":
    # Test Case 1: Sample 2 (Medicines)
    sample_2_url = "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png?sv=2025-07-05&spr=https&st=2025-11-24T14%3A13%3A22Z&se=2026-11-25T14%3A13%3A00Z&sr=b&sp=r&sig=WFJYfNw0PJdZOpOYlsoAW0XujYGG1x2HSbcDREiFXSU%3D"
    sample_2_expected = {
        "data": {
            "total_item_count": 4,
            "reconciled_amount": 1699.84
        }
    }
    
    # Test Case 2: Sample 1 (Hospital Bill)
    sample_1_url = "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_1.png?sv=2025-07-05&spr=https&st=2025-11-24T14%3A21%3A03Z&se=2026-11-25T14%3A21%3A00Z&sr=b&sp=r&sig=2szJobwLVzcVSmg5IPWjRT9k7pHq2Tvifd6seRa2xRI%3D"
    sample_1_expected = {
        "data": {
            "total_item_count": 30,
            "reconciled_amount": 21800.00
        }
    }

    test_extraction("Sample 2 (Medicines)", sample_2_url, sample_2_expected)
    print("-" * 50)
    test_extraction("Sample 1 (Hospital)", sample_1_url, sample_1_expected)
