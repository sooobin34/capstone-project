import os
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt

from torchvision import datasets, transforms, models
from torchvision.models import ResNet50_Weights
from torch.utils.data import DataLoader, WeightedRandomSampler
from torch.optim.lr_scheduler import ReduceLROnPlateau

DATA_DIR = "../data"

BATCH_SIZE = 8
EPOCHS = 60
LEARNING_RATE = 0.00003
PATIENCE = 10
SEED = 42
IMAGE_SIZE = 384

MODEL_SAVE_PATH = "models/water_classifier_resnet50_best.pth"
RESULT_DIR = "results_resnet50"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("사용 장치:", DEVICE)


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


set_seed(SEED)


train_transform = transforms.Compose([
    transforms.Resize((420, 420)),
    transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.9, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(5),
    transforms.ColorJitter(
        brightness=0.1,
        contrast=0.1,
        saturation=0.1
    ),
    transforms.ToTensor(),
])

val_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
])


train_dataset = datasets.ImageFolder(
    root=os.path.join(DATA_DIR, "train"),
    transform=train_transform
)

val_dataset = datasets.ImageFolder(
    root=os.path.join(DATA_DIR, "val"),
    transform=val_transform
)

class_names = train_dataset.classes
print("클래스:", class_names)

targets = [label for _, label in train_dataset.samples]
class_counts = np.bincount(targets)

class_sample_weights = 1.0 / class_counts
sample_weights = [class_sample_weights[label] for label in targets]
sample_weights = torch.DoubleTensor(sample_weights)

sampler = WeightedRandomSampler(
    weights=sample_weights,
    num_samples=len(sample_weights),
    replacement=True
)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    sampler=sampler
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False
)

print("클래스별 train 개수:", class_counts)


weights = ResNet50_Weights.DEFAULT

model = models.resnet50(weights=weights)
model.fc = nn.Linear(model.fc.in_features, len(class_names))
model = model.to(DEVICE)


class_weights = torch.tensor([
    1.0,   # high
    1.4,   # low
    1.0    # mid
]).to(DEVICE)

criterion = nn.CrossEntropyLoss(weight=class_weights)

optimizer = optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=0.0001
)

scheduler = ReduceLROnPlateau(
    optimizer,
    mode="max",
    factor=0.5,
    patience=4
)


os.makedirs("models", exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

best_acc = 0.0
best_epoch = 0
early_stop_count = 0

train_losses = []
val_accuracies = []
learning_rates = []


for epoch in range(EPOCHS):
    model.train()
    running_loss = 0.0

    for images, labels in train_loader:
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        optimizer.zero_grad()

        outputs = model(images)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    avg_train_loss = running_loss / len(train_loader)
    train_losses.append(avg_train_loss)

    model.eval()

    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(DEVICE)
            labels = labels.to(DEVICE)

            outputs = model(images)
            _, predicted = torch.max(outputs, 1)

            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    accuracy = 100 * correct / total
    val_accuracies.append(accuracy)

    current_lr = optimizer.param_groups[0]["lr"]
    learning_rates.append(current_lr)

    scheduler.step(accuracy)

    print(f"\nEpoch [{epoch + 1}/{EPOCHS}]")
    print(f"Train Loss: {avg_train_loss:.4f}")
    print(f"Validation Accuracy: {accuracy:.2f}%")
    print(f"Learning Rate: {current_lr}")

    if accuracy > best_acc:
        best_acc = accuracy
        best_epoch = epoch + 1
        early_stop_count = 0

        torch.save(model.state_dict(), MODEL_SAVE_PATH)

        print(f"Best model saved! Epoch: {best_epoch}, Accuracy: {best_acc:.2f}%")

    else:
        early_stop_count += 1
        print(f"EarlyStopping Count: {early_stop_count}/{PATIENCE}")

    if early_stop_count >= PATIENCE:
        print("\nEarly stopping triggered.")
        break


plt.figure()
plt.plot(train_losses)
plt.xlabel("Epoch")
plt.ylabel("Train Loss")
plt.title("ResNet50 Training Loss")
plt.savefig(os.path.join(RESULT_DIR, "train_loss.png"))
plt.close()

plt.figure()
plt.plot(val_accuracies)
plt.xlabel("Epoch")
plt.ylabel("Validation Accuracy (%)")
plt.title("ResNet50 Validation Accuracy")
plt.savefig(os.path.join(RESULT_DIR, "val_accuracy.png"))
plt.close()

plt.figure()
plt.plot(learning_rates)
plt.xlabel("Epoch")
plt.ylabel("Learning Rate")
plt.title("ResNet50 Learning Rate Schedule")
plt.savefig(os.path.join(RESULT_DIR, "learning_rate.png"))
plt.close()

print("\n학습 완료!")
print(f"가장 좋은 모델: Epoch {best_epoch}, Validation Accuracy {best_acc:.2f}%")
print(f"저장 위치: {MODEL_SAVE_PATH}")
print(f"그래프 저장 위치: {RESULT_DIR}/")