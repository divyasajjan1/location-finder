import io
import json
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms
import os

# ---------------- Paths and Model Loading ----------------
# Adjusted BASE_DIR for predict.py being in backend/api/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, "models", "landmark_resnet18.pth")
CLASS_NAMES_PATH = os.path.join(BASE_DIR, "models", "class_names.json")

device = torch.device("cpu") # Consider using "cuda" if a GPU is available

model = None
classes = None

# ---------------- Transforms ----------------
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ---------------- Load model and class names once ----------------
def load_model_and_classes():
    global model, classes
    if model is None or classes is None:
        # Load class names
        with open(CLASS_NAMES_PATH) as f:
            classes = json.load(f)

        checkpoint = torch.load(MODEL_PATH, map_location=device)
        num_classes = len(classes)

        model = models.resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
    return model, classes

# ---------------- Prediction function ----------------
def predict_image(image_bytes: bytes):
    model, classes = load_model_and_classes()

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

