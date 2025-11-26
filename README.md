# Bill Extraction API

A robust API to extract line items and totals from scanned bills and invoices using Google Gemini Vision.

## Features
- **Input**: Supports PDF, JPEG, PNG.
- **Extraction**: Powered by Google Gemini 1.5 Flash Vision.

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
