#!/usr/bin/python3
import mysql.connector
import os
import socket
from datetime import datetime

# ==============================
# MySQL 연결 설정
# ==============================
DB_HOST = "10.4.4.11"  
DB_USER = "backup_admin"
DB_PASS = "BackupPass1."
DB_NAME = "nas_backup"

db_connection = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME
)
cursor = db_connection.cursor()

# ==============================
# 복구 함수
# ==============================
def restore_file():
    pc_input = input("복구할 PC 이름을 입력하세요 (예: PC1, PC2 등, 숫자만 입력 가능): ")
    # 숫자만 입력하면 PC숫자 형태로 변환
    pc_name = f"PC{pc_input}" if pc_input.isdigit() else pc_input
    table_name = f"{pc_name}_backup"

    # 테이블 존재 여부 확인
    cursor.execute("SHOW TABLES")
    tables = [t[0] for t in cursor.fetchall()]
    if table_name not in tables:
        print(f"[ERROR] {table_name} 테이블이 존재하지 않습니다.")
        return

    # 해당 PC의 파일 목록 조회
    cursor.execute(f"SELECT id, filename, uploaded_at FROM {table_name}")
    files = cursor.fetchall()
    if not files:
        print(f"[{pc_name}] 테이블에 파일이 없습니다.")
        return

    # 복구할 파일 선택
    filename_to_restore = input("복구할 파일 이름을 입력하세요: ")

    # 동일 이름 파일 여러 개 확인
    matching_files = [f for f in files if f[1] == filename_to_restore]
    if not matching_files:
        print(f"파일 '{filename_to_restore}'이 데이터베이스에 존재하지 않습니다.")
        return

    if len(matching_files) > 1:
        print("같은 이름의 파일이 여러 개 있습니다. ID를 선택하세요:")
        for f in matching_files:
            print(f"ID: {f[0]}, 파일명: {f[1]}, 업로드: {f[2]}")
        file_id = input("복구할 파일 ID 입력: ")
        cursor.execute(f"SELECT file_data FROM {table_name} WHERE id = %s", (file_id,))
        file_data = cursor.fetchone()
    else:
        cursor.execute(f"SELECT file_data FROM {table_name} WHERE filename = %s", (filename_to_restore,))
        file_data = cursor.fetchone()

    if file_data:
        file_data = file_data[0]
        # 로컬 복구 경로 생성
        restore_dir = f"./restored_{pc_name}"
        os.makedirs(restore_dir, exist_ok=True)
        restore_path = os.path.join(restore_dir, f"{filename_to_restore}")
        with open(restore_path, 'wb') as f:
            f.write(file_data)
        print(f"파일 '{filename_to_restore}' 복원이 완료되었습니다. 저장 위치: {restore_path}")

        # 백업 로그 기록 (backup_list.txt)
        log_path = os.path.join(restore_dir, "backup_list.txt")
        with open(log_path, "a") as log_file:
            log_file.write(f"{filename_to_restore} >> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    else:
        print("복구 중 오류가 발생했습니다.")

# ==============================
# 목록보기 함수
# ==============================
def show_file_list():
    while True:
        print("\n--- 목록보기 ---")
        print("1) 모든 PC 목록 보기")
        print("2) 특정 PC 파일 보기")
        print("3) 이전 메뉴로 돌아가기")
        choice = input("선택: ")

        if choice == '1':
            cursor.execute("SHOW TABLES")
            tables = [t[0] for t in cursor.fetchall()]
            pc_tables = [t for t in tables if t.endswith("_backup")]
            print("\nPC 목록:")
            for t in pc_tables:
                print(f"- {t.replace('_backup','')}")
        elif choice == '2':
            cursor.execute("SHOW TABLES")
            tables = [t[0] for t in cursor.fetchall()]
            pc_tables = [t for t in tables if t.endswith("_backup")]

            pc_choice = input("PC 선택 (번호 입력): ")
            try:
                pc_index = int(pc_choice) - 1
                pc_table = pc_tables[pc_index]
                cursor.execute(f"SELECT id, filename, uploaded_at FROM {pc_table}")
                files = cursor.fetchall()
                if files:
                    print(f"[{pc_table.replace('_backup','')}] 파일 목록:")
                    for f in files:
                        print(f"ID: {f[0]}, 파일명: {f[1]}, 업로드: {f[2]}")
                else:
                    print("파일이 없습니다.")
            except (ValueError, IndexError):
                print("잘못된 입력입니다.")
        elif choice == '3':
            break
        else:
            print("잘못된 선택입니다. 1, 2, 3 중 선택해주세요.")

# ==============================
# 메인 메뉴
# ==============================
while True:
    print("\n=== 백업 복구 메뉴 ===")
    print("1) 복구")
    print("2) 백업 목록")
    print("3) 종료")
    choice = input("선택: ")

    if choice == '1':
        restore_file()
    elif choice == '2':
        show_file_list()
    elif choice == '3':
        print("복구 프로그램을 종료합니다~\n")
        break
    else:
        print("잘못된 선택입니다. 1, 2, 3 중 선택해주세요.")

# DB 연결 종료
cursor.close()
db_connection.close()

