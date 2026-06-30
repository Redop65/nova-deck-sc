@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python no esta instalado o el launcher "py" no esta en PATH.
  echo Instala Python 3.11 o posterior desde https://www.python.org/downloads/windows/
  pause
  exit /b 1
)
if not exist .venv py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] No se pudieron instalar las dependencias.
  pause
  exit /b 1
)
echo.
echo Instalacion completada. Ejecuta start.bat o start-test.bat.
pause
