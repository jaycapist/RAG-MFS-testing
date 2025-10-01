import os
import subprocess

def sync_pdfs_from_drive(folder_id, output_dir="data/Minutes"):
    print("Downloading PDFs.")
    os.makedirs(output_dir, exist_ok=True)
    cmd = [
        "gdown",
        "--folder",
        folder_id,
        "--output",
        output_dir,
        "--quiet"
    ]
    subprocess.run(cmd, check=True)