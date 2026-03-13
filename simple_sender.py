import socket

# ==========================================
# ★ 설정: Ubuntu(ROS) 컴퓨터의 IP 주소
# ==========================================
# Ubuntu 터미널에서 'hostname -I' 쳐서 나온 IP를 넣으세요.
ROS_IP = '192.168.194.128'  
ROS_PORT = 65432

def run_test_sender():
    try:
        # 1. 소켓 생성 및 연결
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f">> 접속 시도 중... ({ROS_IP}:{ROS_PORT})")
        client_socket.connect((ROS_IP, ROS_PORT))
        print(">> ✅ 연결 성공! ROS 서버와 연결되었습니다.")
        print(">> 좌표를 '행,열' 형태로 입력하세요. (예: 2,3)")
        print(">> 종료하려면 'q'를 입력하세요.")

        while True:
            # 2. 사용자 입력 받기
            user_input = input("\n[Input] 가고 싶은 좌표 (row,col): ")
            
            if user_input.lower() == 'q':
                print(">> 종료합니다.")
                break
            
            # 입력값 검증 (간단히)
            if ',' not in user_input:
                print("⚠️ 형식이 틀렸습니다. '2,3' 처럼 쉼표를 쓰세요.")
                continue

            # 3. 데이터 전송
            # BCI 코드와 똑같은 형식으로 문자열을 보냅니다.
            client_socket.sendall(user_input.encode())
            print(f"🚀 전송 완료: '{user_input}' -> 로봇이 움직이는지 확인하세요!")

    except ConnectionRefusedError:
        print("\n❌ 연결 실패!")
        print(f"   1. Ubuntu IP({ROS_IP})가 맞는지 확인하세요.")
        print("   2. Ubuntu에서 'python3 ros_bci_server.py'를 먼저 실행했는지 확인하세요.")
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    run_test_sender()