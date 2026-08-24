@echo off
title Push To GitHub - wududegw/tudonghoashoppe3buoc
cls
echo ===================================================================
echo   DANG DAY MA NGUON LEN GITHUB: tudonghoashoppe3buoc
echo ===================================================================
echo.
set /p GH_TOKEN="Nhap GitHub Token (ghp_...): "
if "%GH_TOKEN%"=="" (
    echo [!] Token khong duoc de trong.
    pause
    exit /b
)
git remote remove origin 2>nul
git remote add origin https://%GH_TOKEN%@github.com/wududegw/tudonghoashoppe3buoc.git
git add .
git commit -m "Update Shopee Video Automation"
git push -u origin main --force
pause
