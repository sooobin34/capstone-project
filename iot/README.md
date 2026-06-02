## LoRaWAN 통신 구조

### 사용 환경

- STM32WL55JC1
- RAK7268V2 Gateway
- LoRaWAN (OTAA)
- Region: KR920

### 구현 내용

- 초음파 센서 데이터 수집
- 수위 계산
- LoRaWAN Payload 생성
- Gateway 연동
- Backend 연계 구조 설계

### 데이터 흐름

Sensor
→ STM32
→ LoRaWAN
→ Gateway
→ Backend
→ PostgreSQL