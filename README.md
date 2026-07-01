# NOVA DECK // SC

Panel táctil local, estilo Stream Deck, para ejecutar atajos de teclado de Star Citizen desde un celular o tablet. Es un proyecto independiente, sin logos ni recursos oficiales.

## Qué incluye

- Seis perfiles: Flight, MobiGlas, Combat, Mining, FPS y Camera / OBS.
- Interfaz responsive para celular, tablet y escritorio.
- Teclas simples y combinaciones como `F1`, `Alt+N` o `Ctrl+F12`.
- Catálogo editable en `config/buttons.json`, recargado automáticamente al guardar.
- Editor visual para crear, modificar, mover y borrar botones desde el navegador.
- Modo de prueba visual que no inyecta ninguna tecla.
- Validación de comandos: el navegador solo puede invocar botones declarados en el JSON.
- Mensajes visibles de éxito y error.

## Requisitos de Windows

- Windows 10 u 11.
- Python 3.11 o posterior, con la opción **Add Python to PATH** habilitada.
- PC y dispositivo móvil conectados a la misma red WiFi/LAN.
- Permiso de Firewall de Windows para Python en redes **privadas** cuando aparezca el aviso.

## Instalación rápida

1. Ejecuta `install.bat` una sola vez. Creará `.venv` e instalará FastAPI, Uvicorn y pynput.
2. Primero ejecuta `start-test.bat`.
3. En el PC abre `http://localhost:8765`.
4. Busca la IPv4 del PC con `ipconfig` (por ejemplo, `192.168.1.42`).
5. En el celular abre `http://192.168.1.42:8765`, sustituyendo esa IP por la tuya.
6. Prueba los botones: la consola inferior debe indicar `SIMULATED`.
7. Cuando hayas revisado tus bindings, detén el servidor con `Ctrl+C` y usa `start.bat` para permitir la salida real de teclado.

También puedes activar **TEST MODE** desde la esquina superior de la interfaz. `start-test.bat` es más seguro para la primera prueba porque bloquea la inyección en el servidor y el interruptor no puede desactivarla.

## Uso real con Star Citizen

1. Inicia el servidor con `start.bat`.
2. Abre Star Citizen y deja la ventana del juego enfocada.
3. Toca un botón desde el celular. El PC enviará el binding como si se hubiera pulsado en el teclado.

Los bindings de Star Citizen cambian entre versiones y configuraciones personales. El JSON incluido es un ejemplo inicial: revísalo contra `Options > Keybindings` dentro del juego antes de usarlo. Si el juego se ejecuta como administrador, Windows puede impedir que una aplicación sin elevar le envíe teclas; lo recomendado es ejecutar ambos con el mismo nivel de privilegio.

En Flight, **Extend / Retract Wings** usa `Alt+K` (la acción de transformación/configuración de nave). **Open All Doors** queda inicialmente deshabilitado con `F9` como atajo sugerido: primero asigna `F9` a la acción correspondiente dentro de `Advanced Controls Customization` y después habilita el botón desde **CONFIG**. No se usa una combinación basada en `O`, porque Star Citizen puede interpretarla como el comando de escudos. La cuadrícula compacta de Flight admite hasta diez botones visibles.

Para OBS, configura `Ctrl+F12` como hotkey de **Start/Stop Recording** en `Settings > Hotkeys`, o cambia el valor en el JSON para que coincida con tu configuración.

## Editor visual de botones

Pulsa **CONFIG** en la esquina superior derecha del panel. Desde esa pantalla puedes:

- Crear un botón con **NEW BUTTON**.
- Seleccionar cualquier botón del catálogo para modificar su nombre, ID, página, binding, icono, color o estado.
- Mover un botón eligiendo otra página y guardando.
- Borrarlo mediante **DELETE** y la confirmación posterior.

Cada operación válida se guarda inmediatamente en `config/buttons.json`. El servidor escribe primero un archivo temporal y después reemplaza el JSON, reduciendo el riesgo de dejar una configuración incompleta. Los IDs deben ser únicos en todas las páginas y un binding inválido solo puede guardarse si el botón queda deshabilitado.

Como el editor escribe en disco, evita editar `buttons.json` manualmente al mismo tiempo. El editor no permite crear o borrar páginas; conserva los seis perfiles de la estructura actual.

## Edición manual y formato JSON

Edita `config/buttons.json` con un editor de texto. No hace falta reiniciar: el backend vuelve a leerlo después de guardar y la página se actualiza al recargar el navegador.

Ejemplo:

```json
{
  "id": "open-comms",
  "name": "Open Comms",
  "icon": "COM",
  "keys": "F11",
  "color": "cyan",
  "hold_ms": 0
}
```

Añádelo dentro de la lista `buttons` de la página deseada. Campos:

| Campo | Uso |
|---|---|
| `id` | Identificador único, sin repetir en ninguna página. |
| `name` | Texto que se muestra en el botón. |
| `icon` | Texto corto opcional; puede omitirse. |
| `keys` | Una tecla o combinación separada por `+`. |
| `color` | `cyan`, `blue`, `violet`, `amber`, `orange`, `green` o `red`. |
| `hold_ms` | Milisegundos que la tecla permanece presionada, entre `0` y `5000`. |
| `disabled` | Opcional. Con `true`, muestra el botón pero impide ejecutarlo. |

Teclas aceptadas: letras y dígitos individuales, `F1` a `F24`, `Ctrl`, `Alt`, `Shift`, `Win`, `Enter`, `Esc`, `Space`, `Tab`, `Backspace`, `Delete`, `Insert`, `Home`, `End`, `PageUp`, `PageDown` y flechas. Por ejemplo: `Shift+F4` o `Ctrl+Alt+K`.

Quantum Drive incluye `"hold_ms": 1000`, por lo que mantiene `B` presionada durante un segundo antes de soltarla. Esta duración también puede modificarse desde **CONFIG**.

`Missile Mode` viene deshabilitado porque muchas configuraciones lo asignan a un botón del ratón. Asígnale una tecla dentro del juego, reemplaza `Mouse4` por esa tecla y elimina `"disabled": true`.

## Estructura

```text
StarCitizen/
├── app/
│   ├── main.py          # API y servidor web
│   ├── config.py        # Carga/validación del JSON
│   └── keyboard.py      # Parser e inyección de teclas
├── config/
│   └── buttons.json     # Perfiles y acciones editables
├── frontend/
│   ├── index.html
│   └── assets/
│       ├── app.js
│       └── styles.css
├── tests/
├── install.bat
├── start.bat
└── start-test.bat
```

## Seguridad de red local

Esta versión no tiene login. **Cualquier dispositivo que pueda acceder al puerto 8765 puede activar botones y usar el editor para cambiar `config/buttons.json`.** Úsala únicamente en una red doméstica privada y de confianza.

- No abras ni reenvíes el puerto 8765 en el router.
- No la publiques mediante túneles, proxy inverso, VPN pública o servicios cloud.
- En Firewall de Windows permite el acceso solo en redes privadas, nunca públicas.
- Detén el servidor con `Ctrl+C` cuando no lo uses.
- Para usar solo el navegador del propio PC, cambia `--host 0.0.0.0` por `--host 127.0.0.1` en el script; el celular dejará de tener acceso.

## Desarrollo y pruebas

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
pytest
python -m app.main --test-mode
```

Para probar con una copia de la configuración puedes usar `python -m app.main --test-mode --config ruta\buttons-copia.json`.

La documentación interactiva de la API queda disponible localmente en `http://localhost:8765/docs`.

## Problemas frecuentes

- **El celular no conecta:** confirma misma WiFi, usa la IPv4 correcta, conserva `:8765` y permite Python solo en redes privadas del Firewall.
- **La web responde pero el juego no:** enfoca el juego, comprueba el binding y revisa que juego y servidor tengan el mismo nivel de privilegio.
- **Error de configuración:** valida comas, comillas e IDs únicos en `config/buttons.json`; el detalle aparecerá en la interfaz/API.
- **El puerto está ocupado:** cambia `8765` en `start.bat` y usa ese mismo puerto en la URL del celular.
- **`activate.bat` no se reconoce:** descarga la versión más reciente del repositorio y vuelve a ejecutar `install.bat`. El instalador reparará un `.venv` incompleto y nunca continuará instalando dependencias globalmente. Si Python de Microsoft Store no logra crear el entorno, instala Python 3.12 desde python.org con **Add python.exe to PATH** habilitado.
