import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import os

# Paths (DO NOT CHANGE STRUCTURE)
MODEL_PATH = os.path.join("ml", "models", "landmark_resnet18.pth")
DATA_DIR = os.path.join("data", "raw")
IMG_SIZE = 224

# Device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# Image preprocessing (same as training)
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# Load model
def load_model():
    checkpoint = torch.load(MODEL_PATH, map_location=device)

    model = models.resnet18(pretrained=False)
    model.fc = nn.Linear(model.fc.in_features, len(checkpoint["classes"]))

    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    return model, checkpoint["classes"]


model, classes = load_model()

# Predict function
def predict_image(image_path: str) -> str:
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(image)
        _, predicted = torch.max(outputs, 1)

    return classes[predicted.item()]


# CLI testing (optional)
if __name__ == "__main__":
    test_image = input("Enter image path: ")
    prediction = predict_image(test_image)
    print("Predicted Landmark:", prediction)
