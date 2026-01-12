# ml/inference/predict.py

import io
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms
import os

# ---------------- Paths ----------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "landmark_resnet18.pth")

device = torch.device("cpu")

# ---------------- Transforms ----------------
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ---------------- Load model once ----------------
def load_model():
    checkpoint = torch.load(MODEL_PATH, map_location=device)

    classes = checkpoint["classes"]
    num_classes = len(classes)

    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    return model, classes

model, classes = load_model()

# ---------------- Prediction function ----------------
def predict_image(image_bytes: bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        outputs = model(img_tensor)
        probs = torch.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probs, 1)

    return {
        "label": classes[predicted.item()],
        "confidence": round(confidence.item(), 4)
    }
