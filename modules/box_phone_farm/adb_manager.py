import subprocess
from typing import List, Optional
from loguru import logger
from config.settings import FARM_CONFIG

class ADBManager:
    """Quản lý kết nối ADB, nạp video và dọn dẹp bộ nhớ trên Box Phone Farm."""

    def __init__(self, host: str = FARM_CONFIG["adb_host"], port: int = FARM_CONFIG["adb_port"]):
        self.host = host
        self.port = port

    def run_adb_cmd(self, device_id: str, command: str) -> str:
        """Chạy 1 lệnh adb shell trên thiết bị cụ thể."""
        full_cmd = f"adb -s {device_id} {command}"
        try:
            res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=30)
            return res.stdout.strip()
        except Exception as e:
            logger.error(f"❌ Lỗi chạy ADB cmd ({device_id}): {e}")
            return ""

    def get_connected_devices(self) -> List[str]:
        """Lấy danh sách Device ID các máy đang kết nối."""
        try:
            res = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
            lines = res.stdout.strip().split("\n")[1:]
            devices = []
            for line in lines:
                parts = line.split("\t")
                if len(parts) >= 2 and parts[1].strip() == "device":
                    devices.append(parts[0].strip())
            return devices
        except Exception as e:
            logger.error(f"❌ Lỗi kiểm tra danh sách thiết bị: {e}")
            return []

    def push_video(self, device_id: str, local_video_path: str, remote_filename: str = "upload_temp.mp4") -> str:
        """Đẩy 1 file video duy nhất vào máy và kích hoạt quét media gallery."""
        remote_path = f"/sdcard/DCIM/Camera/{remote_filename}"
        try:
            # Tạo thư mục nếu chưa có
            self.run_adb_cmd(device_id, "shell mkdir -p /sdcard/DCIM/Camera")

            # Push file
            cmd_push = f"push \"{local_video_path}\" {remote_path}"
            self.run_adb_cmd(device_id, cmd_push)

            # Quét media gallery để Shopee nhận diện video mới
            self.run_adb_cmd(device_id, f"shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{remote_path}")
            logger.info(f"📲 Đã nạp video vào {device_id}: {remote_path}")
            return remote_path
        except Exception as e:
            logger.error(f"❌ Lỗi push video sang {device_id}: {e}")
            return ""

    def cleanup_video(self, device_id: str, remote_path: str):
        """Xóa video khỏi bộ nhớ sau khi đăng bài xong."""
        try:
            self.run_adb_cmd(device_id, f"shell rm -f {remote_path}")
            self.run_adb_cmd(device_id, f"shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{remote_path}")
            logger.info(f"🧹 Đã xóa dọn dẹp {remote_path} trên {device_id}")
        except Exception as e:
            logger.error(f"❌ Lỗi dọn dẹp video trên {device_id}: {e}")
