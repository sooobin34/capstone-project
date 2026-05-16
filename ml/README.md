### ml 프로젝트 구조

```text
ml/
 ┣ train_water_classifier.py
 ┣ evaluate_water_classifier.py
 ┃
 ┣ train_boundary_low_mid.py
 ┣ evaluate_boundary_low_mid.py
 ┃
 ┣ evaluate_hierarchical_classifier.py
 ┣ inference.py
 ┃
 ┣ models/
 ┃ ┣ water_classifier_best.pth
 ┃ ┗ water_classifier_low_mid_best.pth
 ┃
 ┣ results/
 ┣ results_low_mid/
 ┃
 ┣ notebooks/
 ┗ README.md
```

---

## 설명

### train_water_classifier.py

* 실제 논 환경 사진 기반 LOW / MID / HIGH 분류 모델 학습
* PyTorch ResNet18 기반 모델 사용
* train / validation 데이터셋을 이용해 모델 학습 수행
* 최종 모델은 `models/water_classifier_best.pth`로 저장

---

### evaluate_water_classifier.py

* 학습 완료된 기본 LOW / MID / HIGH 모델 평가
* test 데이터 기준 Accuracy / Confusion Matrix / Classification Report 출력
* 오분류 이미지 목록 확인 가능

---

### train_boundary_low_mid.py

* LOW(1cm)와 MID(2~3cm) 경계 구간 전용 보정 모델 학습
* 실제 논 환경에서 LOW와 MID의 시각적 경계가 유사하여 추가 실험 수행
* 최종 모델은 `models/water_classifier_low_mid_best.pth`로 저장

---

### evaluate_boundary_low_mid.py

* LOW-MID 경계 전용 모델 평가
* LOW ↔ MID 오분류 개선 여부 확인 목적

---

### evaluate_hierarchical_classifier.py

* 계층형(Hierarchical) 구조 기반 최종 평가 수행

구조:
```text
1차 모델:
LOW / MID / HIGH 분류

↓

1차 결과가 MID일 경우
LOW-MID 경계 모델 재검사 수행

↓

최종 결과 보정
```

* 기본 모델 대비 성능 향상 여부 비교 목적
* 최종 test accuracy 기준 약 86.30% 수준 확인

---

### inference.py (구현 중...)

* FastAPI 연동용 실제 추론(Inference) 코드
* 업로드된 이미지 1장을 입력받아 LOW / MID / HIGH 예측 수행
* 계층형 구조 기반으로 최종 결과 반환

반환 정보 예시:
```json
{
  "predicted_class": "LOW",
  "confidence": 0.54
}
```

---

### models/

* 학습 완료된 모델(.pth) 저장 폴더
* FastAPI 서버에서 실제 추론 시 사용

파일:
* `water_classifier_best.pth`
  * 기본 LOW / MID / HIGH 분류 모델

* `water_classifier_low_mid_best.pth`
  * LOW-MID 경계 보정 모델

---

### results/

* 기본 모델 학습 결과 그래프 저장 폴더
* Loss / Accuracy / Learning Rate 그래프 저장

---

### results_low_mid/

* LOW-MID 경계 모델 학습 결과 그래프 저장 폴더

---

### notebooks/

* 실험 및 테스트용 Jupyter Notebook 저장 폴더
* 데이터 확인 및 모델 실험 목적

---

## 모델 구조

### 기본 모델

* PyTorch ResNet18 기반 CNN 사용
* 실제 논 환경 이미지 기준 LOW / MID / HIGH 분류 수행

---

### 계층형(Hierarchical) 구조

실제 논 환경에서는 1~3cm 구간의 흙탕물, 반사, 조명 변화 등으로 인해 LOW와 MID의 경계가 시각적으로 매우 유사하게 나타나는 문제가 존재함.

이를 보완하기 위해 다음과 같은 2단계 계층형 구조를 적용함.

```text
1차 모델:
LOW / MID / HIGH 분류

↓

MID로 판단된 경우

↓

2차 LOW-MID 경계 모델 재검사 수행
```

이를 통해 LOW ↔ MID 오분류 일부를 개선하였으며, 기본 모델 대비 test accuracy가 향상됨.

---

## 실험 환경

* Framework: PyTorch
* Backbone: ResNet18
* Language: Python
* Device: CUDA / CPU 지원

---

## 데이터셋 구성

```text
train/
val/
test/
```

촬영 높이 일반화 검증을 위해 높이 기준으로 데이터 분리 수행.

예시:
* train: 10cm / 50cm / 80cm / 110cm
* validation: 140cm
* test: 170cm

---

## 현재 한계

* 실제 논 환경의 흙탕물, 반사, 조명 변화 영향 존재
* 1~3cm 경계 구간에서 시각적 차이가 매우 작음
* HIGH(4~5cm) 일부가 MID로 오분류되는 현상 존재
* 정확한 cm 단위 추정에는 추가적인 알고리즘 개선 필요

---

## 향후 개선 방향

* ROI 기반 수면 분석
* segmentation 기반 수면 영역 검출
* 센서값 + 이미지 기반 복합 검증 구조
* 실제 cm 단위 추정 모델 실험