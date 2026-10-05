# Kana Tray 🇯🇵

Widget de bandeja del sistema para aprender **hiragana** y **katakana** sin
sentarte a estudiar. Cada cierto tiempo aparece una tarjeta chica en la esquina
con un kana grande y su dibujo mnemotécnico; escribís el romaji, Enter, y te
dice si está bien. Todo queda registrado, así que a fin de mes sabés cuántas
acertaste, cuántas fallaste y qué kana te está costando.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
![Linux](https://img.shields.io/badge/Linux-probado-success)
![Windows](https://img.shields.io/badge/Windows-soportado-blue)

---

## Contenido

- [Qué hace](#qué-hace)
- [Requisitos](#requisitos)
- [Instalación en Linux](#instalación-en-linux)
- [Instalación en Windows](#instalación-en-windows)
- [Instalación manual](#instalación-manual-sin-el-script)
- [Desinstalar](#desinstalar)
- [Cómo se usa](#cómo-se-usa)
- [Dónde queda guardado todo](#dónde-queda-guardado-todo)
- [Las imágenes](#las-imágenes)
- [Las mnemotecnias (kana.json)](#las-mnemotecnias-kanajson)
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
  (が, ざ, だ, ば, ぱ…) y **yōon** (きゃ, しゅ, ちょ…): 208 entradas en total.

La tabla completa de respuestas y mnemotecnias está en **[KANA.md](KANA.md)**.

---

## Requisitos

| | |
|---|---|
| **Sistema** | **Linux** con bandeja del sistema (KDE Plasma, XFCE, Cinnamon, MATE; en GNOME hace falta la extensión AppIndicator) o **Windows 10/11**. Desarrollado y usado en KDE; ver [qué está probado](#qué-está-probado-y-qué-no). |
| **Python** | 3.9 o más nuevo |
| **Dependencias** | `PyQt6` (una sola; el instalador la resuelve) |
| **Fuente japonesa** | En Linux, `noto-fonts-cjk` o equivalente (si no, los kana salen como cuadraditos). En Windows ya viene con el sistema. |
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

En Windows es lo mismo en otros lugares:

| Ruta | Qué es |
|---|---|
| `%APPDATA%\kana-tray\` | config, historial y reportes |
| `…\Menú Inicio\Programas\Kana Tray.lnk` | acceso directo |
| `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` → `Kana Tray` | arranque con la sesión |

El historial es `.jsonl` a propósito: lo podés leer con `jq`, importarlo a una
planilla o borrar líneas a mano sin romper nada.

### Línea de comandos

```bash
python3 kana_tray.py              # arranca el widget
python3 kana_tray.py --tabla      # regenera KANA.md desde kana.json
python3 kana_tray.py --ico x.ico  # exporta el ícono a .ico (lo usa install.ps1)
python3 tests/test_windows_port.py   # pruebas del soporte de Windows
```

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

> El script busca una fuente CJK entre varias rutas conocidas de Linux, Windows
> y macOS, y te dice cuáles probó si no encuentra ninguna. Las imágenes ya vienen
> generadas en el repo, así que sólo necesitás esto si querés recortarlas distinto.

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

## Instalación en Windows

Windows 10 y 11 están soportados: el arranque automático usa la clave `Run` del
registro del usuario y los datos van a `%APPDATA%\kana-tray`.

```powershell
git clone https://github.com/astorlucas/kana-tray.git
cd kana-tray
.\install.ps1
```

Si PowerShell bloquea el script (política de ejecución por defecto):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```

### Qué hace `install.ps1`

1. Busca Python 3.9+ (`py -3`, `python` o `python3`).
2. Usa el Python del sistema si ya tiene PyQt6; si no, crea `.venv\` e instala
   PyQt6 ahí.
3. Genera `kana-tray.ico` con el mismo dibujo que el ícono de la bandeja.
4. Crea el acceso directo **Kana Tray** en el menú Inicio, apuntando a
   `pythonw.exe` (así no queda una ventana de consola abierta).

Opciones, iguales a las de Linux:

```powershell
.\install.ps1 -Venv        # forzar entorno virtual
.\install.ps1 -System      # exigir PyQt6 en el Python del sistema
.\install.ps1 -Autostart   # además arrancar con la sesión
.\install.ps1 -Uninstall   # quitar acceso directo, autostart, .venv e ícono
```

No pide permisos de administrador: todo queda en el perfil del usuario.

### Qué está probado y qué no

Desarrollé y probé la app en Linux. Para Windows:

| | |
|---|---|
| ✅ probado | La lógica del registro y de `%APPDATA%`, con un `winreg` falso y `sys.platform` parcheado: `python3 tests/test_windows_port.py` (6 tests, corren en cualquier sistema operativo) |
| ✅ probado | Que en Linux no cambie nada: mismas rutas, mismo `.desktop`, Noto primero en la lista de fuentes |
| ⚠️ sin probar | `install.ps1` corriendo de verdad en una máquina Windows — no tengo uno a mano. Si algo falla ahí, abrí un issue con el mensaje de error |

La fuente ya no es un problema: la app pide una lista de familias
(`Noto Sans CJK JP` → `Yu Gothic UI` → `Meiryo` → `MS Gothic` → `Hiragino Sans`)
y Qt usa la primera que exista, así que los kana se ven en Windows sin instalar
nada.

### Si el ícono no aparece

Windows 11 esconde los íconos nuevos del área de notificación. Están en la
flechita `^` de la barra de tareas; para fijarlo: *Configuración → Personalización
→ Barra de tareas → Otros iconos de la bandeja del sistema* y prendé **Kana Tray**.

---

## ¿Y en macOS?

La app corre (PyQt6 anda y el ícono va a la barra de menú de arriba, con
`Hiragino Sans` como fuente), pero el **arranque automático no está
implementado**: haría falta un `LaunchAgent` en `~/Library/LaunchAgents/*.plist`.
Para que no falle en silencio, en macOS la opción «Iniciar con la computadora»
aparece deshabilitada. Sin probar en una Mac.

---

## Estructura del repo

```
kana_tray.py              la app entera (tray, tarjeta, stats, tabla)
kana.json                 los kana: romaji, alternativas y mnemotecnia
KANA.md                   tabla autogenerada desde kana.json — no editar
requirements.txt          PyQt6
install.sh                instalador / desinstalador para Linux
install.ps1               instalador / desinstalador para Windows
kana-tray.desktop         plantilla de lanzador (install.sh completa las rutas)
icon.svg                  ícono (el .ico de Windows lo genera --ico)
images/pista/             dibujo mnemotécnico, se ve antes de responder
images/resultado/         tarjeta con la respuesta, se ve después
assets/                   los charts originales de donde se recortan las imágenes
tools/extract_images.py   recorta y genera las imágenes desde assets/
tests/                    pruebas del soporte de Windows (corren en cualquier SO)
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

Las mnemotecnias y los charts mnemotécnicos de `assets/` vienen del método de
**[Tofugu](https://www.tofugu.com/japanese/learn-hiragana/)** (*Learn Hiragana*
y *Learn Katakana*), que son gratis en su sitio y pertenecen a Tofugu LLC. Las
imágenes de `images/` son recortes de esos charts: están acá sólo para que la
app funcione, no son propias y la licencia MIT no las cubre. Si vas a hacer algo
público con esto, pedí permiso o reemplazá las imágenes por tus propios dibujos
(el formato está explicado arriba).

`assets/kana-chart-by-hwangje.jpg` es una tabla de kana de **[hwangje](https://www.deviantart.com/hwangje)** (DeviantArt), incluida como
referencia; tampoco la cubre la licencia MIT.
