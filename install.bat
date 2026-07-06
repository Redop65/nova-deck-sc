@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "VENV_PY=.venv\Scripts\python.exe"
set "PY_CMD="

where py >nul 2>nul
if not errorlevel 1 set "PY_CMD=py -3"
if not defined PY_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PY_CMD=python"
)
if not defined PY_CMD (
  echo [ERROR] Python no esta instalado o no esta disponible en PATH.
  echo Instala Python 3.11 o posterior desde https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

%PY_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
  echo [ERROR] NOVA DECK requiere Python 3.11 o posterior.
  %PY_CMD% --version
  pause
  exit /b 1
)

if not exist "%VENV_PY%" (
  echo Creando entorno virtual local...
  if exist ".venv" (
    echo Se encontro un entorno incompleto. Intentando repararlo...
    %PY_CMD% -m venv --clear ".venv"
  ) else (
    %PY_CMD% -m venv ".venv"
  )
  if errorlevel 1 goto :venv_error
)

if not exist "%VENV_PY%" goto :venv_error

if not exist "config\settings.json" (
  copy /Y "config\settings.example.json" "config\settings.json" >nul
  echo Creado config\settings.json desde la plantilla segura.
)

echo Instalando dependencias dentro de .venv...
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 goto :dependency_error
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :dependency_error

echo.
echo Validando instalacion...
"%VENV_PY%" -c "import fastapi, uvicorn, pynput, obsws_python"
if errorlevel 1 goto :dependency_error

echo.
echo Instalacion completada correctamente.
echo Ejecuta start-test.bat para probar sin enviar teclas.
echo Ejecuta start.bat para usar NOVA DECK normalmente.
echo.
choice /C SN /N /M "Crear acceso directo NOVA DECK en el escritorio? [S/N]: "
if errorlevel 2 goto :install_done
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create-shortcut.ps1" -NoPrompt
if errorlevel 1 echo [AVISO] Puedes crearlo mas tarde con: start.bat --shortcut

:install_done
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
