@echo off
REM NewsFilter FastAPI 一鍵啟動腳本
REM 此腳本會自動激活 Conda 環境並啟動 API 服務

echo ========================================
echo NewsFilter FastAPI 啟動腳本
echo ========================================
echo.

REM 設置 Conda 環境路徑
set CONDA_ENV_PATH=C:\Users\admin\anaconda3\envs\Newsfilter_FastApi

REM 設置 Python 執行文件路徑
set PYTHON_EXE=%CONDA_ENV_PATH%\python.exe

REM 檢查 Python 是否存在
if not exist "%PYTHON_EXE%" (
    echo [錯誤] 找不到 Python 執行文件！
    echo 路徑: %PYTHON_EXE%
    echo.
    echo 請確保 Conda 環境 "Newsfilter_FastApi" 已正確安裝。
    echo.
    pause
    exit /b 1
)

REM 顯示使用的環境信息
echo [信息] 使用 Conda 環境: Newsfilter_FastApi
echo [信息] Python 路徑: %PYTHON_EXE%
echo.

REM 檢查 .env 文件是否存在
if not exist ".env" (
    echo [警告] 未找到 .env 文件！
    echo 請確保已配置環境變量文件。
    echo 可以複製 env.example 為 .env 並填入配置信息。
    echo.
)

REM 啟動 API 服務
echo [信息] 正在啟動 FastAPI 服務...
echo [信息] API 將在 http://localhost:8000 運行
echo [信息] 按 Ctrl+C 可停止服務
echo.
echo ========================================
echo.

REM 使用完整路徑的 Python 執行 newsfilter_api.py
"%PYTHON_EXE%" newsfilter_api.py

REM 如果程序異常退出，暫停以查看錯誤信息
if errorlevel 1 (
    echo.
    echo ========================================
    echo [錯誤] API 啟動失敗！
    echo ========================================
    echo.
    pause
)
