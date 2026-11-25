@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating SENTINEL X dashboard environment...
    py -3 -m venv .venv
    if errorlevel 1 goto :failed
)

".venv\Scripts\python.exe" -m streamlit --version >nul 2>&1
if errorlevel 1 (
    echo Installing dashboard dependency. Internet access is required the first time.
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    if errorlevel 1 goto :failed
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :failed
)

".venv\Scripts\python.exe" -m streamlit run dashboard.py --server.address 127.0.0.1
if errorlevel 1 goto :failed
goto :eof

:failed
echo.
echo SENTINEL X dashboard could not start. Check Python and your internet connection.
pause
