@echo off
chcp 65001 >nul
rem Tilawa Studio - lancement (Windows). Laisse cette fenetre ouverte / Keep this window open.
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
uv run --no-dev tilawa app
pause
