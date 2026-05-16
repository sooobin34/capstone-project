- ultrasonic_test : 초음파 센서 UART 테스트용
- LoRaWAN_End_Node_LBM : LoRaWAN uplink 테스트용
- 현재 증상 : JOINFAIL 반복 / RX timeout


## IoT / LoRaWAN 확인 필요 사항

현재 STM32 보드와 LoRa 게이트웨이를 다시 연결해 실시간 로그를 확인하지 못한 상태이므로 정확한 원인은 아직 확정하지 못했습니다.

다만 이전 Tera Term 로그 기준으로는 초음파 센서값 읽기, Water Level 계산, LoRa Payload 생성, TX DONE까지는 확인되었습니다.  
이후 RX1/RX2 timeout이 발생하고 `JOINFAIL`이 반복되는 상황이었습니다.

### 수정 및 확인한 주요 파일

- `lora_app.c`
  - 초음파 센서 UART 수신
  - 수위값 변환
  - LoRa Payload 생성
  - Join 및 Uplink 요청 흐름 확인

- `se-identity.h`
  - DevEUI
  - JoinEUI(AppEUI)
  - AppKey 설정 확인

- `lorawan_conf.h`
  - Region 설정 확인
  - AS923 / KR920 설정 확인 필요

- `Commissioning.h`
  - `se-identity.h` 포함 여부 확인

- `backend/app/api/lora_webhook.py`
  - LoRa webhook 수신
  - payload decode
  - DB 저장 처리

### 현재 의심되는 부분

- 단말과 게이트웨이 간 Region 설정 불일치
- Sync Word 불일치 가능성
- DevEUI / JoinEUI / AppKey 불일치 가능성
- DevEUI 또는 AppKey 바이트오더 문제
- 게이트웨이에서 JoinRequest가 실제로 수신되는지 확인 필요
- JoinRequest는 보이나 JoinAccept가 오지 않는 경우 서버 키 설정 확인 필요

### 다음 확인 순서

1. 게이트웨이 패킷 스니핑 기능으로 JoinRequest 수신 여부 확인
2. JoinRequest가 보이지 않으면 단말-게이트웨이 설정 확인
3. JoinRequest가 보이는데 JoinAccept가 없으면 단말-서버 키 설정 확인
4. DevEUI / JoinEUI / AppKey / Region / 바이트오더 재확인
5. Join 성공 후 Render `/lora-webhook` 로그 및 DB 저장 여부 확인