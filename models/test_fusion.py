import torch
from fusion import MultiModalFusion

model = MultiModalFusion()
model.eval()

image_features = torch.randn(1, 1024)
text_features = torch.randn(1, 768)

with torch.no_grad():
    logits = model(image_features, text_features)
    probabilities = torch.softmax(logits, dim=1)

classes = [
    "Atelectasis",
    "Cardiomegaly",
    "Consolidation",
    "Edema",
    "Effusion",
    "Emphysema",
    "Fibrosis",
    "Hernia",
    "Infiltration",
    "Mass",
    "Nodule",
    "Pleural Thickening",
    "Pneumonia",
    "Pneumothorax"
]

for name, prob in zip(classes, probabilities[0]):
    print(f"{name}: {prob.item():.4f}")