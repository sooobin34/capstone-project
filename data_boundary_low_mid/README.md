# data_boundary_low_mid

LOW(1cm)와 MID(2~3cm) 경계 구간 전용 모델 학습을 위한 데이터셋입니다.

실제 논 환경에서는 LOW와 MID 상태가 시각적으로 매우 유사하게 나타나는 문제가 있어,
LOW ↔ MID 오분류 개선을 위한 추가 실험 목적으로 구성하였습니다.

## 구조

```text
data_boundary_low_mid/
 ┣ train/
 ┣ val/
 ┗ test/
```

각 폴더 내부:
```text
low/
mid/
```

## 데이터 구성

* low
  * low1 계열 이미지 사용
  * 약 1cm 수준의 낮은 수위 상태

* mid
  * mid2 / mid3 계열 이미지 사용
  * 약 2~3cm 수준의 중간 수위 상태

## 목적

기본 LOW / MID / HIGH 분류 모델에서 발생하는
LOW ↔ MID 경계 오분류를 줄이기 위한 경계 전용(Binary) 분류 실험 수행 목적.