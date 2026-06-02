### data 프로젝트 구조

```text
data/
 ┣ train/ (촬영 높이: 10~110cm)
 ┃ ┣ low/   (수위 0~1cm)
 ┃ ┣ mid/   (수위 2~3cm)
 ┃ ┗ high/  (수위 4~5cm)
 ┃
 ┣ val/ (촬영 높이: 140cm)
 ┃ ┣ low/
 ┃ ┣ mid/
 ┃ ┗ high/
 ┃
 ┗ test/ (촬영 높이: 170cm)
   ┣ low/
   ┣ mid/
   ┗ high/
```

---

### 설명

* train/

  * AI 모델 학습에 사용하는 이미지 데이터
  * 촬영 높이 10cm, 50cm, 80cm, 110cm 사진 사용

* val/

  * 학습 중 성능 검증용 데이터
  * 촬영 높이 140cm 사진 사용
  * 과적합(overfitting) 확인 목적

* test/

  * 최종 성능 평가용 데이터
  * 촬영 높이 170cm 사진 사용
  * 실제 새로운 환경에서 얼마나 잘 동작하는지 확인

---

### 클래스 기준
- low : 0cm(마른논), 0cm(젖은논), 1.1cm 
- mid : 2.1cm, 3.5cm 
- high : 4.5cm, 5cm

---

### 높이 기준 분리 
- train : 10cm, 50cm, 80cm, 110cm 
- val : 140cm 
- test : 170cm

