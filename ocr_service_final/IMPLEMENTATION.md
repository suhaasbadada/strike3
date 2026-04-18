# Strike3 OCR Service — Implementation Reference

## Overview

A FastAPI microservice (port 8001) that takes a base64-encoded noisy document image and returns extracted text. The pipeline has four stages: **Denoise → Segment → Classify → Join**.

---

## Pipeline Flow

```
Input Image (base64)
       │
       ▼
  1. DENOISE
  DenoisingCNN (DnCNN-style, 8 layers)
  Trained on NoisyOffice paired images (_TR split)
  Fallback: cv2.fastNlMeansDenoising if weights missing
       │
       ▼
  2. SEGMENT
  Otsu binarization (THRESH_BINARY_INV → white text, black bg)
  Morphology cleanup (2x2 MORPH_OPEN, removes noise pixels)
  Connected components (cv2.connectedComponentsWithStats)
  Group blobs into lines (Y-centroid clustering)
  Merge tiny fragments (i-dots, punctuation)
  Detect word spaces (gap > 0.5 × median char width)
  Split touching characters (vertical projection valleys)
  Resize each crop to 28×28 float32 [0,1]
       │
       ▼
  3. CLASSIFY
  OCRPCNN — 3 conv blocks, 47-class output
  Batch GPU inference (all crops in one forward pass)
  Output: predicted char label + confidence per crop
       │
       ▼
  4. JOIN
  Reassemble chars in reading order
  Insert spaces (is_space flag) and newlines (line breaks)
  Return plain text string
```

---

## Files

| File | Purpose |
|------|---------|
| `model.py` | CNN architecture + load_model() + label_to_char() |
| `denoiser.py` | DenoisingCNN architecture + load_denoiser() |
| `segmenter.py` | Full segmentation pipeline + join_predictions() |
| `noise.py` | Gaussian + salt-and-pepper augmentation functions |
| `train_ocr.py` | Train OCR CNN on EMNIST balanced dataset |
| `train_denoiser.py` | Train denoiser on NoisyOffice paired images |
| `generate_printed_chars.py` | Render 47 EMNIST classes with system fonts → PNG |
| `fine_tune.py` | Fine-tune OCR CNN on EMNIST + printed chars mix |
| `evaluate.py` | Measure per-noise-profile accuracy → results.json |
| `main.py` | FastAPI app, /health + /ocr endpoints |
| `test_pipeline.py` | End-to-end test without server (CLI) |
| `debug_pipeline.py` | Saves binary + crop images to /tmp/debug/ |
| `finetune_job.sh` | SLURM job: generate printed chars → fine-tune |

---

## Model: OCRPCNN (`model.py`)

**Architecture:**
```
Input: (N, 1, 28, 28)

Conv Block 1:
  Conv2d(1, 32, 3, padding=1) → BatchNorm → ReLU → MaxPool(2,2)
  Output: (N, 32, 14, 14)

Conv Block 2:
  Conv2d(32, 64, 3, padding=1) → BatchNorm → ReLU → MaxPool(2,2)
  Dropout(0.15)
  Output: (N, 64, 7, 7)

Conv Block 3:
  Conv2d(64, 128, 3, padding=1) → BatchNorm → ReLU
  (No MaxPool — preserves spatial detail)
  Output: (N, 128, 7, 7)

Flatten: (N, 6272)

FC1: 6272 → 512 → ReLU → Dropout(0.3)
FC2: 512 → 256 → ReLU
FC3: 256 → 47 (logits)
```

**Classes:** 47 EMNIST balanced classes  
`0-9, A-Z, a b d e f g h n q r t`

**Training:**
- Dataset: EMNIST balanced (112,800 train / 18,800 test)
- Augmentation: Gaussian noise (σ~0.1) + salt-and-pepper (p~0.05), applied randomly
- Optimizer: Adam, LR=0.001
- Scheduler: ReduceLROnPlateau (patience=3, factor=0.5)
- Best val accuracy: ~90% on EMNIST test set

**Fine-tuning (for printed text):**
- Added synthetic printed chars from PIL (47 classes × multiple fonts × augmentations)
- Mixed with EMNIST: `ConcatDataset([emnist_train, printed_repeated × 8])`
- LR=0.0003 (lower to preserve existing weights)
- Saves `ocr_finetuned.pth`; main.py auto-loads this if it exists

---

## Denoiser: DenoisingCNN (`denoiser.py`)

**Architecture:** DnCNN-style residual denoiser
```
8 conv layers (64 filters each, 3×3, padding=1)
Layers 2-7 include BatchNorm
Final layer: Conv2d(64, 1, 3, padding=1)
Output: x - net(x)  (residual subtraction, clamped to [0,1])
```

**Training:**
- Dataset: NoisyOffice paired images (_TR split only)
- Extracts 64×64 patches from (noisy, clean) pairs
- Loss: MSELoss
- Converged to ~0.000339 val loss on _VA split
- Saves `denoiser_best.pth`

---

## Segmenter: (`segmenter.py`)

**Step-by-step:**

1. **Binarize** — Otsu + `THRESH_BINARY_INV`  
   → Expects black text on white background (document style)  
   → Output: white text (255) on black (0)

2. **Morphology cleanup** — `MORPH_OPEN` with 2×2 kernel  
   → Removes isolated noise pixels

3. **Connected components** — `cv2.connectedComponentsWithStats`  
   → Filters: area < 10 (noise) or area > 80% of image (background artifact)

4. **Group into lines** — Y-centroid clustering  
   → Threshold: 0.6 × median blob height

5. **Merge fragments** — Merges blobs with area < 20% of median into nearest neighbor  
   → Handles i-dots, accent marks, punctuation fragments

6. **Detect spaces** — Gap normalized by median char width  
   → Gap > 0.5 × median_char_w → word space

7. **Split touching chars** — Vertical projection valleys  
   → Splits wide blobs (width > 1.8× avg) at deepest central valley

8. **Resize** — Pad to square → `cv2.resize(28,28)` → normalize to [0,1]

---

## API (`main.py`)

**Endpoint:** `POST /ocr`  
**Port:** 8001

**Request:**
```json
{
  "image": "<base64 encoded image>",
  "noise_type": "auto"   // "gaussian" | "salt_pepper" | "auto"
}
```

**Response:**
```json
{
  "text": "extracted text here",
  "confidence": 0.85,
  "char_count": 142,
  "noise_type_detected": "gaussian",
  "char_accuracy_on_profile": 0.90,
  "latency_ms": 320.5
}
```

**Noise auto-detection:**  
Pixels with value < 10 or > 245 counted as "extreme".  
Ratio > 5% → salt_pepper, else → gaussian.

**`char_accuracy_on_profile`** loaded from `results.json` (generated by `evaluate.py`).

---

## Weight Files

| File | Size | Description |
|------|------|-------------|
| `weights/ocr_best.pth` | ~14MB | Base OCR CNN trained on EMNIST |
| `weights/ocr_finetuned.pth` | ~14MB | Fine-tuned on EMNIST + printed chars |
| `weights/denoiser_best.pth` | ~892KB | DenoisingCNN trained on NoisyOffice |

`main.py` auto-prefers `ocr_finetuned.pth` if it exists.

---

## Datasets

| Dataset | Used For | Location on BigRed |
|---------|----------|--------------------|
| EMNIST balanced | Train + test OCR CNN | `./data/` (auto-download) |
| NoisyOffice | Train denoiser | `./SimulatedNoisyOffice/` |
| Synthetic printed chars | Fine-tune OCR | `./data/printed_chars/` (generated) |

---

## SLURM Jobs

**Fine-tune job** (`finetune_job.sh`):
```
Account: r00896
Partition: gpu
GPUs: 1
Memory: 16G
Time limit: 1 hour

Steps:
  1. python generate_printed_chars.py --output-dir ./data/printed_chars --augmentations 5
  2. python fine_tune.py --printed-dir ./data/printed_chars --weights-dir ./weights \
       --epochs 10 --batch-size 256 --lr 0.0003 --printed-repeat 8
```

Submit: `sbatch finetune_job.sh`  
Monitor: `tail -f finetune_log_<jobid>.out`

---

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| OCR CNN training | Done | 90% val acc on EMNIST |
| Denoiser training | Done | 0.000339 val MSE |
| Fine-tuning | Done | ocr_finetuned.pth created |
| Segmenter | Working | Finding chars, space detection may be over-triggering |
| OCR output quality | Poor | Still outputting I/1/L on printed docs — needs debugging |
| evaluate.py | Not run | results.json missing — needed for grad G1 |
| FastAPI server | Not tested | main.py ready but not started |

---

## Known Issues & Next Steps

1. **OCR output is mostly I/1/L** — model likely not seeing correct crops  
   Debug: run `debug_pipeline.py` and inspect `/tmp/debug/crop_*.png`

2. **Space detection over-triggering** — almost every char flagged as space  
   Likely caused by segmenter seeing noise blobs between every real character

3. **Denoiser may be hurting clean images** — trained on noisy inputs; on clean input it may distort strokes  
   Fix: run with `--no-denoise` flag in `debug_pipeline.py` to isolate

4. **evaluate.py not run** — need `results.json` for grad requirement G1  
   Run after OCR quality is acceptable

---

## Run Order (BigRed)

```bash
# 1. Train denoiser (already done)
sbatch train_denoiser_job.sh

# 2. Train OCR CNN (already done)
sbatch train_ocr_job.sh

# 3. Fine-tune on printed chars (already done)
sbatch finetune_job.sh

# 4. Debug pipeline
module load python/gpu
python debug_pipeline.py --image ./SimulatedNoisyOffice/clean_images_grayscale/Fontfre_Clean_TR.png --no-denoise

# 5. Test pipeline end-to-end
python test_pipeline.py --image ./SimulatedNoisyOffice/clean_images_grayscale/Fontfre_Clean_TR.png

# 6. Run evaluate (after quality is acceptable)
python evaluate.py

# 7. Start API server
uvicorn main:app --host 0.0.0.0 --port 8001
```
