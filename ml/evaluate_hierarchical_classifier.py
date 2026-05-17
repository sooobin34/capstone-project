# =========================================================
# evaluate_hierarchical_classifier.py
# =========================================================

# 기본 ResNet18 수위 분류 모델과
# LOW-MID 경계 보정 모델을 결합한
# 계층형(Hierarchical) 평가 코드
#
# 동작 방식:
# 1차 기본 모델에서 LOW / MID / HIGH 예측 수행
# LOW 또는 MID 로 예측된 경우,
# LOW-MID 경계 모델로 한 번 더 재분류 수행
#
# 목적:
# LOW ↔ MID 경계 구간 오분류 감소
#
# 출력:
# - Hierarchical Test Accuracy
# - Confusion Matrix
# - Classification Report
# - 오분류 이미지 목록
#
# 최종 계층형 모델 성능:
# Hierarchical Test Accuracy: 87.67%
# =========================================================

import os
import torch
import torch.nn as nn
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
from sklearn.metrics import confusion_matrix, classification_report

DATA_DIR = "../data"

MAIN_MODEL_PATH = "models/water_classifier_best.pth"
LOW_MID_MODEL_PATH = "models/water_classifier_low_mid_best.pth"

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
print("1차 모델 클래스:", class_names)

# =========================
# 1차 LOW/MID/HIGH 모델
# =========================

main_model = models.resnet18(pretrained=True)
main_model.fc = nn.Linear(main_model.fc.in_features, len(class_names))
main_model.load_state_dict(torch.load(MAIN_MODEL_PATH, map_location=DEVICE))
main_model = main_model.to(DEVICE)
main_model.eval()

# =========================
# 2차 LOW/MID 경계 모델
# =========================

boundary_class_names = ["low", "mid"]

low_mid_model = models.resnet18(pretrained=True)
low_mid_model.fc = nn.Linear(low_mid_model.fc.in_features, 2)
low_mid_model.load_state_dict(torch.load(LOW_MID_MODEL_PATH, map_location=DEVICE))
low_mid_model = low_mid_model.to(DEVICE)
low_mid_model.eval()

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

        main_outputs = main_model(images)
        _, main_preds = torch.max(main_outputs, 1)

        final_preds = []

        for i in range(len(images)):
            main_pred_idx = main_preds[i].item()
            main_pred_name = class_names[main_pred_idx]

            # 1차 모델이 MID라고 판단한 경우만 LOW-MID 경계 모델로 재검사
            if main_pred_name == "mid":
                single_image = images[i].unsqueeze(0)

                boundary_outputs = low_mid_model(single_image)
                _, boundary_pred = torch.max(boundary_outputs, 1)

                boundary_pred_name = boundary_class_names[boundary_pred.item()]
                final_pred_name = boundary_pred_name

            else:
                final_pred_name = main_pred_name

            final_pred_idx = class_names.index(final_pred_name)
            final_preds.append(final_pred_idx)

        final_preds = torch.tensor(final_preds).to(DEVICE)

        total += labels.size(0)
        correct += (final_preds == labels).sum().item()

        for i in range(len(labels)):
            true_idx = labels[i].item()
            pred_idx = final_preds[i].item()

            if true_idx != pred_idx:
                file_path = test_dataset.samples[sample_index + i][0]
                wrong_files.append({
                    "file": file_path,
                    "true": class_names[true_idx],
                    "pred": class_names[pred_idx],
                })

        sample_index += len(labels)

        all_labels.extend(labels.cpu().numpy())
        all_preds.extend(final_preds.cpu().numpy())

accuracy = 100 * correct / total

print(f"\nHierarchical Test Accuracy: {accuracy:.2f}%")

print("\nConfusion Matrix:")
print(confusion_matrix(all_labels, all_preds))

print("\nClassification Report:")
print(
    classification_report(
        all_labels,
        all_preds,
        target_names=class_names
    )
)

print("\nMisclassified Images:")
for item in wrong_files:
    print(f"파일: {item['file']}")
    print(f"정답: {item['true']} / 예측: {item['pred']}")
    print("-" * 50)