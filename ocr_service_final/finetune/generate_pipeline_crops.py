"""
Generates labeled training crops by running known text through the exact
same pipeline the model sees at inference time.

Strategy: render one CHARACTER at a time → run through pipeline →
label is guaranteed correct. No alignment issues.

Then renders WORDS for context verification — shows labeled grid
so you can visually confirm labeling is correct before training.

Usage:
    python3 generate_pipeline_crops.py \
        --output-dir ./data/pipeline_crops \
        --verify      # saves verification grids to /tmp/verify/

Output:
    ./data/pipeline_crops/{label_idx}/crop_{i}.png
"""

import argparse
import random
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ── EMNIST class mapping ───────────────────────────────────────────────────────

EMNIST_CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabdefghnqrt'
CHAR_TO_LABEL = {c: i for i, c in enumerate(EMNIST_CHARS)}


# ── Fonts to render with ───────────────────────────────────────────────────────

FONTS = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Courier.ttc",
    "/System/Library/Fonts/Avenir.ttc",
    "/System/Library/Fonts/NewYork.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman Bold Italic.ttf",
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/System/Library/Fonts/Supplemental/Verdana.ttf",
    "/System/Library/Fonts/Supplemental/Verdana Italic.ttf",
    "/System/Library/Fonts/Supplemental/Trebuchet MS.ttf",
    "/System/Library/Fonts/Supplemental/Trebuchet MS Italic.ttf",
    "/System/Library/Fonts/Supplemental/Courier New.ttf",
    "/System/Library/Fonts/Supplemental/Rockwell.ttc",
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/System/Library/Fonts/Supplemental/Seravek.ttc",
    "/System/Library/Fonts/Supplemental/Charter.ttc",
]

FONT_SIZES = [18, 20, 22, 24, 26]


def load_fonts() -> list[tuple]:
    loaded = []
    for path in FONTS:
        if not Path(path).exists():
            continue
        for size in FONT_SIZES:
            try:
                font = ImageFont.truetype(path, size)
                loaded.append((font, Path(path).stem, size))
            except Exception:
                pass
    print(f"Loaded {len(loaded)} font/size combinations")
    return loaded


# ── Pipeline (must match step3_split.py exactly) ───────────────────────────────

def preprocess(gray: np.ndarray) -> np.ndarray:
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary


def normalize_crop(crop: np.ndarray) -> np.ndarray:
    rows = np.any(crop > 0, axis=1)
    cols = np.any(crop > 0, axis=0)
    if rows.any() and cols.any():
        r0, r1 = np.where(rows)[0][[0, -1]]
        c0, c1 = np.where(cols)[0][[0, -1]]
        crop = crop[r0:r1+1, c0:c1+1]
    if crop.size == 0:
        return None
    margin = 3
    ch, cw = crop.shape
    size = max(ch, cw) + margin * 2
    padded = np.zeros((size, size), dtype=np.uint8)
    padded[(size-ch)//2:(size-ch)//2+ch, (size-cw)//2:(size-cw)//2+cw] = crop
    return cv2.resize(padded, (28, 28), interpolation=cv2.INTER_AREA)


# ── Render a single character and extract crop via pipeline ───────────────────

def render_single_char(char: str, font, canvas_size=80) -> np.ndarray:
    """Render one char on white background (document style) → run pipeline."""
    img = Image.new("L", (canvas_size, canvas_size), color=255)  # white bg
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), char, font=font)
    x = (canvas_size - (bbox[2] - bbox[0])) // 2 - bbox[0]
    y = (canvas_size - (bbox[3] - bbox[1])) // 2 - bbox[1]
    draw.text((x, y), char, fill=0, font=font)  # black text

    gray = np.array(img, dtype=np.uint8)
    binary = preprocess(gray)

    # Find the character blob
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    best = None
    best_area = 0
    for i in range(1, num_labels):
        x_, y_, w_, h_, area = stats[i]
        if area > best_area:
            best_area = area
            best = (x_, y_, w_, h_)

    if best is None or best_area < 10:
        return None

    x_, y_, w_, h_ = best
    crop = binary[y_:y_+h_, x_:x_+w_]
    return normalize_crop(crop)


# ── Verification grid ─────────────────────────────────────────────────────────

def save_verification_grid(samples: list[tuple], out_path: str, cols: int = 20):
    """
    Saves a grid image: each cell = crop image + character label below it.
    samples: list of (crop_28x28, char_label, font_name)
    """
    if not samples:
        return

    cell_w, cell_h = 36, 46   # extra height for label text
    rows = (len(samples) + cols - 1) // cols

    grid = np.ones((rows * cell_h, cols * cell_w, 3), dtype=np.uint8) * 240

    for i, (crop, char, font_name) in enumerate(samples):
        r, c = divmod(i, cols)
        y0 = r * cell_h
        x0 = c * cell_w

        # Place crop (center it in cell)
        crop_bgr = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)
        grid[y0:y0+28, x0:x0+28] = crop_bgr

        # Draw character label in red below the crop
        cv2.putText(grid, char,
                    (x0 + 10, y0 + 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 200), 1)

        # Draw thin border around crop
        cv2.rectangle(grid, (x0, y0), (x0+28, y0+28), (180, 180, 180), 1)

    cv2.imwrite(out_path, grid)
    print(f"Grid: {rows} rows × {cols} cols = {len(samples)} samples")


# ── Main generation loop ───────────────────────────────────────────────────────

def generate(args):
    out_dir = Path(args.output_dir)
    verify_dir = Path("/tmp/verify")
    if args.verify:
        verify_dir.mkdir(exist_ok=True)

    fonts = load_fonts()
    if not fonts:
        print("ERROR: No fonts loaded")
        return

    # Create output dirs for each class
    for i in range(len(EMNIST_CHARS)):
        (out_dir / str(i)).mkdir(parents=True, exist_ok=True)

    total = 0
    per_class = {i: 0 for i in range(len(EMNIST_CHARS))}
    verify_samples = []   # one sample per char for grid

    print(f"Generating pipeline crops for {len(EMNIST_CHARS)} classes...")
    print(f"Fonts: {len(fonts)}  |  Augmentations: {args.augmentations}\n")

    for char in EMNIST_CHARS:
        label_idx = CHAR_TO_LABEL[char]
        char_dir  = out_dir / str(label_idx)
        count     = 0
        char_verified = False

        for font, font_name, size in fonts:
            crop = render_single_char(char, font)
            if crop is None:
                continue

            # Save base crop
            path = char_dir / f"{font_name}_{size}_base.png"
            Image.fromarray(crop).save(path)
            count += 1

            # One sample per char for verification grid (use size=22 for consistency)
            if not char_verified and size == 22:
                verify_samples.append((crop, char, font_name))
                char_verified = True

            # Augmented versions — add noise only (shape already normalized)
            for aug_i in range(args.augmentations):
                aug = crop.copy().astype(np.float32) / 255.0
                aug_tensor_np = aug

                r = random.random()
                if r < 0.4:
                    noise = np.random.normal(0, 0.08, aug_tensor_np.shape)
                    aug_tensor_np = np.clip(aug_tensor_np + noise, 0, 1)
                elif r < 0.6:
                    mask = np.random.random(aug_tensor_np.shape) < 0.04
                    aug_tensor_np[mask] = np.random.choice([0.0, 1.0], mask.sum())

                aug_uint8 = (aug_tensor_np * 255).astype(np.uint8)
                aug_path  = char_dir / f"{font_name}_{size}_aug{aug_i}.png"
                Image.fromarray(aug_uint8).save(aug_path)
                count += 1

        per_class[label_idx] = count
        total += count

    print(f"Total crops generated: {total}")
    print(f"Per class — min: {min(per_class.values())}  max: {max(per_class.values())}  avg: {total//len(EMNIST_CHARS)}")
    print(f"Saved to: {out_dir}")
    print(f"\nVerification samples collected: {len(verify_samples)}")
    print(f"Characters covered: {''.join(s[1] for s in verify_samples)}")

    if args.verify and verify_samples:
        grid_path = str(verify_dir / "label_check.png")
        save_verification_grid(verify_samples, grid_path)
        print(f"\nVerification grid: {grid_path}")
        print("Open it and confirm each crop matches its label (red text below each crop).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir",    default="./data/pipeline_crops")
    parser.add_argument("--augmentations", type=int, default=10)
    parser.add_argument("--verify",        action="store_true")
    args = parser.parse_args()
    generate(args)
