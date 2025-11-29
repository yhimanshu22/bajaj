# Bill Extraction API

A robust API to extract line items and totals from scanned bills and invoices using Google Gemini Vision.

## Features
- **Input**: Supports PDF, JPEG, PNG.
- **Extraction**: Powered by Google Gemini 1.5 Flash Vision.

## Differentiators
- **Adaptive Image Enhancement**: Automatically enhances contrast and sharpness of uploaded images to improve OCR accuracy on low-quality documents.
- **AI-Powered Fraud Detection**: Detects suspicious elements like inconsistent fonts, digital tampering, or whitener usage.
- **Total Amount Validation**: Automatically cross-references the printed total against the sum of individual line items to detect calculation fraud (e.g., inflated totals).
- **Latency Optimization**: Smart image resizing and compression to reduce payload size and speed up AI processing without compromising accuracy.
- **In-Memory Caching**: Implements a TTL-based cache to instantly return results for previously processed documents, making repeat requests lightning fast.

## Requirements
- Python 3.8+
- Google Gemini API Key

## Installation

1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate   # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   Create a `.env` file:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Deployment
### Backend (Render/Railway)
**Current Deployment:** [https://medbill-g3hr.onrender.com/](https://medbill-g3hr.onrender.com/)

1.  Push code to GitHub.
2.  Connect repository to **Render** (Web Service).
3.  Set Build Command: `pip install -r requirements.txt`
4.  Set Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5.  Add Environment Variable: `GEMINI_API_KEY`

### Frontend (Streamlit Cloud)
1.  Connect repository to **Streamlit Cloud**.
2.  Select file: `frontend/dashboard.py`
3.  Add Environment Variable in Advanced Settings:
    -   `API_BASE_URL`: The URL of your deployed backend (e.g., `https://my-api.onrender.com`)

## Usage

1. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```
2. Send a POST request to `/extract-bill-data` with a JSON body:
   ```bash
   curl -X POST "http://127.0.0.1:8000/extract-bill-data" \
     -H "Content-Type: application/json" \
     -d '{"document": "https://example.com/bill.jpg"}'
   ```

## API Response
Returns a JSON object with:
- `is_success`: Boolean indicating success
- `data`: Object containing:
  - `pagewise_line_items`: List of pages with items
  - `total_item_count`: Total number of items
  - `reconciled_amount`: Sum of item amounts
