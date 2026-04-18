"""
Step 4 — Validate crops before sending to CNN.

Checks each 28x28 crop for:
  - Has enough foreground (not blank)
  - Character is not cut off at edges
  - Foreground is reasonably centered
  - Aspect ratio looks natural
  - Background is black, text is white (correct polarity)

Also saves a visual grid of all crops for quick inspection.

Usage:
    python3 step4_validate.py --crops-dir /tmp/step3_crops
    python3 step4_validate.py --image <path>   (runs full pipeline + validates)

Output:
    /tmp/step4_grid.png   — all crops in a grid, red border = failed check
"""

import argparse
from pathlib import Path

import cv2
import numpy as np


def validate_crop(img: np.ndarray) -> tuple[bool, list[str]]:
    """
    Returns (passed, list_of_issues).
    img is a 28x28 uint8 image, white text on black background.
    """
    issues = []
    h, w = img.shape

    white = (img > 128).sum()
    total = h * w

    # 1. Must have some foreground
    if white < 10:
        issues.append("too few white pixels (blank crop)")

    # 2. Must not be mostly foreground (inverted / all white)
    if white > total * 0.7:
        issues.append("too many white pixels (likely inverted)")

    # 3. Character must not be cut off at edges
    top_row    = img[0, :].max()
    bottom_row = img[-1, :].max()
    left_col   = img[:, 0].max()
    right_col  = img[:, -1].max()
    edge_thresh = 128

    if top_row > edge_thresh:
        issues.append("cut off at top")
    if bottom_row > edge_thresh:
        issues.append("cut off at bottom")
    if left_col > edge_thresh:
        issues.append("cut off at left")
    if right_col > edge_thresh:
        issues.append("cut off at right")

    # 4. Character should be roughly centered
    rows_with_fg = np.where(img.max(axis=1) > 128)[0]
    cols_with_fg = np.where(img.max(axis=0) > 128)[0]

    if len(rows_with_fg) > 0 and len(cols_with_fg) > 0:
        cy = (rows_with_fg[0] + rows_with_fg[-1]) / 2
        cx = (cols_with_fg[0] + cols_with_fg[-1]) / 2
        if abs(cy - 14) > 8:
            issues.append(f"not centered vertically (cy={cy:.1f})")
        if abs(cx - 14) > 8:
            issues.append(f"not centered horizontally (cx={cx:.1f})")

        # 5. Aspect ratio — character height vs width should be reasonable
        char_h = rows_with_fg[-1] - rows_with_fg[0] + 1
        char_w = cols_with_fg[-1] - cols_with_fg[0] + 1
        ratio = char_h / max(char_w, 1)
        if ratio > 5.0:
            issues.append(f"too tall and narrow (h/w={ratio:.1f})")
        if ratio < 0.2:
            issues.append(f"too wide and flat (h/w={ratio:.1f})")

    return len(issues) == 0, issues


def make_grid(images: list, labels: list[str], passed: list[bool], cols: int = 10) -> np.ndarray:
    """Arrange crops into a grid. Red border = failed, green = passed."""
    cell = 32  # 28px + 2px border each side
    rows = (len(images) + cols - 1) // cols
    grid = np.zeros((rows * cell, cols * cell, 3), dtype=np.uint8)

    for i, (img, passed_check) in enumerate(zip(images, passed)):
        r, c = divmod(i, cols)
        color_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        # Add 2px border
        bordered = cv2.copyMakeBorder(color_img, 2, 2, 2, 2, cv2.BORDER_CONSTANT,
                                      value=(0, 200, 0) if passed_check else (0, 0, 220))
        grid[r*cell:(r+1)*cell, c*cell:(c+1)*cell] = bordered

    return grid


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--crops-dir", default="/tmp/step3_crops",
                        help="Directory of 28x28 PNG crops from step3")
    parser.add_argument("--image", default=None,
                        help="If provided, runs full pipeline first then validates")
    args = parser.parse_args()

    # Optionally run full pipeline first
    if args.image:
        import subprocess, sys
        print("Running step3_split.py first...")
        subprocess.run([sys.executable, "step3_split.py", "--image", args.image], check=True)
        print()

    crops_dir = Path(args.crops_dir)
    crop_files = sorted(crops_dir.glob("crop_*.png"))

    if not crop_files:
        print(f"No crops found in {crops_dir}")
        exit(1)

    print(f"Validating {len(crop_files)} crops...\n")

    images, all_passed, all_issues = [], [], []

    for f in crop_files:
        img = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        passed, issues = validate_crop(img)
        images.append(img)
        all_passed.append(passed)
        all_issues.append(issues)

        status = "OK" if passed else "FAIL"
        issue_str = ", ".join(issues) if issues else ""
        print(f"  {f.name}: {status}  {issue_str}")

    total   = len(images)
    n_pass  = sum(all_passed)
    n_fail  = total - n_pass

    print(f"\nResults: {n_pass}/{total} passed  ({n_fail} failed)")
    print(f"Pass rate: {100*n_pass/total:.1f}%")

    grid = make_grid(images, [f.name for f in crop_files], all_passed)
    cv2.imwrite("/tmp/step4_grid.png", grid)
    print(f"\nSaved grid: /tmp/step4_grid.png")
    print("Green border = passed, Red border = failed")
