# Bill Extraction API

A robust API to extract line items and totals from scanned bills and invoices.

## Features
- **Input**: Supports PDF, JPEG, PNG.
- **Preprocessing**: Denoising and grayscale conversion using OpenCV.
- **OCR**: Text extraction using Tesseract.
- **Extraction**: Heuristic-based parsing of line items and totals.

## Requirements
- Python 3.8+
- Tesseract OCR (`sudo apt install tesseract-ocr`)
- Poppler Utils (`sudo apt install poppler-utils`) - Required for PDF processing.

## Installation

1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```
2. Send a POST request to `/extract` with a file:
   ```bash
   curl -X POST "http://127.0.0.1:8000/extract" -F "file=@/path/to/bill.jpg"
   ```

## API Response
Returns a JSON object with:
- `bill_id`: Unique ID
- `line_items`: List of extracted items
- `subtotals`: Detected subtotals
- `final_total`: Final bill amount
- `flags`: Metadata and warnings
