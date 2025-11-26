import httpx
import tempfile
import os

from typing import Tuple

async def download_file(url: str) -> Tuple[bytes, str]:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content, response.headers.get("content-type", "application/octet-stream")
