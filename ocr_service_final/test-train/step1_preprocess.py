"""
Step 1 — Preprocessing only.
Applies classical denoising + adaptive threshold and saves result.

Usage:
    python step1_preprocess.py --image <path>

Output:
    /tmp/step1_gray.png    — grayscale input
    /tmp/step1_denoised.png — after denoising
    /tmp/step1_binary.png  — after binarization (what segmenter will see)
"""

import argparse
import numpy as np
import cv2


def detect_noise_type(gray: np.ndarray) -> str:
    flat = gray.flatten().astype(np.float32)
    extreme_ratio = ((flat < 10) | (flat > 245)).sum() / len(flat)
    return "salt_pepper" if extreme_ratio > 0.05 else "gaussian"


def preprocess(gray: np.ndarray) -> tuple[np.ndarray, np.ndarray, str]:
    noise_type = detect_noise_type(gray)
    print(f"Detected noise type: {noise_type}")

    if noise_type == "salt_pepper":
        denoised = cv2.medianBlur(gray, 3)
    else:
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

    binary = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=15,
        C=10
    )

    return denoised, binary, noise_type


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    args = parser.parse_args()

    gray = cv2.imread(args.image, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        print(f"ERROR: Cannot load {args.image}")
        exit(1)

    print(f"Image size: {gray.shape[1]}x{gray.shape[0]}")

    denoised, binary, noise_type = preprocess(gray)

    cv2.imwrite("/tmp/step1_gray.png",     gray)
    cv2.imwrite("/tmp/step1_denoised.png", denoised)
    cv2.imwrite("/tmp/step1_binary.png",   binary)

    white_pixels = (binary == 255).sum()
    total_pixels = binary.size
    print(f"Binary: {white_pixels} white pixels ({100*white_pixels/total_pixels:.1f}% of image)")
    print(f"\nSaved:")
    print(f"  /tmp/step1_gray.png")
    print(f"  /tmp/step1_denoised.png")
    print(f"  /tmp/step1_binary.png")
    print(f"\nOpen these and check if text is clearly visible as white on black.")
