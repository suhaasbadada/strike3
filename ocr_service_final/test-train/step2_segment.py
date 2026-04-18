"""
Step 2 — Segmentation with line-first approach.

Pipeline:
  binary image → lines → chunks → split wide chunks → single chars

Usage:
    python3 step2_segment.py --image <path>

Output:
    /tmp/step2_boxes.png   — bounding boxes drawn (each color = one line)
    /tmp/step2_crops/      — individual 28x28 character crops
"""

import argparse
from pathlib import Path

import cv2
import numpy as np


# Step 1: Preprocessing 

def preprocess(gray: np.ndarray) -> np.ndarray:
    """Variant A + gentle erosion — best balance of stroke preservation vs separation."""
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (1, 1))
    binary = cv2.erode(binary, kernel, iterations=1)
    return binary


# Step 2: Line segmentation via horizontal projection

def find_lines(binary: np.ndarray) -> list[tuple[int, int]]:
    """
    Sum white pixels across each row.
    Rows with very low sum = gaps between lines.
    Returns list of (y_start, y_end) for each line strip.
    """
    h_proj = binary.sum(axis=1)  # sum across columns, one value per row

    threshold = binary.shape[1] * 0.01  # row must have >1% white pixels to count
    in_line = False
    lines = []
    y_start = 0

    for y, val in enumerate(h_proj):
        if not in_line and val > threshold:
            in_line = True
            y_start = y
        elif in_line and val <= threshold:
            in_line = False
            if y - y_start > 5:  # ignore tiny strips
                lines.append((y_start, y))

    if in_line:
        lines.append((y_start, len(h_proj)))

    return lines


# Step 3: Get chunks within a line via connected components

def find_chunks_in_line(binary: np.ndarray, y_start: int, y_end: int) -> list[dict]:
    """Extract connected component blobs within a line strip."""
    strip = binary[y_start:y_end, :]

    num_labels, _, stats, centroids = cv2.connectedComponentsWithStats(strip, connectivity=8)

    strip_area = strip.shape[0] * strip.shape[1]
    chunks = []

    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        cx, cy = centroids[i]

        if area < 20:                   continue  # noise
        if area > strip_area * 0.8:     continue  # background artifact
        if w < 2 or h < 2:             continue  # degenerate

        chunks.append({
            "x": int(x),
            "y": int(y) + y_start,   # offset back to full image coords
            "w": int(w),
            "h": int(h),
            "cx": float(cx),
            "cy": float(cy) + y_start,
            "area": int(area),
        })

    return sorted(chunks, key=lambda c: c["x"])


# Step 4: Split wide chunks via vertical projection valleys

def estimate_char_width(chunks: list[dict]) -> float:
    """Median width of all chunks as a proxy for single character width."""
    widths = sorted([c["w"] for c in chunks])
    # Use lower half to avoid wide blobs skewing estimate
    lower = widths[:max(1, len(widths) // 2)]
    return float(np.median(lower))


def split_chunk(binary: np.ndarray, chunk: dict, expected_w: float) -> list[dict]:
    """
    Split a wide chunk using vertical projection valleys.
    Recursively splits until each piece is character-width.
    """
    x, y, w, h = chunk["x"], chunk["y"], chunk["w"], chunk["h"]
    crop = binary[y:y+h, x:x+w]

    v_proj = crop.sum(axis=0).astype(np.float32)

    # Find local minima
    valleys = []
    for i in range(1, len(v_proj) - 1):
        if v_proj[i] < v_proj[i-1] and v_proj[i] < v_proj[i+1]:
            valleys.append((i, v_proj[i]))

    if not valleys:
        return [chunk]

    # Pick valley closest to center with lowest projection
    center = w / 2
    max_proj = v_proj.max() if v_proj.max() > 0 else 1
    best = min(valleys, key=lambda v: v[1] / max_proj + abs(v[0] - center) / w)
    split_col = best[0]

    left_w  = split_col
    right_w = w - split_col

    if left_w < 3 or right_w < 3:
        return [chunk]

    left_chunk  = {"x": x,              "y": y, "w": left_w,  "h": h,
                   "cx": x + left_w/2,  "cy": y + h/2, "area": int(crop[:, :split_col].sum())}
    right_chunk = {"x": x + split_col,  "y": y, "w": right_w, "h": h,
                   "cx": x + split_col + right_w/2, "cy": y + h/2,
                   "area": int(crop[:, split_col:].sum())}

    result = []
    # Recursively split if still too wide
    for part in [left_chunk, right_chunk]:
        if part["w"] > expected_w * 1.6:
            result.extend(split_chunk(binary, part, expected_w))
        else:
            result.append(part)

    return result


# Full pipeline

def segment(binary: np.ndarray) -> tuple[list[list[dict]], list[tuple[int,int]]]:
    """Returns (lines_of_chars, line_bounds) where each line is a list of char dicts."""
    line_bounds = find_lines(binary)
    print(f"  Lines detected: {len(line_bounds)}")

    all_lines = []
    for y_start, y_end in line_bounds:
        chunks = find_chunks_in_line(binary, y_start, y_end)
        if not chunks:
            continue
        all_lines.append(chunks)

    # Estimate char width from all chunks across all lines
    all_chunks = [c for line in all_lines for c in line]
    if not all_chunks:
        return [], line_bounds

    expected_w = estimate_char_width(all_chunks)
    print(f"  Estimated char width: {expected_w:.1f}px")

    # Split wide chunks
    split_lines = []
    for line in all_lines:
        split_line = []
        for chunk in line:
            if chunk["w"] > expected_w * 1.6:
                parts = split_chunk(binary, chunk, expected_w)
                split_line.extend(parts)
            else:
                split_line.append(chunk)
        split_lines.append(sorted(split_line, key=lambda c: c["x"]))

    return split_lines, line_bounds


# Main

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
    lines, line_bounds = segment(binary)

    total_chars = sum(len(l) for l in lines)
    print(f"  Total chars after split: {total_chars}")
    for i, line in enumerate(lines):
        print(f"  Line {i+1}: {len(line)} chars")

    # Visualize — draw boxes, each line a different color
    vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    colors = [(0,255,0), (0,180,255), (255,100,0), (180,0,255),
              (0,255,200), (255,255,0), (200,0,255), (0,100,255)]

    for line_idx, line in enumerate(lines):
        color = colors[line_idx % len(colors)]
        for chunk in line:
            cv2.rectangle(vis,
                (chunk["x"], chunk["y"]),
                (chunk["x"] + chunk["w"], chunk["y"] + chunk["h"]),
                color, 1)

    cv2.imwrite("/tmp/step2_boxes.png", vis)
    print(f"\nSaved: /tmp/step2_boxes.png")
    print("Each color = one line. Each box should wrap one character.")

    # Save first 20 crops
    crops_dir = Path("/tmp/step2_crops")
    crops_dir.mkdir(exist_ok=True)

    all_chars = [c for line in lines for c in line]
    for i, chunk in enumerate(all_chars[:20]):
        x, y, w, h = chunk["x"], chunk["y"], chunk["w"], chunk["h"]
        crop = binary[y:y+h, x:x+w]
        resized = cv2.resize(crop, (28, 28), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(crops_dir / f"crop_{i:03d}.png"), resized)

    print(f"Saved first 20 crops to /tmp/step2_crops/")
