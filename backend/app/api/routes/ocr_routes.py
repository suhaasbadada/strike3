import csv
import io
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from app.api.routes.compression_routes import compress_text, decompress_text, verify_text
from app.schemas.compression_schema import CompressRequest, DecompressRequest, VerifyRequest
from app.schemas.ocr_schema import OcrResponse, ProcessImageResponse

torch.set_num_threads(max(1, torch.get_num_threads()))

EMNIST_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabdefghnqrt"


class PrintedCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
        )
        self.conv3 = nn.Sequential(
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
        )
        self.conv4 = nn.Sequential(
            nn.Conv2d(128, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256 * 3 * 3, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, len(EMNIST_CHARS)),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        return self.classifier(x)


CHAR_RULES = [
    (r"(?<=[a-zA-Z])0(?=[a-zA-Z])", "o"),
    (r"(?<=[a-zA-Z])1(?=[a-zA-Z])", "l"),
    (r"(?<=[a-z])I(?=[a-z])", "l"),
    (r"(?<=[a-z])S(?=[a-z])", "s"),
    (r"(?<=[a-z])O(?=[a-z])", "o"),
    (r"(?<=[a-z])C(?=[a-z])", "c"),
    (r"(?<=[a-z])U(?=[a-z])", "u"),
    (r"(?<=[a-z])M(?=[a-z])", "m"),
    (r"(?<=[a-z])N(?=[a-z])", "n"),
    (r"(?<=[a-z])B(?=[a-z])", "b"),
    (r"(?<=[a-z])D(?=[a-z])", "d"),
    (r"(?<=[a-z])F(?=[a-z])", "f"),
    (r"(?<=[a-z])G(?=[a-z])", "g"),
    (r"(?<=[a-z])H(?=[a-z])", "h"),
    (r"(?<=[a-z])R(?=[a-z])", "r"),
    (r"(?<=[a-z])T(?=[a-z])", "t"),
    (r"(?<=[a-z])V(?=[a-z])", "v"),
    (r"(?<=[a-z])W(?=[a-z])", "w"),
    (r"(?<=[a-z])X(?=[a-z])", "x"),
    (r"(?<=[a-z])Y(?=[a-z])", "y"),
    (r"rn", "m"),
    (r"vv", "w"),
    (r"VV", "W"),
]

_OCR_MODEL = None
_OCR_VOCAB: set[str] = set()
_OCR_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _label_to_char(idx: int) -> str:
    if 0 <= idx < len(EMNIST_CHARS):
        return EMNIST_CHARS[idx]
    return "?"


def _get_ocr_paths() -> Tuple[Path, Path]:
    backend_root = Path(__file__).resolve().parents[3]
    pth_root = backend_root / "pth"
    model_path = Path(os.getenv("OCR_PRINTED_MODEL_PATH", str(pth_root / "printed_cnn.pth")))
    csv_path = Path(
        os.getenv(
            "OCR_VOCAB_CSV_PATH",
            str(backend_root / "SimulatedNoisyOffice" / "tesseract_metadata.csv"),
        )
    )
    return model_path, csv_path


def _load_vocab(csv_path: Path) -> set[str]:
    vocab: set[str] = set()
    if not csv_path.exists():
        return vocab

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            text = row.get("text", "")
            words = re.findall(r"[a-zA-Z']+", text)
            for word in words:
                token = word.strip("'").lower()
                if len(token) >= 2:
                    vocab.add(token)
    return vocab


def _load_ocr_once() -> Tuple[nn.Module, set[str], torch.device]:
    global _OCR_MODEL, _OCR_VOCAB
    if _OCR_MODEL is not None:
        return _OCR_MODEL, _OCR_VOCAB, _OCR_DEVICE

    model_path, csv_path = _get_ocr_paths()
    if not model_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {model_path}")

    model = PrintedCNN().to(_OCR_DEVICE)
    state_dict = torch.load(model_path, map_location=_OCR_DEVICE)
    model.load_state_dict(state_dict)
    model.eval()

    _OCR_MODEL = model
    _OCR_VOCAB = _load_vocab(csv_path)
    return _OCR_MODEL, _OCR_VOCAB, _OCR_DEVICE


def _preprocess(gray: np.ndarray) -> np.ndarray:
    if gray.mean() < 127:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary


def _find_lines(binary: np.ndarray) -> List[Tuple[int, int]]:
    h_proj = binary.sum(axis=1)
    threshold = binary.shape[1] * 0.01
    in_line, lines, y_start = False, [], 0
    for y, val in enumerate(h_proj):
        if not in_line and val > threshold:
            in_line, y_start = True, y
        elif in_line and val <= threshold:
            in_line = False
            if y - y_start > 5:
                lines.append((y_start, y))
    if in_line:
        lines.append((y_start, len(h_proj)))
    return lines


def _find_chunks(binary: np.ndarray, y_start: int, y_end: int) -> List[Dict[str, float]]:
    strip = binary[y_start:y_end, :]
    num_labels, _, stats, centroids = cv2.connectedComponentsWithStats(strip, connectivity=8)
    strip_area = strip.shape[0] * strip.shape[1]
    chunks: List[Dict[str, float]] = []
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        cx, cy = centroids[i]
        if area < 20 or area > strip_area * 0.8 or w < 2 or h < 2:
            continue
        chunks.append(
            {
                "x": int(x),
                "y": int(y) + y_start,
                "w": int(w),
                "h": int(h),
                "cx": float(cx),
                "cy": float(cy) + y_start,
                "area": int(area),
            }
        )
    return sorted(chunks, key=lambda c: c["x"])


def _find_valleys(v_proj: np.ndarray) -> List[Tuple[int, float]]:
    v_smooth = np.convolve(v_proj, np.ones(3) / 3, mode="same")
    valleys = []
    for i in range(1, len(v_smooth) - 1):
        if v_smooth[i] < v_smooth[i - 1] and v_smooth[i] < v_smooth[i + 1]:
            valleys.append((i, float(v_smooth[i])))
    return valleys


def _validate_piece(piece: Dict[str, float], expected_w: float, binary: np.ndarray) -> bool:
    if piece["w"] < expected_w * 0.3:
        return False
    x, y, w, h = int(piece["x"]), int(piece["y"]), int(piece["w"]), int(piece["h"])
    crop = binary[y : y + h, x : x + w]
    return (crop > 0).sum() / max(crop.size, 1) >= 0.03


def _multi_split(binary: np.ndarray, blob: Dict[str, float], expected_w: float) -> List[Dict[str, float]]:
    x, y, w, h = int(blob["x"]), int(blob["y"]), int(blob["w"]), int(blob["h"])
    crop = binary[y : y + h, x : x + w]
    v_proj = crop.sum(axis=0).astype(np.float32)
    max_proj = v_proj.max() if v_proj.max() > 0 else 1
    all_valleys = [(i, v) for i, v in _find_valleys(v_proj) if v < 0.35 * max_proj]
    if not all_valleys:
        return [blob]

    min_sep = max(int(expected_w * 0.4), 4)
    filtered = [all_valleys[0]]
    for valley in all_valleys[1:]:
        if valley[0] - filtered[-1][0] >= min_sep:
            filtered.append(valley)

    boundaries = [0] + sorted(v[0] for v in filtered) + [w]
    pieces = []
    for i in range(len(boundaries) - 1):
        c0, c1 = boundaries[i], boundaries[i + 1]
        pw = c1 - c0
        if pw < 2:
            continue
        piece = {
            "x": x + c0,
            "y": y,
            "w": pw,
            "h": h,
            "cx": x + c0 + pw / 2,
            "cy": y + h / 2,
            "area": int(crop[:, c0:c1].sum()),
        }
        if _validate_piece(piece, expected_w, binary):
            pieces.append(piece)
    return pieces if len(pieces) >= 2 else [blob]


def _normalize_crop(crop: np.ndarray) -> np.ndarray:
    rows = np.any(crop > 0, axis=1)
    cols = np.any(crop > 0, axis=0)
    if rows.any() and cols.any():
        r0, r1 = np.where(rows)[0][[0, -1]]
        c0, c1 = np.where(cols)[0][[0, -1]]
        crop = crop[r0 : r1 + 1, c0 : c1 + 1]
    if crop.size == 0:
        return np.zeros((28, 28), dtype=np.uint8)

    margin = 3
    ch, cw = crop.shape
    size = max(ch, cw) + margin * 2
    padded = np.zeros((size, size), dtype=np.uint8)
    y_off = (size - ch) // 2
    x_off = (size - cw) // 2
    padded[y_off : y_off + ch, x_off : x_off + cw] = crop
    return cv2.resize(padded, (28, 28), interpolation=cv2.INTER_AREA)


def _detect_spaces(blobs: List[Dict[str, float]]) -> List[bool]:
    flags = [False] * len(blobs)
    if len(blobs) <= 1:
        return flags
    median_w = float(np.median([b["w"] for b in blobs]))
    for i in range(1, len(blobs)):
        gap = blobs[i]["x"] - (blobs[i - 1]["x"] + blobs[i - 1]["w"])
        flags[i] = gap > median_w * 0.5
    return flags


def _get_all_crops(binary: np.ndarray) -> Tuple[List[np.ndarray], List[bool], List[int]]:
    lines = _find_lines(binary)
    all_crops: List[np.ndarray] = []
    all_spaces: List[bool] = []
    all_lines: List[int] = []

    for line_idx, (y_start, y_end) in enumerate(lines):
        chunks = _find_chunks(binary, y_start, y_end)
        if not chunks:
            continue

        widths = sorted(c["w"] for c in chunks)
        expected_w = float(np.median(widths[: max(1, len(widths) // 2)]))
        median_h = float(np.median([c["h"] for c in chunks]))

        final_blobs = []
        for blob in chunks:
            if blob["w"] > expected_w * 1.6 or (median_h > 0 and blob["w"] / blob["h"] > 1.0):
                final_blobs.extend(_multi_split(binary, blob, expected_w))
            else:
                final_blobs.append(blob)

        final_blobs = sorted(final_blobs, key=lambda b: b["x"])
        space_flags = _detect_spaces(final_blobs)

        for blob, is_space in zip(final_blobs, space_flags):
            x, y, w, h = int(blob["x"]), int(blob["y"]), int(blob["w"]), int(blob["h"])
            raw = binary[y : y + h, x : x + w]
            all_crops.append(_normalize_crop(raw))
            all_spaces.append(is_space)
            all_lines.append(line_idx)

    return all_crops, all_spaces, all_lines


def _classify_crops(crops: List[np.ndarray], model: nn.Module, device: torch.device) -> Tuple[List[str], List[float]]:
    tensors = []
    for crop in crops:
        # Match torchvision.transforms.ToTensor() behavior for grayscale arrays.
        arr = crop.astype(np.float32) / 255.0
        tensors.append(torch.from_numpy(arr).unsqueeze(0))

    batch = torch.stack(tensors).to(device)
    model.eval()
    with torch.no_grad():
        probs = torch.softmax(model(batch), dim=1)

    confs = probs.max(dim=1).values.cpu().tolist()
    idxs = probs.argmax(dim=1).cpu().tolist()
    return [_label_to_char(i) for i in idxs], confs


def _assemble_text(labels: List[str], space_flags: List[bool], line_indices: List[int]) -> str:
    if not labels:
        return ""
    text_lines: List[str] = []
    current_line = line_indices[0] if line_indices else 0
    current = ""

    for label, is_space, line_idx in zip(labels, space_flags, line_indices):
        if line_idx != current_line:
            text_lines.append(current)
            current = ""
            current_line = line_idx
        if is_space:
            current += " "
        current += label
    text_lines.append(current)
    return "\n".join(text_lines)


def _apply_char_rules(text: str) -> str:
    out = text
    for pattern, replacement in CHAR_RULES:
        out = re.sub(pattern, replacement, out)
    return out


def _edit_distance(a: str, b: str) -> int:
    if len(a) < len(b):
        return _edit_distance(b, a)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]


def _fuzzy_match(word: str, vocab: set[str], max_dist: int = 2) -> str | None:
    word_lower = word.lower()
    if word_lower in vocab:
        return None
    if len(word_lower) < 4:
        return None

    best_word = None
    best_dist = max_dist + 1
    for candidate in vocab:
        if abs(len(candidate) - len(word_lower)) > max_dist:
            continue
        dist = _edit_distance(word_lower, candidate)
        if dist < best_dist:
            best_dist = dist
            best_word = candidate
        elif dist == best_dist:
            best_word = None

    if best_word and best_dist <= max_dist:
        return best_word.capitalize() if word[:1].isupper() else best_word
    return None


def _apply_domain_correction(text: str, vocab: set[str]) -> str:
    if not vocab:
        return text

    corrected_lines = []
    for line in text.split("\n"):
        tokens = line.split(" ")
        out_tokens = []
        for token in tokens:
            stripped = re.sub(r"[^a-zA-Z]", "", token)
            if len(stripped) >= 4:
                fix = _fuzzy_match(stripped, vocab, max_dist=2)
                if fix:
                    token = token.replace(stripped, fix)
            out_tokens.append(token)
        corrected_lines.append(" ".join(out_tokens))

    return "\n".join(corrected_lines)


def _clean_text(raw_text: str, vocab: set[str]) -> str:
    layer1 = _apply_char_rules(raw_text)
    layer2 = _apply_domain_correction(layer1, vocab)
    return layer2


def _recognize_image_bytes(payload: bytes) -> str:
    model, vocab, device = _load_ocr_once()
    image = Image.open(io.BytesIO(payload)).convert("L")
    gray = np.array(image, dtype=np.uint8)

    binary = _preprocess(gray)
    crops, space_flags, line_indices = _get_all_crops(binary)
    if not crops:
        return ""

    labels, _ = _classify_crops(crops, model, device)
    raw_text = _assemble_text(labels, space_flags, line_indices)
    return _clean_text(raw_text, vocab)

router = APIRouter(tags=["ocr"])

@router.post("/ocr", response_model=OcrResponse)
async def extract_text(file: UploadFile = File(...)):
    start = time.perf_counter()
    contents = await file.read()
    try:
        text = _recognize_image_bytes(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    latency_ms = int((time.perf_counter() - start) * 1000)
    return OcrResponse(text=text, latency=latency_ms)

@router.post("/process-image", response_model=ProcessImageResponse)
async def process_image_pipeline(file: UploadFile = File(...)):
    start_total = time.perf_counter()
    
    # 1. OCR
    ocr_start = time.perf_counter()
    contents = await file.read()
    try:
        text = _recognize_image_bytes(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    ocr_latency = int((time.perf_counter() - ocr_start) * 1000)

    if not text:
        text = "EMPTY_TEXT"
        
    # 2. Compress
    compress_req = CompressRequest(text=text)
    compress_res = compress_text(compress_req)
    
    # 3. Decompress
    decompress_req = DecompressRequest(compressed_data=compress_res.compressed_data)
    decompress_res = decompress_text(decompress_req)
    
    # 4. Verify
    verify_req = VerifyRequest(original_text=text, decompressed_text=decompress_res.text)
    verify_res = verify_text(verify_req)
    
    total_latency = int((time.perf_counter() - start_total) * 1000)
    
    return ProcessImageResponse(
        ocr_text=text,
        ocr_latency=ocr_latency,
        compression=compress_res,
        decompression=decompress_res,
        verification=verify_res,
        total_latency=total_latency
    )
