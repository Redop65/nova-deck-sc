@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PORT=8765"
set "VENV_PY=.venv\Scripts\python.exe"
set "OPEN_BROWSER=ASK"
set "TEST_ARG="
set "MODE_LABEL=MODO NORMAL"
set "CHECK_ONLY=NO"

:parse_args
if "%~1"=="" goto :args_done
if /I "%~1"=="--browser" set "OPEN_BROWSER=YES"
if /I "%~1"=="--no-browser" set "OPEN_BROWSER=NO"
if /I "%~1"=="--test-mode" (
  set "TEST_ARG=--test-mode"
  set "MODE_LABEL=MODO PRUEBA - NO ENVIA TECLAS"
)
if /I "%~1"=="--check" set "CHECK_ONLY=YES"
if /I "%~1"=="--shortcut" goto :create_shortcut
shift
goto :parse_args

:args_done
title NOVA DECK // SC
echo.
echo ============================================================
echo   NOVA DECK // SC - INICIO PARA WINDOWS
echo ============================================================
echo.

if not exist "%VENV_PY%" (
  echo [ERROR] Falta el entorno virtual de NOVA DECK.
  echo.
  echo Solucion: ejecuta install.bat y espera a que finalice.
  goto :fail
)

if not exist "config\buttons.json" (
  echo [ERROR] No existe config\buttons.json.
  echo Restaura el archivo desde GitHub o desde un backup valido.
  goto :fail
)

if not exist "config\settings.json" (
  if not exist "config\settings.example.json" (
    echo [ERROR] No existe config\settings.json ni su plantilla.
    goto :fail
  )
  copy /Y "config\settings.example.json" "config\settings.json" >nul
  echo [INFO] Se creo config\settings.json desde la plantilla.
)

echo [1/4] Validando Python y dependencias...
"%VENV_PY%" -c "import fastapi, uvicorn, pynput" >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Faltan dependencias o el entorno esta danado.
  echo Solucion: ejecuta update.bat. Si continua, ejecuta install.bat.
  goto :fail
)

echo [2/4] Comprobando el puerto %PORT%...
powershell -NoProfile -Command "if (Get-NetTCPConnection -State Listen -LocalPort %PORT% -ErrorAction SilentlyContinue) { exit 1 }" >nul 2>nul
if errorlevel 1 (
  echo [ERROR] El puerto %PORT% ya esta siendo usado por otro programa.
  echo Puede que NOVA DECK ya este abierto en otra ventana.
  echo Revisa con: netstat -ano ^| findstr :%PORT%
  goto :fail
)

echo [3/4] Detectando la red local...
set "LOCAL_IP="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$ip=''; try{$udp=New-Object Net.Sockets.UdpClient;$udp.Connect('8.8.8.8',53);$ip=$udp.Client.LocalEndPoint.Address.IPAddressToString;$udp.Close()}catch{}; if(-not $ip){foreach($a in [Net.Dns]::GetHostAddresses($env:COMPUTERNAME)){if($a.AddressFamily -eq [Net.Sockets.AddressFamily]::InterNetwork -and $a.IPAddressToString -notlike '127.*' -and $a.IPAddressToString -notlike '169.254.*'){$ip=$a.IPAddressToString;break}}}; if($ip){$ip}"`) do set "LOCAL_IP=%%I"
if not defined LOCAL_IP set "LOCAL_IP=IP_DEL_PC"

set "NETWORK_CATEGORY="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$profiles=Get-NetConnectionProfile -ErrorAction SilentlyContinue; foreach($p in $profiles){if($p.IPv4Connectivity -ne 'Disconnected'){$p.NetworkCategory;break}}"`) do set "NETWORK_CATEGORY=%%I"

echo [4/4] Preparando servidor...
echo.
echo ------------------------------------------------------------
echo   ESTADO:  %MODE_LABEL%
echo   PC:      http://localhost:%PORT%
echo   CELULAR: http://%LOCAL_IP%:%PORT%
echo ------------------------------------------------------------
echo.
echo Abre la URL CELULAR desde un equipo conectado a la misma WiFi.
echo Deja esta ventana abierta. Pulsa Ctrl+C para detener NOVA DECK.
echo.
echo [FIREWALL] Permite Python solo en redes PRIVADAS.
echo No abras el puerto en el router, no uses DMZ y no habilites
echo la regla para redes publicas.
if /I "%NETWORK_CATEGORY%"=="Public" (
  echo.
  echo [ADVERTENCIA] Windows detecta la red activa como PUBLICA.
  echo Cambiala a PRIVADA antes de conectar el celular.
)
echo.

if /I "%CHECK_ONLY%"=="YES" (
  echo [OK] Diagnostico completado. NOVA DECK esta listo para iniciar.
  exit /b 0
)

if /I "%OPEN_BROWSER%"=="ASK" (
  choice /C SN /N /M "Abrir NOVA DECK en el navegador del PC? [S/N]: "
  if errorlevel 2 (set "OPEN_BROWSER=NO") else set "OPEN_BROWSER=YES"
)
if /I "%OPEN_BROWSER%"=="YES" (
  echo Abriendo navegador cuando el servidor este listo...
  start "" powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://localhost:%PORT%'"
)

echo Iniciando servidor...
"%VENV_PY%" -m app.main --host 0.0.0.0 --port %PORT% %TEST_ARG%
set "SERVER_EXIT=%errorlevel%"
echo.
if "%SERVER_EXIT%"=="0" (
  echo NOVA DECK se detuvo correctamente.
) else (
  echo [ERROR] NOVA DECK se cerro con codigo %SERVER_EXIT%.
  echo Revisa los mensajes anteriores o la seccion Troubleshooting del README.
)
pause
exit /b %SERVER_EXIT%

:create_shortcut
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create-shortcut.ps1"
exit /b %errorlevel%

:fail
echo.
pause
exit /b 1
