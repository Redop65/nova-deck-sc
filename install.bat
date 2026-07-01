@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "VENV_PY=.venv\Scripts\python.exe"

where py >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python no esta instalado o el launcher "py" no esta en PATH.
  echo Instala Python 3.11 o posterior desde https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
  echo [ERROR] NOVA DECK requiere Python 3.11 o posterior.
  py -3 --version
  pause
  exit /b 1
)

if not exist "%VENV_PY%" (
  echo Creando entorno virtual local...
  if exist ".venv" (
    echo Se encontro un entorno incompleto. Intentando repararlo...
    py -3 -m venv --clear ".venv"
  ) else (
    py -3 -m venv ".venv"
  )
  if errorlevel 1 goto :venv_error
)

if not exist "%VENV_PY%" goto :venv_error

echo Instalando dependencias dentro de .venv...
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 goto :dependency_error
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :dependency_error

echo.
echo Instalacion completada. Ejecuta start.bat o start-test.bat.
pause
exit /b 0

:dependency_error
  echo [ERROR] No se pudieron instalar las dependencias.
  echo Revisa tu conexion a Internet y vuelve a ejecutar install.bat.
  pause
  exit /b 1

:venv_error
echo.
echo [ERROR] No se pudo crear el entorno virtual .venv.
echo El instalador se detuvo para evitar instalar paquetes globalmente.
echo Si usas Python de Microsoft Store, instala Python 3.12 desde:
echo https://www.python.org/downloads/windows/
echo Marca "Add python.exe to PATH" durante la instalacion y reintenta.
pause
exit /b 1
