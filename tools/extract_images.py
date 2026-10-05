"""Crop per-kana images out of the charts in assets/ into images/pista and images/resultado."""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(sys.argv[1])
A = ROOT / "assets"
PISTA = ROOT / "images" / "pista"
RES = ROOT / "images" / "resultado"
PISTA.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)
V = "a i u e o".split()

# ---- Hiragana mnemonic chart (original px) ----
hm = Image.open(A / "hiragana-mnemonic-chart-by-tofugu.jpg").convert("RGB")
H_COLS = ["", "k", "s", "t", "n", "h", "m", "r", "y"]
H_LEFT = [63, 417, 770, 1124, 1478, 1836, 2193, 2551, 2908]
H_TOP = [425, 767, 1109, 1450, 1792]
SPECIAL_ROM = {"si": "shi", "ti": "chi", "tu": "tsu", "hu": "fu"}
cells = {}
for ci, c in enumerate(H_COLS):
    for ri, v in enumerate(V):
        rom = SPECIAL_ROM.get(c + v, c + v)
        if c == "y" and v in "ie":
            continue
        cells[rom] = (H_LEFT[ci], H_TOP[ri])
cells["wa"] = (233, 2125)
cells["wo"] = (582, 2125)
cells["n"] = (2729, 2117)
for rom, (x, y) in cells.items():
    # picture half (right side of the top area) -> hint
    hm.crop((x + 176, y + 34, x + 318, y + 176)).save(PISTA / f"h_{rom}.png")
    # whole cell incl. romaji bubble and caption -> result
    hm.crop((x - 8, y - 48, x + 334, y + 314)).save(RES / f"h_{rom}.png")

# ---- Katakana chart (display coords * 1.65) ----
kc = Image.open(A / "katakana-chart-by-tofugu.jpg").convert("RGB")
S = 1.65


def kcrop(l, t, w, h, name):
    kc.crop((int(l * S), int(t * S), int((l + w) * S), int((t + h) * S))).save(RES / name)


K_COLS = ["", "k", "s", "t", "n", "h", "m", "y", "r", "w"]
K_LEFT = [57, 175, 293, 411, 529, 647, 767, 887, 1007, 1128]
K_TOP = [168, 318, 467, 617, 767]
for ci, c in enumerate(K_COLS):
    for ri, v in enumerate(V):
        rom = SPECIAL_ROM.get(c + v, c + v)
        if c == "y" and v in "ie":
            continue
        if c == "w":
            rom = {"a": "wa", "u": "wo", "o": "n"}.get(v)
            if not rom:
                continue
        if c == "r" and False:
            pass
        kcrop(K_LEFT[ci] - 6, K_TOP[ri] - 32, 112, 140, f"k_{rom}.png")

D_COLS = ["g", "z", "d", "b", "p"]
D_LEFT = [1251, 1369, 1487, 1605, 1723]
D_ROM = {"zi": "ji", "di": "ji_di", "du": "zu_du"}
for ci, c in enumerate(D_COLS):
    for ri, v in enumerate(V):
        rom = D_ROM.get(c + v, c + v)
        kcrop(D_LEFT[ci] - 6, K_TOP[ri] - 32, 112, 140, f"k_{rom}.png")

Y_COLS = ["ky", "sh", "ch", "ny", "hy", "my", "ry", "gy", "j", None, "by", "py"]
Y_LEFT = [257, 393, 535, 677, 819, 961, 1103, 1245, 1387, 1529, 1671, 1813]
Y_TOP = [925, 1030, 1134]
for ci, c in enumerate(Y_COLS):
    if not c:
        continue
    for ri, v in enumerate("auo"):
        kcrop(Y_LEFT[ci] - 6, Y_TOP[ri] - 30, 138, 104, f"k_{c}{v}.png")

# ---- Hiragana dakuten / yoon: the sample chart is too low-res, so draw the
# card in the same Tofugu style (rounded box + black romaji bubble).
import json
from PIL import ImageDraw, ImageFont

# Fuentes para dibujar las tarjetas: se usa la primera que exista en el sistema.
CJK_CANDIDATES = [
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Black.ttc",           # Arch
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc",      # Debian/Ubuntu
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Black.ttc",
    "C:/Windows/Fonts/YuGothB.ttc",                              # Windows
    "C:/Windows/Fonts/msgothic.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",                # macOS
]
LAT_CANDIDATES = [
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def pick_font(candidates, what):
    for path in candidates:
        if Path(path).exists():
            return path
    raise SystemExit(
        f"No encontré una fuente {what} para dibujar las tarjetas. Probé:\n  "
        + "\n  ".join(candidates)
        + "\nInstalá Noto CJK (pacman -S noto-fonts-cjk / apt install fonts-noto-cjk)\n"
          "o agregá la ruta de tu fuente a este script."
    )


CJK = pick_font(CJK_CANDIDATES, "japonesa")
LAT = pick_font(LAT_CANDIDATES, "latina en negrita")


def draw_card(kana, label, name):
    wide = len(kana) > 1
    W, H = (228, 172) if wide else (185, 231)
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    top = 26
    d.rounded_rectangle((6, top, W - 7, H - 7), radius=16, outline="black", width=5)
    lf = ImageFont.truetype(LAT, 20, index=0)
    tw = d.textlength(label, font=lf)
    bw = max(52, tw + 30)
    d.rounded_rectangle(((W - bw) / 2, 4, (W + bw) / 2, 48), radius=22, fill="black")
    d.text((W / 2, 25), label, font=lf, fill="white", anchor="mm")
    kf = ImageFont.truetype(CJK, 92 if wide else 130, index=0)
    d.text((W / 2, (top + H) / 2 + 8), kana, font=kf, fill="black", anchor="mm")
    im.save(RES / name)


for e in json.load(open(ROOT / "kana.json", encoding="utf-8")):
    if e["script"] == "hiragana" and e["group"] != "basic":
        label = e["romaji"].upper()
        if e.get("alt") and e["id"] in ("h_ji_di", "h_zu_du"):
            label += " / " + e["alt"][0].upper()
        draw_card(e["kana"], label, f"{e['id']}.png")
print(len(list(PISTA.iterdir())), len(list(RES.iterdir())))
