#!/bin/bash
#SBATCH -J strike3_finetune
#SBATCH -A r00896
#SBATCH --partition=gpu
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH -o finetune_log_%j.out
#SBATCH -e finetune_log_%j.err

module load python/gpu

cd /N/project/Shen_lab_01/exp_wodipg_abhay/luddy_26/ocr_service

echo "Step 1: Generating printed character images..."
python generate_printed_chars.py --output-dir ./data/printed_chars --augmentations 10

echo "Step 2: Fine-tuning model on EMNIST + printed chars (50x repeat)..."
python fine_tune.py \
  --printed-dir  ./data/printed_chars \
  --weights-dir  ./weights \
  --data-dir     ./data \
  --epochs       15 \
  --batch-size   256 \
  --lr           0.0001 \
  --printed-repeat 50

echo "Done."
