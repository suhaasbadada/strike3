"""
Train PrintedCNN from scratch on synthetic printed characters only.
No EMNIST — pure printed font data.

Usage:
    python train_printed_only.py \
        --printed-dir ./data/printed_chars \
        --weights-dir ./weights \
        --epochs 30
"""

import argparse
import random
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import transforms

from model_printed import PrintedCNN, NUM_CLASSES
from noise import apply_gaussian, apply_salt_pepper


class PrintedCharDataset(Dataset):
    def __init__(self, root_dir: str, augment: bool = True):
        self.augment = augment
        self.samples: list[tuple[Path, int]] = []

        root = Path(root_dir)
        for label_dir in sorted(root.iterdir()):
            if not label_dir.is_dir():
                continue
            try:
                label = int(label_dir.name)
            except ValueError:
                continue
            for img_path in label_dir.glob("*.png"):
                self.samples.append((img_path, label))

        print(f"Dataset: {len(self.samples)} images, {NUM_CLASSES} classes")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        img = Image.open(img_path).convert("L")
        tensor = transforms.ToTensor()(img)   # (1, 28, 28) float [0,1]

        if self.augment:
            r = random.random()
            if r < 0.3:
                tensor = apply_gaussian(tensor)
            elif r < 0.5:
                tensor = apply_salt_pepper(tensor)

        return tensor, label


def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # ── Dataset ───────────────────────────────────────────────────────────────
    # Two separate instances to avoid shared augment flag
    train_dataset = PrintedCharDataset(args.printed_dir, augment=True)
    val_dataset   = PrintedCharDataset(args.printed_dir, augment=False)

    val_size   = int(len(train_dataset) * 0.1)
    train_size = len(train_dataset) - val_size

    train_indices, val_indices = torch.utils.data.random_split(
        range(len(train_dataset)), [train_size, val_size],
        generator=torch.Generator().manual_seed(42)
    )

    from torch.utils.data import Subset
    train_set = Subset(train_dataset, train_indices.indices)
    val_set   = Subset(val_dataset,   val_indices.indices)

    train_loader = DataLoader(train_set, batch_size=args.batch_size,
                              shuffle=True, num_workers=2, pin_memory=True)
    val_loader   = DataLoader(val_set,   batch_size=args.batch_size,
                              shuffle=False, num_workers=2, pin_memory=True)

    print(f"Train: {train_size}  Val: {val_size}\n")

    # ── Model ─────────────────────────────────────────────────────────────────
    model = PrintedCNN().to(device)
    out_path = Path(args.weights_dir) / "printed_cnn.pth"

    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", patience=3, factor=0.5
    )
    criterion = nn.CrossEntropyLoss()

    best_acc = 0.0
    patience_counter = 0

    print(f"Training for up to {args.epochs} epochs | LR: {args.lr}\n")

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()

        model.train()
        train_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(images), labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        train_loss /= len(train_loader)

        model.eval()
        correct = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                preds = model(images).argmax(dim=1)
                correct += (preds == labels).sum().item()

        val_acc = correct / val_size
        elapsed = time.time() - t0

        print(f"Epoch {epoch:>3}/{args.epochs} | "
              f"Loss: {train_loss:.4f} | "
              f"Val Acc: {val_acc:.4f} | "
              f"Time: {elapsed:.1f}s")

        scheduler.step(val_acc)

        if val_acc > best_acc:
            best_acc = val_acc
            patience_counter = 0
            torch.save(model.state_dict(), out_path)
            print(f"  ✓ Saved (acc={best_acc:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= args.early_stop:
                print(f"\nEarly stopping after {args.early_stop} epochs no improvement")
                break

    print(f"\nDone. Best val accuracy: {best_acc:.4f}")
    print(f"Weights saved: {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--printed-dir", default="./data/printed_chars")
    parser.add_argument("--weights-dir", default="./weights")
    parser.add_argument("--epochs",      type=int,   default=30)
    parser.add_argument("--batch-size",  type=int,   default=128)
    parser.add_argument("--lr",          type=float, default=0.001)
    parser.add_argument("--early-stop",  type=int,   default=6)
    args = parser.parse_args()
    train(args)
