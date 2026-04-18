"""
Step 3 — Split wide blobs into individual characters using vertical projection.

Pipeline:
  For each line:
    sort blobs left to right
    for each blob:
      if roughly character-sized → keep
      if too wide → split at vertical projection valleys

Usage:
    python3 step3_split.py --image <path>

Output:
    /tmp/step3_before.png  — boxes before splitting
    /tmp/step3_after.png   — boxes after splitting
    /tmp/step3_crops/      — final 28x28 character crops
"""

import argparse
from pathlib import Path

import cv2
import numpy as np


# ── Preprocessing (locked: Otsu + gentle erosion) ─────────────────────────────

def preprocess(gray: np.ndarray) -> np.ndarray:
    """Auto-detect image polarity so text is always white on black."""
    if gray.mean() < 127:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary


# ── Line segmentation (locked from Step 2) ────────────────────────────────────

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


def find_chunks_in_line(binary: np.ndarray, y_start: int, y_end: int) -> list[dict]:
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


# ── Step 3: Estimate char width + split wide blobs ─────────────────────────────

def estimate_line_stats(chunks: list[dict]) -> dict:
    """Estimate per-line stats: median width, height, aspect ratio."""
    widths  = sorted(c["w"] for c in chunks)
    heights = [c["h"] for c in chunks]
    lower_w = widths[:max(1, len(widths) // 2)]
    return {
        "expected_w": float(np.median(lower_w)),
        "median_h":   float(np.median(heights)),
    }


def find_valleys(v_proj: np.ndarray) -> list[tuple[int, float]]:
    v_smooth = np.convolve(v_proj, np.ones(5) / 5, mode="same")
    valleys = []
    for i in range(1, len(v_smooth) - 1):
        if v_smooth[i] < v_smooth[i-1] and v_smooth[i] < v_smooth[i+1]:
            valleys.append((i, float(v_smooth[i])))
    return valleys


def is_suspicious(blob: dict, expected_w: float, median_h: float) -> bool:
    """Returns True if blob likely contains multiple characters."""
    w, h = blob["w"], blob["h"]
    if w > expected_w * 1.6:
        return True
    if h > 0 and w / h > 1.0:
        return True
    return False


def make_blob(x, y, w, h, crop_slice) -> dict:
    return {
        "x": x, "y": y, "w": w, "h": h,
        "cx": x + w / 2, "cy": y + h / 2,
        "area": int(crop_slice.sum()),
    }


def validate_piece(piece: dict, expected_w: float, binary: np.ndarray) -> bool:
    """Reject pieces that are too tiny or nearly blank."""
    if piece["w"] < expected_w * 0.3:
        return False
    x, y, w, h = piece["x"], piece["y"], piece["w"], piece["h"]
    crop = binary[y:y+h, x:x+w]
    white_ratio = (crop > 0).sum() / max(crop.size, 1)
    if white_ratio < 0.03:
        return False
    return True


def multi_split(binary: np.ndarray, blob: dict, expected_w: float) -> list[dict]:
    """
    Split a suspicious blob at ALL valid deep valleys.
    - Finds all valleys below threshold, separated by min distance
    - Splits into multiple pieces in one pass
    - Validates each piece — discards blank/tiny ones
    - Falls back to original blob if split produces bad pieces
    """
    x, y, w, h = blob["x"], blob["y"], blob["w"], blob["h"]
    crop = binary[y:y+h, x:x+w]
    v_proj = crop.sum(axis=0).astype(np.float32)
    max_proj = v_proj.max() if v_proj.max() > 0 else 1

    # Find deep valleys only
    all_valleys = [(i, v) for i, v in find_valleys(v_proj) if v < 0.35 * max_proj]

    if not all_valleys:
        return [blob]

    # Keep valleys separated by at least 0.4 * expected_w to avoid over-splitting
    min_sep = max(int(expected_w * 0.4), 4)
    filtered = [all_valleys[0]]
    for valley in all_valleys[1:]:
        if valley[0] - filtered[-1][0] >= min_sep:
            filtered.append(valley)

    if not filtered:
        return [blob]

    # Build split points
    split_cols = sorted(v[0] for v in filtered)

    # Split into pieces
    boundaries = [0] + split_cols + [w]
    pieces = []
    for i in range(len(boundaries) - 1):
        c0, c1 = boundaries[i], boundaries[i+1]
        piece_w = c1 - c0
        if piece_w < 2:
            continue
        piece = make_blob(x + c0, y, piece_w, h, crop[:, c0:c1])
        pieces.append(piece)

    # Validate all pieces
    valid = [p for p in pieces if validate_piece(p, expected_w, binary)]

    # If validation throws away too many, keep original
    if len(valid) < 2:
        return [blob]

    return valid


def split_all_lines(binary, lines_chunks):
    if not lines_chunks:
        return lines_chunks

    split_lines = []
    total_before = total_after = 0

    for line in lines_chunks:
        total_before += len(line)

        stats = estimate_line_stats(line)
        expected_w = stats["expected_w"]
        median_h   = stats["median_h"]

        split_line = []
        for blob in line:
            if is_suspicious(blob, expected_w, median_h):
                parts = multi_split(binary, blob, expected_w)
            else:
                parts = [blob]
            split_line.extend(parts)
        split_line = sorted(split_line, key=lambda c: c["x"])
        split_lines.append(split_line)
        total_after += len(split_line)

    print(f"  Blobs before split: {total_before}")
    print(f"  Blobs after split:  {total_after}")
    return split_lines


# ── Visualization helper ───────────────────────────────────────────────────────

def draw_boxes(gray, lines, title=""):
    vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    colors = [(0,255,0),(0,180,255),(255,100,0),(180,0,255),(0,255,200),(255,255,0)]
    for line_idx, line in enumerate(lines):
        color = colors[line_idx % len(colors)]
        for blob in line:
            cv2.rectangle(vis,
                (blob["x"], blob["y"]),
                (blob["x"]+blob["w"], blob["y"]+blob["h"]),
                color, 1)
    if title:
        cv2.putText(vis, title, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2)
    return vis


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    args = parser.parse_args()

    gray = cv2.imread(args.image, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        print(f"ERROR: Cannot load {args.image}")
        exit(1)

    print(f"Image: {gray.shape[1]}x{gray.shape[0]}")

    binary = preprocess(gray)

    line_bounds = find_lines(binary)
    print(f"Lines detected: {len(line_bounds)}")

    lines_chunks = []
    for y_start, y_end in line_bounds:
        chunks = find_chunks_in_line(binary, y_start, y_end)
        if chunks:
            lines_chunks.append(chunks)

    before_vis = draw_boxes(gray, lines_chunks, "BEFORE split")

    print("Splitting wide blobs...")
    split_lines = split_all_lines(binary, lines_chunks)

    after_vis = draw_boxes(gray, split_lines, "AFTER split")

    for i, line in enumerate(split_lines):
        print(f"  Line {i+1}: {len(line)} chars")

    cv2.imwrite("/tmp/step3_before.png", before_vis)
    cv2.imwrite("/tmp/step3_after.png",  after_vis)
    print("\nSaved: /tmp/step3_before.png  /tmp/step3_after.png")

    # Save all crops
    crops_dir = Path("/tmp/step3_crops")
    crops_dir.mkdir(exist_ok=True)

    all_chars = [c for line in split_lines for c in line]
    for i, blob in enumerate(all_chars):
        x, y, w, h = blob["x"], blob["y"], blob["w"], blob["h"]
        crop = binary[y:y+h, x:x+w]

        # Fix 3: trim to tight foreground bounding box before padding
        rows = np.any(crop > 0, axis=1)
        cols = np.any(crop > 0, axis=0)
        if rows.any() and cols.any():
            r0, r1 = np.where(rows)[0][[0, -1]]
            c0, c1 = np.where(cols)[0][[0, -1]]
            crop = crop[r0:r1+1, c0:c1+1]

        if crop.size == 0:
            continue

        # Add margin so character doesn't touch edges after resize
        margin = 3
        ch, cw = crop.shape
        size = max(ch, cw) + margin * 2
        padded = np.zeros((size, size), dtype=np.uint8)
        y_off = (size - ch) // 2
        x_off = (size - cw) // 2
        padded[y_off:y_off+ch, x_off:x_off+cw] = crop

        resized = cv2.resize(padded, (28, 28), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(crops_dir / f"crop_{i:03d}.png"), resized)

    print(f"Saved first 30 crops to /tmp/step3_crops/")
    print("\nCheck: each box = one char, crops look like recognizable letters.")
