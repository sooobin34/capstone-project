- ultrasonic_test : 초음파 센서 UART 테스트용
- LoRaWAN_End_Node_LBM : LoRaWAN uplink 테스트용
- 현재 증상 : JOINFAIL 반복 / RX timeout

## LoRaWAN Gateway 현재 진행 상황

### 현재 환경
- STM32WL55JC1
- RAK7268V2 Built-in LoRa Server
- OTAA 사용
- Region: KR920

---

## 현재 정상 동작 확인된 부분

### 1. 초음파 센서 UART 통신 정상
STM32에서 초음파 센서 데이터를 정상적으로 수신하고 있음.

Tera Term 로그에서 아래 내용 확인:
- RX header TEST: 0xFF
- Packet TEST: FF 08 A3 AA
- Raw Distance 계산
- Water Level 계산
- LoRa Payload 생성

예시:
LoRa Payload HEX: FF 38

---

### 2. LoRaWAN Join 성공
LoRaWAN Join 과정 정상 확인.

Tera Term 로그:
Event received: JOINED
Event received: TXDONE

---

### 3. 게이트웨이 RF 수신 정상
RAK7268V2 게이트웨이에서 RF uplink 패킷 수신 확인.

게이트웨이 시스템 로그:
Permitted to join
Mote 0080e115061bf02c Joined addr 021f5525

RF 관련 로그:
- RF packets received by concentrator 증가 확인
- RF packets forwarded 증가 확인

즉 STM32 uplink 자체는 게이트웨이까지 정상적으로 전달되는 것으로 보임.

---

## 현재 문제 상황

Join 및 uplink 전송은 성공하지만,
sensor uplink 데이터가 backend/database까지 전달되지 않는 상황.

### 1. MQTT Explorer 확인 결과
- application/.../join 토픽은 생성됨
- application/.../rx 토픽은 생성되지 않음

### 2. Render webhook 로그
join 이벤트는 정상 수신됨:
POST /lora-webhook?event=up

하지만 body에는:
- devEUI
- devAddr

만 존재하며 아래 필드가 없음:
- data
- fPort

예시:
{
  "applicationID":"1",
  "applicationName":"SensorApp",
  "deviceName":"NUCLEO_WL55JC1",
  "devEUI":"0080e115061bf02c",
  "timestamp":1779362824,
  "devAddr":"021f5525"
}

### 3. Packet Capture 확인 결과
Packet Capture 화면에서도 uplink payload(rx)가 표시되지 않음.

---

## 현재 의심되는 원인

현재까지 확인된 정상 동작:
- STM32 UART 센서 수신
- Water Level 계산
- Payload 생성
- LoRaWAN Join
- RF uplink 전송
- Gateway RF 수신

현재 의심되는 부분:
- RAK7268V2 Built-in Network Server/App Server
- uplink rx publish 문제
- HTTP forwarding 문제

즉 RF uplink 자체는 정상 동작하지만,
게이트웨이 내부 Application Server 단계에서 uplink payload 전달이 이루어지지 않는 것으로 추정 중.

---

## 현재 설정 상태

- Region: KR920
- OTAA 사용
- HTTP Integration ON
- MQTT Uplink Topic 기본값 사용

application/{{application_name}}/device/{{device_EUI}}/rx

---

## 추가 진행 시도 사항

외부 ChirpStack 환경도 시도하였으나:
- Oracle VM 계정 생성 문제
- VMware 네트워크/IP 할당 문제

등으로 인해 아직 구축하지 못한 상태.

### 다음 확인 순서

1. 게이트웨이 패킷 스니핑 기능으로 JoinRequest 수신 여부 확인
2. JoinRequest가 보이지 않으면 단말-게이트웨이 설정 확인
3. JoinRequest가 보이는데 JoinAccept가 없으면 단말-서버 키 설정 확인
4. DevEUI / JoinEUI / AppKey / Region / 바이트오더 재확인
5. Join 성공 후 Render `/lora-webhook` 로그 및 DB 저장 여부 확인
