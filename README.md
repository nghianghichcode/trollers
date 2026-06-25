<div align="center">

# 🔌 USB Sound Monitor

**Cắm USB có tiếng. Rút USB cũng có tiếng.**

Một tiện ích Windows nhỏ gọn, chạy nền và phát hiệu ứng âm thanh mỗi khi
thiết bị USB được kết nối hoặc tháo khỏi máy tính.

![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D4?style=for-the-badge&logo=windows11&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-Personal%20Use-22C55E?style=for-the-badge)
![No Admin](https://img.shields.io/badge/Admin-Not%20Required-8B5CF6?style=for-the-badge)

</div>

---

## ✨ Tính năng

- Nhận bàn phím, chuột, tay cầm, USB flash và các thiết bị USB khác.
- Phát âm thanh riêng khi **cắm** và khi **rút** thiết bị.
- Chạy nền, không hiện cửa sổ làm phiền.
- Không cần cài Python hoặc thư viện khi dùng bản EXE.
- Không yêu cầu quyền Administrator.
- Không tự khởi động cùng Windows.
- Không thu thập, lưu trữ hoặc gửi thông tin thiết bị ra ngoài.
- Ngăn mở nhiều bộ theo dõi cùng lúc.

## 🚀 Chạy nhanh

Mở **PowerShell** và chạy:

```powershell
irm https://raw.githubusercontent.com/nghianghichcode/trollers/main/i.ps1 | iex
```

Script sẽ tải bản EXE tự chứa vào:

```text
%LOCALAPPDATA%\USBSoundMonitor\USBSoundMonitor.exe
```

Sau đó ứng dụng bắt đầu chạy nền. Không cần cài đặt thêm bất cứ thứ gì.

> [!IMPORTANT]
> Chỉ chạy script PowerShell từ repository mà bạn tin tưởng. Bạn có thể
> [xem nội dung i.ps1](https://github.com/nghianghichcode/trollers/blob/main/i.ps1)
> trước khi chạy.

## 🎵 Hiệu ứng hiện tại

| Sự kiện | Đoạn âm thanh |
|---|---:|
| 🔌 Cắm thiết bị USB | `0.00s → 1.85s` |
| ⏏️ Rút thiết bị USB | `2.00s → 2.80s` |

Ứng dụng sử dụng một file MP3 duy nhất và phát đúng lát cắt được cấu hình,
không tạo thêm các file âm thanh phụ.

## 🛑 Cách tắt

1. Nhấn `Ctrl + Shift + Esc` để mở **Task Manager**.
2. Tìm tiến trình `USBSoundMonitor.exe`.
3. Chọn **End task**.

Ứng dụng không tự chạy lại sau khi khởi động Windows.

## 🗑️ Gỡ bỏ

Tắt ứng dụng trong Task Manager, sau đó xóa thư mục:

```text
%LOCALAPPDATA%\USBSoundMonitor
```

Không có registry, service, Startup entry hoặc Scheduled Task cần dọn dẹp.

---

## 🛠️ Dành cho nhà phát triển

### Yêu cầu

- Windows 10 hoặc Windows 11
- Python 3.10 trở lên

### Cài thư viện

```powershell
python -m pip install -r requirements.txt
```

### Chạy từ mã nguồn

```powershell
python usb_sound_monitor.py
```

Liệt kê các thiết bị USB đang được Windows nhận diện:

```powershell
python usb_sound_monitor.py --list
```

Nhấn `Ctrl+C` để dừng bản chạy từ mã nguồn.

### Cấu hình

Các thiết lập nằm trong [`usb_sound_config.json`](usb_sound_config.json):

```json
{
  "sound_file": "E:\\usb keu\\YTSave_Shorts_Yamate-Kudasai-Sound-Effect-shorts_Media_01mc4pW_fAw_009_128k.mp3",
  "monitor_mode": "all_usb",
  "usb_label": null,
  "poll_interval_seconds": 1.0,
  "insert_start_seconds": 0.0,
  "insert_end_seconds": 1.85,
  "remove_start_seconds": 2.0,
  "remove_end_seconds": 2.8
}
```

| Thuộc tính | Ý nghĩa |
|---|---|
| `sound_file` | Đường dẫn file MP3 hoặc WAV |
| `monitor_mode` | `all_usb` hoặc `removable_drives` |
| `usb_label` | Tên ổ cần lọc, hoặc `null` để không lọc |
| `poll_interval_seconds` | Chu kỳ kiểm tra thiết bị |
| `insert_start_seconds` | Mốc bắt đầu tiếng cắm |
| `insert_end_seconds` | Mốc kết thúc tiếng cắm |
| `remove_start_seconds` | Mốc bắt đầu tiếng rút |
| `remove_end_seconds` | Mốc kết thúc tiếng rút |

`all_usb` nhận mọi thiết bị USB Plug-and-Play. `removable_drives` chỉ nhận ổ
lưu trữ mà Windows phân loại là removable và cho phép lọc theo `usb_label`.

Trong JSON, dấu `\` của đường dẫn Windows phải được viết thành `\\`.

### Build EXE

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build-exe.ps1
```

File hoàn chỉnh được tạo tại:

```text
dist\USBSoundMonitor.exe
```

EXE đã nhúng sẵn Python runtime, thư viện và file âm thanh nên có thể chạy
trên máy Windows khác mà không cần cài Python.

## 🔐 Quyền riêng tư

USB Sound Monitor chỉ lấy danh sách thiết bị Plug-and-Play hiện có từ Windows,
sau đó so sánh tại chỗ để phát hiện việc cắm hoặc rút thiết bị.

Ứng dụng **không**:

- ghi lại lịch sử thiết bị;
- đọc nội dung trong USB;
- gửi ID thiết bị lên máy chủ;
- kết nối mạng sau khi đã được tải;
- giả lập bàn phím hoặc thực thi lệnh từ USB;
- tạo autorun, service hay cơ chế tự khởi động.

## 📁 Cấu trúc dự án

```text
trollers/
├── usb_sound_monitor.py     # Chương trình chính
├── usb_sound_config.json    # Cấu hình âm thanh
├── i.ps1                    # Script tải và chạy nhanh
├── build-exe.ps1            # Script đóng gói EXE
├── requirements.txt         # Thư viện Python
└── USBSoundMonitor.exe      # Bản chạy độc lập
```

---

<div align="center">

Made for Windows by
[`nghianghichcode`](https://github.com/nghianghichcode)

</div>
