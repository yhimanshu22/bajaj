import sys
import os

# Add current directory to sys.path
sys.path.append(os.getcwd())

try:
    from app.main import app
    print("Successfully imported app.main")
except Exception as e:
    print(f"Failed to import app.main: {e}")
    sys.exit(1)
