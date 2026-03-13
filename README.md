# EEG P300 Navigation

이 프로젝트는 Emotiv Epoc X와 같은 뇌파(EEG) 측정 장비와 LSL(Lab Streaming Layer) 네트워크 프로토콜을 활용하여 **P300 기반 뇌-컴퓨터 인터페이스(BCI)**를 구현한 프로젝트입니다. 실시간으로 뇌파를 분석하여 사용자가 의도한 목표 지점을 예측하고, 이를 통해 **ROS 기반 모바일 로봇을 제어(Navigation)**하는 것을 목표로 합니다.

## 📂 파일 구성 (File Structure)

*   **`bci_map_stimulus.py`**: P300 Speller 기반 자극 UI 
    *   화면에 6x6 격자를 표시하고 행(Row)/열(Column) 단위로 랜덤하게 점멸 자극을 제공합니다.
    *   발생한 자극 시점(Marker)을 LSL 스트림으로 송출합니다.
*   **`bci_data_recorder.py`**: 뇌파 데이터 수집
    *   LSL을 통해 들어오는 실시간 뇌파(EEG) 데이터와 자극 마커(Marker) 데이터를 동기화하여 `data/` 폴더 내에 `.csv` 형식으로 저장합니다.
*   **`bci_train_model.py`**: P300 예측 모델 학습 (※ 위 파일 구조에는 보이지 않으나 역할을 바탕으로 추정)
    *   수집된 뇌파 CSV 데이터들을 전처리하고 머신러닝 모델(`p300_model.pkl`)을 학습시킵니다.
*   **`bci_realtime_demo.py`**: 실시간 로봇 제어 데모
    *   실시간 뇌파를 수신하여 목표 지점(행, 열)을 예측하고, TCP 소켓 통신을 통해 원격지(ROS 기반 리눅스/우분투 서버)로 이동 명령을 보냅니다.
*   **`emotiv-lsl-main/`**: Emotiv-LSL 브릿지
    *   Emotiv 장비의 신호를 LSL 통신 포맷으로 묶어서 보내주기 위한 오픈소스 폴더입니다.
*   **`map.png`**: 자극기에 표시되는 지도 배경 이미지입니다.

## 🚀 실행 단계 (How to Run)

1.  **LSL 스트림 준비 (EEG 송출)**
    *   먼저 뇌파 장비가 연결되어야 합니다. `emotiv-lsl-main/emotiv-lsl-main/main.py`를 실행하여 뇌파 신호가 LSL 네트워크 상에 뿌려지도록 합니다.
2.  **화면 자극기 실행**
    *   새 터미널에서 `python bci_map_stimulus.py`를 실행하여 지도와 자극용 격자 화면을 띄웁니다.
3.  **데이터 수집모드 (옵션)**
    *   로봇 제어 전 학습용 데이터가 필요하다면 `python bci_data_recorder.py`를 실행하여 데이터를 모읍니다.
    *   수집된 데이터를 `bci_train_model.py`에 넘겨서 모델을 학습시킵니다.
4.  **로봇 제어 모드 (실시간 데모)**
    *   `bci_realtime_demo.py` 안에 있는 `ROS_IP` 변수를 ROS를 구동하는 Linux PC(Ubuntu 등)의 IP로 수정합니다.
    *   코드를 실행하고 화면을 응시하여 로봇을 움직입니다.
