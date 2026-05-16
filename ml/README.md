### ml 프로젝트 구조
```text
ml/
 ┣ train_water_classifier.py
 ┣ inference.py
 ┣ models/
 ┃ ┗ water_classifier.pth
 ┣ checkpoints/
 ┣ notebooks/
 ┗ README.md
```
---

### 설명

* train_water_classifier.py

  * 이미지 데이터셋을 이용해 AI 모델 학습 수행
  * train/val 데이터를 사용하여 LOW/MID/HIGH 분류 모델 생성

* inference.py

  * 학습 완료된 모델을 이용해 이미지 예측 수행
  * 입력 이미지가 LOW/MID/HIGH 중 어떤 상태인지 출력

* models/

  * 학습 완료된 모델(.pth) 저장 폴더
  * 최종 배포 시 사용되는 모델 위치

* checkpoints/

  * 학습 중간 저장 파일 저장 폴더
  * epoch 단위로 weight 백업 가능

* notebooks/

  * 실험 및 테스트용 Jupyter Notebook 저장 폴더
  * 데이터 확인 및 모델 실험 목적

* README.md

  * ML 관련 코드 및 실행 방법 설명 문서


