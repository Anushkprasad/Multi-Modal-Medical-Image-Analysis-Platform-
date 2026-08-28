import torch
import torch.nn as nn


class MultiModalFusion(nn.Module):
    def __init__(self, image_dim=1024, text_dim=768, num_classes=14):
        super().__init__()

        self.classifier = nn.Sequential(
            nn.Linear(image_dim + text_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )

    def forward(self, image_features, text_features):
        fused = torch.cat((image_features, text_features), dim=1)
        return self.classifier(fused)