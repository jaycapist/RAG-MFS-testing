import os
import json
import requests
from pathlib import Path
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

FOLDER_ID = "1lfB7MZcCjU-GPu3afgAAupEAnOzLdW4u"
CREDENTIALS_FILE = "sync_account.json"
DEST_DIR = Path("data/")
GDRIVE_MAP = Path("scripts/gdrive_map.json")

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

def walk_folder(folder_id, file_map):zip
    try:
        pdf_query = f"'{folder_id}' in parents and mimeType='application/pdf'"
        pdfs = drive_service.files().list(q=pdf_query, fields="files(id, name)").execute().get("files", [])
    except Exception as e:
        print(f"Error listing PDFs in folder {folder_id}: {e}")
        return

    for file in pdfs:
        file_id = file['id']
        name = file['name']
        link = f"https://drive.google.com/file/d/{file_id}/view"
        file_map[name] = file_id

        dest_path = DEST_DIR / name
        if not dest_path.exists():
            print(f"⬇ Downloading: {name}")
            try:
                request = drive_service.files().get_media(fileId=file_id)
                with open(dest_path, "wb") as f:
                    f.write(request.execute())
            except Exception as e:
                print(f"Failed to download : {name} : {e}")
        else:
            print(f"Already downloaded: {name}")

    try:
        folder_query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
        subfolders = drive_service.files().list(q=folder_query, fields="files(id, name)").execute().get("files", [])
    except Exception as e:
        print(f"Error listing subfolders : {folder_id}: {e}")
        return

    for folder in subfolders:
        print(f"Entering folder: {folder['name']}")
        walk_folder(folder['id'], file_map)


def sync_drive_folder():
    DEST_DIR.mkdir(exist_ok=True)
    print(f"Scanning Drive folder: {FOLDER_ID}")
    
    file_map = {}

    walk_folder(FOLDER_ID, file_map)

    print(f"\nSaving gdrive_map.json")
    with open(GDRIVE_MAP, "w") as f:
        json.dump(file_map, f, indent=2)

    print("Sync complete.")

if __name__ == "__main__":
    sync_drive_folder()
