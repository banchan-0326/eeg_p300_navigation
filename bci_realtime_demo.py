import pandas as pd
import numpy as np
import pickle
import time
import socket  # [추가] 통신 라이브러리
from pylsl import resolve_streams, StreamInlet
from scipy.signal import butter, lfilter
import os

# ==========================================
# ★ 사용자 설정 (여기를 꼭 수정하세요!)
# ==========================================
ROS_IP = '192.168.0.15'  # <--- 아까 성공했던 Ubuntu의 IP 주소를 넣으세요!
ROS_PORT = 65432         # Linux 서버 코드와 같아야 함

DURATION = 15            # 데이터 수집 시간 (초)
FS = 128                 # 샘플링 레이트
EPOCH_SAMPLES = int(FS * 0.8) 
MODEL_PATH = "p300_model.pkl"

# ==========================================
# 필터 및 함수
# ==========================================
def butter_bandpass(lowcut, highcut, fs, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def filter_data(data, lowcut=1.0, highcut=20.0, fs=128):
    if len(data) < fs: return data
    b, a = butter_bandpass(lowcut, highcut, fs)
    filtered = lfilter(b, a, data, axis=0) 
    return filtered

def run_realtime_prediction():
    # 1. 모델 로드
    if not os.path.exists(MODEL_PATH):
        print("❌ 모델 파일이 없습니다. bci_train_model.py를 먼저 실행하세요.")
        return
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    print(f">> Model loaded: {MODEL_PATH}")

    # 2. [추가] ROS 연결 시도
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print(f">> Connecting to ROS ({ROS_IP}:{ROS_PORT})...")
        client_socket.connect((ROS_IP, ROS_PORT))
        print(">> ✅ Connected to ROS! Robot is ready.")
    except:
        print("❌ ROS 연결 실패! (네비게이션 없이 진행합니다)")
        client_socket = None

    # 3. LSL 스트림 연결
    print(">> Looking for LSL streams...")
    streams = resolve_streams()
    eeg_inlet = None
    marker_inlet = None

    for stream in streams:
        if stream.type() == 'EEG':
            eeg_inlet = StreamInlet(stream)
            print(f"  -> EEG Connected: {stream.name()}")
        elif stream.type() == 'Markers':
            marker_inlet = StreamInlet(stream)
            print(f"  -> Markers Connected: {stream.name()}")

    if not eeg_inlet or not marker_inlet:
        print("❌ 스트림을 찾을 수 없습니다. main.py와 UI를 실행했나요?")
        return

    # 4. 실시간 루프
    while True:
        print("\n" + "="*50)
        input(">> 🎯 원하는 지점을 응시하고 [Enter]를 누르세요! (종료: Ctrl+C)")
        print(f">> {DURATION}초 동안 데이터를 수집합니다... 집중하세요!")
        print("="*50)

        eeg_buffer = []    
        marker_buffer = [] 
        start_time = time.time()

        # 데이터 수집
        while time.time() - start_time < DURATION:
            chunk, ts = eeg_inlet.pull_chunk(timeout=0.0)
            if ts:
                for i in range(len(ts)):
                    eeg_buffer.append([ts[i]] + chunk[i])
            
            marker, ts_m = marker_inlet.pull_sample(timeout=0.0)
            if marker:
                marker_buffer.append([ts_m, marker[0]])
            
            time.sleep(0.005)

        print("\n>> 분석 중... (Thinking...)")
        
        if len(eeg_buffer) == 0:
            print("❌ 데이터가 없습니다.")
            continue
            
        # 전처리 및 예측 로직
        eeg_arr = np.array(eeg_buffer)
        timestamps = eeg_arr[:, 0]
        eeg_raw = eeg_arr[:, 1:15] 
        eeg_filtered = filter_data(eeg_raw, fs=FS)

        row_scores = {i: [] for i in range(6)} 
        col_scores = {i: [] for i in range(6)}

        for m_time, m_str in marker_buffer:
            try:
                m_type, m_idx = m_str.split('_')
                m_idx = int(m_idx)
            except: continue

            idx_start = np.searchsorted(timestamps, m_time)
            idx_end = idx_start + EPOCH_SAMPLES

            if idx_end < len(eeg_filtered):
                epoch = eeg_filtered[idx_start:idx_end, :]
                feat = epoch.flatten().reshape(1, -1)
                score = model.decision_function(feat)[0]
                
                if m_type == 'row': row_scores[m_idx].append(score)
                elif m_type == 'col': col_scores[m_idx].append(score)

        best_row = -1
        max_r_score = -999
        best_col = -1
        max_c_score = -999

        for r_idx, scores in row_scores.items():
            if len(scores) > 0:
                avg = np.mean(scores)
                if avg > max_r_score: max_r_score = avg; best_row = r_idx

        for c_idx, scores in col_scores.items():
            if len(scores) > 0:
                avg = np.mean(scores)
                if avg > max_c_score: max_c_score = avg; best_col = c_idx

        # 결과 출력 및 전송
        print("\n" + "#"*40)
        print(f"🏆 예측 결과: 행(Row) {best_row}, 열(Col) {best_col}")
        
        # [추가] ROS로 전송
        if client_socket and best_row != -1:
            msg = f"{best_row},{best_col}"
            try:
                client_socket.sendall(msg.encode())
                print(f"🚀 [Command Sent] ROS로 이동 명령 전송: {msg}")
            except:
                print("❌ 전송 실패 (연결 끊김?)")
        
        print("#"*40 + "\n")

if __name__ == "__main__":
    run_realtime_prediction()