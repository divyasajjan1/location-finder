import os
from pathlib import Path
import torch
from torch import nn, optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms, models
import json

# ---------------- Config ----------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BASE_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
MODEL_DIR = os.path.join(BASE_DIR, "models")
CLASS_NAMES_PATH = os.path.join(MODEL_DIR, "class_names.json")
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

def train_model(landmark_name: str):
    print(f"Starting training for landmark: {landmark_name}")

    # DEBUG: See exactly what Python sees on the disk
    disk_folders = [f for f in os.listdir(BASE_DATA_DIR) if os.path.isdir(os.path.join(BASE_DATA_DIR, f))]
    print(f"Folders found on disk: {disk_folders}")
    # ImageFolder automatically expects subdirectories as classes
    # e.g., BASE_DATA_DIR/landmark1/, BASE_DATA_DIR/landmark2/
    full_dataset = datasets.ImageFolder(BASE_DATA_DIR, transform=data_transforms)
    print(f"Classes recognized by PyTorch: {full_dataset.classes}")
    num_classes = len(full_dataset.classes)
    print(f"Total classes to train: {num_classes}") 
    if landmark_name not in full_dataset.classes:
        return {
            'status': 'error', 
            'message': f'Landmark "{landmark_name}" found on disk but ignored by PyTorch. Check if images are inside and have .jpg extensions.'
        }

    # Filter dataset to only include the specified landmark if necessary
    # For now, we'll train on all available data and assume filtering happens at data upload
    # If a user wants to train only on a specific landmark, the data structure needs to change
    # to only include that landmark's data for this training run.
    # For simplicity, we are currently training on ALL data in BASE_DATA_DIR
    # and saving the model that can predict all classes present in BASE_DATA_DIR.

    if len(full_dataset) < 2: # Need at least 2 samples for train/val split
        return {'status': 'error', 'message': f'Insufficient image data in {BASE_DATA_DIR}. Need at least 2 images across all landmarks for training.'}

    total_len = len(full_dataset)
    train_len = int(0.7 * total_len)
    val_len = int(0.15 * total_len)
    test_len = total_len - train_len - val_len

    if train_len == 0 or val_len == 0: # Ensure there's data for both train and val
        return {'status': 'error', 'message': f'Not enough data to create proper training and validation sets. Adjust total images or split ratios.'}

    train_dataset, val_dataset, test_dataset = random_split(
        full_dataset, [train_len, val_len, test_len],
        generator=torch.Generator().manual_seed(42)
    )

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

    num_classes = len(full_dataset.classes)
    model = models.resnet18(pretrained=True)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LR)

    training_metrics = []

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

        model.eval()
        correct = 0
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
                outputs = model(imgs)
                _, preds = torch.max(outputs, 1)
                correct += torch.sum(preds == labels).item()
        val_acc = correct / len(val_loader.dataset)

        training_metrics.append({
            'epoch': epoch + 1,
            'loss': round(epoch_loss, 4),
            'accuracy': round(val_acc, 4)
        })
        print(f"Epoch [{epoch+1}/{EPOCHS}] Loss: {epoch_loss:.4f} Val Acc: {val_acc:.4f}")

    os.makedirs(MODEL_DIR, exist_ok=True)
    model_save_path = os.path.join(MODEL_DIR, "landmark_resnet18.pth")
    torch.save({
        "model_state_dict": model.state_dict(),
        "classes": full_dataset.classes
    }, model_save_path)

    # Save class names to a JSON file
    with open(CLASS_NAMES_PATH, 'w') as f:
        json.dump(full_dataset.classes, f)

    print(f"Training complete! Model saved at {model_save_path}")
    print(f"Class names saved at {CLASS_NAMES_PATH}")

    final_metrics = {
        'status': 'Complete',
        'epochs_run': EPOCHS,
        'total_images_processed': total_len,
        'final_accuracy': training_metrics[-1]['accuracy'] if training_metrics else 0,
        'final_loss': training_metrics[-1]['loss'] if training_metrics else 0,
        'detailed_metrics': training_metrics
    }
    return final_metrics
