# Strike3 — Stage 1: Noisy Document OCR Service

A CNN-based OCR microservice that extracts text from noisy document images. Designed as Stage 1 of a 2-stage neural compression pipeline: **OCR → Adaptive Huffman Compression**.

---

## What We Built

Stage 1 is a standalone FastAPI service (port 8001) that takes a base64-encoded image of a noisy document and returns extracted text with confidence scores. It runs a full pipeline: preprocessing → segmentation → CNN classification → post-processing correction.

### Key Features

- **4-layer CNN classifier** trained on 47 printed character classes (0–9, A–Z, subset of lowercase)
- **Projection-based segmentation** for line and character extractio
- **Blob splitting** to handle touching/ligated characters via vertical projection valleys
- **3-layer post-processing** pipeline (character rules → domain vocabulary fuzzy match → conservative spell correction)
- **Noise-aware preprocessing** with automatic polarity detection and Otsu thresholding
- **Confidence scoring** per character and aggregated for the full extraction

---

## Pipeline Overview

```
Base64 Image
     │
     ▼
┌──────────────────────────────────────┐
│ 1. PREPROCESSING                     │
│    Median blur → polarity detect     │
│    → Otsu threshold → binary image   │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│ 2. SEGMENTATION                      │
│    Horizontal projection → lines     │
│    Connected components → chars      │
│    Valley splitting → split blobs    │
│    Gap analysis → word spaces        │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│ 3. NORMALIZATION                     │
│    Largest component only            │
│    Tight-trim → proportional margin  │
│    Pad to square → resize 28×28      │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│ 4. CNN INFERENCE (PrintedCNN)        │
│    Batch all crops → softmax         │
│    → argmax per crop → confidence    │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│ 5. POST-PROCESSING                   │
│    Char rules → vocab fuzzy match    │
│    → optional spell correction       │
└──────────────────┬───────────────────┘
                   │
                   ▼
             Extracted Text
```

---

## Model Architecture

**PrintedCNN** — 4 convolutional blocks + fully connected classifier:

```
Input:  (N, 1, 28, 28)

Conv1:  1→32  filters, 3×3, pad=1  →  MaxPool(2,2)  →  (N, 32, 14, 14)
Conv2:  32→64 filters, 3×3, pad=1  →  MaxPool(2,2)  →  (N, 64, 7, 7)
Conv3:  64→128 filters, 3×3, pad=1 →  MaxPool(2,2)  →  (N, 128, 3, 3)
Conv4:  128→256 filters, 3×3, pad=1                  →  (N, 256, 3, 3)

Flatten:  256×3×3 = 2304
FC1:      2304 → 512  →  ReLU  →  Dropout(0.2)
FC2:      512 → 47 logits

Output: softmax probabilities over 47 classes
```

**Classes (47 total):** digits 0–9, uppercase A–Z, lowercase subset: a, b, d, e, f, g, h, n, q, r, t

---

## How We Trained the Model

### Datasets

We combined three sources of training data, each contributing differently to the model's robustness:

**1. EMNIST Balanced** — ~112,800 samples (47 classes)
- The standard benchmark dataset for character recognition
- 28×28 grayscale images of handwritten digits + uppercase + partial lowercase
- 2,400 samples per class; 112,800 train / 18,800 test split
- Used as the base distribution to establish character shape priors
- Note: EMNIST images are stored transposed — we apply a `.permute(0, 2, 1)` fix at load time

**2. MNIST** — 60,000 training + 10,000 test samples (digits 0–9 only)
- Classic handwritten digit dataset, 28×28 grayscale
- Used for supplementary digit training; digit classes are heavily represented here
- Helps the model distinguish between visually similar digits (0/O, 1/I/l, 5/S)

**3. Pipeline Crops Dataset** (generated internally) — ~47 × 20 fonts × 5 sizes × 10 augmentations ≈ **~47,000 samples**
- Our most targeted dataset: render one character at a time through 20 system fonts (Helvetica, Arial, Times New Roman, Georgia, Courier, Verdana, Avenir, Rockwell, Seravek, Charter, and bold/italic variants) at 5 font sizes (18–26px)
- Each rendered character is passed through the **exact same preprocessing pipeline** as inference — Otsu threshold → connected component crop → tight-trim → proportional margin → 28×28 resize
- This guarantees the training distribution matches what the model sees at inference time (domain alignment)
- 10 augmented copies per base crop with inline Gaussian (σ=0.08) or S&P (rate=0.04) noise
- Organized as `data/pipeline_crops/{label_idx}/crop_{i}.png`

**4. Printed Fonts Dataset** — ~47 classes × fonts × sizes (supplementary)
- Additional synthetic data from PIL-rendered printed characters
- Same font library as pipeline crops but rendered without the full pipeline normalization
- Used to augment class coverage for visually distinct printed-style characters
- Organized as `data/printed_chars/{label}/{image}.png`

**Total effective training set: ~220,000+ samples across 47 classes**

### Training Configuration

| Parameter | Value |
|-----------|-------|
| Optimizer | Adam, lr=0.001 |
| Scheduler | ReduceLROnPlateau (patience=3, factor=0.5) |
| Loss | CrossEntropyLoss |
| Epochs | 30 (early stop after 6 with no improvement) |
| Batch size | 128 |
| Train/Val split | 80/20 |

### Noise Augmentation (applied per batch during training)

Two augmentation strategies applied randomly per sample:
- **Gaussian noise:** σ sampled from [0.05, 0.2], applied with 30% probability
- **Salt-and-pepper noise:** pixel flip rate sampled from [0.02, 0.1], applied with 20% probability
- Remaining 50% of samples are trained clean

This forces the model to be robust to the same noise types it sees at inference time.

### Output

Weights saved to `./weights/printed_cnn.pth` (~6.4MB).

---

## API Reference

### `POST /ocr`

**Request:**
```json
{
  "image": "<base64 encoded grayscale image>",
  "noise_type": "auto"
}
```

`noise_type` options: `"auto"` (default), `"gaussian"`, `"salt_pepper"`

**Response:**
```json
{
  "text": "final corrected text",
  "text_raw": "raw CNN output before correction",
  "text_layer1": "after character-level rules",
  "confidence": 0.85,
  "char_count": 142,
  "noise_type_detected": "gaussian",
  "latency_ms": 85.5
}
```

### `GET /health`

```json
{
  "status": "ok",
  "model_loaded": true,
  "vocab_size": 4523,
  "device": "cpu"
}
```

---

## Segmentation — What We Observed and What We Built

Segmentation was the hardest part of the pipeline. The classifier is only as good as the crops it receives. A miscut crop — half a character, two characters fused together, or a fragment of noise will produce a wrong prediction regardless of how well the model is trained. We learned this the hard way: early iterations had high model accuracy on EMNIST but terrible end-to-end accuracy because the crops fed to the model were garbage.

Here's what we observed and how we addressed each failure mode:

---

### Observation 1: Documents are lines, not a flat bag of characters

Naively running connected components on the entire image failed immediately. Characters from adjacent lines would merge into one giant blob when they sat close vertically. We also lost all reading order, connected components returns blobs in arbitrary order.

**What we implemented — Line-first segmentation via horizontal projection:**

Sum the foreground pixel count across every row of the binary image. Rows with content produce high values; gaps between text lines produce near-zero values. We identify contiguous runs of "active" rows (threshold: >1% of image width) as line strips. Each strip is processed independently, which:
- Prevents vertical bleeding between lines
- Preserves reading order naturally (strips are top-to-bottom)
- Gives us a coordinate frame (strip height) for filtering noise

```
h_proj[y] = sum(binary[y, :])   # one value per row
threshold  = image_width × 0.01
line strips = contiguous runs where h_proj > threshold, height > 5px
```

---

### Observation 2: Connected components give you blobs, not characters

Within each line strip, we run `cv2.connectedComponentsWithStats`. This works well for well-separated text, but in practice two problems appeared:

**Problem A — Noise blobs:** Documents with salt-and-pepper or scan artifacts produce hundreds of tiny components (single pixels, 2×2 clusters). Feeding these as character crops collapses to the model predicting high-frequency characters like `.` or `i` everywhere.

**Problem B — Background components:** In some polarity-ambiguous images, the background itself becomes a single massive connected component covering 80%+ of the strip area.

**What we implemented — Dual-sided area filter:**

```python
if area < 20:               continue  # noise speckle
if area > strip_area * 0.8: continue  # background artifact
if w < 2 or h < 2:         continue  # degenerate single-axis component
```

This alone removed the majority of garbage crops and was one of the biggest accuracy improvements we made.

---

### Observation 3: Characters touch — blobs are not always single characters

In noisy printed documents, especially with degraded ink or compression artifacts, adjacent characters' pixel blobs merge into one wide connected component. A naive system classifies "TH" as a single unknown character.

We observed that fused blobs have a characteristic signature: their width is significantly larger than typical single characters on that line.

**What we implemented — Estimated character width + valley splitting:**

We compute `expected_w` as the median of the lower half of all blob widths across the entire image (using the lower half avoids wide blobs skewing the estimate upward):

```python
widths = sorted([c["w"] for c in all_chunks])
expected_w = median(widths[:len(widths)//2])
```

Any blob with `width > 1.6 × expected_w` (or aspect ratio > 1.0 in the final implementation) is flagged as a candidate fusion. We then split it using vertical projection valleys:

1. Compute the column-wise sum of foreground pixels within the blob (`v_proj`)
2. Smooth with a 5-point kernel to remove micro-noise in the projection
3. Find local minima where `v_proj[i] < v_proj[i-1]` and `v_proj[i] < v_proj[i+1]`
4. Filter: minima must be below 35% of the max projection value (genuine gaps, not slight dips)
5. Filter: minimum separation between valleys = `max(0.4 × expected_w, 4px)` (prevents over-splitting)
6. Pick the best valley: weighted by projection depth and proximity to blob center
7. Recursively split each half if still too wide

This correctly separates "TH", "fi", "rn" and other common fusion cases.

---

### Observation 4: Crops must match training distribution exactly

Even with correct bounding boxes, crops looked different from EMNIST samples: they were tightly packed with no margin, aspect ratios varied wildly (tall thin `l` vs wide `W`), and resizing with nearest-neighbor produced aliasing artifacts.

We also noticed that noise within a character blob — speckle inside the loop of `O`, for example — would confuse the model because the crop contained multiple connected components.

**What we implemented — `_normalize_crop` (the most iterated function in the project):**

```
1. Keep only the largest connected component
   → removes internal speckle noise without touching the character outline

2. Reject degenerate crops:
   → foreground pixels < 20, height < 5px, or width < 3px → return blank 28×28

3. Tight-trim to foreground bounding box
   → eliminates empty margins that distort aspect ratio

4. Add proportional margin:
   margin = max(2px, 15% of max(height, width))
   → preserves natural character breathing room, matches how printed chars appear

5. Pad to square canvas (size = max(h, w) + 2×margin)
   → preserves aspect ratio without stretching

6. Resize to 28×28 with cv2.INTER_AREA
   → area-based downsampling preserves stroke thickness better than bilinear
```

The proportional margin (step 4) was particularly important: without it, characters like `I` and `l` became a single-pixel vertical line after resizing, indistinguishable from noise.

---

### Observation 5: Word boundaries matter for text assembly

Feeding characters in sequence without spaces produces unreadable output (`thequickbrownfox`). We needed a way to detect word boundaries without any semantic knowledge.

**What we implemented — Gap-based space detection:**

```python
gap = next_char.x - (current_char.x + current_char.w)
median_char_width = median([c.w for c in line])

if gap > 0.5 × median_char_width:
    insert space token
```

The 0.5× threshold was tuned empirically. In practice, inter-word gaps are 1–2× character width, while inter-character gaps within a word are 0–0.3×. The 0.5× midpoint correctly separates them in most cases.

---

### Why This All Matters

The model sees 28×28 binary patches. Every decision in the segmentation pipeline — which pixels are foreground, where one character ends and the next begins, how much margin to add — directly determines what the model is asked to classify. A well-trained model on a bad segmentation pipeline produces bad results. Getting segmentation right was the prerequisite to everything else.

---

## Post-Processing Pipeline

Three correction layers applied in sequence:

| Layer | Method | Example |
|-------|---------|---------|
| 1. Char rules | Regex substitutions targeting systematic OCR errors | `"0"` flanked by letters → `"o"` |
| 2. Domain vocab | Fuzzy match (edit distance ≤ 2) against `tesseract_metadata.csv` | `"teh"` → `"the"` |
| 3. Spell correction | Conservative edit-distance-1 for words ≥ 5 chars | `"hourse"` → `"house"` |

---

## Running the Service

```bash
# Install dependencies
pip install -r requirements.txt

# Start OCR service
cd ocr_service_final
python main.py
# Listens on http://0.0.0.0:8001
```

### Test a single image

```bash
cd ocr_service_final/test-train
python step5_classify.py --image <path_to_image> --weights-dir ../weights
```

---

## Project Structure

```
ocr_service_final/
├── main.py                    # FastAPI app + full OCR pipeline
├── postprocess.py             # 3-layer text correction
├── finetune/
│   └── train_printed_only.py  # CNN training script
├── test-train/
│   └── step5_classify.py      # Single-image test harness
└── weights/
    └── printed_cnn.pth        # Trained model weights (~6.4MB)
```

---

## Future Improvements

### Model
- **CRNN (CNN + LSTM):** Process full text lines instead of isolated characters — eliminates segmentation errors entirely and handles cursive/connected text
- **Attention decoder:** CTC or sequence-to-sequence decoding for variable-length line outputs
- **Larger real dataset:** EMNIST balanced (112K samples) or real scanned document datasets (IAM, FUNSD) instead of synthetic PIL fonts
- **Richer augmentation:** Elastic distortions, affine transforms, random rotations for broader noise robustness

### Segmentation
- **Deep layout models:** Replace projection heuristics with a lightweight detector (e.g., CRAFT text detector) for complex multi-column documents
- **Adaptive thresholding:** Sauvola or Bradley method for uneven illumination documents
- **Word spacing classifier:** Train on inter-character gap distributions rather than a fixed median-width threshold

### Post-Processing
- **Language model reranking:** Use a character-level n-gram or small transformer to rerank top-k CNN predictions per character in context — significant accuracy gains with no retraining
- **Domain-specific vocabularies:** Swap vocabulary for technical domains (medical, legal, scientific) without retraining the CNN

### Infrastructure
- **GPU batching:** Queue and batch crop inference for throughput under high load
- **INT8 quantization:** ~4× memory reduction, ~2× latency improvement for CPU deployment
- **Confidence thresholding:** Flag low-confidence regions for human review instead of silently guessing

---

## System Context

Stage 1 feeds directly into Stage 2 (Adaptive Huffman Compression), which encodes the extracted text and reports compression ratio, Shannon entropy, and encoding efficiency.

```
Noisy Document Image
       │
  [Stage 1: OCR]          ← this service
       │
  Extracted Text
       │
  [Stage 2: Adaptive Huffman Compression]
       │
  Compressed Bitstream + Metrics
       │
  [Frontend Dashboard]
```
