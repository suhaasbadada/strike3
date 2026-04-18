from collections import Counter
from math import log2

def entropy_from_text(text: str) -> float:
    data = text.encode("utf-8")
    if not data:
        return 0.0

    total = len(data)
    counts = Counter(data)

    entropy = 0.0
    for count in counts.values():
        probability = count / total
        entropy -= probability * log2(probability)

    return round(entropy, 6)

def bytes_to_bitstring(data: bytes) -> str:
    return "".join(f"{byte:08b}" for byte in data)

def bitstring_to_bytes(bitstring: str) -> bytes:
    if len(bitstring) % 8 != 0:
        raise ValueError("Bitstring length must be a multiple of 8")
    return bytes(int(bitstring[i:i + 8], 2) for i in range(0, len(bitstring), 8))

def get_text_match_stats(original_text: str, decompressed_text: str) -> tuple[int, int, float]:
    char_match = sum(1 for a, b in zip(original_text, decompressed_text) if a == b)
    char_total = len(original_text)
    match_percentage = (char_match / char_total * 100) if char_total else 100.0

    return char_match, char_total, round(match_percentage, 2)
