@echo off
title Shopee Video Automation - BUOC 1 VA BUOC 2
cls
echo ===================================================================
echo   KHOI DONG HE THONG SHOPEE VIDEO AUTOMATION (BUOC 1 VA BUOC 2)
echo ===================================================================
echo.

set "PY_CMD="

where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :found_python
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :found_python
)

if exist "C:\Program Files\Python311\python.exe" (
    set "PY_CMD=C:\Program Files\Python311\python.exe"
    goto :found_python
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :found_python
)
if exist "C:\Python311\python.exe" (
    set "PY_CMD=C:\Python311\python.exe"
    goto :found_python
)

:not_found
echo [!] KHONG TIM THAY PYTHON TREN MAY!
echo [*] Vui long cai dat Python 3.10 hoac 3.11 de chay.
echo.
pause
exit /b 1

:found_python
echo [*] Tim thay Python: %PY_CMD%
echo [*] Dang khoi chay main.py...
echo.
"%PY_CMD%" main.py
echo.
pause
