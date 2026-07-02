@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo [ERROR] Falta el entorno virtual. Ejecuta install.bat primero.
  pause
  exit /b 1
)
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$ip=(Get-NetIPAddress -AddressFamily IPv4 ^| Where-Object {$_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -ne 'WellKnown'} ^| Sort-Object InterfaceMetric ^| Select-Object -First 1 -ExpandProperty IPAddress); if($ip){$ip}else{'IP_DEL_PC'}"`) do set "LOCAL_IP=%%I"
echo Iniciando NOVA DECK...
echo PC:      http://localhost:8765
echo Celular: http://%LOCAL_IP%:8765
echo [SEGURIDAD] Usa esta URL solo en tu red local privada. No abras el puerto 8765 en el router.
echo Pulsa Ctrl+C para detenerlo.
.venv\Scripts\python.exe -m app.main --host 0.0.0.0 --port 8765
pause
