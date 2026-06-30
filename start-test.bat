@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo [ERROR] Falta el entorno virtual. Ejecuta install.bat primero.
  pause
  exit /b 1
)
echo Iniciando NOVA DECK en MODO PRUEBA en http://0.0.0.0:8765
echo Ninguna tecla sera enviada. Pulsa Ctrl+C para detenerlo.
.venv\Scripts\python.exe -m app.main --host 0.0.0.0 --port 8765 --test-mode
pause
