# USB Sound Monitor cho Windows

Chương trình theo dõi ổ USB `removable`: khi cắm, nó phát câu đầu trong file
MP3; khi rút, nó phát hiệu ứng cuối. Chương trình không dùng autorun USB,
không giả lập bàn phím, không chạy lệnh ẩn và không tự cài lên máy khác.

## Chạy nhanh, không cần cài Python

Sau khi repository được đẩy lên GitHub, người dùng mở PowerShell và chạy:

```powershell
irm https://raw.githubusercontent.com/nghianghichcode/trollers/main/i.ps1 | iex
```

Lệnh này tải EXE tự chứa vào `%LOCALAPPDATA%\USBSoundMonitor` và mở ứng dụng.
Nó không cài Python/thư viện, không xin quyền Administrator, không tạo Startup
hoặc Scheduled Task và không tự chạy lại sau khi khởi động Windows.

Ứng dụng chạy nền với tên `USBSoundMonitor.exe`. Để tắt:

1. Nhấn `Ctrl + Shift + Esc` để mở Task Manager.
2. Tìm `USBSoundMonitor.exe`.
3. Chọn **End task**.

Ứng dụng chỉ so sánh danh sách thiết bị USB ngay trên máy để biết lúc cắm/rút.
Nó không ghi lại lịch sử và không gửi ID hoặc thông tin thiết bị lên mạng.

> Lưu ý: chỉ chạy lệnh tải từ GitHub khi bạn tin tưởng chủ repository. Người
> dùng có thể mở `i.ps1` trên GitHub để đọc nội dung trước khi chạy.

## 1. Chuẩn bị

Cài Python 3.10 trở lên từ <https://www.python.org/downloads/windows/>.
Trong trình cài đặt Python, chọn **Add Python to PATH**.

Mở PowerShell trong thư mục này và cài thư viện:

```powershell
python -m pip install -r requirements.txt
```

## 2. Cấu hình

Mở `usb_sound_config.json` và sửa đường dẫn âm thanh:

```json
{
  "sound_file": "E:\\usb keu\\YTSave_Shorts_Yamate-Kudasai-Sound-Effect-shorts_Media_01mc4pW_fAw_009_128k.mp3",
  "monitor_mode": "all_usb",
  "usb_label": null,
  "poll_interval_seconds": 1.0,
  "insert_start_seconds": 0.0,
  "insert_end_seconds": 2.50,
  "remove_start_seconds": 2.52,
  "remove_end_seconds": null
}
```

Lưu ý: trong JSON, dấu `\` trong đường dẫn Windows phải được viết thành `\\`.

- `"usb_label": null`: phát với mọi ổ USB removable.
- `"monitor_mode": "all_usb"`: nhận cả bàn phím, chuột, tay cầm và ổ flash.
- `"monitor_mode": "removable_drives"`: chỉ nhận ổ lưu trữ removable; lúc này
  có thể dùng `usb_label` để lọc tên ổ.
- `"usb_label": "MYUSB"`: chỉ phát khi tên ổ USB là `MYUSB`, không phân biệt
  chữ hoa và chữ thường.
- `poll_interval_seconds`: số giây giữa mỗi lần kiểm tra.
- `insert_start_seconds` và `insert_end_seconds`: đoạn phát khi cắm USB.
- `remove_start_seconds` và `remove_end_seconds`: đoạn phát khi rút USB.
  Giá trị `null` ở mốc kết thúc có nghĩa là phát đến hết file.

Với file âm thanh hiện tại:

- Cắm USB: phát từ `0.00` đến `1.85` giây để nghe rõ âm cuối.
- Rút USB: phát một tiếng ngắn từ `2.52` đến `3.15` giây.

Để xem chính xác tên các USB đang cắm:

```powershell
python usb_sound_monitor.py --list
```

## 3. Chạy thử

Đảm bảo USB cần thử chưa được cắm, sau đó chạy:

```powershell
python usb_sound_monitor.py
```

Cắm USB vào máy. Chương trình sẽ in ổ đĩa và tên USB ra màn hình rồi phát
âm thanh nếu bộ lọc tên phù hợp. Nhấn `Ctrl+C` để dừng.

Nếu muốn dùng một file cấu hình ở nơi khác:

```powershell
python usb_sound_monitor.py --config "C:\USBSound\my_config.json"
```

## 4. Cho chạy khi đăng nhập Windows

Cách đơn giản, minh bạch và chỉ áp dụng cho tài khoản Windows hiện tại:

1. Nhấn `Win + R`, nhập `shell:startup`, rồi nhấn Enter.
2. Trong thư mục Startup vừa mở, nhấp chuột phải và chọn
   **New > Shortcut**.
3. Ở ô vị trí, nhập lệnh dưới đây và thay hai đường dẫn bằng đường dẫn thật:

   ```text
   "C:\Path\To\python.exe" "C:\Path\To\usb_sound_monitor.py"
   ```

4. Đặt tên shortcut là `USB Sound Monitor` rồi hoàn tất.
5. Đăng xuất và đăng nhập lại để thử. Cửa sổ chương trình sẽ hiện ra và in
   trạng thái bình thường; chương trình không chạy ẩn.

Tìm đường dẫn Python bằng lệnh:

```powershell
where.exe python
```

Muốn tắt tự khởi động, chỉ cần xóa shortcut `USB Sound Monitor` khỏi thư mục
Startup. Không đặt chương trình hoặc shortcut này trên USB nếu không muốn nó
phụ thuộc vào USB đó.

## Ghi chú

Một số ổ SSD/HDD gắn ngoài có thể được Windows báo là ổ cố định thay vì
`removable`; theo yêu cầu, chương trình chỉ nhận thiết bị mà Windows phân loại
là `DRIVE_REMOVABLE`.
