#!/usr/bin/env python3
"""
Kana Tray - practicá hiragana y katakana desde la bandeja del sistema.

Cada cierto tiempo aparece una tarjeta con un kana grande y una imagen
mnemotécnica; escribís el romaji y te dice si está bien. Todas las respuestas
se guardan para sacar métricas por mes (aciertos / fallos y cuáles te cuestan).

Las mnemotecnias viven en kana.json (junto a este archivo) y se pueden editar
desde la app; KANA.md se regenera solo con la tabla de respuestas.

    python3 kana_tray.py            # arranca el widget
    python3 kana_tray.py --tabla    # sólo regenera KANA.md desde kana.json
"""

import json
import os
import random
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

APP_DIR = Path(__file__).absolute().parent
KANA_FILE = APP_DIR / "kana.json"
KANA_TABLE_FILE = APP_DIR / "KANA.md"   # tabla autogenerada (el README se escribe a mano)
IMAGES_DIR = APP_DIR / "images"
HINT_DIR = IMAGES_DIR / "pista"          # dibujo mnemotécnico, antes de responder
RESULT_DIR = IMAGES_DIR / "resultado"    # tarjeta con romaji/explicación, después

CONFIG_DIR = Path.home() / ".config" / "kana-tray"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history.jsonl"
REPORTS_DIR = CONFIG_DIR / "reportes"
AUTOSTART_FILE = Path.home() / ".config" / "autostart" / "kana-tray.desktop"

INTERVAL_PRESETS_MIN = [15, 30, 45, 60, 90, 120, 180, 240]
PER_SESSION_PRESETS = [1, 3, 5, 10]
SNOOZE_MIN = 10
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif")

MONTHS_ES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
             "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
GROUP_TITLES = {"basic": "Básicos", "dakuten": "Dakuten / handakuten (゛ ゜)",
                "yoon": "Yōon (combinaciones con ゃ ゅ ょ)"}

DEFAULT_CONFIG = {
    "interval_min": 60,
    "per_session": 3,
    "mode": "both",               # hiragana | katakana | both
    "dakuten": True,
    "yoon": True,
    "picture_first": True,        # mostrar la imagen mnemotécnica antes de responder
    "active_start": 9,            # horario en que puede preguntar (hora local)
    "active_end": 23,
    "dnd": False,
    "dnd_until": None,            # epoch; None = indefinido mientras dnd sea True
    "next_due": None,
    "last_report_month": None,
}


# --------------------------------------------------------------------------- #
# Datos
# --------------------------------------------------------------------------- #
def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text()))
        except (json.JSONDecodeError, OSError):
            pass
    return cfg


def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def load_kana():
    return json.loads(KANA_FILE.read_text(encoding="utf-8"))


def save_kana(kana):
    KANA_FILE.write_text(json.dumps(kana, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")


def append_history(record):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_history():
    if not HISTORY_FILE.exists():
        return []
    out = []
    for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def accepted_answers(entry):
    return {entry["romaji"].lower(), *(a.lower() for a in entry.get("alt", []))}


def normalize(text):
    return "".join(text.lower().split()).replace("'", "").replace("-", "")


def _find_image(folder, entry):
    for ext in IMAGE_EXTS:
        p = folder / f"{entry['id']}{ext}"
        if p.exists():
            return p
    return None


def hint_image(entry):
    """Mnemonic drawing shown before answering (images/pista/<id>.*)."""
    return _find_image(HINT_DIR, entry)


def result_image(entry):
    """Card shown after answering (images/resultado/<id>.*); falls back to the hint."""
    return _find_image(RESULT_DIR, entry) or hint_image(entry)


def month_key(ts):
    return ts[:7]  # "YYYY-MM" from an ISO timestamp


def month_label(key):
    if key == "all":
        return "Todo el historial"
    y, m = key.split("-")
    return f"{MONTHS_ES[int(m)].capitalize()} {y}"


# --------------------------------------------------------------------------- #
# Estadísticas
# --------------------------------------------------------------------------- #
def compute_stats(history, kana_by_id, month="all"):
    rows = [h for h in history if month == "all" or month_key(h["ts"]) == month]
    per = defaultdict(lambda: {"ok": 0, "bad": 0, "wrong_answers": defaultdict(int)})
    by_script = defaultdict(lambda: [0, 0])
    days = set()
    for h in rows:
        p = per[h["id"]]
        entry = kana_by_id.get(h["id"], {})
        script = entry.get("script", "?")
        days.add(h["ts"][:10])
        if h["ok"]:
            p["ok"] += 1
            by_script[script][0] += 1
        else:
            p["bad"] += 1
            by_script[script][1] += 1
            p["wrong_answers"][h.get("given", "")] += 1
    ok = sum(1 for h in rows if h["ok"])
    return {
        "month": month,
        "total": len(rows),
        "ok": ok,
        "bad": len(rows) - ok,
        "days": len(days),
        "by_script": dict(by_script),
        "per": dict(per),
    }


def pct(ok, total):
    return 100.0 * ok / total if total else 0.0


def report_markdown(stats, kana_by_id):
    s = stats
    lines = [
        f"# Reporte kana — {month_label(s['month'])}",
        "",
        f"- Preguntas respondidas: **{s['total']}**",
        f"- Aciertos: **{s['ok']}** ✅",
        f"- Fallos: **{s['bad']}** ❌",
        f"- Precisión: **{pct(s['ok'], s['total']):.1f}%**",
        f"- Días practicados: **{s['days']}**",
        "",
    ]
    for script in ("hiragana", "katakana"):
        o, b = s["by_script"].get(script, [0, 0])
        if o + b:
            lines.append(f"- {script.capitalize()}: {o}/{o + b} ({pct(o, o + b):.1f}%)")
    lines += ["", "## Los que más fallaste", "",
              "| Kana | Romaji | ✅ | ❌ | % | Pusiste |", "|---|---|---|---|---|---|"]
    ranked = sorted(s["per"].items(),
                    key=lambda kv: (-kv[1]["bad"], pct(kv[1]["ok"], kv[1]["ok"] + kv[1]["bad"])))
    for kid, p in ranked:
        e = kana_by_id.get(kid)
        if not e:
            continue
        wrong = ", ".join(f"{w or '(vacío)'}×{n}" for w, n in
                          sorted(p["wrong_answers"].items(), key=lambda x: -x[1]))
        t = p["ok"] + p["bad"]
        lines.append(f"| {e['kana']} | {e['romaji']} | {p['ok']} | {p['bad']} | "
                     f"{pct(p['ok'], t):.0f}% | {wrong} |")
    return "\n".join(lines) + "\n"


def write_report(stats, kana_by_id):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{stats['month']}.md"
    path.write_text(report_markdown(stats, kana_by_id), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# Tabla de kana (KANA.md, autogenerada desde kana.json)
# --------------------------------------------------------------------------- #
KANA_TABLE_HEAD = """# Tabla de kana

Todas las respuestas que acepta la app, con su mnemotecnia y la imagen que
muestra. El **id** es el nombre del archivo en `images/pista/` y
`images/resultado/`.

> Este archivo se **regenera automáticamente** desde `kana.json` cada vez que
> editás una mnemotecnia desde la app. No lo edites a mano: editá `kana.json`
> y corré `python3 kana_tray.py --tabla`.
"""


def generate_kana_table(kana):
    parts = [KANA_TABLE_HEAD]
    for script in ("hiragana", "katakana"):
        parts.append(f"\n## {script.capitalize()}\n")
        for group in ("basic", "dakuten", "yoon"):
            entries = [e for e in kana if e["script"] == script and e["group"] == group]
            if not entries:
                continue
            parts.append(f"\n### {GROUP_TITLES[group]}\n")
            parts.append("| Kana | Romaji | También vale | Imagen | Mnemotecnia | id |")
            parts.append("|:---:|:---:|:---:|:---:|---|---|")
            for e in entries:
                alt = ", ".join(e.get("alt", [])) or "—"
                mn = e["mnemonic"].replace("|", "\\|").replace("\n", " ")
                img = hint_image(e) or result_image(e)
                cell = (f'<img src="{img.relative_to(APP_DIR).as_posix()}" height="70">'
                        if img else "—")
                parts.append(f"| **{e['kana']}** | {e['romaji']} | {alt} | {cell} | "
                             f"{mn} | `{e['id']}` |")
    KANA_TABLE_FILE.write_text("\n".join(parts) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# Selección de kana (más peso a los que fallás)
# --------------------------------------------------------------------------- #
def pick_kana(pool, history, n):
    now = time.time()
    seen = defaultdict(lambda: {"ok": 0, "bad": 0, "last": 0.0, "last_ok": True})
    for h in history:
        s = seen[h["id"]]
        s["ok" if h["ok"] else "bad"] += 1
        s["last"] = h.get("epoch", 0.0)
        s["last_ok"] = h["ok"]

    def weight(e):
        s = seen.get(e["id"])
        if not s:
            return 2.5  # nunca preguntado
        total = s["ok"] + s["bad"]
        w = 1.0 + 4.0 * s["bad"] / total
        if not s["last_ok"]:
            w += 2.0
        if s["ok"] >= 5 and s["bad"] == 0:
            w *= 0.4  # ya lo sabés
        if now - s["last"] < 3600:
            w *= 0.3  # recién preguntado
        return w

    remaining = list(pool)
    chosen = []
    for _ in range(min(n, len(remaining))):
        e = random.choices(remaining, weights=[weight(x) for x in remaining])[0]
        chosen.append(e)
        remaining.remove(e)
    return chosen


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #
from PyQt6.QtCore import QRectF, QSize, Qt, QTimer, QUrl, pyqtSignal  # noqa: E402
from PyQt6.QtGui import (  # noqa: E402
    QAction, QActionGroup, QColor, QDesktopServices, QFont, QIcon, QPainter,
    QPixmap,
)
from PyQt6.QtWidgets import (  # noqa: E402
    QAbstractItemView, QApplication, QComboBox, QDialog, QDialogButtonBox,
    QFormLayout, QFrame, QHBoxLayout, QHeaderView, QInputDialog, QLabel,
    QLineEdit, QMenu, QPlainTextEdit, QPushButton, QSystemTrayIcon,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

JP_FONT = "Noto Sans CJK JP"
OK_COLOR = "#2ecc71"
BAD_COLOR = "#e74c3c"
ACCENT = "#e0457b"

CARD_STYLE = """
#card { background: #1b1f27; border: 1px solid #2f3643; border-radius: 16px; }
QLabel { color: #d7dbe3; }
#title { color: #9aa4b2; font-size: 12px; font-weight: 600; }
#quadrant { background: #f7f3ea; border: 2px solid #3a4150; border-radius: 12px; color: #1b1f27; }
#picture { background: #ffffff; border: 2px solid #3a4150; border-radius: 12px; color: #9aa4b2; }
#mnemonic { color: #c9ced8; font-size: 13px; }
#feedback { font-size: 15px; font-weight: 600; }
QLineEdit {
    background: #11141a; color: #f2f4f8; border: 1px solid #3a4150;
    border-radius: 8px; padding: 8px 10px; font-size: 18px;
}
QLineEdit:focus { border-color: #e0457b; }
QPushButton {
    background: #262c38; color: #d7dbe3; border: 1px solid #343b49;
    border-radius: 7px; padding: 5px 10px; font-size: 12px;
}
QPushButton:hover { background: #2f3645; }
#close { background: transparent; border: none; color: #6b7280; font-size: 14px; }
#close:hover { color: #f2f4f8; }
"""


def make_tray_icon(dnd=False):
    size = 64
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#6b7280" if dnd else ACCENT))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(2, 2, size - 4, size - 4), 14, 14)
    f = QFont(JP_FONT)
    f.setPixelSize(44)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("white"))
    p.drawText(QRectF(0, 0, size, size - 2), Qt.AlignmentFlag.AlignCenter, "あ")
    if dnd:
        p.setBrush(QColor("#1b1f27"))
        p.drawEllipse(QRectF(38, 38, 24, 24))
        f.setPixelSize(16)
        p.setFont(f)
        p.drawText(QRectF(38, 37, 24, 24), Qt.AlignmentFlag.AlignCenter, "z")
    p.end()
    return QIcon(pix)


def load_pixmap(path, w, h):
    pm = QPixmap(str(path)) if path else QPixmap()
    if pm.isNull():
        return None
    return pm.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio,
                     Qt.TransformationMode.SmoothTransformation)


class EditMnemonicDialog(QDialog):
    def __init__(self, entry, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Editar mnemotecnia — {entry['kana']} ({entry['romaji']})")
        self.setMinimumWidth(460)
        form = QFormLayout(self)
        self.alt = QLineEdit(", ".join(entry.get("alt", [])))
        self.alt.setPlaceholderText("ej: si, shi")
        self.text = QPlainTextEdit(entry.get("mnemonic", ""))
        self.text.setMinimumHeight(110)
        form.addRow("Kana", QLabel(f"<span style='font-size:28px'>{entry['kana']}</span>"
                                   f"  →  <b>{entry['romaji']}</b>   <code>{entry['id']}</code>"))
        form.addRow("También vale", self.alt)
        form.addRow("Mnemotecnia", self.text)
        hint = QLabel(f"Imágenes: images/pista/{entry['id']}.png (antes) y "
                      f"images/resultado/{entry['id']}.png (después)")
        hint.setStyleSheet("color:#888; font-size:11px")
        form.addRow("", hint)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save
                                | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def values(self):
        alts = [a.strip().lower() for a in self.alt.text().split(",") if a.strip()]
        return alts, self.text.toPlainText().strip()


class QuizCard(QWidget):
    answered = pyqtSignal(dict, str, bool, bool)   # entry, given, ok, hint_used
    finished = pyqtSignal(int, int)                 # ok count, total answered
    snoozed = pyqtSignal()
    edit_requested = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
                            | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Kana")
        self.queue, self.idx = [], 0
        self.done = False
        self.hint_used = False
        self.picture_first = True
        self.session_ok = self.session_total = 0

        self.card = QFrame(self)
        self.card.setObjectName("card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.addWidget(self.card)

        lay = QVBoxLayout(self.card)
        lay.setContentsMargins(18, 12, 18, 16)
        lay.setSpacing(10)

        head = QHBoxLayout()
        self.title = QLabel()
        self.title.setObjectName("title")
        close = QPushButton("✕")
        close.setObjectName("close")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(self.close_session)
        head.addWidget(self.title)
        head.addStretch()
        head.addWidget(close)
        lay.addLayout(head)

        # Cuadrante: kana grande + imagen mnemotécnica
        row = QHBoxLayout()
        row.setSpacing(12)
        self.quadrant = QLabel()
        self.quadrant.setObjectName("quadrant")
        self.quadrant.setFixedSize(230, 230)
        self.quadrant.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.picture = QLabel()
        self.picture.setObjectName("picture")
        self.picture.setFixedSize(230, 230)
        self.picture.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self.quadrant)
        row.addWidget(self.picture)
        lay.addLayout(row)

        mrow = QHBoxLayout()
        self.mnemonic = QLabel()
        self.mnemonic.setObjectName("mnemonic")
        self.mnemonic.setWordWrap(True)
        self.mnemonic.setFixedWidth(420)
        self.edit_btn = QPushButton("✏️")
        self.edit_btn.setToolTip("Editar la mnemotecnia de este kana")
        self.edit_btn.setFixedWidth(34)
        self.edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.current()))
        mrow.addWidget(self.mnemonic)
        mrow.addWidget(self.edit_btn, 0, Qt.AlignmentFlag.AlignTop)
        lay.addLayout(mrow)

        self.input = QLineEdit()
        self.input.setPlaceholderText("¿Qué sonido es? (romaji) + Enter")
        self.input.returnPressed.connect(self._on_enter)
        lay.addWidget(self.input)

        self.feedback = QLabel()
        self.feedback.setObjectName("feedback")
        self.feedback.setWordWrap(True)
        lay.addWidget(self.feedback)

        btns = QHBoxLayout()
        self.hint_btn = QPushButton("💡 Pista")
        self.hint_btn.clicked.connect(self._hint)
        snooze = QPushButton(f"⏰ +{SNOOZE_MIN} min")
        snooze.clicked.connect(self._snooze)
        self.skip_btn = QPushButton("Saltar")
        self.skip_btn.clicked.connect(self._next)
        self.next_btn = QPushButton("Siguiente →")
        self.next_btn.clicked.connect(self._next)
        for b in (self.hint_btn, snooze, self.skip_btn, self.next_btn):
            btns.addWidget(b)
        lay.addLayout(btns)

        self.setStyleSheet(CARD_STYLE)

    def current(self):
        return self.queue[self.idx]

    def start(self, entries, picture_first):
        self.queue, self.idx = entries, 0
        self.picture_first = picture_first
        self.session_ok = self.session_total = 0
        self._show_entry()
        self.show()
        self._dock()
        self.raise_()
        self.activateWindow()
        self.input.setFocus()

    def _show_entry(self):
        e = self.current()
        self.done = False
        self.hint_used = False
        self.title.setText(f"{e['script'].upper()}  ·  {self.idx + 1}/{len(self.queue)}")
        f = QFont(JP_FONT)
        f.setPixelSize(120 if len(e["kana"]) == 1 else 82)
        self.quadrant.setFont(f)
        self.quadrant.setText(e["kana"])
        self._set_picture(hint_image(e) if self.picture_first else None)
        self.mnemonic.setText("")
        self.mnemonic.setVisible(False)
        self.edit_btn.setVisible(False)
        self.feedback.setText("")
        self.feedback.setVisible(False)
        self.input.clear()
        self.input.setReadOnly(False)
        self.hint_btn.setEnabled(True)
        self.skip_btn.setVisible(True)
        self.next_btn.setVisible(False)
        self.input.setFocus()
        if self.isVisible():
            self._dock()

    def _dock(self):
        """Stick to the bottom-right corner, right above the taskbar."""
        self.adjustSize()
        screen = (self.screen() or QApplication.primaryScreen()).availableGeometry()
        self.move(screen.right() - self.width() + 4, screen.bottom() - self.height() + 4)

    def _set_picture(self, path):
        pm = load_pixmap(path, 220, 220)
        if pm:
            self.picture.setPixmap(pm)
        else:
            self.picture.clear()
            self.picture.setText("?")
            self.picture.setStyleSheet("font-size:64px;")

    def _reveal(self):
        e = self.current()
        self._set_picture(result_image(e) if self.done else hint_image(e))
        self.mnemonic.setText(e["mnemonic"])
        self.mnemonic.setVisible(True)
        self.edit_btn.setVisible(True)
        if self.isVisible():
            self._dock()

    def refresh_current(self, entry):
        """Called after the mnemonic was edited."""
        self.queue[self.idx] = entry
        if self.mnemonic.isVisible():
            self._reveal()
        else:
            self._set_picture(hint_image(entry) if self.picture_first else None)

    def _hint(self):
        self.hint_used = True
        self.hint_btn.setEnabled(False)
        self._reveal()
        self.input.setFocus()

    def _on_enter(self):
        if self.done:
            self._next()
            return
        given = normalize(self.input.text())
        if not given:
            return
        e = self.current()
        ok = given in accepted_answers(e)
        self.done = True
        self.session_total += 1
        self.session_ok += ok
        self.input.setReadOnly(True)
        if ok:
            self.feedback.setStyleSheet(f"color:{OK_COLOR}")
            self.feedback.setText(f"✓ ¡Bien!  {e['kana']} = {e['romaji']}")
        else:
            self.feedback.setStyleSheet(f"color:{BAD_COLOR}")
            self.feedback.setText(f"✗ Era «{e['romaji']}»  (pusiste «{given}»)")
        self.feedback.setVisible(True)
        self._reveal()
        self.hint_btn.setEnabled(False)
        self.skip_btn.setVisible(False)
        self.next_btn.setVisible(True)
        self.next_btn.setText("Siguiente →" if self.idx + 1 < len(self.queue) else "Terminar")
        self.answered.emit(e, given, ok, self.hint_used)

    def _next(self):
        if self.idx + 1 < len(self.queue):
            self.idx += 1
            self._show_entry()
        else:
            self.hide()
            self.finished.emit(self.session_ok, self.session_total)

    def _snooze(self):
        self.hide()
        self.snoozed.emit()

    def close_session(self):
        self.hide()
        self.finished.emit(self.session_ok, self.session_total)

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key.Key_Escape:
            self.close_session()
        else:
            super().keyPressEvent(ev)


class StatsWindow(QWidget):
    COLS = ["Kana", "Romaji", "✅", "❌", "%", "Pusiste"]

    def __init__(self, get_data):
        super().__init__()
        self.get_data = get_data  # -> (history, kana_by_id)
        self.setWindowTitle("Kana — Estadísticas")
        self.resize(620, 640)
        lay = QVBoxLayout(self)

        top = QHBoxLayout()
        self.month = QComboBox()
        self.month.currentIndexChanged.connect(self.render)
        top.addWidget(QLabel("Mes:"))
        top.addWidget(self.month, 1)
        export = QPushButton("Exportar reporte .md")
        export.clicked.connect(self.export)
        folder = QPushButton("Abrir carpeta")
        folder.clicked.connect(lambda: (REPORTS_DIR.mkdir(parents=True, exist_ok=True),
                                        QDesktopServices.openUrl(QUrl.fromLocalFile(str(REPORTS_DIR)))))
        top.addWidget(export)
        top.addWidget(folder)
        lay.addLayout(top)

        self.summary = QLabel()
        self.summary.setTextFormat(Qt.TextFormat.RichText)
        self.summary.setStyleSheet("font-size:14px; padding:8px 2px;")
        lay.addWidget(self.summary)

        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(False)
        hh = self.table.horizontalHeader()
        for c in range(len(self.COLS) - 1):
            hh.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(len(self.COLS) - 1, QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.table)

    def open(self, month=None):
        history, _ = self.get_data()
        months = sorted({month_key(h["ts"]) for h in history}, reverse=True)
        current = datetime.now().strftime("%Y-%m")
        if current not in months:
            months.insert(0, current)
        self.month.blockSignals(True)
        self.month.clear()
        for m in months:
            self.month.addItem(month_label(m), m)
        self.month.addItem(month_label("all"), "all")
        idx = self.month.findData(month or current)
        self.month.setCurrentIndex(max(idx, 0))
        self.month.blockSignals(False)
        self.render()
        self.show()
        self.raise_()
        self.activateWindow()

    def _stats(self):
        history, kana_by_id = self.get_data()
        return compute_stats(history, kana_by_id, self.month.currentData() or "all"), kana_by_id

    def render(self):
        s, kana_by_id = self._stats()
        acc = pct(s["ok"], s["total"])
        color = OK_COLOR if acc >= 80 else ("#f39c12" if acc >= 60 else BAD_COLOR)
        scripts = "  ·  ".join(
            f"{k.capitalize()}: {v[0]}/{v[0] + v[1]} ({pct(v[0], v[0] + v[1]):.0f}%)"
            for k, v in sorted(s["by_script"].items()))
        self.summary.setText(
            f"<b>{s['total']}</b> respuestas en <b>{s['days']}</b> días — "
            f"<span style='color:{OK_COLOR}'><b>{s['ok']}</b> embocadas</span>, "
            f"<span style='color:{BAD_COLOR}'><b>{s['bad']}</b> falladas</span> — "
            f"<span style='color:{color}; font-size:18px'><b>{acc:.1f}%</b></span>"
            f"<br><span style='color:#888'>{scripts}</span>")

        ranked = sorted(s["per"].items(),
                        key=lambda kv: (-kv[1]["bad"], pct(kv[1]["ok"], kv[1]["ok"] + kv[1]["bad"])))
        self.table.setRowCount(0)
        for kid, p in ranked:
            e = kana_by_id.get(kid)
            if not e:
                continue
            r = self.table.rowCount()
            self.table.insertRow(r)
            t = p["ok"] + p["bad"]
            wrong = ", ".join(f"{w}×{n}" for w, n in sorted(p["wrong_answers"].items(), key=lambda x: -x[1]))
            vals = [e["kana"], e["romaji"], str(p["ok"]), str(p["bad"]), f"{pct(p['ok'], t):.0f}%", wrong]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c == 0:
                    it.setFont(QFont(JP_FONT, 18))
                if c < 5:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if c == 4:
                    it.setForeground(QColor(OK_COLOR if pct(p["ok"], t) >= 80 else BAD_COLOR))
                self.table.setItem(r, c, it)

    def export(self):
        s, kana_by_id = self._stats()
        path = write_report(s, kana_by_id)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


class KanaTableWindow(QWidget):
    COLS = ["Kana", "Romaji", "También vale", "Imagen", "Mnemotecnia"]

    def __init__(self, get_kana, on_edit):
        super().__init__()
        self.get_kana, self.on_edit = get_kana, on_edit
        self.setWindowTitle("Kana — Tabla de respuestas")
        self.resize(820, 680)
        lay = QVBoxLayout(self)
        top = QHBoxLayout()
        self.filter = QComboBox()
        for label, key in [("Hiragana — básicos", ("hiragana", "basic")),
                           ("Katakana — básicos", ("katakana", "basic")),
                           ("Hiragana — dakuten", ("hiragana", "dakuten")),
                           ("Katakana — dakuten", ("katakana", "dakuten")),
                           ("Hiragana — yōon", ("hiragana", "yoon")),
                           ("Katakana — yōon", ("katakana", "yoon"))]:
            self.filter.addItem(label, key)
        self.filter.currentIndexChanged.connect(self.render)
        top.addWidget(self.filter, 1)
        top.addWidget(QLabel("Doble click en una fila para editar la explicación"))
        lay.addLayout(top)
        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setWordWrap(True)
        hh = self.table.horizontalHeader()
        for c in range(4):
            hh.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setIconSize(QSize(90, 90))
        self.table.cellDoubleClicked.connect(self._edit)
        lay.addWidget(self.table)
        self.rows = []

    def open(self):
        self.render()
        self.show()
        self.raise_()
        self.activateWindow()

    def render(self):
        script, group = self.filter.currentData()
        self.rows = [e for e in self.get_kana() if e["script"] == script and e["group"] == group]
        self.table.setRowCount(len(self.rows))
        for r, e in enumerate(self.rows):
            vals = [e["kana"], e["romaji"], ", ".join(e.get("alt", [])), "", e["mnemonic"]]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c == 0:
                    it.setFont(QFont(JP_FONT, 22))
                elif c == 3:
                    pm = load_pixmap(hint_image(e) or result_image(e), 90, 90)
                    if pm:
                        it.setData(Qt.ItemDataRole.DecorationRole, pm)
                if c < 4:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, it)
        self.table.resizeRowsToContents()

    def _edit(self, row, _col):
        self.on_edit(self.rows[row], self)


class KanaTray(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.kana = load_kana()
        self.session_count = 0

        self.card = QuizCard()
        self.card.answered.connect(self._on_answered)
        self.card.finished.connect(self._on_finished)
        self.card.snoozed.connect(self._on_snoozed)
        self.card.edit_requested.connect(lambda e: self.edit_entry(e, self.card))
        self.stats = StatsWindow(lambda: (load_history(), self.kana_by_id()))
        self.table = KanaTableWindow(lambda: self.kana, self.edit_entry)

        self.tray = QSystemTrayIcon(self)
        self.tray.activated.connect(self._on_tray_activated)
        self.menu = QMenu(self)
        self.tray.setContextMenu(self.menu)

        if not self.config.get("last_report_month"):
            self.config["last_report_month"] = datetime.now().strftime("%Y-%m")
        now = time.time()
        if not self.config.get("next_due") or self.config["next_due"] < now:
            self.config["next_due"] = now + 120  # no preguntar apenas prende la compu
        save_config(self.config)

        self._rebuild_menu()
        self._update_icon()
        self.tray.show()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(20_000)
        self.tick()

    # ---- helpers -------------------------------------------------------- #
    def kana_by_id(self):
        return {e["id"]: e for e in self.kana}

    def pool(self):
        c = self.config
        scripts = {"hiragana", "katakana"} if c["mode"] == "both" else {c["mode"]}
        groups = {"basic"} | ({"dakuten"} if c["dakuten"] else set()) | ({"yoon"} if c["yoon"] else set())
        return [e for e in self.kana if e["script"] in scripts and e["group"] in groups]

    def dnd_active(self):
        c = self.config
        if not c["dnd"]:
            return False
        if c.get("dnd_until") and time.time() >= c["dnd_until"]:
            c["dnd"], c["dnd_until"] = False, None
            save_config(c)
            self._rebuild_menu()
            self._update_icon()
            return False
        return True

    def in_active_hours(self):
        start, end, h = self.config["active_start"], self.config["active_end"], datetime.now().hour
        if start == end:
            return True
        return start <= h < end if start < end else (h >= start or h < end)

    def _save(self):
        save_config(self.config)

    # ---- scheduling ----------------------------------------------------- #
    def tick(self):
        self._check_month_report()
        if not self.card.isVisible() and not self.dnd_active() and self.in_active_hours():
            if time.time() >= self.config["next_due"]:
                self.ask_now()
        self._update_tooltip()

    def ask_now(self):
        if self.card.isVisible():
            self.card.raise_()
            self.card.activateWindow()
            return
        entries = pick_kana(self.pool(), load_history(), self.config["per_session"])
        if not entries:
            return
        self.config["next_due"] = time.time() + self.config["interval_min"] * 60
        self._save()
        self.card.start(entries, self.config["picture_first"])

    def _on_answered(self, entry, given, ok, hint):
        now = datetime.now()
        append_history({"ts": now.isoformat(timespec="seconds"), "epoch": now.timestamp(),
                        "id": entry["id"], "kana": entry["kana"], "answer": entry["romaji"],
                        "given": given, "ok": ok, "hint": hint})
        self._update_tooltip()

    def _on_finished(self, ok, total):
        if total:
            self.tray.showMessage("Kana", f"Tanda terminada: {ok}/{total} bien",
                                  QSystemTrayIcon.MessageIcon.Information, 3000)
        self._update_tooltip()

    def _on_snoozed(self):
        self.config["next_due"] = time.time() + SNOOZE_MIN * 60
        self._save()
        self._update_tooltip()

    def _check_month_report(self):
        current = datetime.now().strftime("%Y-%m")
        last = self.config.get("last_report_month")
        if last == current:
            return
        self.config["last_report_month"] = current
        self._save()
        first = datetime.now().replace(day=1)
        prev = (first - timedelta(days=1)).strftime("%Y-%m")
        history = load_history()
        stats = compute_stats(history, self.kana_by_id(), prev)
        if stats["total"]:
            path = write_report(stats, self.kana_by_id())
            self.tray.showMessage(
                f"Reporte de {month_label(prev)}",
                f"{stats['ok']} embocadas, {stats['bad']} falladas "
                f"({pct(stats['ok'], stats['total']):.1f}%). Guardado en {path.name}",
                QSystemTrayIcon.MessageIcon.Information, 10000)
            self.stats.open(prev)

    # ---- tray ----------------------------------------------------------- #
    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.ask_now()

    def _update_icon(self):
        self.tray.setIcon(make_tray_icon(self.config["dnd"]))

    def _update_tooltip(self):
        today = datetime.now().strftime("%Y-%m-%d")
        rows = [h for h in load_history() if h["ts"].startswith(today)]
        ok = sum(1 for h in rows if h["ok"])
        if self.dnd_active():
            until = self.config.get("dnd_until")
            status = ("No molestar hasta las " + datetime.fromtimestamp(until).strftime("%H:%M")
                      if until else "No molestar activado")
        elif not self.in_active_hours():
            status = (f"Fuera de horario ({self.config['active_start']}–"
                      f"{self.config['active_end']} h)")
        else:
            mins = max(0, int((self.config["next_due"] - time.time()) / 60))
            status = f"Próxima pregunta en {mins} min"
        self.tray.setToolTip(f"Kana Tray\n{status}\nHoy: {ok}/{len(rows)} bien")

    def _rebuild_menu(self):
        m = self.menu
        m.clear()
        c = self.config

        head = QAction("あ ア  Kana Tray", self)
        head.setEnabled(False)
        m.addAction(head)
        m.addSeparator()
        m.addAction("Preguntar ahora", self.ask_now)
        m.addAction("Estadísticas…", self.stats.open)
        m.addAction("Tabla de kana (respuestas)…", self.table.open)
        m.addSeparator()

        freq = m.addMenu("Frecuencia")
        grp = QActionGroup(self)
        presets = list(INTERVAL_PRESETS_MIN)
        if c["interval_min"] not in presets:
            presets = sorted(presets + [c["interval_min"]])
        for mins in presets:
            label = f"Cada {mins} min" if mins < 60 else f"Cada {mins / 60:g} h"
            a = QAction(label, self, checkable=True, checked=mins == c["interval_min"])
            a.triggered.connect(lambda _c, v=mins: self.set_interval(v))
            grp.addAction(a)
            freq.addAction(a)
        freq.addSeparator()
        freq.addAction("Personalizada…", self.custom_interval)

        per = m.addMenu("Preguntas por vez")
        grp2 = QActionGroup(self)
        for n in PER_SESSION_PRESETS:
            a = QAction(str(n), self, checkable=True, checked=n == c["per_session"])
            a.triggered.connect(lambda _c, v=n: self.set_value("per_session", v))
            grp2.addAction(a)
            per.addAction(a)

        what = m.addMenu("Qué practicar")
        grp3 = QActionGroup(self)
        for key, label in [("hiragana", "Sólo hiragana"), ("katakana", "Sólo katakana"),
                           ("both", "Hiragana + katakana")]:
            a = QAction(label, self, checkable=True, checked=c["mode"] == key)
            a.triggered.connect(lambda _c, v=key: self.set_value("mode", v))
            grp3.addAction(a)
            what.addAction(a)
        what.addSeparator()
        for key, label in [("dakuten", "Incluir dakuten (が, ぱ…)"),
                           ("yoon", "Incluir yōon (きゃ, しゅ…)"),
                           ("picture_first", "Mostrar imagen antes de responder")]:
            a = QAction(label, self, checkable=True, checked=bool(c[key]))
            a.triggered.connect(lambda checked, k=key: self.set_value(k, checked))
            what.addAction(a)

        m.addAction(f"Horario activo ({c['active_start']}–{c['active_end']} h)…", self.set_hours)

        dnd = m.addMenu("No molestar" + ("  ✓" if c["dnd"] else ""))
        dnd.addAction("1 hora", lambda: self.set_dnd(60))
        dnd.addAction("3 horas", lambda: self.set_dnd(180))
        dnd.addAction("Hasta mañana", lambda: self.set_dnd("tomorrow"))
        dnd.addAction("Indefinido", lambda: self.set_dnd(None))
        if c["dnd"]:
            dnd.addSeparator()
            dnd.addAction("Desactivar", lambda: self.set_dnd(0))

        m.addSeparator()
        auto = QAction("Iniciar con la computadora", self, checkable=True,
                       checked=AUTOSTART_FILE.exists())
        auto.triggered.connect(self.set_autostart)
        m.addAction(auto)
        m.addAction("Editar kana.json…", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(KANA_FILE))))
        m.addAction("Carpeta de imágenes…", self.open_images)
        m.addSeparator()
        m.addAction("Salir", self.quit_app)

    # ---- acciones ------------------------------------------------------- #
    def set_value(self, key, value):
        self.config[key] = value
        self._save()
        self._rebuild_menu()

    def set_interval(self, mins):
        self.config["interval_min"] = mins
        self.config["next_due"] = time.time() + mins * 60
        self._save()
        self._rebuild_menu()
        self._update_tooltip()

    def custom_interval(self):
        mins, ok = QInputDialog.getInt(None, "Frecuencia", "Preguntar cada cuántos minutos:",
                                       self.config["interval_min"], 1, 24 * 60)
        if ok:
            self.set_interval(mins)

    def set_hours(self):
        start, ok = QInputDialog.getInt(None, "Horario activo", "Desde (hora, 0–23):",
                                        self.config["active_start"], 0, 23)
        if not ok:
            return
        end, ok = QInputDialog.getInt(None, "Horario activo",
                                      "Hasta (hora, 0–23; igual a 'desde' = todo el día):",
                                      self.config["active_end"], 0, 23)
        if ok:
            self.config["active_start"], self.config["active_end"] = start, end
            self._save()
            self._rebuild_menu()
            self._update_tooltip()

    def set_dnd(self, minutes):
        c = self.config
        if minutes == 0:
            c["dnd"], c["dnd_until"] = False, None
            c["next_due"] = max(c["next_due"], time.time() + 60)
        else:
            c["dnd"] = True
            if minutes is None:
                c["dnd_until"] = None
            elif minutes == "tomorrow":
                tomorrow = datetime.now() + timedelta(days=1)
                c["dnd_until"] = tomorrow.replace(hour=c["active_start"], minute=0,
                                                  second=0, microsecond=0).timestamp()
            else:
                c["dnd_until"] = time.time() + minutes * 60
            if self.card.isVisible():
                self.card.close_session()
        self._save()
        self._rebuild_menu()
        self._update_icon()
        self._update_tooltip()

    def set_autostart(self, enabled):
        if enabled:
            AUTOSTART_FILE.parent.mkdir(parents=True, exist_ok=True)
            AUTOSTART_FILE.write_text(desktop_entry())
        elif AUTOSTART_FILE.exists():
            AUTOSTART_FILE.unlink()
        self._rebuild_menu()

    def open_images(self):
        IMAGES_DIR.mkdir(exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(IMAGES_DIR)))

    def edit_entry(self, entry, parent=None):
        dlg = EditMnemonicDialog(entry, parent)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        alts, text = dlg.values()
        for e in self.kana:
            if e["id"] == entry["id"]:
                e["alt"] = alts
                e["mnemonic"] = text or e["mnemonic"]
                updated = e
                break
        else:
            return
        save_kana(self.kana)
        generate_kana_table(self.kana)
        if self.card.isVisible() and self.card.current()["id"] == updated["id"]:
            self.card.refresh_current(updated)
        if self.table.isVisible():
            self.table.render()

    def quit_app(self):
        self._save()
        QApplication.instance().quit()


def desktop_entry():
    return (
        "[Desktop Entry]\n"
        "Name=Kana Tray\n"
        "Comment=Practicá hiragana y katakana desde la bandeja del sistema\n"
        f"Exec={sys.executable} {APP_DIR / 'kana_tray.py'}\n"
        f"Icon={APP_DIR / 'icon.svg'}\n"
        "Type=Application\n"
        "Terminal=false\n"
        "Categories=Education;Languages;\n"
        "X-GNOME-Autostart-enabled=true\n"
        "StartupNotify=false\n"
    )


def main():
    if "--tabla" in sys.argv or "--readme" in sys.argv:
        generate_kana_table(load_kana())
        print(f"Tabla regenerada: {KANA_TABLE_FILE}")
        return

    # Wayland no deja que una app elija la posición de su ventana; vía XWayland
    # sí, así la tarjeta queda pegada a la barra de tareas y no en el medio.
    if os.environ.get("XDG_SESSION_TYPE") == "wayland" and "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Kana Tray")
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("No hay bandeja del sistema disponible.", file=sys.stderr)
        sys.exit(1)
    if not KANA_TABLE_FILE.exists():
        generate_kana_table(load_kana())
    tray = KanaTray()  # noqa: F841 - vive mientras corre la app
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
