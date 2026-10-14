@echo off
REM Khoi dong SRT Whiteboard Studio (giao dien PySide6)
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py "%~dp0app\launch.py" %*
) else (
  python "%~dp0app\launch.py" %*
)
endlocal
pause
