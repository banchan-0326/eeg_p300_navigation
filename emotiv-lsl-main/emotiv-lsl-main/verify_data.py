import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

def load_latest_file(pattern):
    files = glob.glob(pattern)
    if not files: return None
    return max(files, key=os.path.getctime)

def verify():
    # 1. 최신 데이터 불러오기
    eeg_file = load_latest_file("data/eeg_*.csv")
    marker_file = load_latest_file("data/markers_*.csv")

    if not eeg_file or not marker_file:
        print("❌ 실패: 데이터 파일이 없습니다.")
        return

    print(f"📂 EEG 파일: {eeg_file}")
    print(f"📂 마커 파일: {marker_file}")

    df_eeg = pd.read_csv(eeg_file)
    df_marker = pd.read_csv(marker_file)

    # 2. 데이터 기본 점검
    print(f"📊 EEG 데이터 크기: {df_eeg.shape} (행, 열)")
    print(f"📍 마커 개수: {len(df_marker)} 개")

    if df_eeg.empty or df_marker.empty:
        print("❌ 실패: 파일 내용이 비어있습니다.")
        return

    # 3. 시각화 (동기화 확인)
    plt.figure(figsize=(15, 6))
    
    # EEG 채널 중 하나만 그림 (예: 3번 채널)
    # Emotiv 데이터가 보통 값이 크거나 DC offset이 있을 수 있으니 평균을 빼서 그림
    plt.plot(df_eeg['Timestamp'], df_eeg.iloc[:, 1] - df_eeg.iloc[:, 1].mean(), 
             label='EEG Channel 1', color='black', linewidth=0.5)

    # 마커 위치에 빨간 선 그리기
    for t in df_marker['Timestamp']:
        plt.axvline(x=t, color='red', alpha=0.3, linestyle='--')

    plt.title("Synchronization Check: EEG (Black) + Stimulus Markers (Red)")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Amplitude (uV)")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    verify()