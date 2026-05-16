import os
import torch
import torch.nn as nn
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
from sklearn.metrics import confusion_matrix, classification_report

DATA_DIR = "../data"
MODEL_PATH = "models/water_classifier_best.pth"
BATCH_SIZE = 8

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("사용 장치:", DEVICE)

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

test_dataset = datasets.ImageFolder(
    root=os.path.join(DATA_DIR, "test"),
    transform=transform
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False
)

class_names = test_dataset.classes
print("클래스:", class_names)

model = models.resnet18(pretrained=True)
model.fc = nn.Linear(model.fc.in_features, len(class_names))
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model = model.to(DEVICE)
model.eval()

all_labels = []
all_preds = []
wrong_files = []

correct = 0
total = 0

sample_index = 0

with torch.no_grad():
    for images, labels in test_loader:
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        outputs = model(images)
        _, predicted = torch.max(outputs, 1)

        total += labels.size(0)
        correct += (predicted == labels).sum().item()

        for i in range(len(labels)):
            true_idx = labels[i].item()
            pred_idx = predicted[i].item()

            if true_idx != pred_idx:
                file_path = test_dataset.samples[sample_index + i][0]
                wrong_files.append({
                    "file": file_path,
                    "true": class_names[true_idx],
                    "pred": class_names[pred_idx]
                })

        sample_index += len(labels)

        all_labels.extend(labels.cpu().numpy())
        all_preds.extend(predicted.cpu().numpy())

accuracy = 100 * correct / total

print(f"\nTest Accuracy: {accuracy:.2f}%")

print("\nConfusion Matrix:")
print(confusion_matrix(all_labels, all_preds))

print("\nClassification Report:")
print(classification_report(all_labels, all_preds, target_names=class_names))

print("\nMisclassified Images:")
for item in wrong_files:
    print(f"파일: {item['file']}")
    print(f"정답: {item['true']} / 예측: {item['pred']}")
    print("-" * 50)