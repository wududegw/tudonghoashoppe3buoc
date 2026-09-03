@echo off
title Test Buoc 1 - Shopee Crawler va Link Affiliate
cls
echo ===================================================================
echo   [BUOC 1] KIEM THU CRAWLER SHOPEE VA TAO LINK AFFILIATE
echo ===================================================================
echo.

set "PY_CMD="

:: 1. Kiem tra python co san trong PATH
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :found_python
)

:: 2. Kiem tra py launcher
where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :found_python
)

:: 3. Kiem tra cac duong dan mac dinh
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
echo [*] Vui long cai dat Python 3.10 hoac 3.11 de chay du an.
echo.
pause
exit /b 1

:found_python
echo [*] Tim thay Python: %PY_CMD%
echo [*] Dang chay test_step1_crawler.py...
echo.
"%PY_CMD%" test_step1_crawler.py
echo.
echo ===================================================================
echo   HOAN TAT KIEM THU BUOC 1
echo ===================================================================
pause
