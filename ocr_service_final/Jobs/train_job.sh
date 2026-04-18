#!/bin/bash
#SBATCH -J strike3_ocr_train
#SBATCH -A r00896
#SBATCH --partition=gpu
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH -o train_log_%j.out
#SBATCH -e train_log_%j.err

module load python/gpu

cd /N/project/Shen_lab_01/exp_wodipg_abhay/luddy_26/ocr_service

python train_ocr.py \
  --data-dir ./data \
  --weights-dir ./weights
