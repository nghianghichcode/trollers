$ErrorActionPreference = "Stop"

# Chỉ tải ứng dụng tự chứa; không cài Python, không tạo Startup/Task Scheduler.
$installDir = Join-Path $env:LOCALAPPDATA "USBSoundMonitor"
$exePath = Join-Path $installDir "USBSoundMonitor.exe"
$downloadUrl = "https://raw.githubusercontent.com/nghianghichcode/trollers/main/USBSoundMonitor.exe"

New-Item -ItemType Directory -Path $installDir -Force | Out-Null
Write-Host "Dang tai USB Sound Monitor..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $downloadUrl -OutFile $exePath -UseBasicParsing

Start-Process -FilePath $exePath
Write-Host "Da chay USB Sound Monitor." -ForegroundColor Green
Write-Host "Xem huong dan su dung va cach tat trong README tren GitHub."
