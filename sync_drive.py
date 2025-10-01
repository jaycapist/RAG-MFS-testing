import subprocess
import os

def ensure_rclone_config():
    config_path = "/app/config/rclone.conf"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            f.write(os.environ["RCLONE_CONFIG_CONTENT"])
            
def sync_from_drive():
    print("Syncing")
    os.makedirs("data/", exist_ok=True)
    
    try:
        subprocess.run([
            "rclone", "copy", "goodrive:", "data/",
            "--drive-shared-with-me", "--progress"
        ], check=True)
        print("Synced")
    except subprocess.CalledProcessError as e:
        print("Failed to Sync", e)
