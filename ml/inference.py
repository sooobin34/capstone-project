import os
from typing import Dict, Any

import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms, models

# Render 메모리/CPU 부담 완화
torch.set_num_threads(1)

# =========================
# 경로 설정
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MAIN_MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "water_classifier_best.pth"
)

LOW_MID_MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "water_classifier_low_mid_best.pth"
)

# =========================
# 클래스 설정
# =========================

MAIN_CLASS_NAMES = ["high", "low", "mid"]
BOUNDARY_CLASS_NAMES = ["low", "mid"]

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =========================
# 이미지 전처리
# =========================

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

# =========================
# 모델 로드
# =========================

def load_resnet18(num_classes: int, model_path: str):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {model_path}")

    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)

    checkpoint = torch.load(model_path, map_location=DEVICE)

    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        checkpoint = checkpoint["model_state_dict"]

    model.load_state_dict(checkpoint)
    model = model.to(DEVICE)
    model.eval()

    return model


# import 순간 로드하지 않도록 None으로 시작
main_model = None
low_mid_model = None


def get_models():
    global main_model, low_mid_model

    if main_model is None:
        main_model = load_resnet18(
            num_classes=3,
            model_path=MAIN_MODEL_PATH
        )

    if low_mid_model is None:
        low_mid_model = load_resnet18(
            num_classes=2,
            model_path=LOW_MID_MODEL_PATH
        )

    return main_model, low_mid_model


# =========================
# 예측 함수
# =========================

def predict_water_level(image_path: str) -> Dict[str, Any]:
    """
    이미지 1장을 입력받아 LOW / MID / HIGH 예측 결과 반환

    계층형 구조:
    1차 모델: high / low / mid
    2차 모델: 1차 결과가 mid일 경우 low / mid 재검사
    """

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

    # AI 분석 요청이 들어왔을 때 처음 1번만 모델 로드
    main_model, low_mid_model = get_models()

    # 이미지 파일 안전하게 열고 닫기
    with Image.open(image_path) as img:
        image = img.convert("RGB")

    image_tensor = transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        main_outputs = main_model(image_tensor)
        main_probs = torch.softmax(main_outputs, dim=1)

        main_confidence, main_pred = torch.max(main_probs, 1)

        main_pred_idx = main_pred.item()
        main_pred_name = MAIN_CLASS_NAMES[main_pred_idx]

        final_pred_name = main_pred_name
        final_confidence = main_confidence.item()

        boundary_result = None

        if main_pred_name == "mid":
            boundary_outputs = low_mid_model(image_tensor)
            boundary_probs = torch.softmax(boundary_outputs, dim=1)

            boundary_confidence, boundary_pred = torch.max(boundary_probs, 1)

            boundary_pred_idx = boundary_pred.item()
            boundary_pred_name = BOUNDARY_CLASS_NAMES[boundary_pred_idx]

            final_pred_name = boundary_pred_name
            final_confidence = boundary_confidence.item()

            boundary_result = {
                "predicted_class": boundary_pred_name.upper(),
                "confidence": round(boundary_confidence.item(), 4),
                "probabilities": {
                    BOUNDARY_CLASS_NAMES[i].upper(): round(
                        boundary_probs[0][i].item(),
                        4
                    )
                    for i in range(len(BOUNDARY_CLASS_NAMES))
                }
            }

        result = {
            "predicted_class": final_pred_name.upper(),
            "confidence": round(final_confidence, 4),
            "main_model": {
                "predicted_class": main_pred_name.upper(),
                "confidence": round(main_confidence.item(), 4),
                "probabilities": {
                    MAIN_CLASS_NAMES[i].upper(): round(
                        main_probs[0][i].item(),
                        4
                    )
                    for i in range(len(MAIN_CLASS_NAMES))
                }
            },
            "boundary_model": boundary_result
        }

    return result


if __name__ == "__main__":
    test_image_path = input("이미지 경로 입력: ").strip()
    result = predict_water_level(test_image_path)
    print(result)