import subprocess
import os

def sync_pdfs_from_drive(folder_id, output_dir="data/"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("Downloading PDFs.")
    cmd = [
        "gdown",
        "--folder",
        f"https://drive.google.com/drive/folders/{folder_id}",
        "--output", output_dir,
        "--quiet"
    ]
    subprocess.run(cmd, check=True)
    print("Downloaded PDFs.")
