# data_boundary_mid_high

MID(2~3cm)와 HIGH(4~5cm) 경계 구간 전용 모델 학습을 위한 실험 데이터셋입니다.

실제 논 환경에서 HIGH 상태 일부가 MID로 오분류되는 현상을 개선하기 위해 추가 실험을 수행하였습니다.

## 구조

```text
data_boundary_mid_high/
 ┣ train/
 ┣ val/
 ┗ test/
```

각 폴더 내부:
```text
mid/
high/
```

## 데이터 구성

* mid
  * mid2 / mid3 계열 이미지 사용
  * 약 2~3cm 수준의 중간 수위 상태

* high
  * high4 / high5 계열 이미지 사용
  * 약 4~5cm 수준의 높은 수위 상태

## 목적

MID ↔ HIGH 경계 구간 오분류 개선을 위한 Binary 분류 모델 실험 목적.

## 결과

실험 결과 HIGH 데이터를 MID로 과소분류하는 경향이 강하게 나타났으며,
최종 계층형(Hierarchical) 구조에는 포함하지 않았습니다.