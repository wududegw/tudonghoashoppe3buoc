@echo off
title Cai Dat Chrome Extension - Shopee Crawler
cls
echo ===================================================================
echo   HUONG DAN CAI DAT CHROME EXTENSION (BUOC 1 - SHOPEE CRAWLER)
echo ===================================================================
echo.
echo [1] Trinh duyet Chrome va thu muc Extension se duoc mo len ngay bay gio...
echo.
echo [2] CAC BUOC CAI DAT TRONG 10 GIAY:
echo     - Buoc A: Tren trang chrome://extensions vua mo, bat cong tac
echo               "Che do danh cho nha phat trien" (Developer mode) o goc phai tren.
echo     - Buoc B: Bam nut "Tai tien ich da giai nen" (Load unpacked) o goc trai tren.
echo     - Buoc C: Chon thu muc "extension" (dang mo truoc mat ban) roi bam Select.
echo.
echo [3] SAU KHI CAI DAT XONG:
echo     - Mo https://shopee.vn, vao bat ky Shop nao.
echo     - Bam nut cam noi "QUET SAN PHAM SHOPEE" hoac icon tren thanh cong cu!
echo ===================================================================
echo.

:: Mo trang cai dat extension trong Chrome
start chrome.exe "chrome://extensions"

:: Mo thu muc extension trong File Explorer
explorer.exe "%~dp0extension"

echo [*] Da mo Chrome va thu muc extension!
echo.
pause
