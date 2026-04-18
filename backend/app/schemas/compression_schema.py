from pydantic import BaseModel

class CompressRequest(BaseModel):
    text: str

class CompressResponse(BaseModel):
    compressed_data: str
    compression_ratio: float
    entropy: float
    encoding_efficiency: float
    original_size: int
    compressed_size: int
    latency: int

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