"""
Theo dõi ổ USB mới được cắm vào Windows và phát một file âm thanh.

Chương trình chỉ kiểm tra các ổ đĩa trên chính máy đang chạy, không dùng
autorun USB, không giả lập bàn phím và không thực thi lệnh ẩn.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import msvcrt
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import miniaudio
import psutil


APP_NAME = "USBSoundMonitor"
SOUND_FILENAME = (
    "YTSave_Shorts_Yamate-Kudasai-Sound-Effect-shorts_"
    "Media_01mc4pW_fAw_009_128k.mp3"
)
DEFAULT_CONFIG = {
    "monitor_mode": "all_usb",
    "usb_label": None,
    "poll_interval_seconds": 1.0,
    "insert_start_seconds": 0.0,
    "insert_end_seconds": 1.85,
    "remove_start_seconds": 2.52,
    "remove_end_seconds": 3.15,
}
DRIVE_REMOVABLE = 2
DIGCF_PRESENT = 0x00000002
DIGCF_ALLCLASSES = 0x00000004
ERROR_NO_MORE_ITEMS = 259
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class GUID(ctypes.Structure):
    """Cấu trúc GUID mà Windows SetupAPI sử dụng."""

    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class SP_DEVINFO_DATA(ctypes.Structure):
    """Thông tin một thiết bị Plug-and-Play."""

    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("ClassGuid", GUID),
        ("DevInst", wintypes.DWORD),
        ("Reserved", ctypes.c_size_t),
    ]


def resource_path(filename: str) -> Path:
    """Lấy đường dẫn tài nguyên khi chạy source hoặc EXE PyInstaller."""
    bundle_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return bundle_dir / filename


DEFAULT_CONFIG_PATH = resource_path("usb_sound_config.json")


def configure_console_output() -> None:
    """Dùng UTF-8 để thông báo tiếng Việt không lỗi trên Windows Terminal."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def load_config(config_path: Path) -> dict[str, Any]:
    """Đọc và kiểm tra các thiết lập cần thiết từ file JSON."""
    try:
        with config_path.open("r", encoding="utf-8") as file:
            config = json.load(file)
    except FileNotFoundError:
        # Bản EXE vẫn chạy độc lập ngay cả khi không có file JSON bên ngoài.
        config = dict(DEFAULT_CONFIG)
        config["sound_file"] = str(resource_path(SOUND_FILENAME))
    except json.JSONDecodeError as error:
        raise SystemExit(
            f"File cấu hình không phải JSON hợp lệ: {config_path}\n{error}"
        )

    # Đường dẫn trên máy build không được dùng trên máy người tải EXE.
    if getattr(sys, "frozen", False):
        config["sound_file"] = str(resource_path(SOUND_FILENAME))

    sound_file = config.get("sound_file")
    if not isinstance(sound_file, str) or not sound_file.strip():
        raise SystemExit("Cấu hình 'sound_file' phải là một đường dẫn hợp lệ.")

    poll_interval = config.get("poll_interval_seconds", 1.0)
    if not isinstance(poll_interval, (int, float)) or poll_interval <= 0:
        raise SystemExit("'poll_interval_seconds' phải là một số lớn hơn 0.")

    usb_label = config.get("usb_label")
    if usb_label is not None and not isinstance(usb_label, str):
        raise SystemExit("'usb_label' phải là chuỗi hoặc null.")

    return config


def acquire_single_instance():
    """Khóa một byte trong file để chỉ một bộ theo dõi được phép chạy."""
    app_dir = Path(tempfile.gettempdir()) / APP_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    try:
        lock_path = app_dir / f"{APP_NAME}.lock"
        if not lock_path.exists():
            lock_path.write_bytes(b"\0")
        lock_file = lock_path.open("r+b")
        lock_file.seek(0)
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        if "lock_file" in locals():
            lock_file.close()
        return None
    return lock_file


def get_volume_label(root_path: str) -> str:
    """Lấy tên (volume label) của ổ đĩa, ví dụ MYUSB."""
    volume_name_buffer = ctypes.create_unicode_buffer(261)
    file_system_buffer = ctypes.create_unicode_buffer(261)
    serial_number = ctypes.c_ulong()
    maximum_component_length = ctypes.c_ulong()
    file_system_flags = ctypes.c_ulong()

    success = ctypes.windll.kernel32.GetVolumeInformationW(
        ctypes.c_wchar_p(root_path),
        volume_name_buffer,
        len(volume_name_buffer),
        ctypes.byref(serial_number),
        ctypes.byref(maximum_component_length),
        ctypes.byref(file_system_flags),
        file_system_buffer,
        len(file_system_buffer),
    )
    return volume_name_buffer.value if success else ""


def find_removable_drives() -> dict[str, str]:
    """
    Trả về {đường_dẫn_ổ: tên_USB} cho các ổ removable hiện có.

    psutil dùng để liệt kê phân vùng; GetDriveTypeW của Windows giúp xác nhận
    ổ đó thuộc loại removable.
    """
    drives: dict[str, str] = {}

    for partition in psutil.disk_partitions(all=False):
        mountpoint = partition.mountpoint
        if not mountpoint:
            continue

        drive_type = ctypes.windll.kernel32.GetDriveTypeW(
            ctypes.c_wchar_p(mountpoint)
        )
        if drive_type == DRIVE_REMOVABLE:
            drives[mountpoint.upper()] = get_volume_label(mountpoint)

    return drives


def find_usb_devices() -> set[str]:
    """
    Liệt kê ID của mọi thiết bị USB Plug-and-Play đang hiện diện.

    Khác với psutil, Windows SetupAPI nhận cả bàn phím, chuột, tay cầm,
    điện thoại và ổ flash USB. Không cần chạy PowerShell hay lệnh ẩn.
    """
    setupapi = ctypes.WinDLL("setupapi", use_last_error=True)

    setupapi.SetupDiGetClassDevsW.argtypes = [
        ctypes.c_void_p,
        wintypes.LPCWSTR,
        wintypes.HWND,
        wintypes.DWORD,
    ]
    setupapi.SetupDiGetClassDevsW.restype = ctypes.c_void_p
    setupapi.SetupDiEnumDeviceInfo.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(SP_DEVINFO_DATA),
    ]
    setupapi.SetupDiEnumDeviceInfo.restype = wintypes.BOOL
    setupapi.SetupDiGetDeviceInstanceIdW.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(SP_DEVINFO_DATA),
        wintypes.LPWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    setupapi.SetupDiGetDeviceInstanceIdW.restype = wintypes.BOOL
    setupapi.SetupDiDestroyDeviceInfoList.argtypes = [ctypes.c_void_p]
    setupapi.SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL

    device_info_set = setupapi.SetupDiGetClassDevsW(
        None,
        None,
        None,
        DIGCF_PRESENT | DIGCF_ALLCLASSES,
    )
    if device_info_set == INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error())

    usb_devices: set[str] = set()
    index = 0

    try:
        while True:
            device_info = SP_DEVINFO_DATA()
            device_info.cbSize = ctypes.sizeof(SP_DEVINFO_DATA)

            if not setupapi.SetupDiEnumDeviceInfo(
                device_info_set, index, ctypes.byref(device_info)
            ):
                error = ctypes.get_last_error()
                if error == ERROR_NO_MORE_ITEMS:
                    break
                raise ctypes.WinError(error)

            index += 1
            required_size = wintypes.DWORD()
            setupapi.SetupDiGetDeviceInstanceIdW(
                device_info_set,
                ctypes.byref(device_info),
                None,
                0,
                ctypes.byref(required_size),
            )
            if required_size.value == 0:
                continue

            instance_id = ctypes.create_unicode_buffer(required_size.value)
            if setupapi.SetupDiGetDeviceInstanceIdW(
                device_info_set,
                ctypes.byref(device_info),
                instance_id,
                required_size.value,
                None,
            ):
                value = instance_id.value.upper()
                if value.startswith("USB\\"):
                    usb_devices.add(value)
    finally:
        setupapi.SetupDiDestroyDeviceInfoList(device_info_set)

    return usb_devices


class SoundPlayer:
    """Giải mã một file MP3/WAV và phát từng đoạn theo mốc thời gian."""

    def __init__(self, sound_path: Path) -> None:
        self.sound_path = sound_path
        self.decoded: miniaudio.DecodedSoundFile | None = None
        self.device: miniaudio.PlaybackDevice | None = None

    def _initialize(self) -> bool:
        """Chỉ giải mã và mở thiết bị âm thanh ở lần phát đầu tiên."""
        if self.decoded is not None and self.device is not None:
            return True

        if not self.sound_path.is_file():
            print(f"[LỖI] Không tìm thấy file âm thanh: {self.sound_path}")
            return False

        try:
            self.decoded = miniaudio.decode_file(
                str(self.sound_path),
                output_format=miniaudio.SampleFormat.SIGNED16,
            )
            self.device = miniaudio.PlaybackDevice(
                output_format=miniaudio.SampleFormat.SIGNED16,
                nchannels=self.decoded.nchannels,
                sample_rate=self.decoded.sample_rate,
            )
            return True
        except (OSError, miniaudio.MiniaudioError) as error:
            print(f"[LỖI] Không thể phát âm thanh: {error}")
            self.decoded = None
            self.device = None
            return False

    def play_segment(self, start_seconds: float, end_seconds: float | None) -> None:
        """Phát đoạn [start_seconds, end_seconds] từ file âm thanh."""
        if not self._initialize():
            return

        assert self.decoded is not None
        assert self.device is not None

        total_seconds = self.decoded.num_frames / self.decoded.sample_rate
        start_seconds = max(0.0, min(start_seconds, total_seconds))
        if end_seconds is None:
            end_seconds = total_seconds
        end_seconds = max(start_seconds, min(end_seconds, total_seconds))

        first_sample = int(
            start_seconds * self.decoded.sample_rate * self.decoded.nchannels
        )
        last_sample = int(
            end_seconds * self.decoded.sample_rate * self.decoded.nchannels
        )
        samples = self.decoded.samples[first_sample:last_sample]

        if not samples:
            print("[CẢNH BÁO] Đoạn âm thanh được chọn không có dữ liệu.")
            return

        try:
            # Dừng đoạn cũ nếu USB được cắm/rút liên tiếp quá nhanh.
            self.device.stop()
            stream = miniaudio.stream_raw_pcm_memory(
                samples,
                nchannels=self.decoded.nchannels,
                sample_width=2,  # SIGNED16 = 2 byte mỗi mẫu
            )
            next(stream)  # Miniaudio yêu cầu generator được khởi động trước.
            self.device.start(stream)
        except miniaudio.MiniaudioError as error:
            print(f"[LỖI] Không thể phát đoạn âm thanh: {error}")

    def close(self) -> None:
        if self.device is not None:
            self.device.close()
            self.device = None


def label_matches(actual_label: str, wanted_label: str | None) -> bool:
    """So sánh tên USB không phân biệt chữ hoa/thường."""
    if wanted_label is None or not wanted_label.strip():
        return True
    return actual_label.casefold() == wanted_label.strip().casefold()


def print_drive_list(drives: dict[str, str]) -> None:
    if not drives:
        print("Không tìm thấy ổ USB removable nào.")
        return

    print("Các ổ USB removable đang có:")
    for drive, label in sorted(drives.items()):
        print(f"  - {drive}  Tên: {label or '(không có tên)'}")


def print_usb_device_list(devices: set[str]) -> None:
    if not devices:
        print("Không tìm thấy thiết bị USB Plug-and-Play nào.")
        return

    print("Các thiết bị USB Plug-and-Play đang có:")
    for device_id in sorted(devices):
        print(f"  - {device_id}")


def monitor(config_path: Path) -> None:
    config = load_config(config_path)
    sound_path = Path(config["sound_file"]).expanduser()
    wanted_label = config.get("usb_label")
    monitor_mode = config.get("monitor_mode", "all_usb")
    poll_interval = float(config.get("poll_interval_seconds", 1.0))
    insert_start = float(config.get("insert_start_seconds", 0.0))
    insert_end = config.get("insert_end_seconds")
    insert_end = float(insert_end) if insert_end is not None else None
    remove_start = float(config.get("remove_start_seconds", 2.52))
    remove_end = config.get("remove_end_seconds")
    remove_end = float(remove_end) if remove_end is not None else None
    player = SoundPlayer(sound_path)

    # Tạo trạng thái ban đầu để không phát với USB đã cắm trước khi mở app.
    if monitor_mode == "all_usb":
        known_devices = find_usb_devices()
    elif monitor_mode == "removable_drives":
        known_devices = find_removable_drives()
    else:
        raise SystemExit(
            "'monitor_mode' phải là 'all_usb' hoặc 'removable_drives'."
        )

    print("Đang theo dõi USB. Nhấn Ctrl+C để dừng.")
    print(f"Âm thanh: {sound_path}")
    if monitor_mode == "all_usb":
        print("Chế độ: mọi thiết bị USB (gồm bàn phím, chuột và ổ flash).")
        print_usb_device_list(known_devices)
    else:
        print(
            "Bộ lọc tên USB: "
            + (wanted_label if wanted_label else "Tất cả USB removable")
        )
        print_drive_list(known_devices)

    try:
        while True:
            time.sleep(poll_interval)

            try:
                if monitor_mode == "all_usb":
                    current_devices = find_usb_devices()
                else:
                    current_devices = find_removable_drives()
            except Exception as error:
                print(f"[CẢNH BÁO] Không thể cập nhật danh sách USB: {error}")
                continue

            # set(dict) lấy các key, còn set(set) giữ nguyên các ID thiết bị.
            current_ids = set(current_devices)
            previous_ids = set(known_devices)
            new_ids = current_ids - previous_ids
            removed_ids = previous_ids - current_ids

            if new_ids and monitor_mode == "all_usb":
                print(
                    f"[PHÁT HIỆN] Có thiết bị USB mới "
                    f"({len(new_ids)} interface):"
                )
                for device_id in sorted(new_ids):
                    print(f"  + {device_id}")
                print(f"[PHÁT KHI CẮM] {sound_path}")
                player.play_segment(insert_start, insert_end)

            for drive in sorted(new_ids if monitor_mode != "all_usb" else []):
                label = current_devices[drive]
                print(
                    f"[PHÁT HIỆN] USB mới: {drive} | "
                    f"Tên: {label or '(không có tên)'}"
                )
                if label_matches(label, wanted_label):
                    print(
                        f"[PHÁT KHI CẮM] {sound_path} "
                        f"({insert_start:.2f}s–"
                        f"{insert_end if insert_end is not None else 'hết'})"
                    )
                    player.play_segment(insert_start, insert_end)
                else:
                    print(
                        f"[BỎ QUA] Tên USB không khớp bộ lọc "
                        f"'{wanted_label}'."
                    )

            if removed_ids and monitor_mode == "all_usb":
                print(
                    f"[ĐÃ RÚT] Có thiết bị USB bị tháo "
                    f"({len(removed_ids)} interface):"
                )
                for device_id in sorted(removed_ids):
                    print(f"  - {device_id}")
                print(f"[PHÁT KHI RÚT] {sound_path}")
                player.play_segment(remove_start, remove_end)

            for drive in sorted(
                removed_ids if monitor_mode != "all_usb" else []
            ):
                removed_label = known_devices[drive]
                print(
                    f"[ĐÃ RÚT] USB: {drive} | "
                    f"Tên: {removed_label or '(không có tên)'}"
                )
                if label_matches(removed_label, wanted_label):
                    print(
                        f"[PHÁT KHI RÚT] {sound_path} "
                        f"({remove_start:.2f}s–"
                        f"{remove_end if remove_end is not None else 'hết'})"
                    )
                    player.play_segment(remove_start, remove_end)

            known_devices = current_devices
    except KeyboardInterrupt:
        print("\nĐã dừng theo dõi USB.")
    finally:
        player.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Theo dõi USB removable trên Windows và phát âm thanh."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Đường dẫn file cấu hình JSON.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Liệt kê USB hiện có rồi thoát.",
    )
    return parser.parse_args()


def main() -> None:
    configure_console_output()

    if sys.platform != "win32":
        raise SystemExit("Chương trình này chỉ hỗ trợ Windows.")

    instance_lock = acquire_single_instance()
    if instance_lock is None:
        return

    args = parse_args()
    if args.list:
        config = load_config(args.config.resolve())
        if config.get("monitor_mode", "all_usb") == "all_usb":
            print_usb_device_list(find_usb_devices())
        else:
            print_drive_list(find_removable_drives())
        return

    monitor(args.config.resolve())


if __name__ == "__main__":
    main()
