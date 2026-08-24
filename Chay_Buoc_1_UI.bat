@echo off
title Shopee Product Crawler - BUOC 1 DASHBOARD
cls
echo ===================================================================
echo   SHOPEE PRODUCT CRAWLER DASHBOARD (BUOC 1)
echo ===================================================================
echo.
echo [*] Dang kiem tra thu vien requests...
python -c "import requests" 2>nul
if %errorlevel% neq 0 (
    echo [!] Dang cai dat thu vien requests...
    pip install requests
)

echo [*] Dang khoi dong Dashboard Web...
echo [*] Trinh duyet se tu dong mo tai: http://localhost:8888
echo.
python run_step1_ui.py
pause
