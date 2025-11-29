import httpx
import tempfile
import os
import mimetypes
from urllib.parse import urlparse
from typing import Tuple

async def download_file(url: str) -> Tuple[bytes, str]:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        
        mime_type = response.headers.get("content-type", "application/octet-stream")
        
        # If generic binary type, try to guess from URL extension
        if mime_type == "application/octet-stream":
            parsed_url = urlparse(url)
            path = parsed_url.path
            guessed_type, _ = mimetypes.guess_type(path)
            if guessed_type:
                mime_type = guessed_type
                
        return response.content, mime_type
