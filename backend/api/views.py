import os
import io
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
import torch
from torchvision import models, transforms

from api.utils.user_location import get_user_location
from api.utils.distance_to_landmark import distance_to_landmark

# Load class names
CLASS_NAMES_PATH = os.path.join(os.path.dirname(__file__), "../../ml/models/class_names.json")
import json
with open(CLASS_NAMES_PATH) as f:
    classes = json.load(f)

# Load model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../ml/models/landmark_resnet18.pth")
device = "cpu"
model = models.resnet18(weights=None)
model.fc = torch.nn.Linear(model.fc.in_features, len(classes))
checkpoint = torch.load(MODEL_PATH, map_location=device)
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

# Image preprocessing
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

@csrf_exempt
def predict_landmark(request):
    print("FILES:", request.FILES)
    print("POST:", request.POST)
    if request.method != "POST":
        return JsonResponse({"error": "POST an image file"}, status=400)

    try:
        image_file = request.FILES["file"]
        image = Image.open(io.BytesIO(image_file.read())).convert("RGB")
        img_tensor = transform(image).unsqueeze(0)

        # Predict
        with torch.no_grad():
            outputs = model(img_tensor)
            _, predicted = torch.max(outputs, 1)
            predicted_landmark = classes[predicted.item()]

        # Get user coordinates
        user_lat, user_lon = get_user_location()

        # Calculate distance
        distance_km = distance_to_landmark(predicted_landmark)

        return JsonResponse({
            "predicted_landmark": predicted_landmark,
            "user_location": {"lat": user_lat, "lon": user_lon},
            "distance_km": round(distance_km, 2)
        })

    except KeyError:
        return JsonResponse({"error": "No image file provided"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
