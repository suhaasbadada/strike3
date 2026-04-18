from pydantic import BaseModel
from typing import Any

class CompressRequest(BaseModel):
    text: str


class CompressStep(BaseModel):
    index: int
    symbol: int | None
    char: str | None
    tree: dict[str, Any]


class HuffmanTreePayload(BaseModel):
    root: str | None
    structure: dict[str, Any] | None


class CompressResponse(BaseModel):
    compressed_data: str
    compression_ratio: float
    entropy: float
    encoding_efficiency: float
    original_size: int
    compressed_size: int
    latency: int
    huffman_tree: HuffmanTreePayload
    steps: list[CompressStep]

class DecompressRequest(BaseModel):
    compressed_data: str

class DecompressResponse(BaseModel):
    text: str
    latency: int

class VerifyRequest(BaseModel):
    original_text: str
    decompressed_text: str

class VerifyResponse(BaseModel):
    is_lossless: bool
    char_match: int
    char_total: int
    match_percentage: float