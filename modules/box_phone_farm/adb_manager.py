import os
import subprocess
from pathlib import Path

class ADBManager:
    def __init__(self, adb_path: str = "adb"):
        self.adb_path = adb_path

    def run_cmd(self, device_id: str, command: str) -> str:
        """Chạy lệnh ADB shell trên một thiết bị cụ thể"""
        cmd = f"{self.adb_path} -s {device_id} shell {command}"
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return res.stdout.strip()
        except Exception as e:
            print(f"[ADBManager] Lỗi chạy lệnh '{cmd}': {e}")
            return ""

    def push_video(self, device_id: str, local_mp4_path: str, remote_dest_path: str = "/sdcard/DCIM/Camera/temp_post.mp4") -> bool:
        """Đẩy 1 file video vào bộ nhớ của Box Phone"""
        cmd = f"{self.adb_path} -s {device_id} push \"{local_mp4_path}\" \"{remote_dest_path}\""
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            if res.returncode == 0:
                # Ép Android quét và thêm video vào Thư viện ảnh (Gallery) ngay lập tức
                self.rescan_mediastore(device_id, remote_dest_path)
                return True
            return False
        except Exception as e:
            print(f"[ADBManager] Lỗi push video sang {device_id}: {e}")
            return False

    def rescan_mediastore(self, device_id: str, file_path: str):
        """Báo cho Media Scanner của Android cập nhật lại Thư viện ảnh"""
        self.run_cmd(device_id, f"am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{file_path}")

    def cleanup_video(self, device_id: str, remote_dest_path: str = "/sdcard/DCIM/Camera/temp_post.mp4"):
        """XÓA SẠCH video vừa đăng để bộ nhớ máy luôn trống 100%"""
        print(f"[ADBManager] 🧹 Đang dọn dẹp bộ nhớ trên máy {device_id}...")
        self.run_cmd(device_id, f"rm -f {remote_dest_path}")
        self.rescan_mediastore(device_id, remote_dest_path)
        print(f"[ADBManager] ✨ Bộ nhớ máy {device_id} đã được dọn sạch hoàn toàn!")

    def type_vietnamese_text(self, device_id: str, text: str):
        """Gõ tiếng Việt có dấu và icon chuẩn 100% qua ADBKeyBoard"""
        # Nếu đã cài ADBKeyBoard trên Box Phone
        cmd = f"am broadcast -a ADB_INPUT_TEXT --es msg \"{text}\""
        self.run_cmd(device_id, cmd)

    def capture_screenshot(self, device_id: str, local_save_path: str) -> bool:
        """Chụp ảnh màn hình điện thoại gửi báo cáo về Telegram"""
        remote_tmp = "/sdcard/screen_tmp.png"
        self.run_cmd(device_id, f"screencap -p {remote_tmp}")
        cmd = f"{self.adb_path} -s {device_id} pull {remote_tmp} \"{local_save_path}\""
        subprocess.run(cmd, shell=True, capture_output=True, timeout=20)
        self.run_cmd(device_id, f"rm -f {remote_tmp}")
        return Path(local_save_path).exists()
