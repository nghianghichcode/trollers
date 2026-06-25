$ErrorActionPreference = "Stop"

$python = "C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$sound = "YTSave_Shorts_Yamate-Kudasai-Sound-Effect-shorts_Media_01mc4pW_fAw_009_128k.mp3"

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --noconsole `
    --name "USBSoundMonitor" `
    --hidden-import "_cffi_backend" `
    --add-data "${sound};." `
    --add-data "usb_sound_config.json;." `
    "usb_sound_monitor.py"

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

Copy-Item ".\dist\USBSoundMonitor.exe" ".\USBSoundMonitor.exe" -Force
Write-Host "Da tao: dist\USBSoundMonitor.exe" -ForegroundColor Green
Write-Host "Da chep ban phat hanh: USBSoundMonitor.exe" -ForegroundColor Green
