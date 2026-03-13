import sys
import random
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QLabel, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QColor, QPalette
from pylsl import StreamInfo, StreamOutlet

# ==========================================
# 설정 (Configuration)
# ==========================================
GRID_ROWS = 6        # 격자 행 개수 (6x6 = 36개 영역)
GRID_COLS = 6        # 격자 열 개수
FLASH_DURATION = 100 # 자극 유지 시간 (ms)
ISI_DURATION = 75    # 자극 사이 간격 (ms) - Inter-Stimulus Interval
MAP_IMAGE_PATH = "map.png" # 같은 폴더에 지도 이미지가 있어야 합니다.

class MapStimulusWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("P300 Map Speller - Emotiv LSL")
        self.resize(800, 600)

        # 1. LSL 스트림 초기화 (마커 송출용)
        # Type: Markers, Name: P300_Markers, Channel: 1, Freq: 0 (Irregular), Format: string
        self.info = StreamInfo('P300_Markers', 'Markers', 1, 0, 'string', 'myuidw43536')
        self.outlet = StreamOutlet(self.info)
        print(">> LSL Marker Stream Created! Waiting for receiver...")

        # 2. UI 초기화
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 배경 (지도 설정)
        self.background_label = QLabel(self.central_widget)
        self.background_label.setGeometry(0, 0, 800, 600)
        self.background_label.setScaledContents(True)
        
        # 지도 이미지 로드 (없으면 회색 배경)
        try:
            self.background_label.setPixmap(QPixmap(MAP_IMAGE_PATH))
        except:
            self.background_label.setStyleSheet("background-color: #333;")
            print("Warning: 'map.png' not found. Using dark background.")

        # 3. 격자 생성 (Grid Overlay)
        self.grid_layout = QGridLayout(self.central_widget)
        self.cells = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                label = QLabel()
                label.setStyleSheet("background-color: rgba(255, 255, 255, 0); border: 1px solid rgba(0, 255, 0, 0.3);")
                self.grid_layout.addWidget(label, r, c)
                self.cells[r][c] = label

        # 4. 타이머 설정 (자극 루프)
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_stimulus_cycle)
        self.is_flashing = False
        self.current_target = None # 현재 깜빡이는 대상 (type, index)

        # 자극 시작
        self.start_stimulation()

    def start_stimulation(self):
        print(">> Stimulation Started.")
        self.timer.start(ISI_DURATION)

    def run_stimulus_cycle(self):
        # 만약 현재 깜빡이고 있다면 -> 끈다 (OFF)
        if self.is_flashing:
            self.reset_grid()
            self.is_flashing = False
            self.timer.setInterval(ISI_DURATION) # 쉬는 시간(ISI) 설정
        
        # 안 깜빡이고 있다면 -> 켠다 (ON)
        else:
            self.flash_random()
            self.is_flashing = True
            self.timer.setInterval(FLASH_DURATION) # 켜져있는 시간 설정

    def flash_random(self):
        # 행(0)을 깜빡일지, 열(1)을 깜빡일지 랜덤 결정
        mode = random.choice(['ROW', 'COL'])
        
        if mode == 'ROW':
            idx = random.randint(0, GRID_ROWS - 1)
            marker_str = f"row_{idx}"
            # 해당 행의 모든 셀 색상 변경
            for c in range(GRID_COLS):
                self.cells[idx][c].setStyleSheet("background-color: rgba(255, 255, 255, 0.7); border: 1px solid red;")
        else:
            idx = random.randint(0, GRID_COLS - 1)
            marker_str = f"col_{idx}"
            # 해당 열의 모든 셀 색상 변경
            for r in range(GRID_ROWS):
                self.cells[r][idx].setStyleSheet("background-color: rgba(255, 255, 255, 0.7); border: 1px solid red;")

        # ★ 핵심: 자극 시점에 LSL 마커 전송
        self.outlet.push_sample([marker_str])
        # print(f"Sent Marker: {marker_str}") # 디버깅용

    def reset_grid(self):
        # 격자 스타일 초기화 (투명하게)
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                self.cells[r][c].setStyleSheet("background-color: rgba(255, 255, 255, 0); border: 1px solid rgba(0, 255, 0, 0.3);")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MapStimulusWindow()
    window.show()
    sys.exit(app.exec_())