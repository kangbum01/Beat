import mysql.connector
import os
from datetime import datetime

# MySQL 연결
db_connection = mysql.connector.connect(
    host="10.4.4.11",
    user="backup_admin",
    password="BackupPass1.",
    database="nas_backup",
    port=3306
)

cursor = db_connection.cursor()

# PC 테이블명과 폴더명 매핑
pc_map = {
    "PC1": "PC1_ai",
    "PC2": "PC2_web",
    "PC3": "PC3_cicd",
    "PC4": "PC4_db",
    "PC5": "PC5_monitoring",
    "result": "result"
}

base_path = "/mnt/NAS"

for pc_name, folder_name in pc_map.items():
    tar_directory = os.path.join(base_path, folder_name)

    if not os.path.exists(tar_directory):
        print(f"{tar_directory} 경로가 존재하지 않습니다.")
        continue

    backup_list_file = os.path.join(tar_directory, "backup_list.txt")

    for filename in os.listdir(tar_directory):
        if filename.endswith(".tar.gz"):
            tar_file_path = os.path.join(tar_directory, filename)

            try:
                with open(tar_file_path, "rb") as file:
                    file_data = file.read()

                query = f"""
                    INSERT INTO {pc_name}_backup (filename, file_data)
                    VALUES (%s, %s)
                """
                cursor.execute(query, (filename, file_data))
                db_connection.commit()

                # NAS 파일 삭제
                os.remove(tar_file_path)

                # 백업 기록 추가
                with open(backup_list_file, "a") as f:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{filename} {now}\n")

                print(f"[{pc_name}] '{filename}' 백업 완료, NAS 삭제, backup_list.txt에 기록")

            except Exception as e:
                print(f"[ERROR] {filename} 처리 중 오류 발생: {e}")
                db_connection.rollback()

# 연결 종료
cursor.close()
db_connection.close()

print("모든 PC 백업이 완료되었습니다.")

