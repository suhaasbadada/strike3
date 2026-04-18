import time
import io
import os
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn

torch.set_num_threads(max(1, torch.get_num_threads()))
from PIL import Image
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.ocr_schema import OcrResponse, ProcessImageResponse
from app.api.routes.compression_routes import compress_text, decompress_text, verify_text
from app.schemas.compression_schema import CompressRequest, DecompressRequest, VerifyRequest

class CRNN(nn.Module):
    def __init__(self, num_classes: int, hidden_size: int = 256):
        super().__init__()

        self.cnn = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(256, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),
            nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(4, 1), stride=(4, 1)),
        )
        self.rnn = nn.LSTM(
            input_size=512,
            hidden_size=hidden_size,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.2,
        )
        self.classifier = nn.Linear(hidden_size * 2, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.cnn(x)
        features = features.squeeze(2)
        features = features.permute(0, 2, 1)
        rnn_out, _ = self.rnn(features)
        return self.classifier(rnn_out)

def _normalize_text(text: str) -> str:
    return " ".join(text.replace("\n", " ").split())

def _prepare_line_tensor(line_image: Image.Image, max_width: int = 512) -> torch.Tensor:
    if line_image.mode != "L":
        line_image = line_image.convert("L")

    width, height = line_image.size
    new_width = max(16, int(round((width / max(height, 1)) * 64)))
    new_width = min(max_width, new_width)

    resized = line_image.resize((new_width, 64), Image.Resampling.BILINEAR)
    canvas = Image.new("L", (max_width, 64), color=255)
    canvas.paste(resized, (0, 0))

    # Convert grayscale [0,255] -> normalized tensor in [-1,1] with shape (1,1,H,W).
    arr = np.asarray(canvas, dtype=np.float32) / 255.0
    arr = (arr - 0.5) / 0.5
    tensor = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)
    return tensor

def _ctc_greedy_decode(logits: torch.Tensor, idx2char: Dict[int, str], blank_idx: int = 0) -> str:
    preds = logits.argmax(dim=-1).squeeze(0).tolist()

    out = []
    prev = None
    for token in preds:
        if token != blank_idx and token != prev:
            out.append(idx2char.get(token, ""))
        prev = token

    return _normalize_text("".join(out))

def _segment_lines(image: Image.Image) -> List[Image.Image]:
    gray = np.array(image.convert("L"))
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    bw = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        15,
    )

    row_sum = bw.sum(axis=1)
    thresh = max(12, int(0.08 * np.max(row_sum))) if row_sum.size > 0 else 12
    active = row_sum > thresh

    lines: List[Tuple[int, int]] = []
    start = None
    for i, flag in enumerate(active.tolist()):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            if i - start >= 6:
                lines.append((start, i))
            start = None
    if start is not None and len(active) - start >= 6:
        lines.append((start, len(active)))

    if not lines:
        return [image.convert("L")]

    out: List[Image.Image] = []
    h, w = bw.shape
    for y0, y1 in lines:
        y0 = max(0, y0 - 3)
        y1 = min(h, y1 + 3)
        crop_mask = bw[y0:y1, :]
        col_sum = crop_mask.sum(axis=0)
        cols = np.where(col_sum > 0)[0]
        if cols.size == 0:
            continue
        x0 = max(0, int(cols[0]) - 4)
        x1 = min(w, int(cols[-1]) + 5)
        crop = gray[y0:y1, x0:x1]
        if crop.size == 0:
            continue
        out.append(Image.fromarray(crop).convert("L"))

    return out if out else [image.convert("L")]

_OCR_MODEL = None
_OCR_IDX2CHAR = None
_OCR_DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

def _get_checkpoint_paths() -> Tuple[Path, Path]:
    backend_root = Path(__file__).resolve().parents[3]
    pth_root = backend_root / "pth"
    model_path = Path(os.getenv("OCR_CRNN_MODEL_PATH", str(pth_root / "crnn_model.pth")))
    idx2char_path = Path(os.getenv("OCR_CRNN_IDX2CHAR_PATH", str(pth_root / "crnn_idx2char.pth")))
    return model_path, idx2char_path

def _load_ocr_once() -> Tuple[nn.Module, Dict[int, str], torch.device]:
    global _OCR_MODEL, _OCR_IDX2CHAR
    if _OCR_MODEL is not None and _OCR_IDX2CHAR is not None:
        return _OCR_MODEL, _OCR_IDX2CHAR, _OCR_DEVICE

    model_path, idx2char_path = _get_checkpoint_paths()
    if not model_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {model_path}")
    if not idx2char_path.exists():
        raise FileNotFoundError(f"idx2char not found: {idx2char_path}")

    idx2char = torch.load(idx2char_path, map_location="cpu")
    model = CRNN(num_classes=len(idx2char))
    state_dict = torch.load(model_path, map_location=_OCR_DEVICE)
    model.load_state_dict(state_dict)
    model.to(_OCR_DEVICE)
    model.eval()

    _OCR_MODEL = model
    _OCR_IDX2CHAR = idx2char
    return _OCR_MODEL, _OCR_IDX2CHAR, _OCR_DEVICE

def _recognize_line(image: Image.Image, model: nn.Module, idx2char: Dict[int, str], device: torch.device) -> str:
    tensor = _prepare_line_tensor(image).to(device)
    with torch.no_grad():
        logits = model(tensor)
    return _ctc_greedy_decode(logits, idx2char)

def _recognize_image_bytes(payload: bytes) -> str:
    model, idx2char, device = _load_ocr_once()
    image = Image.open(io.BytesIO(payload)).convert("L")

    lines = _segment_lines(image)
    page_lines = [_recognize_line(line, model, idx2char, device) for line in lines[:20]]  # cap at 20 lines
    page_text = "\n".join([t for t in page_lines if t])
    if page_text.strip():
        return page_text

    return _recognize_line(image, model, idx2char, device)

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
