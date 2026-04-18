import base64
import io
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel
from torchvision import transforms

from model_printed import load_printed_model, label_to_char
from postprocess import clean, load_vocab

app = FastAPI(title="Strike3 OCR Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ocr_model = None
vocab     = set()

WEIGHTS_PATH = Path("./weights/printed_cnn.pth")
CSV_PATH     = Path("./SimulatedNoisyOffice/tesseract_metadata.csv")
TRANSFORM    = transforms.ToTensor()


@app.on_event("startup")
def load_models():
    global ocr_model, vocab
    if WEIGHTS_PATH.exists():
        ocr_model = load_printed_model(str(WEIGHTS_PATH), device)
        print(f"Model loaded from {WEIGHTS_PATH}")
    else:
        print(f"WARNING: weights not found at {WEIGHTS_PATH}")
    vocab = load_vocab(str(CSV_PATH))


# Request / Response

class OCRRequest(BaseModel):
    image: str
    noise_type: str = "auto"


class OCRResponse(BaseModel):
    text: str
    text_raw: str
    text_layer1: str
    confidence: float
    char_count: int
    noise_type_detected: str
    latency_ms: float


# Endpoints

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": ocr_model is not None,
        "vocab_size": len(vocab),
        "device": str(device),
    }


@app.post("/ocr", response_model=OCRResponse)
def ocr(request: OCRRequest):
    if ocr_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        image_bytes = base64.b64decode(request.image)
        pil_image   = Image.open(io.BytesIO(image_bytes)).convert("L")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image")

    if pil_image.width < 10 or pil_image.height < 10:
        raise HTTPException(status_code=400, detail="Image too small")
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image too large (max 10MB)")

    gray = np.array(pil_image, dtype=np.uint8)
    t_start = time.perf_counter()

    binary = _preprocess(gray)
    crops, space_flags, line_indices = _get_all_crops(binary)

    if not crops:
        return OCRResponse(
            text="", text_raw="", text_layer1="",
            confidence=0.0, char_count=0,
            noise_type_detected=_detect_noise(request.noise_type, gray),
            latency_ms=round((time.perf_counter() - t_start) * 1000, 2),
        )

    labels, confidences = _classify_crops(crops)
    raw_text = _assemble_text(labels, space_flags, line_indices)
    result   = clean(raw_text, vocab, spell=False)

    return OCRResponse(
        text=result["layer2"],
        text_raw=result["raw"],
        text_layer1=result["layer1"],
        confidence=round(float(np.mean(confidences)), 4),
        char_count=len(labels),
        noise_type_detected=_detect_noise(request.noise_type, gray),
        latency_ms=round((time.perf_counter() - t_start) * 1000, 2),
    )


# Pipeline helpers

def _preprocess(gray: np.ndarray) -> np.ndarray:
    if gray.mean() < 127:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary


def _find_lines(binary: np.ndarray) -> list[tuple[int, int]]:
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


def _find_chunks(binary, y_start, y_end):
    strip = binary[y_start:y_end, :]
    num_labels, _, stats, centroids = cv2.connectedComponentsWithStats(strip, connectivity=8)
    strip_area = strip.shape[0] * strip.shape[1]
    chunks = []
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        cx, cy = centroids[i]
        if area < 20 or area > strip_area * 0.8 or w < 2 or h < 2:
            continue
        chunks.append({"x": int(x), "y": int(y)+y_start, "w": int(w), "h": int(h),
                       "cx": float(cx), "cy": float(cy)+y_start, "area": int(area)})
    return sorted(chunks, key=lambda c: c["x"])


def _find_valleys(v_proj):
    v_smooth = np.convolve(v_proj, np.ones(5)/5, mode="same")
    return [(i, float(v_smooth[i])) for i in range(1, len(v_smooth)-1)
            if v_smooth[i] < v_smooth[i-1] and v_smooth[i] < v_smooth[i+1]]


def _multi_split(binary, blob, expected_w):
    x, y, w, h = blob["x"], blob["y"], blob["w"], blob["h"]
    crop = binary[y:y+h, x:x+w]
    v_proj = crop.sum(axis=0).astype(np.float32)
    max_proj = v_proj.max() if v_proj.max() > 0 else 1
    valleys = [(i, v) for i, v in _find_valleys(v_proj) if v < 0.35 * max_proj]
    if not valleys:
        return [blob]
    min_sep = max(int(expected_w * 0.4), 4)
    filtered = [valleys[0]]
    for v in valleys[1:]:
        if v[0] - filtered[-1][0] >= min_sep:
            filtered.append(v)
    boundaries = [0] + sorted(v[0] for v in filtered) + [w]
    pieces = []
    for i in range(len(boundaries)-1):
        c0, c1 = boundaries[i], boundaries[i+1]
        pw = c1 - c0
        if pw < 2:
            continue
        p = {"x": x+c0, "y": y, "w": pw, "h": h,
             "cx": x+c0+pw/2, "cy": y+h/2, "area": int(crop[:, c0:c1].sum())}
        seg = binary[p["y"]:p["y"]+p["h"], p["x"]:p["x"]+p["w"]]
        if p["w"] >= expected_w * 0.3 and (seg > 0).sum() / max(seg.size, 1) >= 0.03:
            pieces.append(p)
    return pieces if len(pieces) >= 2 else [blob]


def _normalize_crop(crop: np.ndarray) -> np.ndarray:
    rows = np.any(crop > 0, axis=1)
    cols = np.any(crop > 0, axis=0)
    if rows.any() and cols.any():
        r0, r1 = np.where(rows)[0][[0, -1]]
        c0, c1 = np.where(cols)[0][[0, -1]]
        crop = crop[r0:r1+1, c0:c1+1]
    if crop.size == 0:
        return np.zeros((28, 28), dtype=np.uint8)
    margin = 3
    ch, cw = crop.shape
    size = max(ch, cw) + margin * 2
    padded = np.zeros((size, size), dtype=np.uint8)
    padded[(size-ch)//2:(size-ch)//2+ch, (size-cw)//2:(size-cw)//2+cw] = crop
    return cv2.resize(padded, (28, 28), interpolation=cv2.INTER_AREA)


def _detect_spaces(blobs):
    flags = [False] * len(blobs)
    if len(blobs) <= 1:
        return flags
    median_w = float(np.median([b["w"] for b in blobs]))
    for i in range(1, len(blobs)):
        gap = blobs[i]["x"] - (blobs[i-1]["x"] + blobs[i-1]["w"])
        flags[i] = gap > median_w * 0.5
    return flags


def _get_all_crops(binary):
    lines = _find_lines(binary)
    all_crops, all_spaces, all_lines = [], [], []
    for line_idx, (y_start, y_end) in enumerate(lines):
        chunks = _find_chunks(binary, y_start, y_end)
        if not chunks:
            continue
        widths = sorted(c["w"] for c in chunks)
        expected_w = float(np.median(widths[:max(1, len(widths)//2)]))
        median_h   = float(np.median([c["h"] for c in chunks]))
        final = []
        for blob in chunks:
            if blob["w"] > expected_w * 1.6 or (median_h > 0 and blob["w"]/blob["h"] > 1.0):
                final.extend(_multi_split(binary, blob, expected_w))
            else:
                final.append(blob)
        final = sorted(final, key=lambda b: b["x"])
        for blob, is_space in zip(final, _detect_spaces(final)):
            x, y, w, h = blob["x"], blob["y"], blob["w"], blob["h"]
            normalized = _normalize_crop(binary[y:y+h, x:x+w])
            all_crops.append(normalized)
            all_spaces.append(is_space)
            all_lines.append(line_idx)
    return all_crops, all_spaces, all_lines


def _classify_crops(crops):
    tensors = [TRANSFORM(Image.fromarray(c, mode="L")) for c in crops]
    batch = torch.stack(tensors).to(device)
    ocr_model.eval()
    with torch.no_grad():
        probs = torch.softmax(ocr_model(batch), dim=1)
        confs = probs.max(dim=1).values.cpu().tolist()
        idxs  = probs.argmax(dim=1).cpu().tolist()
    return [label_to_char(i) for i in idxs], confs


def _assemble_text(labels, space_flags, line_indices):
    if not labels:
        return ""
    lines, current_line, current = [], line_indices[0], ""
    for label, is_space, line_idx in zip(labels, space_flags, line_indices):
        if line_idx != current_line:
            lines.append(current)
            current, current_line = "", line_idx
        if is_space:
            current += " "
        current += label
    lines.append(current)
    return "\n".join(lines)


def _detect_noise(requested: str, gray: np.ndarray) -> str:
    if requested in ("gaussian", "salt_pepper"):
        return requested
    flat = gray.flatten().astype(np.float32)
    return "salt_pepper" if ((flat < 10) | (flat > 245)).sum() / len(flat) > 0.05 else "gaussian"
