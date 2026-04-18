# Strike3 — 2-Stage Neural Compression Pipeline

A full-stack, end-to-end pipeline that ingests a noisy scanned document image, extracts its text with a custom-trained CRNN, and compresses the output with a from-scratch Adaptive Huffman encoder — all exposed as two communicating FastAPI microservices and visualised in a Next.js dashboard.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Stage 1 — OCR Microservice (CRNN)](#stage-1--ocr-microservice-crnn)
3. [Stage 2 — Compression Microservice (Adaptive Huffman)](#stage-2--compression-microservice-adaptive-huffman)
4. [API Reference](#api-reference)
5. [Frontend](#frontend)
6. [Setup & Running Locally](#setup--running-locally)
7. [Training the CRNN](#training-the-crnn)
8. [Deployment](#deployment)
9. [Benchmarks & Metrics](#benchmarks--metrics)

---

## Architecture Overview

```
┌─────────────────────┐     POST /process-image     ┌──────────────────────────────┐
│   Next.js Frontend  │ ─────────────────────────── │     FastAPI Backend           │
│   (Vercel)          │ ◄─────────────────────────── │     (Render)                 │
└─────────────────────┘       JSON response          │                              │
                                                     │  ┌─────────────────────┐     │
                                                     │  │  Stage 1: CRNN OCR  │     │
                                                     │  │  POST /ocr          │     │
                                                     │  └────────┬────────────┘     │
                                                     │           │ extracted text   │
                                                     │  ┌────────▼────────────┐     │
                                                     │  │  Stage 2: Adaptive  │     │
                                                     │  │  Huffman Encoder    │     │
                                                     │  │  POST /compress     │     │
                                                     │  └─────────────────────┘     │
                                                     └──────────────────────────────┘
```

The `/process-image` endpoint orchestrates both stages in a single call: it runs OCR on the uploaded image, pipes the extracted text into the Adaptive Huffman encoder, decompresses, and verifies lossless recovery — returning all metrics in one JSON response.

---

## Stage 1 — OCR Microservice (CRNN)

### Model Architecture

The OCR model is a **CRNN (Convolutional Recurrent Neural Network)** trained end-to-end with **CTC (Connectionist Temporal Classification) loss** — the standard approach for sequence recognition without explicit character segmentation.

```
Input image  →  CNN Feature Extractor  →  BiLSTM  →  Linear  →  CTC Decode  →  Text
(1 × 64 × W)                              (seq)
```

#### CNN Backbone — 6 convolutional blocks

| Block | Channels | Operation | Spatial change |
|-------|----------|-----------|----------------|
| 1 | 1 → 64 | Conv3×3 + BN + ReLU + MaxPool 2×2 | H/2, W/2 |
| 2 | 64 → 128 | Conv3×3 + BN + ReLU + MaxPool 2×2 | H/4, W/4 |
| 3 | 128 → 256 | Conv3×3 + BN + ReLU | — |
| 4 | 256 → 256 | Conv3×3 + BN + ReLU + MaxPool 2×2 | H/8, W/4 |
| 5 | 256 → 512 | Conv3×3 + BN + ReLU + MaxPool 2×1 | H/16, W/4 |
| 6 | 512 → 512 | Conv3×3 + BN + ReLU + MaxPool 4×1 | H/64 → 1, W/4 |

Height is fully collapsed to 1 after block 6, so the output feature map is `(B, 512, 1, W/4)`. Width is the time axis fed to the RNN.

**Design rationale:**
- `3×3` kernels throughout — best trade-off between receptive field and parameter count.
- `BatchNorm` after every conv — stabilises training and acts as implicit regularisation.
- Asymmetric pooling in blocks 5 & 6 `(H×1)` — collapses height while preserving the horizontal time resolution needed for sequence decoding.

#### RNN Head

- 2-layer **BiLSTM**, hidden size 256 per direction (512 total per timestep)
- `dropout=0.2` between layers
- Final `Linear(512 → num_classes)` projects each timestep to character logits
- **CTC greedy decode** at inference (argmax + collapse repeats + remove blank token 0)

#### Training Data (4 sources)

| Source | Samples | Purpose |
|--------|---------|---------|
| **EMNIST ByMerge** | 6 000 synthesised line images | Handwritten letter/digit diversity |
| **MNIST** | 3 000 synthesised line images | Handwritten digit robustness |
| **Synthetic printed lines** | ~378 labelled images (clean + noisy) | Printed-font generalisation |
| **Tesseract pseudo-labels** | Augmented from synthetic corpus | Cheap label expansion on hard samples |

EMNIST and MNIST characters were randomly concatenated into variable-length "line" images (1–16 characters wide) to generate sequence-level training samples, giving the LSTM meaningful temporal context at training time.

#### Training Configuration

| Hyperparameter | Value |
|---|---|
| Epochs | 35 |
| Batch size | 12 |
| Optimiser | Adam, lr = 1e-3 |
| LR schedule | ReduceLROnPlateau (patience = 3) |
| Gradient clipping | 5.0 |
| CTC blank token | 0 |
| Max image width | 512 px (padded) |
| Image height | 64 px |
| Device | MPS (Apple Silicon) / CUDA / CPU |

#### Noise Profiles Supported

- **Gaussian noise** — additive pixel-level Gaussian noise (σ tunable), simulating scanner sensor noise
- **Salt-and-pepper noise** — random black/white pixel corruption, simulating dust and sensor dropout

Both noise types were applied during synthetic data generation so the model is evaluated against each independently.

#### Preprocessing (at inference)

1. Convert image to grayscale
2. Gaussian blur (3×3) + adaptive threshold for line segmentation
3. Each detected line is cropped, resized to height 64, padded to width 512
4. Normalised to `[-1, 1]` via `(pixel/255 − 0.5) / 0.5`
5. CTC greedy decode on per-line logits; lines joined with `\n`

---

## Stage 2 — Compression Microservice (Adaptive Huffman)

### Algorithm

A **from-scratch FGK (Faller-Gallager-Knuth) Adaptive Huffman** encoder/decoder — no external compression libraries (`zlib`, `gzip`, etc.) are used anywhere.

The encoder maintains a live Sibling Property tree. As each character is encoded:
1. If the symbol is new, emit the NYT (Not Yet Transmitted) codeword + raw Unicode bits
2. If the symbol exists, emit its current Huffman codeword
3. Walk up the tree incrementing weights, swapping nodes to maintain the Sibling Property

The decoder mirrors this process, reconstructing the identical tree state symbol-by-symbol, achieving **lossless recovery** with no transmitted tree or codebook.

### Metrics Reported

| Metric | Formula |
|---|---|
| **Compression ratio** | `original_bytes / compressed_bytes` |
| **Entropy** | $H = -\sum p_i \log_2 p_i$ bits/symbol |
| **Encoding efficiency** | `(entropy × original_bytes) / (compressed_bits) × 100 %` |

---

## API Reference

All endpoints are served by the FastAPI backend (root dir: `backend/`).

### `GET /health`
Returns `{"status": "ok"}`. Used by Render for health checks.

### `POST /ocr`
Upload an image file, receive extracted text.

**Request:** `multipart/form-data`, field `file` (any common image format)

**Response:**
```json
{ "text": "extracted text here" }
```

### `POST /compress`
Compress a text string with Adaptive Huffman.

**Request:** `{"text": "..."}`

**Response:**
```json
{
  "compressed_data": "<bitstring>",
  "compression_ratio": 1.85,
  "entropy": 4.21,
  "encoding_efficiency": 94.3,
  "latency_ms": 12
}
```

### `POST /decompress`
Decompress a previously compressed bitstring.

**Request:** `{"compressed_data": "<bitstring>", "original_length": 123}`

**Response:** `{"text": "original text"}`

### `POST /verify`
Round-trip check: compress → decompress → diff.

**Request:** `{"text": "..."}`

**Response:** `{"match": true, "original": "...", "decompressed": "..."}`

### `POST /process-image`
**Full pipeline endpoint.** Accepts an image, runs OCR then compression+verification internally.

**Request:** `multipart/form-data`, field `file`

**Response:**
```json
{
  "ocr_text": "...",
  "compression": {
    "compressed_data": "...",
    "compression_ratio": 1.85,
    "entropy": 4.21,
    "encoding_efficiency": 94.3
  },
  "verification": { "match": true },
  "total_latency": 340
}
```

---

## Frontend

Built with **Next.js 16 + React 19 + Tailwind CSS**, deployed on Vercel.

Three animated pipeline stages visualised in real time:
- **OCR Stage** — file picker, live extracted text display
- **Compression Stage** — compression ratio, entropy, encoding efficiency cards
- **Verification Stage** — lossless match confirmation

Six live metric cards appear after pipeline completion:
- OCR Accuracy (Gaussian) · OCR Accuracy (Salt & Pepper) · Compression Ratio · Entropy · Encoding Efficiency · E2E Latency

---

## Setup & Running Locally

### Prerequisites
- Python 3.11+
- Node.js 20+

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
# Runs at http://localhost:8000
```

Model checkpoints must be present at `backend/pth/crnn_model.pth` and `backend/pth/crnn_idx2char.pth` (see Training section below or download from releases).

Override checkpoint paths via env vars:
```
OCR_CRNN_MODEL_PATH=/path/to/crnn_model.pth
OCR_CRNN_IDX2CHAR_PATH=/path/to/crnn_idx2char.pth
```

### Frontend

```bash
cd frontend
npm install
# Create .env.local:
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
# Runs at http://localhost:3000
```

---

## Training the CRNN

```bash
cd ocr_service
python train_crnn.py \
  --data_dir ./data/synthetic_lines \
  --epochs 35 \
  --batch_size 12 \
  --max_width 1024 \
  --mnist_line_samples 3000 \
  --emnist_line_samples 6000 \
  --idx_min_chars 1 \
  --idx_max_chars 16 \
  --seed 42
```

Outputs saved to `ocr_service/`:
- `crnn_model.pth` — model weights (best val loss checkpoint)
- `crnn_char2idx.pth` — character → index mapping
- `crnn_idx2char.pth` — index → character mapping

Copy weights to backend before serving:
```bash
cp ocr_service/crnn_model.pth backend/pth/
cp ocr_service/crnn_idx2char.pth backend/pth/
```

---

## Deployment

| Service | Platform | Config |
|---|---|---|
| Backend (FastAPI) | Render | Root dir: `backend/`, Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`, Python 3.11 |
| Frontend (Next.js) | Vercel | Root dir: `frontend/`, env var `NEXT_PUBLIC_API_URL=<render-url>` |

---

## Benchmarks & Metrics

| Metric | Value |
|---|---|
| OCR accuracy — Gaussian noise | **97.4 %** |
| OCR accuracy — Salt & pepper | **95.1 %** |
| Typical compression ratio | **1.8 – 2.2×** |
| Typical encoding efficiency | **~94 %** |
| E2E pipeline latency (local, MPS) | **< 400 ms** |
| E2E pipeline latency (Render CPU) | **2 – 6 s** |

Latency on Render reflects CPU-only inference on a shared instance; local MPS (Apple Silicon) performance is significantly faster.
