@echo off
chcp 65001 >nul
rem Tilawa Studio - installation (Windows). Double-clic, une seule fois / Double-click, once.
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
echo == Installation de Tilawa Studio / Installing Tilawa Studio ==
where uv >nul 2>nul || (
  echo -^> Installation de uv / Installing uv...
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex" || goto :error
  set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)
echo -^> Composants (quelques minutes) / Components (a few minutes)...
uv sync --no-dev || goto :error
echo -^> Moteur de rendu du texte / Text rendering engine...
uv run playwright install chromium || goto :error
echo -^> Modele de recitation (~1,2 Go) et ffmpeg / Recitation model (~1.2 GB) and ffmpeg...
uv run python -c "from tilawa import media, align; media.tools(); align.get_model()" || goto :error
echo.
echo Installation terminee. Lance "Tilawa Studio.bat".
echo Installation complete. Open "Tilawa Studio.bat".
pause
exit /b 0
:error
echo.
echo Une erreur est survenue pendant l'installation. / Something went wrong during the installation.
pause
exit /b 1
