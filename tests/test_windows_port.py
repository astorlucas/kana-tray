"""Pruebas del soporte de Windows, ejecutables desde Linux o macOS.

La app usa la clave Run del registro para el arranque automático y %APPDATA%
para los datos. Nada de eso se puede probar corriendo la app acá, así que se
simula: se parchea sys.platform y se inyecta un módulo winreg falso con un
diccionario como registro.

    pytest tests/                      # o
    python3 tests/test_windows_port.py
"""

import os
import sys
import tempfile
import types
from pathlib import Path
from unittest import mock

APP_DIR = Path(__file__).absolute().parent.parent


# --------------------------------------------------------------------------- #
# winreg falso
# --------------------------------------------------------------------------- #
def build_fake_winreg(registry):
    """Módulo winreg mínimo que guarda los valores en `registry`."""

    class FakeKey:
        def __init__(self, path):
            self.path = path

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def open_key(root, path, reserved=0, access=0):
        if (root, path) not in registry:
            raise FileNotFoundError(2, "no existe la clave")
        return FakeKey((root, path))

    def create_key(root, path):
        registry.setdefault((root, path), {})
        return FakeKey((root, path))

    def query_value_ex(key, name):
        values = registry.get(key.path, {})
        if name not in values:
            raise FileNotFoundError(2, "no existe el valor")
        return values[name], 1

    def set_value_ex(key, name, reserved, kind, value):
        registry[key.path][name] = value

    def delete_value(key, name):
        if name not in registry[key.path]:
            raise FileNotFoundError(2, "no existe el valor")
        del registry[key.path][name]

    mod = types.ModuleType("winreg")
    mod.HKEY_CURRENT_USER = "HKCU"
    mod.REG_SZ = 1
    mod.KEY_SET_VALUE = 2
    mod.OpenKey = open_key
    mod.CreateKey = create_key
    mod.QueryValueEx = query_value_ex
    mod.SetValueEx = set_value_ex
    mod.DeleteValue = delete_value
    return mod


def import_as_windows():
    """Importa kana_tray como si fuera Windows. Devuelve (módulo, registro, appdata)."""
    registry = {}
    sys.modules["winreg"] = build_fake_winreg(registry)
    sys.modules.pop("kana_tray", None)
    sys.path.insert(0, str(APP_DIR))
    appdata = tempfile.mkdtemp(prefix="kana-appdata-")
    with mock.patch.object(sys, "platform", "win32"), \
            mock.patch.dict(os.environ, {"APPDATA": appdata}):
        import kana_tray
    return kana_tray, registry, Path(appdata)


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
def test_detecta_windows():
    k, _, _ = import_as_windows()

    assert k.IS_WINDOWS is True
    assert k.IS_LINUX is False
    assert k.AUTOSTART_SUPPORTED is True


def test_los_datos_van_a_appdata():
    k, _, appdata = import_as_windows()

    assert k.CONFIG_DIR == appdata / "kana-tray"
    assert ".config" not in str(k.CONFIG_DIR)
    assert k.CONFIG_FILE.name == "config.json"
    assert k.HISTORY_FILE.name == "history.jsonl"


def test_autostart_prende_y_apaga_en_el_registro():
    k, registry, _ = import_as_windows()

    assert k.autostart_enabled() is False

    assert k.set_autostart_enabled(True) is None
    assert k.autostart_enabled() is True

    value = registry[("HKCU", k.WIN_RUN_KEY)][k.WIN_RUN_NAME]
    assert value.startswith('"')                   # rutas con espacios, entre comillas
    assert value.endswith('kana_tray.py"')

    assert k.set_autostart_enabled(False) is None
    assert k.autostart_enabled() is False


def test_apagar_dos_veces_no_falla():
    k, _, _ = import_as_windows()

    assert k.set_autostart_enabled(False) is None
    assert k.set_autostart_enabled(False) is None


def test_la_fuente_pide_familias_en_orden():
    k, _, _ = import_as_windows()

    families = k.jp_font(pixel_size=44, bold=True).families()

    assert "Yu Gothic UI" in families, "tiene que haber una fuente que exista en Windows"
    assert families.index("Noto Sans CJK JP") < families.index("Yu Gothic UI"), \
        "Noto primero, así en Linux no cambia nada"


def test_en_linux_nada_cambia():
    sys.modules.pop("kana_tray", None)
    sys.path.insert(0, str(APP_DIR))
    with mock.patch.object(sys, "platform", "linux"):
        import kana_tray as k

    assert k.IS_WINDOWS is False
    assert k.CONFIG_DIR == Path.home() / ".config" / "kana-tray"
    assert k.AUTOSTART_FILE.name == "kana-tray.desktop"
    assert "[Desktop Entry]" in k.desktop_entry()


if __name__ == "__main__":
    failures = []
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_"):
            continue
        try:
            fn()
            print(f"  OK     {name}")
        except AssertionError as e:
            failures.append((name, e))
            print(f"  FALLA  {name}: {e}")
    print("\nTODO OK" if not failures else f"\n{len(failures)} test(s) fallando")
    sys.exit(1 if failures else 0)
