import re
import time

from fastapi import APIRouter, HTTPException

from app.schemas.compression_schema import (
    CompressStep,
    CompressRequest,
    CompressResponse,
    DecompressRequest,
    DecompressResponse,
    HuffmanTreePayload,
    VerifyRequest,
    VerifyResponse,
)

from app.services.adaptive_huffman import AdaptiveHuffman
from utils.compression_utils import (
    bitstring_to_bytes,
    bytes_to_bitstring,
    entropy_from_text,
    get_text_match_stats,
)

router = APIRouter(tags=["compression"])

@router.post("/compress", response_model=CompressResponse)
def compress_text(payload: CompressRequest) -> CompressResponse:
    start = time.perf_counter()
    codec = AdaptiveHuffman()
    step_codec = AdaptiveHuffman()

    compressed_bytes = codec.encode(payload.text)
    compressed_data = bytes_to_bitstring(compressed_bytes)

    original_size = len(payload.text.encode("utf-8"))
    compressed_size = len(compressed_bytes)
    compression_ratio = (original_size / compressed_size) if compressed_size else 0.0

    entropy = entropy_from_text(payload.text)
    theoretical_min_bits = entropy * original_size
    compressed_bits = compressed_size * 8
    encoding_efficiency = (
        (theoretical_min_bits / compressed_bits) * 100 if compressed_bits else 0.0
    )

    step_result = step_codec.encode_with_steps(payload.text)
    steps = [CompressStep(**step) for step in step_result["steps"]]

    final_tree = step_result["steps"][-1]["tree"] if step_result["steps"] else {"nodes": [], "edges": []}
    final_nodes = final_tree.get("nodes", []) if isinstance(final_tree, dict) else []
    root_label = final_nodes[0].get("label") if final_nodes else None

    latency_ms = int((time.perf_counter() - start) * 1000)

    return CompressResponse(
        compressed_data=compressed_data,
        compression_ratio=round(compression_ratio, 2),
        entropy=round(entropy, 2),
        encoding_efficiency=round(encoding_efficiency, 2),
        original_size=original_size,
        compressed_size=compressed_size,
        latency=latency_ms,
        huffman_tree=HuffmanTreePayload(root=root_label, structure=final_tree),
        steps=steps,
    )

@router.post("/decompress", response_model=DecompressResponse)
def decompress_text(payload: DecompressRequest) -> DecompressResponse:
    if not re.fullmatch(r"[01]*", payload.compressed_data):
        raise HTTPException(status_code=400, detail="compressed_data must contain only 0 and 1")

    try:
        compressed_bytes = bitstring_to_bytes(payload.compressed_data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid compressed_data") from exc

    start = time.perf_counter()
    codec = AdaptiveHuffman()
    decoded_text = codec.decode(compressed_bytes)
    latency_ms = int((time.perf_counter() - start) * 1000)

    return DecompressResponse(text=decoded_text, latency=latency_ms)

@router.post("/verify", response_model=VerifyResponse)
def verify_text(payload: VerifyRequest) -> VerifyResponse:
    original_text = payload.original_text
    decompressed_text = payload.decompressed_text

    char_match, char_total, match_percentage = get_text_match_stats(
        original_text,
        decompressed_text,
    )

    return VerifyResponse(
        is_lossless=original_text == decompressed_text,
        char_match=char_match,
        char_total=char_total,
        match_percentage=match_percentage,
    )
