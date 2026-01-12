# NOTE: Not currently used. Kept for potential FastAPI-based inference service.

# backend/api/main.py

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
import io
import json
import os

app = FastAPI(title="Landmark Recognition API")

# ----------------------------
# Paths
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "../../ml/models/landmark_resnet18.pth")
CLASS_NAMES_PATH = os.path.join(BASE_DIR, "../../ml/models/class_names.json")

# ----------------------------
# Load classes
# ----------------------------
with open(CLASS_NAMES_PATH, "r") as f:
    classes = json.load(f)

# ----------------------------
# Initialize model
# ----------------------------
model = models.resnet18(weights=None)
model.fc = nn.Linear(model.fc.in_features, len(classes))  # number of classes

# Load checkpoint correctly
checkpoint = torch.load(MODEL_PATH, map_location="cpu")
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

# ----------------------------
# Image transforms
# ----------------------------
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# ----------------------------
# Routes
# ----------------------------
@app.get("/")
def read_root():
    return {"message": "Landmark Recognition API is running!"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_t = transform(image)
        batch_t = torch.unsqueeze(img_t, 0)  # create batch of 1

        with torch.no_grad():
            out = model(batch_t)
             # Convert logits to probabilities
            probabilities = F.softmax(out, dim=1)
            # Get top prediction
            confidence, predicted = torch.max(probabilities, 1)
            predicted_class = classes[predicted.item()]
            confidence_score = confidence.item()
        return JSONResponse(content={
            "prediction": predicted_class,
            "confidence": round(confidence_score, 4)
        })

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
