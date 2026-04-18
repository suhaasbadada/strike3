#!/bin/bash
#SBATCH -J strike3_printed
#SBATCH -A r00896
#SBATCH --partition=gpu
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:30:00
#SBATCH -o printed_log_%j.out
#SBATCH -e printed_log_%j.err

module load python/gpu

cd /N/project/Shen_lab_01/exp_wodipg_abhay/luddy_26/ocr_service

echo "Step 1: Generating printed chars with more augmentations..."
python generate_printed_chars.py \
  --output-dir ./data/printed_chars \
  --augmentations 15

echo "Step 2: Training PrintedCNN from scratch..."
python train_printed_only.py \
  --printed-dir ./data/printed_chars \
  --weights-dir ./weights \
  --epochs      30 \
  --batch-size  128 \
  --lr          0.001 \
  --early-stop  6

echo "Done."
