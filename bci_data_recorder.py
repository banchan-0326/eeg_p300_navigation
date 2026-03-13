import pandas as pd
import time
from pylsl import resolve_streams, StreamInlet
import os

# ==========================================
# 설정 (Configuration)
# ==========================================
DURATION = 30  # 녹음할 시간 (초) - 테스트용으로 짧게 설정
SAVE_DIR = "data" # 데이터 저장 폴더

def record_data():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    print(">> 1. Looking for LSL streams...")
    
    # 모든 활성화된 LSL 스트림 검색
    streams = resolve_streams()
    
    eeg_inlet = None
    marker_inlet = None

    # 스트림 분류 (EEG vs Markers)
    for stream in streams:
        print(f"Found stream: {stream.name()} [{stream.type()}]")
        if stream.type() == 'EEG':
            eeg_inlet = StreamInlet(stream)
            print(f"  -> Connected to EEG Stream: {stream.name()}")
        elif stream.type() == 'Markers':
            marker_inlet = StreamInlet(stream)
            print(f"  -> Connected to Marker Stream: {stream.name()}")

    # 주의: Emotiv가 연결 안 되어 있으면 EEG 스트림이 없을 수 있음
    if eeg_inlet is None:
        print("\n[Error] EEG stream not found! EmotivPRO LSL is on?")
        # 테스트를 위해 EEG 없이 마커만이라도 기록할지 결정 (여기서는 종료)
        # return 

    if marker_inlet is None:
        print("\n[Error] Marker stream not found! Run the UI script first.")
        return

    print(f"\n>> 2. Recording started for {DURATION} seconds...")
    print("   (Please look at the map and count the flashes!)")

    # 데이터 저장용 리스트
    eeg_data = []
    marker_data = []

    start_time = time.time()
    
    while time.time() - start_time < DURATION:
        # 1) EEG 데이터 수신 (청크 단위로 가져옴)
        if eeg_inlet:
            chunk, timestamps = eeg_inlet.pull_chunk(timeout=0.0)
            if timestamps:
                for i in range(len(timestamps)):
                    # [타임스탬프] + [채널 데이터들...]
                    eeg_data.append([timestamps[i]] + chunk[i])

        # 2) Marker 데이터 수신 (샘플 단위)
        # timeout=0.0으로 설정하여 블로킹 없이 즉시 확인
        marker, timestamp = marker_inlet.pull_sample(timeout=0.0)
        if marker:
            # [타임스탬프, 마커내용]
            print(f"Marker received: {marker[0]} at {timestamp}")
            marker_data.append([timestamp, marker[0]])
        
        # CPU 과부하 방지 (아주 짧은 슬립)
        time.sleep(0.001)

    print("\n>> 3. Recording finished. Saving files...")

    # CSV 파일로 저장
    timestamp_str = time.strftime("%Y%m%d-%H%M%S")
    
    if eeg_data:
        # 컬럼 이름은 Emotiv 채널 수에 맞춰야 함 (여기선 자동 생성)
        num_channels = len(eeg_data[0]) - 1
        cols = ['Timestamp'] + [f'Ch{i+1}' for i in range(num_channels)]
        df_eeg = pd.DataFrame(eeg_data, columns=cols)
        eeg_filename = f"{SAVE_DIR}/eeg_{timestamp_str}.csv"
        df_eeg.to_csv(eeg_filename, index=False)
        print(f"   Saved EEG: {eeg_filename}")

    if marker_data:
        df_marker = pd.DataFrame(marker_data, columns=['Timestamp', 'Event'])
        marker_filename = f"{SAVE_DIR}/markers_{timestamp_str}.csv"
        df_marker.to_csv(marker_filename, index=False)
        print(f"   Saved Markers: {marker_filename}")

if __name__ == "__main__":
    record_data()