import json
from torchvision import datasets, transforms
from pathlib import Path

DATA_DIR = Path("data/raw")
OUTPUT_PATH = Path("ml/models/class_names.json")

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

dataset = datasets.ImageFolder(DATA_DIR, transform=transform)

class_names = dataset.classes  # index → class name

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_PATH, "w") as f:
    json.dump(class_names, f)

print(f"Saved {len(class_names)} classes to {OUTPUT_PATH}")