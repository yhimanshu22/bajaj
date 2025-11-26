import requests
import json

API_URL = "http://127.0.0.1:8000/extract-bill-data"
sample_pharmacy_url = (
    "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png"
    "?sv=2025-07-05&spr=https&st=2025-11-24T14%3A13%3A22Z&se=2026-11-25T14%3A13%3A00Z"
    "&sr=b&sp=r&sig=WFJYfNw0PJdZOpOYlsoAW0XujYGG1x2HSbcDREiFXSU%3D"
)

payload = {"document": sample_pharmacy_url}
try:
    response = requests.post(API_URL, json=payload)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(e)
    if hasattr(e, 'response'):
        print(e.response.text)
