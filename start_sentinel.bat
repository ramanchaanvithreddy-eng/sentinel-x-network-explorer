@echo off
cd /d "%~dp0"
py -3 -m sentinel_x
if errorlevel 1 (
    echo.
    echo SENTINEL X could not start. Check that Python 3 is installed.
)
pause
