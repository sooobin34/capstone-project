# 검증 정확률 (Validation Accuracy) : 87.34%


import os
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt

from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
from torch.optim.lr_scheduler import ReduceLROnPlateau

# =========================
# 설정
# =========================

DATA_DIR = "../data"

BATCH_SIZE = 8
EPOCHS = 50
LEARNING_RATE = 0.00005
SEED = 42

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("사용 장치:", DEVICE)

# =========================
# Seed 고정
# =========================

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

# =========================
# 이미지 전처리
# =========================

train_transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomResizedCrop(224, scale=(0.9, 1.0)),
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
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

# =========================
# 데이터셋 로드
# =========================

train_dataset = datasets.ImageFolder(
    root=os.path.join(DATA_DIR, "train"),
    transform=train_transform
)

val_dataset = datasets.ImageFolder(
    root=os.path.join(DATA_DIR, "val"),
    transform=val_transform
)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False
)

print("클래스:", train_dataset.classes)

# =========================
# 모델 생성
# =========================

model = models.resnet18(pretrained=True)
model.fc = nn.Linear(model.fc.in_features, 3)
model = model.to(DEVICE)

# =========================
# 손실함수 / 옵티마이저 / 스케줄러
# =========================

class_weights = torch.tensor([
    1.0,   # high
    1.5,   # low
    1.0    # mid
]).to(DEVICE)

criterion = nn.CrossEntropyLoss(weight=class_weights)

optimizer = optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE
)

scheduler = ReduceLROnPlateau(
    optimizer,
    mode="max",
    factor=0.5,
    patience=3
)

# =========================
# 저장 설정
# =========================

os.makedirs("models", exist_ok=True)
os.makedirs("results", exist_ok=True)

best_acc = 0.0
best_epoch = 0

train_losses = []
val_accuracies = []
learning_rates = []

# =========================
# 학습
# =========================

for_epoch = range(EPOCHS)
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

    # =====================
    # Validation
    # =====================

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

        torch.save(model.state_dict(), "models/water_classifier_best.pth")

        print(f"Best model saved! Epoch: {best_epoch}, Accuracy: {best_acc:.2f}%")

# =========================
# 그래프 저장
# =========================

plt.figure()
plt.plot(train_losses)
plt.xlabel("Epoch")
plt.ylabel("Train Loss")
plt.title("Training Loss")
plt.savefig("results/train_loss.png")
plt.close()

plt.figure()
plt.plot(val_accuracies)
plt.xlabel("Epoch")
plt.ylabel("Validation Accuracy (%)")
plt.title("Validation Accuracy")
plt.savefig("results/val_accuracy.png")
plt.close()

plt.figure()
plt.plot(learning_rates)
plt.xlabel("Epoch")
plt.ylabel("Learning Rate")
plt.title("Learning Rate Schedule")
plt.savefig("results/learning_rate.png")
plt.close()

# =========================
# 종료
# =========================

print("\n학습 완료!")
print(f"가장 좋은 모델: Epoch {best_epoch}, Validation Accuracy {best_acc:.2f}%")
print("저장 위치: models/water_classifier_best.pth")
print("그래프 저장 위치: results/")