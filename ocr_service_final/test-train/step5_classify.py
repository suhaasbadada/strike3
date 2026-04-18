"""
Step 5 — Classify crops through OCR CNN and show per-crop predictions.

Runs the full pipeline (preprocess → segment → split → normalize)
then passes each crop through the CNN.

Usage:
    python step5_classify.py --image <path> --weights-dir ./weights

Output:
    Per-crop: index, predicted char, confidence, top 3 predictions
    Summary: overall confidence distribution
"""

import argparse
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from torchvision import transforms

from model_printed import load_printed_model, label_to_char
from postprocess import clean, load_vocab


# ── Preprocessing (locked from Step 1) ────────────────────────────────────────

def preprocess(gray: np.ndarray) -> np.ndarray:
    """Auto-detect image polarity so text is always white on black."""
    if gray.mean() < 127:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary


# ── Segmentation (locked from Steps 2 & 3) ────────────────────────────────────

def find_lines(binary: np.ndarray) -> list[tuple[int, int]]:
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


def find_chunks_in_line(binary, y_start, y_end):
    strip = binary[y_start:y_end, :]
    num_labels, _, stats, centroids = cv2.connectedComponentsWithStats(strip, connectivity=8)
    strip_area = strip.shape[0] * strip.shape[1]
    chunks = []
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        cx, cy = centroids[i]
        if area < 20 or area > strip_area * 0.8 or w < 2 or h < 2:
            continue
        chunks.append({
            "x": int(x), "y": int(y) + y_start,
            "w": int(w), "h": int(h),
            "cx": float(cx), "cy": float(cy) + y_start,
            "area": int(area),
        })
    return sorted(chunks, key=lambda c: c["x"])


def find_valleys(v_proj):
    v_smooth = np.convolve(v_proj, np.ones(3) / 3, mode="same")
    valleys = []
    for i in range(1, len(v_smooth) - 1):
        if v_smooth[i] < v_smooth[i-1] and v_smooth[i] < v_smooth[i+1]:
            valleys.append((i, float(v_smooth[i])))
    return valleys


def multi_split(binary, blob, expected_w):
    x, y, w, h = blob["x"], blob["y"], blob["w"], blob["h"]
    crop = binary[y:y+h, x:x+w]
    v_proj = crop.sum(axis=0).astype(np.float32)
    max_proj = v_proj.max() if v_proj.max() > 0 else 1
    all_valleys = [(i, v) for i, v in find_valleys(v_proj) if v < 0.35 * max_proj]
    if not all_valleys:
        return [blob]
    min_sep = max(int(expected_w * 0.4), 4)
    filtered = [all_valleys[0]]
    for valley in all_valleys[1:]:
        if valley[0] - filtered[-1][0] >= min_sep:
            filtered.append(valley)
    split_cols = sorted(v[0] for v in filtered)
    boundaries = [0] + split_cols + [w]
    pieces = []
    for i in range(len(boundaries) - 1):
        c0, c1 = boundaries[i], boundaries[i+1]
        pw = c1 - c0
        if pw < 2:
            continue
        pieces.append({"x": x+c0, "y": y, "w": pw, "h": h,
                       "cx": x+c0+pw/2, "cy": y+h/2, "area": int(crop[:, c0:c1].sum())})
    valid = [p for p in pieces if validate_piece(p, expected_w, binary)]
    return valid if len(valid) >= 2 else [blob]


def estimate_line_stats(chunks):
    widths  = sorted(c["w"] for c in chunks)
    heights = [c["h"] for c in chunks]
    lower_w = widths[:max(1, len(widths) // 2)]
    return {"expected_w": float(np.median(lower_w)), "median_h": float(np.median(heights))}


def is_suspicious(blob, expected_w, median_h):
    w, h = blob["w"], blob["h"]
    if w > expected_w * 1.6:
        return True
    if h > 0 and w / h > 1.0:
        return True
    return False


def validate_piece(piece, expected_w, binary):
    if piece["w"] < expected_w * 0.3:
        return False
    x, y, w, h = piece["x"], piece["y"], piece["w"], piece["h"]
    crop = binary[y:y+h, x:x+w]
    return (crop > 0).sum() / max(crop.size, 1) >= 0.03


def make_blob(x, y, w, h, crop_slice):
    return {"x": x, "y": y, "w": w, "h": h, "cx": x+w/2, "cy": y+h/2, "area": int(crop_slice.sum())}


def normalize_crop(crop: np.ndarray) -> np.ndarray:
    """Tight trim → add margin → pad to square → resize 28x28."""
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
    y_off = (size - ch) // 2
    x_off = (size - cw) // 2
    padded[y_off:y_off+ch, x_off:x_off+cw] = crop
    return cv2.resize(padded, (28, 28), interpolation=cv2.INTER_AREA)


def detect_spaces(line_blobs: list[dict]) -> list[bool]:
    """Returns space flags — True if a word space precedes this char."""
    flags = [False] * len(line_blobs)
    if len(line_blobs) <= 1:
        return flags
    median_w = float(np.median([b["w"] for b in line_blobs]))
    for i in range(1, len(line_blobs)):
        gap = line_blobs[i]["x"] - (line_blobs[i-1]["x"] + line_blobs[i-1]["w"])
        flags[i] = gap > median_w * 0.5
    return flags


def get_all_crops(binary: np.ndarray) -> tuple[list[np.ndarray], list[bool], list[int]]:
    """Returns (crops, space_flags, line_indices)."""
    lines = find_lines(binary)
    all_crops, all_spaces, all_lines = [], [], []

    for line_idx, (y_start, y_end) in enumerate(lines):
        chunks = find_chunks_in_line(binary, y_start, y_end)
        if not chunks:
            continue
        stats = estimate_line_stats(chunks)
        expected_w = stats["expected_w"]
        median_h   = stats["median_h"]

        # Split wide blobs first, then detect spaces on final blob list
        final_blobs = []
        for blob in chunks:
            if is_suspicious(blob, expected_w, median_h):
                final_blobs.extend(multi_split(binary, blob, expected_w))
            else:
                final_blobs.append(blob)
        final_blobs = sorted(final_blobs, key=lambda b: b["x"])

        space_flags = detect_spaces(final_blobs)

        for blob, is_space in zip(final_blobs, space_flags):
            x, y, w, h = blob["x"], blob["y"], blob["w"], blob["h"]
            raw = binary[y:y+h, x:x+w]
            normalized = normalize_crop(raw)
            all_crops.append(normalized)
            all_spaces.append(is_space)
            all_lines.append(line_idx)

    return all_crops, all_spaces, all_lines


# ── CNN inference ──────────────────────────────────────────────────────────────

TRANSFORM = transforms.ToTensor()


def classify_crops(crops: list[np.ndarray], model, device) -> list[dict]:
    tensors = []
    for crop in crops:
        pil = Image.fromarray(crop, mode="L")
        tensors.append(TRANSFORM(pil))

    batch = torch.stack(tensors).to(device)
    model.eval()
    with torch.no_grad():
        logits = model(batch)
        probs  = torch.softmax(logits, dim=1)

    results = []
    for i in range(len(crops)):
        top3_probs, top3_idxs = probs[i].topk(3)
        results.append({
            "pred":       label_to_char(int(top3_idxs[0].item())),
            "confidence": top3_probs[0].item(),
            "top3": [(label_to_char(int(top3_idxs[j].item())), top3_probs[j].item()) for j in range(3)],
        })
    return results


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image",       required=True)
    parser.add_argument("--weights-dir", default="./weights")
    parser.add_argument("--top3",        action="store_true", help="Show top 3 predictions per crop")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    weights = Path(args.weights_dir)
    ocr_path = weights / "printed_cnn.pth"

    print(f"Loading model from {ocr_path}")
    model = load_printed_model(str(ocr_path), device)

    gray = cv2.imread(args.image, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        print(f"ERROR: Cannot load {args.image}")
        exit(1)

    print(f"Image: {gray.shape[1]}x{gray.shape[0]}\n")

    binary = preprocess(gray)
    crops, space_flags, line_indices = get_all_crops(binary)
    print(f"Total crops: {len(crops)}\n")

    if not crops:
        print("No crops found — check segmentation")
        exit(1)

    results = classify_crops(crops, model, device)

    if args.top3:
        print(f"{'IDX':>4}  {'PRED':>4}  {'CONF':>6}  {'SPACE'}  {'TOP3'}")
        print("─" * 60)
        for i, r in enumerate(results):
            top3_str = "  |  ".join(f"{c}:{p:.2f}" for c, p in r["top3"])
            space_str = "SPACE" if space_flags[i] else ""
            print(f"{i:>4}  {r['pred']:>4}  {r['confidence']:>6.3f}  {space_str:<5}  {top3_str}")

    confs = [r["confidence"] for r in results]
    print(f"\n{'─'*50}")
    print(f"Total chars:      {len(results)}")
    print(f"Mean confidence:  {np.mean(confs):.3f}")
    print(f"High conf (>0.8): {sum(c > 0.8 for c in confs)} ({100*sum(c>0.8 for c in confs)/len(confs):.1f}%)")
    print(f"Low conf (<0.5):  {sum(c < 0.5 for c in confs)} ({100*sum(c<0.5 for c in confs)/len(confs):.1f}%)")

    # Assemble text with spaces and line breaks
    text_lines = []
    current_line = line_indices[0] if line_indices else 0
    current = ""
    for r, is_space, line_idx in zip(results, space_flags, line_indices):
        if line_idx != current_line:
            text_lines.append(current)
            current = ""
            current_line = line_idx
        if is_space:
            current += " "
        current += r["pred"]
    text_lines.append(current)

    raw_text = "\n".join(text_lines)

    vocab = load_vocab("./SimulatedNoisyOffice/tesseract_metadata.csv")
    result = clean(raw_text, vocab, spell=False)

    print(f"\nRaw OCR:")
    print("─" * 60)
    print(result["raw"])

    print(f"\nLayer 1 — char rules:")
    print("─" * 60)
    print(result["layer1"])

    print(f"\nFinal — domain-aware corrected OCR:")
    print("─" * 60)
    print(result["layer2"])
