import os
import sys
import uvicorn
from pyngrok import ngrok
from dotenv import load_dotenv
import threading
import time

# Load environment variables
load_dotenv()

def start_ngrok():
    # Open a HTTP tunnel on the default port 8000
    # <NgrokTunnel: "http://<public_sub>.ngrok.io" -> "http://localhost:8000">
    public_url = ngrok.connect(8000).public_url
    print(f" * ngrok tunnel \"{public_url}\" -> \"http://127.0.0.1:8000\"")
    
    # Update .env file with the new URL
    env_path = ".env"
    # Read existing lines
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
            
    # Filter out existing API_BASE_URL
    lines = [line for line in lines if not line.startswith("API_BASE_URL=")]
    
    # Add new URL
    lines.append(f"API_BASE_URL={public_url}\n")
    
    with open(env_path, "w") as f:
        f.writelines(lines)
    
    print(f" * Updated API_BASE_URL in {env_path}")

def main():
    # Start ngrok in a separate thread or just before uvicorn if we want to print it
    # But uvicorn blocks, so we need to start ngrok first or in parallel.
    # Actually, we can just start ngrok, print the URL, and then start uvicorn.
    
    # Set auth token if available in env, otherwise it might fail or be anonymous (which has limits)
    ngrok_auth_token = os.getenv("NGROK_AUTH_TOKEN")
    if ngrok_auth_token:
        ngrok.set_auth_token(ngrok_auth_token)
    
    start_ngrok()
    
    # Start Uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
