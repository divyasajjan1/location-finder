import os
import torch
from torch import nn, optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms, models

# ---------------- Config ----------------
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "raw")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
BATCH_SIZE = 16
EPOCHS = 5
LR = 1e-3
IMG_SIZE = 224
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ---------------- Transforms ----------------
data_transforms = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],   # mean for pretrained models
                         [0.229, 0.224, 0.225])  # std
])

# ---------------- Dataset ----------------
full_dataset = datasets.ImageFolder(DATA_DIR, transform=data_transforms)

# Split dataset into train/val/test
total_len = len(full_dataset)
train_len = int(0.7 * total_len)
val_len = int(0.15 * total_len)
test_len = total_len - train_len - val_len

train_dataset, val_dataset, test_dataset = random_split(
    full_dataset, [train_len, val_len, test_len],
    generator=torch.Generator().manual_seed(42)
)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

# ---------------- Model ----------------
num_classes = len(full_dataset.classes)
model = models.resnet18(pretrained=True)
model.fc = nn.Linear(model.fc.in_features, num_classes)
model = model.to(DEVICE)

# ---------------- Loss & Optimizer ----------------
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LR)

# ---------------- Training Loop ----------------
for epoch in range(EPOCHS):
    model.train()
    running_loss = 0.0
    for imgs, labels in train_loader:
        imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()
        outputs = model(imgs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * imgs.size(0)
    epoch_loss = running_loss / len(train_loader.dataset)

    # Validation
    model.eval()
    correct = 0
    with torch.no_grad():
        for imgs, labels in val_loader:
            imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
            outputs = model(imgs)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels).item()
    val_acc = correct / len(val_loader.dataset)

    print(f"Epoch [{epoch+1}/{EPOCHS}] Loss: {epoch_loss:.4f} Val Acc: {val_acc:.4f}")

# ---------------- Save Model ----------------
os.makedirs(MODEL_DIR, exist_ok=True)
torch.save({
    "model_state_dict": model.state_dict(),
    "classes": full_dataset.classes
}, os.path.join(MODEL_DIR, "landmark_resnet18.pth"))

print(f"Training complete! Model saved at {os.path.join(MODEL_DIR, 'landmark_resnet18.pth')}")
