@echo off
chcp 65001 >nul
rem Tilawa Studio - installation (Windows). Double-clic, une seule fois.
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
echo == Installation de Tilawa Studio ==
where uv >nul 2>nul || (
  echo -^> Installation de uv...
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex" || goto :error
  set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)
echo -^> Installation des composants (quelques minutes)...
uv sync --no-dev || goto :error
echo -^> Installation du moteur de rendu du texte...
uv run playwright install chromium || goto :error
echo -^> Telechargement du modele de recitation (~1,2 Go) et de ffmpeg...
uv run python -c "from tilawa import media, align; media.tools(); align.get_model()" || goto :error
echo.
echo Installation terminee. Lance "Tilawa Studio.bat".
pause
exit /b 0
:error
echo.
echo Une erreur est survenue pendant l'installation.
pause
exit /b 1
