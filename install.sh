#!/usr/bin/env bash
#
# Instalador de Kana Tray para Linux (KDE, GNOME, XFCE… cualquier escritorio
# con bandeja del sistema).
#
#   ./install.sh                  instala (venv si hace falta) + lanzador + menú
#   ./install.sh --venv           fuerza entorno virtual en .venv
#   ./install.sh --system         usa el Python del sistema (PyQt6 ya instalado)
#   ./install.sh --autostart      además lo arranca al iniciar sesión
#   ./install.sh --uninstall      saca lanzador, menú y autostart (no borra datos)
#
set -euo pipefail

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="kana-tray"
MIN_PY_MINOR=9

BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
AUTOSTART_DIR="${HOME}/.config/autostart"
DATA_DIR="${HOME}/.config/${APP_NAME}"
VENV_DIR="${APP_DIR}/.venv"

LAUNCHER="${BIN_DIR}/${APP_NAME}"
DESKTOP_FILE="${DESKTOP_DIR}/${APP_NAME}.desktop"
AUTOSTART_FILE="${AUTOSTART_DIR}/${APP_NAME}.desktop"

MODE="auto"       # auto | venv | system
WANT_AUTOSTART=0
ACTION="install"

short() { local path="$1"; printf '%s' "${path/#"$HOME"/\~}"; }
say()  { printf '  %s\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*" >&2; }
die()  { printf '\n  \033[31m✗ %s\033[0m\n\n' "$*" >&2; exit 1; }

for arg in "$@"; do
  case "$arg" in
    --venv)      MODE="venv" ;;
    --system)    MODE="system" ;;
    --autostart) WANT_AUTOSTART=1 ;;
    --uninstall) ACTION="uninstall" ;;
    -h|--help)   sed -n '3,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)           die "Opción desconocida: ${arg} (probá --help)" ;;
  esac
done

# --------------------------------------------------------------------------- #
# Desinstalar
# --------------------------------------------------------------------------- #
if [[ "$ACTION" == "uninstall" ]]; then
  printf '\n  Desinstalando Kana Tray\n\n'
  for f in "$LAUNCHER" "$DESKTOP_FILE" "$AUTOSTART_FILE"; do
    if [[ -e "$f" ]]; then rm -f "$f"; ok "borrado $(short "$f")"; else say "no estaba $(short "$f")"; fi
  done
  if [[ -d "$VENV_DIR" ]]; then rm -rf "$VENV_DIR"; ok "borrado $(short "$VENV_DIR")"; fi
  command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
  printf '\n'
  say "Tus estadísticas siguen en $(short "$DATA_DIR")"
  say "Para borrarlas también:  rm -rf $(short "$DATA_DIR")"
  printf '\n'
  exit 0
fi

# --------------------------------------------------------------------------- #
# Chequeos
# --------------------------------------------------------------------------- #
printf '\n  Instalando Kana Tray\n\n'

[[ -f "${APP_DIR}/kana_tray.py" ]] || die "No encuentro kana_tray.py; corré el script desde el repo."
[[ -f "${APP_DIR}/kana.json" ]]   || die "Falta kana.json: el repo está incompleto."

command -v python3 >/dev/null 2>&1 || die "No hay python3 en el PATH. Instalá Python 3.${MIN_PY_MINOR}+ y volvé a probar."

PY_VER="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, ${MIN_PY_MINOR}) else 1)" \
  || die "Python ${PY_VER} es muy viejo; hace falta 3.${MIN_PY_MINOR} o más."
ok "Python ${PY_VER}"

has_pyqt() { "$1" -c 'import PyQt6.QtWidgets' >/dev/null 2>&1; }

# --------------------------------------------------------------------------- #
# Intérprete: sistema si ya tiene PyQt6, venv si no
# --------------------------------------------------------------------------- #
PYTHON=""
case "$MODE" in
  system)
    has_pyqt python3 || die $'PyQt6 no está instalado en el Python del sistema.\n    Instalalo con tu gestor de paquetes (ej. pacman -S python-pyqt6,\n    apt install python3-pyqt6, dnf install python3-pyqt6) o corré ./install.sh --venv'
    PYTHON="$(command -v python3)"
    ok "uso el Python del sistema (ya tiene PyQt6)"
    ;;
  auto)
    if has_pyqt python3; then
      PYTHON="$(command -v python3)"
      ok "PyQt6 ya está en el Python del sistema, no hace falta entorno virtual"
    else
      MODE="venv"
    fi
    ;;
esac

if [[ "$MODE" == "venv" ]]; then
  if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    say "creando entorno virtual en .venv/ …"
    python3 -m venv "$VENV_DIR" \
      || die $'No pude crear el entorno virtual.\n    En Debian/Ubuntu instalá primero:  apt install python3-venv'
  fi
  PYTHON="${VENV_DIR}/bin/python"
  if ! has_pyqt "$PYTHON"; then
    say "instalando PyQt6 (puede tardar un rato, son ~70 MB) …"
    "${VENV_DIR}/bin/pip" install --quiet --upgrade pip
    "${VENV_DIR}/bin/pip" install --quiet -r "${APP_DIR}/requirements.txt" \
      || die "Falló la instalación de PyQt6. Mirá el error de pip más arriba."
  fi
  has_pyqt "$PYTHON" || die "PyQt6 quedó instalado pero no se puede importar."
  ok "PyQt6 listo en .venv/"
fi

# --------------------------------------------------------------------------- #
# Tabla de kana, lanzador y entrada de menú
# --------------------------------------------------------------------------- #
[[ -f "${APP_DIR}/KANA.md" ]] || "$PYTHON" "${APP_DIR}/kana_tray.py" --tabla >/dev/null

mkdir -p "$BIN_DIR" "$DESKTOP_DIR"

cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
# Generado por install.sh — no editar a mano.
exec "${PYTHON}" "${APP_DIR}/kana_tray.py" "\$@"
EOF
chmod +x "$LAUNCHER"
ok "lanzador en $(short "$LAUNCHER")"

render_desktop() {
  sed -e "s|__EXEC__|${PYTHON} ${APP_DIR}/kana_tray.py|g" \
      -e "s|__ICON__|${APP_DIR}/icon.svg|g" \
      "${APP_DIR}/${APP_NAME}.desktop" > "$1"
}

render_desktop "$DESKTOP_FILE"
ok "entrada de menú en $(short "$DESKTOP_FILE")"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

if [[ "$WANT_AUTOSTART" == "1" ]]; then
  mkdir -p "$AUTOSTART_DIR"
  render_desktop "$AUTOSTART_FILE"
  ok "arranca con la sesión ($(short "$AUTOSTART_FILE"))"
fi

# --------------------------------------------------------------------------- #
# Avisos finales
# --------------------------------------------------------------------------- #
printf '\n'
case ":${PATH}:" in
  *":${BIN_DIR}:"*) ;;
  *) warn "$(short "$BIN_DIR") no está en tu PATH; agregalo o usá la entrada del menú." ;;
esac

FONTS="$(fc-list 2>/dev/null || true)"
if ! grep -qiE 'noto (sans|serif) cjk|source han|droid sans japanese|takao|ipa(g|m)' <<<"$FONTS"; then
  warn $'No encontré una fuente japonesa; los kana pueden salir como cuadraditos.\n    Instalá por ejemplo:  pacman -S noto-fonts-cjk  /  apt install fonts-noto-cjk'
fi

[[ "${XDG_SESSION_TYPE:-}" == "wayland" ]] && say "Sesión Wayland: la app usa XWayland sola para poder ubicar la tarjeta."

printf '\n  Listo. Arrancalo con:  %s\n' "$APP_NAME"
[[ "$WANT_AUTOSTART" == "1" ]] || printf '  Para que arranque solo: menú del ícono → «Iniciar con la computadora»\n'
printf '\n'
