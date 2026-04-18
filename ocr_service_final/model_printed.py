"""
4-layer CNN for printed character recognition.
Lighter regularization than OCRPCNN — printed chars are clean and consistent.
"""

import torch
import torch.nn as nn

NUM_CLASSES = 47


class PrintedCNN(nn.Module):
    def __init__(self):
        super().__init__()

        self.conv1 = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),        # 28x28 → 14x14
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),        # 14x14 → 7x7
        )
        self.conv3 = nn.Sequential(
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),        # 7x7 → 3x3
        )
        self.conv4 = nn.Sequential(
            nn.Conv2d(128, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            # No MaxPool — preserve spatial info at this scale
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256 * 3 * 3, 512),
            nn.ReLU(),
            nn.Dropout(0.2),           # lighter than before (was 0.3)
            nn.Linear(512, NUM_CLASSES),
        )

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        return self.classifier(x)


def load_printed_model(path: str, device: torch.device) -> "PrintedCNN":
    model = PrintedCNN().to(device)
    model.load_state_dict(torch.load(path, map_location=device))
    model.eval()
    return model


EMNIST_CHARS = (
    '0123456789'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    'abdefghnqrt'
)

def label_to_char(idx: int) -> str:
    if 0 <= idx < len(EMNIST_CHARS):
        return EMNIST_CHARS[idx]
    return "?"
