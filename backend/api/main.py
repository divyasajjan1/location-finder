from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import torch
import torchvision.transforms as transforms
import io
import json
from pathlib import Path
from torchvision import models

# ------------------
# App init
# ------------------
app = FastAPI(title="Landmark Finder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------
# Paths
# ------------------
BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "ml" / "models" / "landmark_resnet18.pth"
CLASS_MAP_PATH = BASE_DIR / "ml" / "models" / "class_names.json"

# ------------------
# Load classes
# ------------------
with open(CLASS_MAP_PATH, "r") as f:
    class_names = json.load(f)

num_classes = len(class_names)

# ------------------
# Load model
# ------------------
model = models.resnet18(weights=None)
model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
model.eval()

# ------------------
# Transforms
# ------------------
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# ------------------
# Routes
# ------------------
@app.get("/")
def health_check():
    return {"status": "API is running"}


@app.post("/predict")
def predict_landmark(file: UploadFile = File(...)):
    image_bytes = file.file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    input_tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        outputs = model(input_tensor)
        probabilities = torch.softmax(outputs, dim=1)
        confidence, predicted_idx = torch.max(probabilities, 1)

    predicted_landmark = class_names[str(predicted_idx.item())]

    return {
        "predicted_landmark": predicted_landmark,
        "confidence": round(confidence.item(), 4)
    }
