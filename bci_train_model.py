import pandas as pd
import numpy as np
import glob
import os
import pickle
from scipy.signal import butter, lfilter
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import cross_val_score

# ==========================================
# 사용자 설정 (녹화할 때 어디를 보고 있었나요?)
# ==========================================
TARGET_ROW = 2   # 예: 사용자가 2행을 보고 있었다면 2
TARGET_COL = 2   # 예: 사용자가 3열을 보고 있었다면 3
# ==========================================

def load_latest_file(pattern):
    files = glob.glob(pattern)
    if not files: return None
    return max(files, key=os.path.getctime)

def butter_bandpass(lowcut, highcut, fs, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def filter_data(data, lowcut, highcut, fs=128):
    b, a = butter_bandpass(lowcut, highcut, fs)
    # 데이터프레임의 각 채널(열)에 필터 적용
    filtered = data.copy()
    for col in data.columns:
        if col.startswith('Ch'): # 채널 데이터만 필터링
            filtered[col] = lfilter(b, a, data[col])
    return filtered

def train_model():
    print(">> 1. Loading Data...")
    eeg_file = load_latest_file("data/eeg_*.csv")
    marker_file = load_latest_file("data/markers_*.csv")
    
    if not eeg_file or not marker_file:
        print("Error: Data files not found.")
        return

    print(f"   EEG: {eeg_file}")
    print(f"   Markers: {marker_file}")
    
    df_eeg = pd.read_csv(eeg_file)
    df_marker = pd.read_csv(marker_file)

    # 2. 전처리 (Bandpass Filter 1-20Hz)
    print(">> 2. Preprocessing (Filtering)...")
    df_eeg = filter_data(df_eeg, 1.0, 20.0, fs=128)

    # 3. 에포킹 (Epoching) & 라벨링 (Labeling)
    # Target(내가 본 곳) = 1, Non-Target(안 본 곳) = 0
    X = [] # 특징 벡터 (Feature)
    y = [] # 정답 라벨 (Label)
    
    timestamps = df_eeg['Timestamp'].values
    # EEG 데이터만 numpy array로 변환 (속도 최적화)
    eeg_values = df_eeg.drop(columns=['Timestamp']).values 
    
    print(f">> 3. Epoching (Target: Row {TARGET_ROW}, Col {TARGET_COL})...")
    
    for idx, row in df_marker.iterrows():
        marker = row['Event'] # 예: 'row_2'
        t_start = row['Timestamp']
        
        # 정답 여부 확인
        is_target = 0
        if f"row_{TARGET_ROW}" == marker: is_target = 1
        if f"col_{TARGET_COL}" == marker: is_target = 1
        
        # 시간 매핑 (가장 가까운 EEG 인덱스 찾기)
        # np.searchsorted는 정렬된 배열에서 위치를 매우 빠르게 찾아줌
        start_idx = np.searchsorted(timestamps, t_start)
        
        # 0ms ~ 800ms 구간 추출 (128Hz * 0.8s = 약 103 샘플)
        duration_samples = int(128 * 0.8)
        end_idx = start_idx + duration_samples
        
        if end_idx < len(eeg_values):
            epoch = eeg_values[start_idx:end_idx, :] # (Time, Channels)
            
            # 특징 추출 (Feature Extraction)
            # 단순화를 위해 '모든 채널의 시간대별 전압'을 쭉 펴서(Flatten) 사용
            # 차원 축소나 더 복잡한 특징은 성능 개선 시 적용
            feature_vector = epoch.flatten()
            
            X.append(feature_vector)
            y.append(is_target)

    X = np.array(X)
    y = np.array(y)
    
    print(f"   Total Epochs: {len(y)}")
    print(f"   Target Samples: {sum(y)} / Non-Target Samples: {len(y)-sum(y)}")

    # 4. 분류 모델 학습 (LDA)
    print(">> 4. Training LDA Classifier...")
    clf = LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')
    
    # 교차 검증으로 정확도 미리 보기
    scores = cross_val_score(clf, X, y, cv=5)
    print(f"   Model Accuracy (CV): {scores.mean()*100:.2f}%")
    
    # 전체 데이터로 학습
    clf.fit(X, y)
    
    # 5. 모델 저장
    model_filename = "p300_model.pkl"
    with open(model_filename, 'wb') as f:
        pickle.dump(clf, f)
    
    print(f">> 5. Model Saved to '{model_filename}'")
    print("   Now you can run the real-time test!")

if __name__ == "__main__":
    train_model()