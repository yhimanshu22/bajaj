import google.generativeai as genai
import os

# 1. Setup API Key
api_key = "AIzaSyCESwO709JbqKOfVzfkuMzVXu7mMnBHYdQ"
genai.configure(api_key=api_key)

print("--- Available Models (v1beta) ---")
try:
    # 2. List models. This automatically hits the v1beta endpoint.
    for m in genai.list_models():
        # Optional: Filter for only 'generateContent' models (chat/text/vision)
        if 'generateContent' in m.supported_generation_methods:
            print(f"Name: {m.name}")
            print(f"   Display: {m.display_name}")
            print(f"   Version: {m.version}")
            print("-" * 30)
            
except Exception as e:
    print(f"Error listing models: {e}")