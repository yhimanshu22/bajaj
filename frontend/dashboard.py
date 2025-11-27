import streamlit as st
import requests
import json
from PIL import Image
import io

import os

# Configure page
st.set_page_config(page_title="Bill Extractor", layout="wide")

st.title("🧾 Bill Extraction Dashboard")

# Sidebar configuration
st.sidebar.header("Configuration")

# Get default from env or use localhost
default_url = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
base_url = st.sidebar.text_input("API Base URL", default_url)

# Create tabs
tab1, tab2 = st.tabs(["📁 Upload File", "🔗 Enter URL"])

def display_results(result):
    if result.get("is_success"):
        st.success("Extraction Successful!")
        
        data = result.get("data", {})
        
        # Fraud Detection Display
        fraud = data.get("fraud_signals", {})
        if fraud and fraud.get("is_suspicious"):
            st.error("🚨 POTENTIAL FRAUD DETECTED")
            for warning in fraud.get("warnings", []):
                st.markdown(f":red[**⚠️ {warning}**]")
        else:
            st.success("✅ No Fraud Detected")

        col1, col2 = st.columns(2)
        col1.metric("Total Items", data.get("total_item_count", 0))
        col2.metric("Total Amount", f"{data.get('reconciled_amount', 0.0):.2f}")
        
        st.subheader("Extracted Data (JSON)")
        st.json(data)
        
        st.subheader("Line Items Detail")
        items = []
        for page in data.get("pagewise_line_items", []):
            for item in page.get("bill_items", []):
                items.append(item)
        
        if items:
            st.table(items)
    else:
        st.error("Extraction failed.")

# --- Tab 1: File Upload ---
with tab1:
    st.markdown("Upload a local bill image or PDF.")
    uploaded_file = st.file_uploader("Choose a file", type=['png', 'jpg', 'jpeg', 'pdf'])
    
    if uploaded_file is not None:
        if uploaded_file.type.startswith('image'):
            image = Image.open(uploaded_file)
            st.image(image, caption='Uploaded Bill', use_column_width=True)
        elif uploaded_file.type == 'application/pdf':
            st.info("PDF uploaded. Preview not available.")

        if st.button("Extract from File"):
            with st.spinner("Extracting..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{base_url}/extract-from-file", files=files)
                    response.raise_for_status()
                    display_results(response.json())
                except Exception as e:
                    st.error(f"Error: {e}")

# --- Tab 2: URL Input ---
with tab2:
    st.markdown("Enter a URL to a bill image or PDF.")
    url_input = st.text_input("Document URL", "https://example.com/bill.jpg")
    
    if st.button("Extract from URL"):
        with st.spinner("Extracting..."):
            try:
                payload = {"document": url_input}
                response = requests.post(f"{base_url}/extract-bill-data", json=payload)
                response.raise_for_status()
                display_results(response.json())
            except Exception as e:
                st.error(f"Error: {e}")
