# NOVA DECK // SC

Panel táctil local, estilo Stream Deck, para ejecutar atajos de teclado de Star Citizen desde un celular o tablet. Es un proyecto independiente, sin logos ni recursos oficiales.

## Qué incluye

- Perfiles por nave con páginas independientes; incluye Default, Prospector y Vulture.
- Páginas Default: Flight, MobiGlas, Combat, Mining, FPS y Camera / OBS.
- Interfaz responsive para celular, tablet y escritorio.
- Teclas simples y combinaciones como `F1`, `Alt+N` o `Ctrl+F12`.
- Catálogo editable en `config/buttons.json`, recargado automáticamente al guardar.
- Editor visual para crear, modificar, mover y borrar botones desde el navegador.
- Modo de prueba visual que no inyecta ninguna tecla.
- Validación de comandos: el navegador solo puede invocar botones declarados en el JSON.
- Mensajes visibles de éxito y error.
- Integración opcional con OBS Studio mediante OBS WebSocket 5.

## Requisitos de Windows

- Windows 10 u 11.
- Python 3.11 o posterior, con la opción **Add Python to PATH** habilitada.
- PC y dispositivo móvil conectados a la misma red WiFi/LAN.
- Permiso de Firewall de Windows para Python en redes **privadas** cuando aparezca el aviso.

## Instalación en Windows

1. Ejecuta `install.bat` una sola vez. Creará `.venv` e instalará todas las dependencias dentro del proyecto.
2. Primero ejecuta `start-test.bat`.
3. En el PC abre `http://localhost:8765`.
4. Busca la IPv4 del PC con `ipconfig` (por ejemplo, `192.168.1.42`).
5. En el celular abre `http://192.168.1.42:8765`, sustituyendo esa IP por la tuya.
6. Prueba los botones: la consola inferior debe indicar `SIMULATED`.
7. Cuando hayas revisado tus bindings, detén el servidor con `Ctrl+C` y usa `start.bat` para permitir la salida real de teclado.

`start.bat` muestra automáticamente la URL del PC y una URL con la IP local para el celular. `update.bat` actualiza las dependencias del entorno existente; si todavía no existe `.venv`, ejecuta primero la instalación automáticamente.

Para crear un acceso directo: clic derecho sobre `start.bat` → **Mostrar más opciones** → **Enviar a** → **Escritorio (crear acceso directo)**. Puedes renombrarlo a `NOVA DECK` y asignarle un icono desde **Propiedades**.

## Uso desde el celular

1. Conecta el PC y el celular a la misma red privada WiFi/LAN.
2. Ejecuta `start.bat` y deja abierta su ventana.
3. Escribe en el navegador del celular la URL que muestra el script, por ejemplo `http://192.168.1.42:8765`.
4. Mantén Star Citizen enfocado para los botones hotkey/macro. Las acciones OBS no necesitan que OBS esté enfocado.

## Pantalla completa y modo cabina

- Pulsa **FULL** para solicitar pantalla completa. El navegador exige que esta acción nazca de un toque y algunos dispositivos, especialmente Safari, pueden no ofrecer esa API.
- Pulsa **CABIN** para ocultar título, editor, modo prueba, monitor de comandos y recordatorio. Quedan visibles únicamente conexión, perfil, páginas y botones.
- Pulsa **EXIT CABIN** para recuperar la interfaz completa.
- La preferencia de modo cabina se guarda en `localStorage` de ese celular o tablet.
- La interfaz evita selección de texto, zoom accidental y gestos de doble toque sobre controles. Los botones conservan áreas táctiles amplias en vertical y aprovechan más columnas en horizontal.

### Acceso directo en Android

1. Abre la URL local en Chrome.
2. Abre el menú `⋮`.
3. Elige **Añadir a pantalla de inicio** o **Instalar aplicación**, si aparece.
4. Inicia NOVA DECK desde el nuevo ícono.

### Acceso directo en iPhone o iPad

1. Abre la URL local en Safari.
2. Pulsa **Compartir**.
3. Elige **Añadir a pantalla de inicio**.
4. Abre NOVA DECK desde el ícono creado.

La app incluye manifest y metadatos móviles, pero no se publica en tiendas. Como usa una URL HTTP privada de la LAN, algunos navegadores pueden crear solo un acceso directo en vez de instalar una PWA completa. Es normal y no afecta el panel.

## Temas visuales

El selector **THEME** permite cambiar la apariencia inmediatamente:

- **Dark Default:** negro azulado y cian, apariencia original.
- **Space Blue:** azul profundo con acento celeste moderado.
- **Amber Cockpit:** marrón oscuro y ámbar cálido.
- **Red Alert:** rojo oscuro de emergencia sin saturación excesiva.
- **Industrial Mining:** gris verdoso y tonos minerales apagados.

La selección se guarda en `localStorage`, por lo que cada celular o tablet puede conservar su propio tema. Los colores asignados individualmente a los botones siguen teniendo prioridad para íconos y señales; el tema modifica fondo, superficie, borde, texto, alertas y estado presionado.

Para definir el tema inicial de dispositivos que todavía no tengan una preferencia guardada, edita `config/settings.json`:

```json
{
  "app": {
    "debug": false,
    "log_level": "INFO",
    "default_theme": "space-blue"
  }
}
```

Valores válidos: `dark-default`, `space-blue`, `amber-cockpit`, `red-alert` e `industrial-mining`. El selector se oculta en modo cabina, pero el tema elegido permanece activo.

También puedes activar **TEST MODE** desde la esquina superior de la interfaz. `start-test.bat` es más seguro para la primera prueba porque bloquea la inyección en el servidor y el interruptor no puede desactivarla.

## Uso real con Star Citizen

1. Inicia el servidor con `start.bat`.
2. Abre Star Citizen y deja la ventana del juego enfocada.
3. Toca un botón desde el celular. El PC enviará el binding como si se hubiera pulsado en el teclado.

Los bindings de Star Citizen cambian entre versiones y configuraciones personales. El JSON incluido es un ejemplo inicial: revísalo contra `Options > Keybindings` dentro del juego antes de usarlo. Si el juego se ejecuta como administrador, Windows puede impedir que una aplicación sin elevar le envíe teclas; lo recomendado es ejecutar ambos con el mismo nivel de privilegio.

### Recordatorio de actividad

La esquina inferior muestra una pequeña palanca **MODO AFK**. Al activarla inicia una cuenta regresiva aleatoria de 3:30 a 4:30 minutos. Al llegar a cero envía `F2` automáticamente y programa otro intervalo aleatorio. El ciclo continúa hasta que vuelvas a pulsar **MODO AFK** para apagarlo.

El modo es silencioso: no vibra ni muestra notificaciones emergentes. Usa **TEST MODE** para comprobar los ciclos sin inyectar realmente `F2`. El navegador debe permanecer abierto y el PC activo para que el temporizador funcione correctamente.

En Flight, **Extend / Retract Wings** usa `Alt+K` (la acción de transformación/configuración de nave). **Open All Doors** queda inicialmente deshabilitado con `F9` como atajo sugerido: primero asigna `F9` a la acción correspondiente dentro de `Advanced Controls Customization` y después habilita el botón desde **CONFIG**. No se usa una combinación basada en `O`, porque Star Citizen puede interpretarla como el comando de escudos. La cuadrícula compacta de Flight admite hasta diez botones visibles.

## Integración con OBS Studio

OBS Studio 28 o posterior incluye OBS WebSocket 5. La integración es opcional y viene deshabilitada.

1. En OBS abre **Herramientas → Configuración del servidor WebSocket**.
2. Activa el servidor, conserva normalmente el puerto `4455` y habilita autenticación.
3. Copia la contraseña y edita `config/settings.json`:

```json
{
  "obs": {
    "enabled": true,
    "host": "127.0.0.1",
    "port": 4455,
    "password": "TU_PASSWORD",
    "timeout_seconds": 3
  }
}
```

Reinicia NOVA DECK después de cambiar este archivo. No compartas `settings.json`: contiene la contraseña local de OBS. Si OBS está cerrado, deshabilitado o las credenciales son incorrectas, el botón muestra un error y el resto del panel continúa funcionando.

`config/settings.json` está excluido de Git para proteger la contraseña. El repositorio incluye `config/settings.example.json`; `install.bat` lo copia automáticamente si falta el archivo local.

Tipos de botón disponibles: `hotkey`, `macro` y `obs`. Los botones antiguos sin `type` siguen funcionando. Ejemplos OBS:

```json
{"id":"rec","name":"REC","type":"obs","obsAction":"toggle_recording","color":"red"}
{"id":"scene","name":"Cockpit Cam","type":"obs","obsAction":"set_scene","sceneName":"Star Citizen - Cockpit","color":"violet"}
{"id":"mic","name":"Mute Mic","type":"obs","obsAction":"toggle_mute","inputName":"Mic/Aux","color":"orange"}
{"id":"cam","name":"Webcam","type":"obs","obsAction":"set_source_visibility","sceneName":"Star Citizen - Cockpit","sourceName":"Webcam","visible":true,"color":"cyan"}
```

Acciones admitidas: `start_recording`, `stop_recording`, `toggle_recording`, `pause_recording`, `resume_recording`, `set_scene`, `toggle_mute` y `set_source_visibility`. Los nombres de escena, entrada y fuente deben coincidir exactamente con OBS. También puedes crear y editar estas acciones desde **CONFIG**. En TEST MODE se muestran como simuladas y no se establece conexión con OBS.

## Perfiles por nave

El selector **SHIP PROFILE**, ubicado sobre el panel, cambia todas las páginas y botones sin reiniciar el servidor. El navegador recuerda la última selección en `localStorage`; si ese perfil ya no existe, carga `Default`.

La configuración usa una lista `profiles`:

```json
{
  "title": "NOVA DECK // SC",
  "profiles": [
    {
      "id": "default",
      "name": "Default",
      "pages": [
        {
          "id": "flight",
          "name": "Flight",
          "icon": "◇",
          "buttons": [
            {"id": "landing-gear", "name": "Landing Gear", "keys": "N", "color": "cyan"}
          ]
        }
      ]
    }
  ]
}
```

Para crear un perfil:

1. Copia uno de los objetos dentro de `profiles`.
2. Asigna un `id` único en minúsculas, como `c1-spirit`, y un `name` visible.
3. Personaliza su lista `pages`; cada página contiene su propia lista `buttons`.
4. Guarda el JSON. El nuevo perfil aparecerá al recargar la página, sin reiniciar el servidor.

Los IDs de botones deben ser únicos dentro de un perfil, pero pueden repetirse en perfiles distintos. El editor **CONFIG** modifica únicamente el perfil actualmente seleccionado. Los perfiles de ejemplo usan controles genéricos de vuelo, minería y salvaging; revisa sus bindings contra tu configuración del juego.

Compatibilidad: un archivo antiguo con `pages` en la raíz se carga automáticamente como perfil `Default`. La primera modificación realizada desde el editor lo guardará en el nuevo formato `profiles`.

API local:

- `GET /api/profiles`: lista de perfiles disponibles.
- `GET /api/profiles/{profile_id}`: páginas y botones del perfil.
- `POST /api/commands`: acepta `profile_id` junto con `button_id`.

## Editor visual de botones

Pulsa **EDIT** en la esquina superior derecha. El panel entra en modo edición y los botones quedan marcados; al tocar uno se abre su formulario sin ejecutar la acción. Pulsa **DONE** para volver al funcionamiento normal.

Desde el editor puedes:

- Crear un botón con **NEW BUTTON**.
- Modificar label, ID, perfil, página, hotkey, macro, acción OBS, icono, color o estado.
- Duplicar el botón seleccionado con **DUPLICATE**.
- Moverlo entre perfiles o páginas desde los selectores.
- Cambiar su posición con **MOVE UP** y **MOVE DOWN**.
- Borrarlo mediante **DELETE** y la confirmación posterior.

Cada operación válida se guarda inmediatamente en `config/buttons.json`. Antes de crear, modificar, mover, duplicar o borrar, se guarda una copia completa en `config/backups/`. El servidor escribe primero un archivo temporal y después reemplaza el JSON, reduciendo el riesgo de dejar una configuración incompleta. Los IDs deben ser únicos dentro del perfil y un binding inválido solo puede guardarse si el botón queda deshabilitado.

Como el editor escribe en disco, evita editar `buttons.json` manualmente al mismo tiempo. Esta versión todavía no crea perfiles o páginas nuevas; esas estructuras se agregan directamente en JSON.

## Backup, exportación e importación

Abre **CONFIG** para encontrar el panel **CONFIGURATION BACKUP**.

### Exportar

1. Pulsa **EXPORT JSON**.
2. El navegador descargará un archivo como `nova-deck-backup-20260703-143000.json`.
3. Guárdalo en una carpeta privada.

El JSON incluye perfiles, páginas, botones, macros, colores, rutas de íconos, settings generales y configuración OBS. Por seguridad, **la descarga nunca contiene `obs.password`**. Los íconos se incluyen como referencias `assets/icons/...`; si agregaste archivos de ícono propios, conserva también una copia de esos archivos.

### Importar

1. Pulsa **IMPORT JSON** y selecciona un archivo `.json` de hasta 2 MB.
2. Revisa la confirmación antes de continuar.
3. El backend valida completamente el archivo antes de modificar la configuración.
4. Si es válido, perfiles y botones se actualizan sin reiniciar el servidor.

Si el backup descargado no contiene contraseña OBS, se conserva la contraseña que ya existe en ese PC. Al migrar a otro PC, ingrésala nuevamente en `config/settings.json`.

Antes de cada importación válida se crea automáticamente una copia completa en `config/backups/before-import-*.json`. Esa copia local sí conserva la contraseña OBS para permitir una recuperación en el mismo equipo; la carpeta está excluida de Git y nunca se entrega mediante la API de descarga.

También se puede importar directamente un `buttons.json` antiguo. En ese caso solo se reemplazan perfiles, páginas y botones; los settings actuales permanecen intactos.

Si el JSON está mal formado, contiene botones inválidos o usa una versión de backup no soportada, la importación se rechaza y los archivos actuales no se sobrescriben.

## Edición manual y formato JSON

Edita `config/buttons.json` con un editor de texto. No hace falta reiniciar: el backend vuelve a leerlo después de guardar y la página se actualiza al recargar el navegador.

Ejemplo:

```json
{
  "id": "open-comms",
  "name": "Open Comms",
  "icon": "assets/icons/mobiglas.svg",
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
| `icon` | Ruta local bajo `assets/icons/` o etiqueta corta heredada; puede omitirse. |
| `keys` | Una tecla o combinación separada por `+`. |
| `macro` | Lista opcional de pasos; reemplaza a `keys` cuando se usa. |
| `type` | `hotkey`, `macro` u `obs`; si se omite, se deduce para configuraciones antiguas. |
| `obsAction` | Acción OBS; puede requerir `sceneName`, `inputName`, `sourceName` o `visible`. |
| `color` | `cyan`, `blue`, `violet`, `amber`, `orange`, `green` o `red`. |
| `hold_ms` | Milisegundos que la tecla permanece presionada, entre `0` y `5000`. |
| `disabled` | Opcional. Con `true`, muestra el botón pero impide ejecutarlo. |

Teclas aceptadas: letras y dígitos individuales, `F1` a `F24`, `Ctrl`, `Alt`, `Shift`, `Win`, `Enter`, `Esc`, `Space`, `Tab`, `Backspace`, `Delete`, `Insert`, `Home`, `End`, `PageUp`, `PageDown` y flechas. Por ejemplo: `Shift+F4` o `Ctrl+Alt+K`.

Quantum Drive incluye `"hold_ms": 1000`, por lo que mantiene `B` presionada durante un segundo antes de soltarla. Esta duración también puede modificarse desde **CONFIG**.

## Ejemplos de configuración

Todos los botones van dentro de `buttons` en una página. Los IDs deben ser únicos dentro del perfil.

Botón simple:

```json
{"id":"lights","name":"Lights","type":"hotkey","keys":"L","color":"amber"}
```

Macro con pausa:

```json
{
  "id": "mobiglas-map",
  "name": "MobiGlas → Map",
  "type": "macro",
  "color": "violet",
  "macro": [
    {"keys": "F1", "delay_after_ms": 500},
    {"keys": "F2", "hold_ms": 0}
  ]
}
```

Botón OBS:

```json
{"id":"mute-mic","name":"Mute Mic","type":"obs","obsAction":"toggle_mute","inputName":"Mic/Aux","color":"orange"}
```

Botón con ícono local:

```json
{"id":"gear","name":"Landing Gear","type":"hotkey","keys":"N","icon":"assets/icons/landing-gear.svg","color":"cyan"}
```

Perfil por nave:

```json
{
  "id": "explorer",
  "name": "Explorer",
  "pages": [
    {
      "id": "flight",
      "name": "Flight",
      "buttons": [
        {"id":"gear","name":"Landing Gear","keys":"N","color":"cyan"}
      ]
    }
  ]
}
```

Agrega el objeto de perfil dentro de la lista raíz `profiles` y recarga el navegador.

## Macros

Un botón puede ejecutar una secuencia ordenada de teclas con pausas. Usa `macro` en lugar de `keys`:

```json
{
  "id": "mobiglas-to-map",
  "name": "MobiGlas → Star Map",
  "icon": "NAV",
  "color": "violet",
  "macro": [
    {"keys": "F1", "delay_after_ms": 500},
    {"keys": "F2", "hold_ms": 0}
  ]
}
```

Cada paso admite:

- `keys`: tecla o combinación que se enviará.
- `hold_ms`: duración de la pulsación; por defecto `0`, máximo `5000`.
- `delay_after_ms`: pausa después del paso y antes del siguiente; por defecto `0`, máximo `10000`.

Las macros admiten hasta 20 pasos y 60 segundos totales. Desde **CONFIG**, pega la lista de pasos en **Macro JSON** y deja vacío **Key / combination**. El modo prueba muestra la cantidad de pasos sin enviar teclas ni esperar las pausas.

## Íconos personalizados

Guarda imágenes propias dentro de `assets/icons/` y referencia su ruta desde el botón:

```json
{
  "id": "landing-gear",
  "name": "Landing Gear",
  "keys": "N",
  "color": "cyan",
  "icon": "assets/icons/landing-gear.svg"
}
```

Formatos admitidos: SVG, PNG, WebP, JPG y JPEG. Usa nombres simples sin espacios, por ejemplo `mining-laser.svg`. Los SVG deben incluir un `viewBox`; se recomienda `0 0 64 64`, fondo transparente y trazos con buen contraste.

- El nombre del botón siempre permanece visible debajo del ícono.
- Si `icon` se omite, el botón muestra solamente su texto.
- Si la ruta no existe o la imagen falla, la interfaz oculta el ícono y conserva el texto.
- Las etiquetas cortas existentes como `COM` o `REC` siguen siendo compatibles.
- Desde **CONFIG**, escribe la ruta en **Icon / local path** y guarda.

El proyecto incluye ejemplos originales para Landing Gear, Quantum Drive, MobiGlas y Star Map. No se incluyen logos ni recursos oficiales.

`Missile Mode` viene deshabilitado porque muchas configuraciones lo asignan a un botón del ratón. Asígnale una tecla dentro del juego, reemplaza `Mouse4` por esa tecla y elimina `"disabled": true`.

## Estructura

```text
StarCitizen/
├── assets/
│   └── icons/            # SVG, PNG, WebP o JPG personalizados
├── app/
│   ├── main.py          # API y servidor web
│   ├── backup.py        # Exportación, validación, importación y rollback
│   ├── config.py        # Carga/validación del JSON
│   ├── models.py        # Esquemas compartidos de botones y macros
│   ├── settings.py      # Configuración de ejecución y debug
│   ├── obs.py           # Cliente opcional de OBS WebSocket
│   └── keyboard.py      # Parser e inyección de teclas
├── config/
│   ├── buttons.json          # Perfiles y acciones editables
│   ├── settings.example.json # Plantilla segura versionada
│   ├── settings.json         # Credenciales locales, ignoradas por Git
│   └── backups/              # Copias automáticas previas a importación
├── frontend/
│   ├── index.html
│   └── assets/
│       ├── app.js
│       └── styles.css
├── tests/
├── install.bat
├── start.bat
├── update.bat
└── start-test.bat
```

## Seguridad de red local

Esta versión no tiene login. **Cualquier dispositivo que pueda acceder al puerto 8765 puede activar botones y usar el editor para cambiar `config/buttons.json`.** Úsala únicamente en una red doméstica privada y de confianza.

- No abras ni reenvíes el puerto 8765 en el router.
- No la publiques mediante túneles, proxy inverso, VPN pública o servicios cloud.
- No configures reglas de Firewall para redes públicas y no uses DMZ/port forwarding.
- `0.0.0.0` permite escuchar en las interfaces locales del PC; no convierte la app en pública por sí solo, pero sería accesible desde internet si abres el puerto en el router. No lo hagas.
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

## Logs y modo debug

El backend registra inicio de acciones, simulaciones y errores sin mostrar la contraseña de OBS. Para diagnóstico temporal, edita `config/settings.json`:

```json
{
  "app": {
    "debug": true,
    "log_level": "DEBUG"
  }
}
```

También puedes iniciar con `.venv\Scripts\python.exe -m app.main --debug`. Debug aumenta el detalle de la consola, pero no envía trazas internas al navegador. Desactívalo al terminar el diagnóstico.

## Configuración inválida

- Un botón inválido ya no bloquea el panel completo: aparece deshabilitado con `CONFIG ERROR`.
- El monitor inferior muestra la ruta exacta, por ejemplo `profiles.default.pages.flight.buttons[2]`.
- Corrige ese objeto en `config/buttons.json` o desde **CONFIG** cuando conserve un ID único. Los IDs ausentes o duplicados deben corregirse manualmente. El archivo original no se reescribe automáticamente al detectar el problema.
- Errores estructurales que impiden saber dónde están perfiles o páginas —JSON mal cerrado, `profiles` vacío o páginas sin `buttons`— detienen la carga y aparecen como `Configuración inválida`.
- Puedes consultar el diagnóstico local en `http://localhost:8765/api/status` bajo `configuration`.

## Solución de problemas

- **El celular no conecta:** confirma misma WiFi, usa la IPv4 correcta, conserva `:8765` y permite Python solo en redes privadas del Firewall.
- **La web responde pero el juego no:** enfoca el juego, comprueba el binding y revisa que juego y servidor tengan el mismo nivel de privilegio.
- **Error de configuración:** valida comas, comillas e IDs únicos en `config/buttons.json`; el detalle aparecerá en la interfaz/API.
- **El puerto está ocupado:** cambia `8765` en `start.bat` y usa ese mismo puerto en la URL del celular.
- **OBS no responde:** abre OBS, activa WebSocket, revisa puerto/contraseña y confirma que `enabled` sea `true`. Los nombres de escenas y fuentes distinguen mayúsculas.
- **Firewall bloquea el celular:** en **Seguridad de Windows → Firewall y protección de red → Permitir una aplicación**, permite Python únicamente en redes privadas. Como alternativa avanzada, crea una regla de entrada TCP para el puerto `8765`, también solo en perfil privado.
- **`activate.bat` no se reconoce:** descarga la versión más reciente del repositorio y vuelve a ejecutar `install.bat`. El instalador reparará un `.venv` incompleto y nunca continuará instalando dependencias globalmente. Si Python de Microsoft Store no logra crear el entorno, instala Python 3.12 desde python.org con **Add python.exe to PATH** habilitado.
