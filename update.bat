@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [INFO] No existe el entorno local. Ejecutando install.bat...
  call install.bat
  exit /b %errorlevel%
)
echo Actualizando dependencias de NOVA DECK...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m pip install --upgrade -r requirements.txt
if errorlevel 1 goto :error
echo Validando dependencias...
".venv\Scripts\python.exe" -c "import fastapi, uvicorn, pynput, obsws_python"
if errorlevel 1 goto :error
echo.
echo Actualizacion de dependencias completada.
echo Nota: update.bat no descarga codigo desde GitHub.
echo Para actualizar el codigo usa GitHub Desktop o: git pull
pause
exit /b 0
:error
echo.
echo [ERROR] No se pudo actualizar. Revisa Internet y vuelve a intentarlo.
pause
exit /b 1
