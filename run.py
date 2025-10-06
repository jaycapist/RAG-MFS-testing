import os
import base64
import uvicorn
from main import create_app

def write_rclone_config():
    config_base64 = os.getenv("RCLONE_CONFIG_BASE64")
    if config_base64:
        os.makedirs("/root/.config/rclone", exist_ok=True)
        with open("/root/.config/rclone/rclone.conf", "wb") as f:
            f.write(base64.b64decode(config_base64))

if __name__ == "__main__":
    write_rclone_config()
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(create_app, host="0.0.0.0", port=port)
