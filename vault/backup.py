import os
import shutil

BACKUP_DIR = "vault_backup"


def backup_file(file_path):

    os.makedirs(BACKUP_DIR, exist_ok=True)

    file_name = os.path.basename(file_path)

    backup_path = os.path.join(BACKUP_DIR, file_name)

    shutil.copy(file_path, backup_path)

    print("Backup created:", backup_path)