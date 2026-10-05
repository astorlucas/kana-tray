# Kana Tray 🇯🇵

Widget de bandeja del sistema para aprender **hiragana** y **katakana** sin
sentarte a estudiar. Cada cierto tiempo aparece una tarjeta chica en la esquina
con un kana grande y su dibujo mnemotécnico; escribís el romaji, Enter, y te
dice si está bien. Todo queda registrado, así que a fin de mes sabés cuántas
acertaste, cuántas fallaste y qué kana te está costando.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
![Linux](https://img.shields.io/badge/probado%20en-KDE%2FLinux-orange)

---

## Contenido

- [Qué hace](#qué-hace)
- [Requisitos](#requisitos)
- [Instalación en Linux](#instalación-en-linux)
- [Instalación manual](#instalación-manual-sin-el-script)
- [Desinstalar](#desinstalar)
- [Cómo se usa](#cómo-se-usa)
- [Dónde queda guardado todo](#dónde-queda-guardado-todo)
- [Las imágenes](#las-imágenes)
- [Las mnemotecnias (kana.json)](#las-mnemotecnias-kanajson)
- [¿Funciona en Windows?](#funciona-en-windows)
- [¿Y en macOS?](#y-en-macos)
- [Estructura del repo](#estructura-del-repo)
- [Problemas comunes](#problemas-comunes)
- [Créditos y licencia](#créditos-y-licencia)

---

## Qué hace

- **Pregunta sola, cada tanto.** Frecuencia configurable (15 min a 4 h, o la que
  quieras) y cantidad de kana por tanda.
- **Respeta tu horario.** Sólo pregunta en la franja que le digas (ej. 9 a 23) y
  tiene **No molestar** por 1 h, 3 h, hasta mañana o indefinido.
- **Te pregunta más lo que fallás.** La selección pondera los kana con peor
  precisión y los que hace rato no ves, en lugar de ir al azar puro.
- **Mnemotecnias con dibujo.** Primero ves el dibujo (sin el romaji); después de
  responder aparece la tarjeta con la respuesta y la explicación.
- **Acepta romanizaciones alternativas**: `si`/`shi`, `tu`/`tsu`, `hu`/`fu`,
  `zi`/`ji`, `wo`/`o`, `nn`/`n`, etc.
- **Métricas de verdad.** Cada respuesta se guarda; hay estadísticas por mes,
  precisión por kana y exportación a Markdown. Al empezar un mes nuevo te genera
  solo el reporte del mes anterior.
- **Editable desde la app.** Podés reescribir cualquier mnemotecnia y agregar
  respuestas válidas sin tocar código; se guarda en `kana.json` y se regenera
  [`KANA.md`](KANA.md).
- Cubre los **46 hiragana + 46 katakana básicos**, más **dakuten/handakuten**
  (が, ざ, だ, ば, ぱ…) y **yōon** (きゃ, しゅ, ちょ…).

La tabla completa de respuestas y mnemotecnias está en **[KANA.md](KANA.md)**.

---

## Requisitos

| | |
|---|---|
| **Sistema** | Linux con un escritorio que tenga bandeja del sistema (KDE Plasma, GNOME con extensión de AppIndicator, XFCE, Cinnamon, MATE…). Desarrollado y usado en KDE. |
| **Python** | 3.9 o más nuevo |
| **Dependencias** | `PyQt6` (una sola; el instalador la resuelve) |
| **Fuente japonesa** | `noto-fonts-cjk` o equivalente, si no los kana salen como cuadraditos |
| **Opcional** | `Pillow`, sólo si querés regenerar las imágenes desde los charts de `assets/` |

Pesa ~8 MB de imágenes y charts, así que el clone no es instantáneo.

---

## Instalación en Linux

```bash
git clone https://github.com/astorlucas/kana-tray.git
cd kana-tray
./install.sh
```

Después arrancalo con `kana-tray` (o buscá "Kana Tray" en el menú de
aplicaciones). El ícono あ aparece en la bandeja.

### Qué hace `install.sh`

1. Verifica que tengas Python 3.9+.
2. **Si tu Python del sistema ya tiene PyQt6, lo usa tal cual.** Si no, crea un
   entorno virtual en `.venv/` e instala PyQt6 ahí (~70 MB, tarda un rato).
3. Genera `KANA.md` si falta.
4. Escribe un lanzador en `~/.local/bin/kana-tray`.
5. Escribe la entrada de menú en `~/.local/share/applications/kana-tray.desktop`.
6. Avisa si te falta una fuente japonesa o si `~/.local/bin` no está en tu `PATH`.

No usa `sudo`, no toca nada fuera de tu `$HOME` y del directorio del repo.

### Opciones

```bash
./install.sh                # automático: usa el Python del sistema si puede
./install.sh --venv         # fuerza entorno virtual en .venv/
./install.sh --system       # exige PyQt6 en el Python del sistema (falla si no está)
./install.sh --autostart    # además lo deja arrancando al iniciar sesión
./install.sh --uninstall    # saca lanzador, menú y autostart (no borra tus datos)
./install.sh --help
```

> **Por qué el venv:** en Arch, Debian y Fedora modernos `pip install` a nivel
> sistema está bloqueado (PEP 668). Si preferís el paquete de tu distro:
> `pacman -S python-pyqt6` · `apt install python3-pyqt6` ·
> `dnf install python3-pyqt6`, y después `./install.sh --system`.

### Que arranque con la computadora

Dos formas, equivalentes:

- `./install.sh --autostart` al instalar, o
- desde el menú del ícono → **Iniciar con la computadora** (se puede prender y
  apagar cuando quieras).

Ambas escriben `~/.config/autostart/kana-tray.desktop` apuntando al intérprete
correcto (el del venv si instalaste así).

---

## Instalación manual (sin el script)

```bash
git clone https://github.com/astorlucas/kana-tray.git
cd kana-tray

python3 -m venv .venv                    # opcional pero recomendado
source .venv/bin/activate                # fish: source .venv/bin/activate.fish
pip install -r requirements.txt

python3 kana_tray.py
```

Podés dejar el repo donde quieras: la app resuelve todas sus rutas a partir de
la ubicación de `kana_tray.py`.

---

## Desinstalar

```bash
./install.sh --uninstall     # lanzador + menú + autostart + .venv
```

Tus estadísticas quedan en `~/.config/kana-tray`; borrá esa carpeta a mano si
tampoco las querés conservar.

---

## Cómo se usa

**En el ícono de la bandeja:**

- **Click izquierdo** → preguntar ahora.
- **Click derecho** → menú:
  - **Frecuencia**: cada 15 min … 4 h, o personalizada.
  - **Preguntas por vez**: cuántos kana entran en cada tanda.
  - **Qué practicar**: hiragana, katakana o ambos; incluir dakuten y yōon.
  - **Horario activo**: la franja en la que puede molestarte.
  - **No molestar**: 1 h, 3 h, hasta mañana o indefinido (el ícono se pone gris).
  - **Estadísticas**: aciertos/fallos por mes, precisión por kana, exportar `.md`.
  - **Tabla de kana**: todas las respuestas y mnemotecnias; doble click para
    editar una.
  - **Iniciar con la computadora**, **Editar kana.json…**, **Abrir imágenes…**.

**En la tarjeta:**

| Tecla / botón | Qué hace |
|---|---|
| `Enter` | responde; con la respuesta ya dada, pasa al siguiente |
| **💡 Pista** | muestra la explicación antes de responder (queda registrado) |
| **⏰ +10 min** | pospone la tanda |
| **Saltar** | no cuenta ni como acierto ni como fallo |
| **✏️** | edita la mnemotecnia y las respuestas aceptadas de ese kana |

---

## Dónde queda guardado todo

| Ruta | Qué es |
|---|---|
| `~/.config/kana-tray/config.json` | tus preferencias (frecuencia, horario, modo…) |
| `~/.config/kana-tray/history.jsonl` | una línea por respuesta: kana, si acertaste, si pediste pista, cuándo |
| `~/.config/kana-tray/reportes/AAAA-MM.md` | reportes mensuales (automáticos y exportados) |
| `~/.local/bin/kana-tray` | lanzador que escribe el instalador |
| `~/.local/share/applications/kana-tray.desktop` | entrada en el menú de aplicaciones |
| `~/.config/autostart/kana-tray.desktop` | arranque con la sesión (si lo activaste) |

El historial es `.jsonl` a propósito: lo podés leer con `jq`, importarlo a una
planilla o borrar líneas a mano sin romper nada.

---

## Las imágenes

Cada kana puede tener dos imágenes, nombradas con su **id** (la columna `id` de
[KANA.md](KANA.md), ej. `h_ki`):

- `images/pista/<id>.png` — el dibujo mnemotécnico que se ve **antes** de
  responder, sin el romaji. Existen para los 46 hiragana básicos.
- `images/resultado/<id>.png` — la tarjeta que aparece **después** de responder,
  con el romaji y la explicación.

Los kana que no tienen pista (katakana, dakuten, yōon) muestran sólo el kana
grande hasta que respondés.

**Para cambiar una imagen** reemplazá el archivo por el tuyo con el mismo
nombre; se aceptan `.png`, `.jpg`, `.jpeg`, `.webp`, `.svg` y `.gif`.

**Para regenerarlas** desde los charts de `assets/`:

```bash
pip install pillow
python3 tools/extract_images.py .
```

> Ojo: `tools/extract_images.py` tiene las rutas de las fuentes Noto CJK de
> Linux hardcodeadas (`/usr/share/fonts/noto-cjk/…`). Las imágenes ya vienen
> generadas en el repo, así que sólo necesitás este script si querés recortarlas
> distinto.

---

## Las mnemotecnias (`kana.json`)

Una entrada se ve así:

```json
{
  "id": "h_ki",
  "kana": "き",
  "romaji": "ki",
  "alt": [],
  "script": "hiragana",
  "group": "basic",
  "mnemonic": "Una llave (KEY → 'ki')."
}
```

| Campo | Para qué |
|---|---|
| `id` | nombre de archivo de las imágenes; prefijo `h_` hiragana, `k_` katakana |
| `romaji` | la respuesta principal |
| `alt` | otras respuestas que también valen (`["si"]` para し, etc.) |
| `script` | `hiragana` \| `katakana` |
| `group` | `basic` \| `dakuten` \| `yoon` |
| `mnemonic` | el texto que muestra la pista |

Editalo desde la app (menú → **Tabla de kana** → doble click) o a mano. Si lo
editás a mano, regenerá la tabla:

```bash
python3 kana_tray.py --tabla
```

`KANA.md` es **autogenerado**: no lo edites, se sobreescribe.

---

## ¿Funciona en Windows?

**Casi.** La app corre, pero hay dos cosas que no funcionan y una que depende de
cómo la arranques. PyQt6 tiene wheels oficiales para Windows, así que instalar
la dependencia es idéntico, y el 95% del código es `pathlib` + Qt, que son
multiplataforma.

### Qué funciona sin tocar nada

| | |
|---|---|
| ✅ | Ícono en la bandeja (área de notificación), menú, click izquierdo/derecho |
| ✅ | La tarjeta: ventana sin bordes, siempre arriba, pegada abajo a la derecha (`availableGeometry` ya descuenta la barra de tareas) |
| ✅ | Guardado de config, historial y reportes (quedarían en `C:\Users\<vos>\.config\kana-tray`) |
| ✅ | Abrir carpetas y archivos desde el menú (`QDesktopServices` usa el Explorador) |
| ✅ | Estadísticas, exportar reportes, editar mnemotecnias |
| ✅ | El truco de Wayland es un no-op: `XDG_SESSION_TYPE` no existe en Windows |

### Qué hay que cambiar

**1. El autostart — es lo único que está realmente roto.**
`AUTOSTART_FILE` apunta a `~/.config/autostart/kana-tray.desktop`, que en
Windows no significa nada: el menú **Iniciar con la computadora** se prendería y
escribiría un archivo que nadie lee. Hay que usar la clave `Run` del registro
del usuario (o un acceso directo en la carpeta de Inicio).

```python
# en vez de AUTOSTART_FILE, y reemplazando set_autostart()
IS_WINDOWS = sys.platform == "win32"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "Kana Tray"

def _win_launch_cmd():
    # pythonw.exe no abre consola; si no está, cae en python.exe
    pyw = Path(sys.executable).with_name("pythonw.exe")
    exe = pyw if pyw.exists() else Path(sys.executable)
    return f'"{exe}" "{APP_DIR / "kana_tray.py"}"'

def autostart_enabled():
    if not IS_WINDOWS:
        return AUTOSTART_FILE.exists()
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, RUN_NAME)
        return True
    except OSError:
        return False

def set_autostart(enabled):
    if not IS_WINDOWS:
        ...  # el código actual
        return
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if enabled:
            winreg.SetValueEx(k, RUN_NAME, 0, winreg.REG_SZ, _win_launch_cmd())
        else:
            try:
                winreg.DeleteValue(k, RUN_NAME)
            except FileNotFoundError:
                pass
```

El menú también usa `AUTOSTART_FILE.exists()` para saber si está tildado: eso
pasa a ser `autostart_enabled()`.

**2. La fuente japonesa.**
`JP_FONT = "Noto Sans CJK JP"` no existe en Windows. Lo más probable es que Qt
caiga en una fuente que igual dibuje los kana (Windows 10/11 traen Yu Gothic y
MS Gothic), pero no está garantizado y el ícono あ puede salir feo. La forma
correcta es pedir una lista de familias en orden de preferencia:

```python
JP_FAMILIES = ["Noto Sans CJK JP", "Noto Sans JP", "Yu Gothic UI",
               "Meiryo", "MS Gothic", "Hiragino Sans", "sans-serif"]

def jp_font(px=None, pt=None, bold=False):
    f = QFont()
    f.setFamilies(JP_FAMILIES)       # Qt usa la primera que exista
    if px: f.setPixelSize(px)
    if pt: f.setPointSize(pt)
    f.setBold(bold)
    return f
```

Son **4 lugares** donde hoy se hace `QFont(JP_FONT, …)`: el ícono de la bandeja,
el kana grande de la tarjeta y las dos tablas.

**3. Dónde guardar los datos (opcional, pero prolijo).**
`Path.home() / ".config"` funciona en Windows, pero deja una carpeta `.config`
suelta en el perfil del usuario. La convención es `%APPDATA%`:

```python
CONFIG_DIR = (Path(os.environ["APPDATA"]) / "kana-tray" if IS_WINDOWS
              else Path.home() / ".config" / "kana-tray")
```

Si lo cambiás después de haber usado la app, movete el `history.jsonl` a mano o
perdés las estadísticas.

**4. El instalador.**
`install.sh` es bash: sirve en WSL o Git Bash, no en PowerShell. Para Windows el
equivalente son cuatro comandos (no hace falta un `.ps1`):

```powershell
git clone https://github.com/astorlucas/kana-tray.git
cd kana-tray
py -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\pythonw.exe kana_tray.py      # pythonw = sin ventana de consola
```

Para tenerlo a mano: click derecho en `kana_tray.py` → *Enviar a* → *Escritorio
(crear acceso directo)*, y editá el destino para que use
`.venv\Scripts\pythonw.exe`.

### Resumen

Son **dos cambios obligatorios** (autostart y fuente), unas 40 líneas en total,
más dos opcionales de prolijidad. Nada de arquitectura: en la app no hay
llamadas a binarios de Linux, ni `subprocess`, ni rutas absolutas del sistema
(sólo en `tools/extract_images.py`, que es opcional). Si lo arrancás a mano con
`pythonw.exe`, hoy mismo **ya funciona en Windows menos el botón de arranque
automático**.

---

## ¿Y en macOS?

Mismo panorama que Windows: PyQt6 anda, el tray aparece en la barra de menú de
arriba, y lo que hay que cambiar es el autostart (un `LaunchAgent` en
`~/Library/LaunchAgents/*.plist`) y la fuente (`Hiragino Sans`, que viene
instalada). Sin probar.

---

## Estructura del repo

```
kana_tray.py              la app entera (tray, tarjeta, stats, tabla)
kana.json                 los kana: romaji, alternativas y mnemotecnia
KANA.md                   tabla autogenerada desde kana.json — no editar
requirements.txt          PyQt6
install.sh                instalador / desinstalador para Linux
kana-tray.desktop         plantilla de lanzador (install.sh completa las rutas)
icon.svg                  ícono
images/pista/             dibujo mnemotécnico, se ve antes de responder
images/resultado/         tarjeta con la respuesta, se ve después
assets/                   los charts originales de donde se recortan las imágenes
tools/extract_images.py   recorta y genera las imágenes desde assets/
```

Dentro de `kana_tray.py`, de arriba hacia abajo: constantes y config → datos
(`kana.json`, historial) → estadísticas y reportes → generación de `KANA.md` →
selección ponderada de kana → UI (`QuizCard`, `StatsWindow`, `KanaTableWindow`,
`KanaTray`) → `main()`.

---

## Problemas comunes

**"No hay bandeja del sistema disponible."**
Tu escritorio no expone una bandeja. En GNOME 45+ hace falta la extensión
[AppIndicator](https://extensions.gnome.org/extension/615/appindicator-support/).
En KDE, XFCE, Cinnamon y MATE funciona de fábrica.

**Los kana salen como cuadraditos (□□□).**
Falta la fuente japonesa: `pacman -S noto-fonts-cjk` ·
`apt install fonts-noto-cjk` · `dnf install google-noto-sans-cjk-fonts`.

**`pip install PyQt6` falla con "externally-managed-environment".**
Es PEP 668. Usá `./install.sh --venv`, o instalá el paquete de tu distro y
después `./install.sh --system`.

**La tarjeta aparece en el medio de la pantalla (Wayland).**
Wayland no deja que una app elija su posición. La app fuerza XWayland sola
(`QT_QPA_PLATFORM=xcb`); si la arrancás con `QT_QPA_PLATFORM=wayland` explícito,
vuelve al centro.

**No me pregunta nunca.**
Revisá **Horario activo** (por defecto 9 a 23) y que **No molestar** esté
apagado — con DND el ícono está gris. El tooltip del ícono dice cuándo toca la
próxima.

**Cambié `kana.json` y la app muestra lo viejo.**
Se lee al arrancar: reiniciala. Y corré `python3 kana_tray.py --tabla` para
actualizar `KANA.md`.

---

## Créditos y licencia

El código es MIT (ver [LICENSE](LICENSE)).

Las mnemotecnias y los charts de `assets/` vienen del método de
**[Tofugu](https://www.tofugu.com/japanese/learn-hiragana/)** (*Learn Hiragana*
y *Learn Katakana*), que son gratis en su sitio y pertenecen a Tofugu LLC. Las
imágenes de `images/` son recortes de esos charts: están acá sólo para que la
app funcione, no son propias y la licencia MIT no las cubre. Si vas a hacer algo
público con esto, pedí permiso o reemplazá las imágenes por tus propios dibujos
(el formato está explicado arriba).
