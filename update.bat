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
echo.
echo Actualizacion completada.
pause
exit /b 0
:error
echo.
echo [ERROR] No se pudo actualizar. Revisa Internet y vuelve a intentarlo.
pause
exit /b 1
