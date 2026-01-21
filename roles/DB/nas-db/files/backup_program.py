#!/usr/bin/python3
# backup_client.py

import os
import subprocess
import shutil
import socket
import re
from datetime import datetime
import mysql.connector

# ==============================
# 0-1) MySQL 연결 설정
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
# 0-2) 경로 설정 (정리 핵심)
# ==============================
BACKUP_META_DIR = "/home/ansible-admin/backup_list"
BACKUP_LIST_FILE = f"{BACKUP_META_DIR}/backup_list.txt"
os.makedirs(BACKUP_META_DIR, exist_ok=True)

MASTER_IP = "10.4.4.11"

# ==============================
# 0-3) IP → PC 매핑
# ==============================
def get_pc_folder_from_ip():
    ip_address = socket.gethostbyname(socket.gethostname())
    match = re.match(r"10\.4\.(\d+)\.\d+", ip_address)

    if not match:
        return None, ip_address

    subnet = int(match.group(1))
    mapping = {
        1: 'PC1_ai',
        2: 'PC2_web',
        3: 'PC3_cicd',
        4: 'PC4_db',
        5: 'PC5_monitoring'
    }

    return mapping.get(subnet), ip_address

# ==============================
# 0-4) table 표시용 이름 매핑
# ==============================
TABLE_DISPLAY_MAP = {
    "PC1": "ai",
    "PC2": "web",
    "PC3": "cicd",
    "PC4": "db",
    "PC5": "monitoring",
    "result": "result"
}

# ==============================
# 0-5) 마스터 여부
# ==============================
def is_master_node():
    ip = socket.gethostbyname(socket.gethostname())
    return ip == MASTER_IP


# ==============================
# 0-6) 백업 파일명 생성
# ==============================
def get_backup_filename(pc_folder, ip_address):
    last_octet = ip_address.split('.')[-1]
    pc_prefix = pc_folder.split('_')[1].lower()

    try:
        with open(BACKUP_LIST_FILE) as f:
            count = len(f.readlines()) + 1
    except FileNotFoundError:
        count = 1

    return f"{pc_prefix}{last_octet}_backup{count}.tar.gz", count

###################################################################


# ######################################
# 1) 백업하기
# ######################################
def create_backup():
    print("\n=== 백업 생성 ===")
    pc_folder, ip_address = get_pc_folder_from_ip()

    if not pc_folder:
        print("백업할 PC를 자동으로 결정할 수 없습니다.")
        return

    print(f"자동 선택 PC: {pc_folder} ({ip_address})")

    backup_filename, backup_count = get_backup_filename(pc_folder, ip_address)
    source_dir = "/home/ansible-admin/"
    backup_dir = f"/mnt/NAS/{pc_folder}"
    os.makedirs(backup_dir, exist_ok=True)

    # 증분 백업 로직
    if os.path.exists(BACKUP_LIST_FILE) and os.path.getsize(BACKUP_LIST_FILE) > 0:
        while True:
            choice = input("증분 백업을 이어가시겠습니까? (y/n): ").lower()
            if choice == 'y':
                with open(BACKUP_LIST_FILE) as f:
                    last = f.readlines()[-1].strip()
                increment_list = last.split(" - ")[2]
                break
            elif choice == 'n':
                increment_list = f"{BACKUP_META_DIR}/increment_backup{backup_count}"
                open(increment_list, 'w').close()
                break
    else:
        increment_list = f"{BACKUP_META_DIR}/increment_backup{backup_count}"
        open(increment_list, 'w').close()

    print(f"증분 리스트: {increment_list}")

    try:
        subprocess.run(
            ["tar", "-g", increment_list, "-zcf", backup_filename, source_dir],
            check=True
        )

        shutil.move(backup_filename, os.path.join(backup_dir, backup_filename))

        with open(BACKUP_LIST_FILE, "a") as f:
            f.write(f"{backup_filename} - {pc_folder} - {increment_list}\n")

        print("백업 완료")

    except Exception as e:
        print("백업 중 오류:", e)


# ######################################
# 2) 복구하기
# ######################################
def restore_file():
    pc_folder, _ = get_pc_folder_from_ip()
    master = is_master_node()

    cursor.execute("SHOW TABLES")
    all_tables = [t[0] for t in cursor.fetchall() if t[0].endswith("_backup")]

    selectable = []

    if master:
        selectable = all_tables
    else:
        if pc_folder:
            my_table = f"{pc_folder.split('_')[0]}_backup"
            if my_table in all_tables:
                selectable.append(my_table)
        if "result_backup" in all_tables:
            selectable.append("result_backup")

    if not selectable:
        print("복구 가능한 대상이 없습니다.")
        return

    print("\n복구 가능한 대상:")
    table_map = {}
    for i, t in enumerate(selectable, start=1):
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cursor.fetchone()[0]
        print(f"{i}) {t.replace('_backup','')} (파일 {cnt}개)")
        table_map[i] = t

    choice = input("대상 선택: ")

    try:
        table = table_map[int(choice)]
    except:
        print("잘못된 선택")
        return

    cursor.execute(
        f"SELECT id, filename, uploaded_at FROM {table} ORDER BY uploaded_at DESC"
    )
    files = cursor.fetchall()

    if not files:
        print("파일이 없습니다.")
        return

    print("\n파일 목록:")
    for f in files:
        print(f"ID:{f[0]} | {f[1]} | {f[2]}")

    fid = input("복구할 ID 입력: ")
    cursor.execute(
        f"SELECT filename, file_data FROM {table} WHERE id=%s",
        (fid,)
    )
    row = cursor.fetchone()

    if not row:
        print("파일이 존재하지 않습니다.")
        return

    restore_dir = f"./restored_{table.replace('_backup','')}"
    os.makedirs(restore_dir, exist_ok=True)

    with open(os.path.join(restore_dir, row[0]), "wb") as f:
        f.write(row[1])

    print(f"복구 완료 → {restore_dir}/{row[0]}")


# ######################################
# 3) 백업 목록 보기
# ######################################
def show_backup_list():
    while True:
        cursor.execute("SHOW TABLES")
        tables = [t[0] for t in cursor.fetchall() if t[0].endswith("_backup")]

        if not tables:
            print("조회 가능한 테이블이 없습니다.")
            return

        table_map = {}
        print("\n--- 백업 테이블 선택 ---")
        print("0) 이전 메뉴")

        for i, t in enumerate(tables, start=1):
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = cursor.fetchone()[0]

            base = t.replace("_backup", "")
            display = TABLE_DISPLAY_MAP.get(base, base)

            print(f"{i}) {display} ({cnt})")
            table_map[i] = t

        sel = input("선택: ")

        # 이전 메뉴
        if sel == '0':
            return

        try:
            table = table_map[int(sel)]
        except (ValueError, KeyError):
            print("잘못된 선택")
            continue

        cursor.execute(
            """
            SELECT id, filename, uploaded_at
            FROM %s
            ORDER BY uploaded_at DESC
            """ % table
        )
        rows = cursor.fetchall()

        if not rows:
            print("파일이 없습니다.")
            continue

        print("\n파일 목록:")
        for f in rows:
            print(f"ID:{f[0]} | {f[1]} | {f[2]}")


###################################################################

# ######################################
# 메인
# ######################################
def main():
    while True:
        print("\n=== 백업 관리 프로그램 ===")
        print("1) 백업하기")
        print("2) 복구하기")
        print("3) 백업 목록 보기")
        print("4) 종료")

        choice = input("선택: ")

        if choice == '1':
            create_backup()
        elif choice == '2':
            restore_file()
        elif choice == '3':
            show_backup_list()
        elif choice == '4':
            break
        else:
            print("잘못된 선택")

if __name__ == "__main__":
    main()


