from transformers import AutoTokenizer, AutoModel
import torch

MODEL_NAME = "emilyalsentzer/Bio_ClinicalBERT"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

text = "Patient has fever and persistent cough."

inputs = tokenizer(
    text,
    return_tensors="pt",
    padding=True,
    truncation=True
)

with torch.no_grad():
    outputs = model(**inputs)

embedding = outputs.last_hidden_state[:, 0, :]

print("Clinical note:", text)
print("Embedding shape:", embedding.shape)