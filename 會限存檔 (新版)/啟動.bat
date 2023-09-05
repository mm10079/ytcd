@echo off
:menu
cls
echo 請選擇要執行的程序：
echo 1. 開始下載社群
echo 2. 編輯訂閱頻道
set /p choice=請輸入選項: 

if "%choice%"=="" (
    echo 請選擇一個有效的選項
    goto menu
)

if "%choice%"=="1" (
    echo 正在執行 開始下載社群
    python main.py
) else if "%choice%"=="2" (
    echo 正在執行 編輯訂閱頻道
    python manager_channels.py
) else (
    echo 請選擇一個有效的選項
    goto menu
)

pause
