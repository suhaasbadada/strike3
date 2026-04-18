from pydantic import BaseModel
from typing import Any

class OcrResponse(BaseModel):
    text: str
    latency: int

class ProcessImageResponse(BaseModel):
    ocr_text: str
    ocr_latency: int
    compression: Any
    decompression: Any
    verification: Any
    total_latency: int
