import base64
import datetime as dt
import io
import json
import math
import random
from pathlib import Path

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent
FONTS = ROOT / "fonts"

PROFILE = {
    "name": "Mario Stirbu",
    "city": "Hannover",
    "site": "skurllex.com",
    "mail": "hallo@skurllex.com",
    "studio": "edifystudios.de",
    "pages": "https://skurllextv.github.io/SkurllexTV/",
}

BRAND = {
    "navy": "#0F1B2D", "blue": "#2B5BE0", "white": "#FFFFFF", "navy2": "#16233A", "blue_light": "#7FA2FF",
    "blue_soft": "#EEF3FE", "violet": "#7B61E8", "surface": "#F5F7FA", "border": "#E6E8EC", "muted": "#5A6577",
    "success": "#1F9D55",
}

THEMES = {
    "light": dict(
        bg=BRAND["white"], card=BRAND["white"], surface=BRAND["surface"], text=BRAND["navy"], muted=BRAND["muted"],
        border=BRAND["border"], accent=BRAND["blue"], mark=BRAND["blue"], grid="#E9EDF3", pill_bg=BRAND["white"],
        soft=BRAND["blue_soft"], soft_text=BRAND["blue"], v1=BRAND["navy"], v1_text=BRAND["white"], v1_muted="#A9B4C6",
        v1_label=BRAND["blue_light"], v3=BRAND["surface"], v3_text=BRAND["navy"], v3_muted=BRAND["muted"],
        heat=["#E6E8EC", "#C9D7FB", "#8EADF5", "#4D78EA", "#2B5BE0"], glow_op=0.55,
    ),
    "dark": dict(
        bg=BRAND["navy"], card=BRAND["navy2"], surface=BRAND["navy2"], text=BRAND["white"], muted="#9AA6B8",
        border="#24344F", accent=BRAND["blue_light"], mark=BRAND["blue_light"], grid="#1C2A42", pill_bg=BRAND["navy2"],
        soft="#1E3160", soft_text=BRAND["blue_light"], v1=BRAND["navy2"], v1_text=BRAND["white"], v1_muted="#9AA6B8",
        v1_label=BRAND["blue_light"], v3="#1B2A44", v3_text=BRAND["white"], v3_muted="#9AA6B8",
        heat=["#1F2E48", "#24427F", "#2F57C4", "#5A82F0", "#9DB7FF"], glow_op=0.5,
    ),
}

FONT_FILES = {
    "sans400": ("Geist", 400, "Geist-Regular.woff2"),
    "sans600": ("Geist", 600, "Geist-SemiBold.woff2"),
    "sans700": ("Geist", 700, "Geist-Bold.woff2"),
    "sans800": ("Geist", 800, "Geist-ExtraBold.woff2"),
    "mono400": ("GeistMono", 400, "GeistMono-Regular.woff2"),
    "mono500": ("GeistMono", 500, "GeistMono-Medium.woff2"),
    "mono600": ("GeistMono", 600, "GeistMono-SemiBold.woff2"),
}
CHARSET = "".join(chr(c) for c in range(32, 127)) + "äöüÄÖÜß→·–—„“"
_FONT_CACHE: dict[str, TTFont] = {}
_B64_CACHE: dict[str, str] = {}


def font(key: str) -> TTFont:
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = TTFont(FONTS / FONT_FILES[key][2])
    return _FONT_CACHE[key]


def font_b64(key: str) -> str:
    if key not in _B64_CACHE:
        f = TTFont(FONTS / FONT_FILES[key][2])
        opts = Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern"]
        sub = Subsetter(opts)
        sub.populate(text=CHARSET)
        sub.subset(f)
        f.flavor = "woff2"
        buf = io.BytesIO()
        f.save(buf)
        _B64_CACHE[key] = base64.b64encode(buf.getvalue()).decode()
    return _B64_CACHE[key]


def measure(txt: str, key: str, size: float, tracking: float = 0.0) -> float:
    f = font(key)
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    w = sum(hmtx[cmap[ord(c)]][0] for c in txt if ord(c) in cmap)
    return w * size / upm + tracking * size * max(0, len(txt) - 1)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


class Svg:
    def __init__(self, w: float, h: float):
        self.w, self.h = w, h
        self.defs: list[str] = []
        self.body: list[str] = []
        self.used: set[str] = set()

    def add(self, s: str):
        self.body.append(s)

    def text(self, x, y, txt, key, size, fill, tracking=0.0, anchor=None, extra=""):
        self.used.add(key)
        fam, wt, _ = FONT_FILES[key]
        ls = f' letter-spacing="{tracking * size:.2f}"' if tracking else ""
        a = f' text-anchor="{anchor}"' if anchor else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-weight="{wt}" font-size="{size}"'
                 f' fill="{fill}"{ls}{a}{extra} xml:space="preserve">{esc(txt)}</text>')
        return measure(txt, key, size, tracking)

    def render(self) -> str:
        faces = "".join(
            f"@font-face{{font-family:'{FONT_FILES[k][0]}';font-weight:{FONT_FILES[k][1]};"
            f"src:url(data:font/woff2;base64,{font_b64(k)}) format('woff2')}}"
            for k in sorted(self.used)
        )
        style = (f"<style>{faces}.bl{{animation:bl 1.06s steps(1) infinite}}@keyframes bl{{50%{{opacity:0}}}}"
                 ".r{animation:rise .9s cubic-bezier(.2,.7,.3,1) both}"
                 "@keyframes rise{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}</style>")
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" '
                f'fill="none">{style}<defs>{"".join(self.defs)}</defs>{"".join(self.body)}</svg>')


def logo(s: Svg, x, y, size, t, cursor_blink=True, on="auto"):
    mark = t["mark"]
    word = t["text"]
    w1 = s.text(x, y, "~/", "mono600", size, mark)
    w2 = s.text(x + w1, y, "skurllex", "mono600", size, word)
    cx = x + w1 + w2 + size * 0.06
    cls = ' class="bl"' if cursor_blink else ""
    s.add(f'<rect x="{cx:.1f}" y="{y - size * 0.78:.1f}" width="{size * 0.5:.1f}" height="{size * 0.98:.1f}" fill="{mark}"{cls}/>')
    return cx + size * 0.5 - x


def label(s: Svg, x, y, num, title, t):
    s.text(x, y, f"{num} — {title}", "mono500", 13, t["accent"])


def grid(s: Svg, w, h, step, color, fade_id, cx=0.5, cy=0.35, r=0.75):
    s.defs.append(
        f'<radialGradient id="{fade_id}g" cx="{cx}" cy="{cy}" r="{r}"><stop offset="0" stop-color="#fff"/>'
        f'<stop offset=".7" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
        f'<mask id="{fade_id}" maskUnits="userSpaceOnUse" x="0" y="0" width="{w}" height="{h}">'
        f'<rect width="{w}" height="{h}" fill="url(#{fade_id}g)"/></mask>'
    )
    lines = "".join(f"M{x + .5} 0V{h}" for x in range(step, int(w), step))
    lines += "".join(f"M0 {y + .5}H{w}" for y in range(step, int(h), step))
    s.add(f'<path d="{lines}" stroke="{color}" mask="url(#{fade_id})"/>')


def dots(s: Svg, x0, y0, w, h, step, color, op):
    pts = "".join(f'<circle cx="{x}" cy="{y}" r="1.1"/>' for x in range(int(x0) + step // 2, int(x0 + w), step)
                  for y in range(int(y0) + step // 2, int(y0 + h), step))
    s.add(f'<g fill="{color}" opacity="{op}">{pts}</g>')


def glows(s: Svg, blobs, op, uid):
    s.defs.append(f'<filter id="{uid}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="80"/></filter>')
    g = []
    for (cx, cy, r, col, dx, dy, dur) in blobs:
        g.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;{dx} {dy};0 0" dur="{dur}s" '
            f'repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/></circle>'
        )
    s.add(f'<g filter="url(#{uid})" opacity="{op}">{"".join(g)}</g>')


def pill(s: Svg, x, y, txt, t, kind="outline", key="sans600", size=13):
    pad, h = 12, 28
    w = measure(txt, key, size) + pad * 2
    styles = {
        "outline": (t["pill_bg"], t["border"], t["text"]),
        "soft": (t["soft"], t["soft"], t["soft_text"]),
        "solid": (BRAND["blue"], BRAND["blue"], BRAND["white"]),
        "success": (BRAND["success"], BRAND["success"], BRAND["white"]),
    }
    bg, stroke, fg = styles[kind]
    s.add(f'<rect x="{x + .5:.1f}" y="{y + .5:.1f}" width="{w - 1:.1f}" height="{h - 1}" rx="{(h - 1) / 2}" fill="{bg}" stroke="{stroke}"/>')
    s.text(x + pad, y + 18.5, txt, key, size, fg)
    return w


def card(s: Svg, x, y, w, h, fill, stroke=None, r=24):
    st = f' stroke="{stroke}"' if stroke else ""
    s.add(f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="{r}" fill="{fill}"{st}/>')


def rise(delay: float) -> str:
    return f'<g class="r" style="animation-delay:{delay:.2f}s">'


def win(t0, t1, T, f=0.2, attr="opacity", lo="0", hi="1"):
    kt = [0, t0 / T, (t0 + f) / T, (t1 - f) / T, t1 / T, 1]
    return (f'<animate attributeName="{attr}" values="{lo};{lo};{hi};{hi};{lo};{lo}" '
            f'keyTimes="{";".join(f"{k:.4f}" for k in kt)}" dur="{T}s" repeatCount="indefinite"/>')


_UID = [0]


def uid(prefix="u"):
    _UID[0] += 1
    return f"{prefix}{_UID[0]}"


def typed(s: Svg, x, y, txt, key, size, fill, t0, T, speed=0.035, cursor=None, hold_until=None):
    w = measure(txt, key, size)
    d = max(0.15, len(txt) * speed)
    cid = uid("ty")
    end = (t0 + d) / T
    s.defs.append(f'<clipPath id="{cid}"><rect x="{x - 1}" y="{y - size}" height="{size * 1.4}" width="0">'
                  f'<animate attributeName="width" values="0;0;{w + 2:.1f};{w + 2:.1f}" keyTimes="0;{t0 / T:.4f};{end:.4f};1" '
                  f'dur="{T}s" repeatCount="indefinite"/></rect></clipPath>')
    sub = Svg(1, 1)
    sub.text(x, y, txt, key, size, fill)
    s.used.add(key)
    s.add(f'<g clip-path="url(#{cid})">{"".join(sub.body)}</g>')
    if cursor:
        cw = size * 0.58
        h1 = hold_until if hold_until else t0 + d + 0.6
        s.add(f'<rect x="{x}" y="{y - size * 0.8:.1f}" width="{cw:.1f}" height="{size * 1.0:.1f}" fill="{cursor}" opacity="0">'
              f'<animate attributeName="x" values="{x};{x};{x + w + 2:.1f};{x + w + 2:.1f}" keyTimes="0;{t0 / T:.4f};{end:.4f};1" '
              f'dur="{T}s" repeatCount="indefinite"/>{win(max(0.01, t0 - 0.05), min(T - 0.01, h1), T, 0.01)}</rect>')
    return w


def wrap(txt: str, key: str, size: float, max_w: float) -> list[str]:
    lines, cur = [], ""
    for word in txt.split(" "):
        test = f"{cur} {word}".strip()
        if measure(test, key, size) <= max_w:
            cur = test
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


# ---------------------------------------------------------------- hero

TOPICS = ["TypeScript.", "Next.js.", "FiveM.", "DevOps.", "Lua."]


def code_window(s: Svg, x, y, w, h, t, theme, T):
    dark_bg = BRAND["navy"] if theme == "light" else "#0B1424"
    s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="{dark_bg}" stroke="{"#24344F"}"/>')
    for i, c in enumerate(("#3A4A66", "#3A4A66", "#3A4A66")):
        s.add(f'<circle cx="{x + 24 + i * 16}" cy="{y + 24}" r="4.5" fill="{c}"/>')
    s.text(x + w - 22, y + 29, "plan.ts", "mono400", 12, "#7D8AA3", anchor="end")
    s.add(f'<path d="M{x} {y + 47.5}H{x + w}" stroke="#24344F"/>')
    lx, ly, lh = x + 24, y + 84, 26
    kw, fn, st, mu = "#7FA2FF", "#FFFFFF", "#A9C1FF", "#7D8AA3"
    g = []
    s.add(f'<g>{win(0.3, T - 0.4, T, 0.3)}')
    s.text(lx - 2, ly, "1", "mono400", 13, "#3A4A66", anchor="end")
    typed(s, lx + 14, ly, "const plan = await findPlan(goal)", "mono400", 14, fn, 0.6, T, 0.04, cursor=BRAND["blue_light"], hold_until=2.05)
    s.text(lx - 2, ly + lh, "2", "mono400", 13, "#3A4A66", anchor="end")
    typed(s, lx + 14, ly + lh, "plan.start()", "mono400", 14, kw, 2.2, T, 0.04, cursor=BRAND["blue_light"], hold_until=2.8)
    s.text(lx - 2, ly + 2 * lh, "3", "mono400", 13, "#3A4A66", anchor="end")
    typed(s, lx + 14, ly + 2 * lh, "// Lektion 01 · Server Actions", "mono400", 14, mu, 2.9, T, 0.03,
          cursor=BRAND["blue_light"], hold_until=T - 0.45)
    s.add("</g>")


def toast(s: Svg, x, y, t, theme, t0, t1, T, value="+20", text="Lektion abgeschlossen"):
    w = 26 + measure(value, "mono600", 14) + 12 + measure(text, "sans600", 15) + 22
    fill = BRAND["white"] if theme == "light" else BRAND["navy2"]
    stroke = BRAND["border"] if theme == "light" else "#2C3D5C"
    s.defs.append('<filter id="tsh" x="-20%" y="-50%" width="140%" height="220%"><feDropShadow dx="0" dy="10" stdDeviation="12" '
                  'flood-color="#0F1B2D" flood-opacity=".16"/></filter>')
    s.add(f'<g opacity="0">{win(t0, t1, T, 0.25)}'
          f'<animateTransform attributeName="transform" type="translate" values="0 14;0 14;0 0;0 0" '
          f'keyTimes="0;{t0 / T:.4f};{(t0 + 0.35) / T:.4f};1" dur="{T}s" repeatCount="indefinite" calcMode="spline" '
          f'keySplines="0 0 1 1;.2 .7 .3 1;0 0 1 1"/>'
          f'<rect x="{x}" y="{y}" width="{w:.0f}" height="48" rx="14" fill="{fill}" stroke="{stroke}" filter="url(#tsh)"/>')
    s.add(f'<rect x="{x + 14}" y="{y + 12}" width="{measure(value, "mono600", 14) + 14:.0f}" height="24" rx="8" fill="{BRAND["success"]}"/>')
    s.text(x + 21, y + 29, value, "mono600", 14, BRAND["white"])
    s.text(x + 26 + measure(value, "mono600", 14) + 14, y + 30, text, "sans600", 15, t["text"])
    s.add("</g>")
    return w


def build_hero(t, theme):
    W, H = 1200, 520
    s = Svg(W, H)
    card(s, 0, 0, W, H, t["bg"], t["border"], r=28)
    s.defs.append(f'<clipPath id="hc"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="27"/></clipPath>')
    s.add('<g clip-path="url(#hc)">')
    if theme == "light":
        glows(s, [(1010, 110, 190, BRAND["blue_light"], -90, 60, 14), (860, 300, 120, BRAND["blue"], 70, -50, 17),
                  (140, 470, 150, BRAND["violet"], 110, -40, 15)], 0.42, "hg")
        step = 64
    else:
        glows(s, [(1020, 80, 220, BRAND["blue"], -100, 70, 14), (820, 300, 140, BRAND["violet"], 70, -50, 17),
                  (80, 500, 180, "#5B4BD6", 120, -40, 15)], 0.55, "hg")
        step = 56
    grid(s, W, H, step, t["grid"], "hm", cx=0.4, cy=0.45, r=0.85)
    hl = BRAND["blue"] if theme == "light" else BRAND["blue_light"]
    s.defs.append(f'<linearGradient id="sweepv" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{hl}" stop-opacity="0"/>'
                  f'<stop offset=".5" stop-color="{hl}" stop-opacity=".5"/><stop offset="1" stop-color="{hl}" stop-opacity="0"/></linearGradient>'
                  f'<linearGradient id="sweeph" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{hl}" stop-opacity="0"/>'
                  f'<stop offset=".5" stop-color="{hl}" stop-opacity=".45"/><stop offset="1" stop-color="{hl}" stop-opacity="0"/></linearGradient>')
    xs = [step * k for k in range(1, W // step)]
    ys = [step * k for k in range(1, H // step)]
    s.add(f'<g mask="url(#hm)"><rect x="{xs[3] - 0.5}" y="-180" width="1.5" height="180" fill="url(#sweepv)">'
          f'<animate attributeName="y" values="-180;{H};{H}" keyTimes="0;.45;1" dur="9s" repeatCount="indefinite"/>'
          f'<animate attributeName="x" values="{xs[3] - .5};{xs[3] - .5};{xs[11] - .5};{xs[11] - .5}" keyTimes="0;.5;.5001;1" dur="18s" '
          f'repeatCount="indefinite" calcMode="discrete"/></rect>'
          f'<rect x="-260" y="{ys[2] - 0.5}" width="260" height="1.5" fill="url(#sweeph)">'
          f'<animate attributeName="x" values="-260;-260;{W};{W}" keyTimes="0;.35;.8;1" dur="11s" repeatCount="indefinite"/></rect></g>')
    s.add("</g>")

    s.add(rise(0.05))
    logo(s, 72, 92, 26, t)
    s.text(W - 72, 92, f"{PROFILE['city'].lower()} · {PROFILE['site']}", "mono400", 14, t["muted"], anchor="end")
    s.add("</g>")

    size, tr = 62, -0.05
    base1, base2 = 252, 324
    lerne = "Lerne "
    lw = measure(lerne, "sans800", size, tr) + tr * size
    s.add(rise(0.2))
    s.text(72, base1, lerne, "sans800", size, t["text"], tracking=tr)
    s.add("</g>" + rise(0.32))
    l2 = s.text(72, base2, "Aus echten Projekten.", "sans800", size, t["text"], tracking=tr)
    s.add("</g>")

    n, hold, move = len(TOPICS), 2.2, 0.45
    period = hold + move
    total = n * period
    s.defs.append(f'<clipPath id="tc"><rect x="{72 + lw - 4}" y="{base1 - size * 0.95}" width="560" height="{size * 1.17}"/></clipPath>')
    words = []
    hh = size * 1.3
    for i, word in enumerate(TOPICS):
        if i == 0:
            vals = f"0 0;0 0;0 {-hh};0 {-hh};0 {hh};0 0"
            kts = f"0;{hold / total:.4f};{(hold + move) / total:.4f};{(total - move - 0.001) / total:.4f};{(total - move) / total:.4f};1"
        else:
            a, b = i * period - move, i * period
            vals = f"0 {hh};0 {hh};0 0;0 0;0 {-hh};0 {-hh}"
            kts = f"0;{a / total:.4f};{b / total:.4f};{(b + hold) / total:.4f};{(b + hold + move) / total:.4f};1"
        sub = Svg(1, 1)
        sub.text(72 + lw, base1, word, "sans800", size, t["accent"], tracking=tr)
        words.append(f'<g><animateTransform attributeName="transform" type="translate" values="{vals}" keyTimes="{kts}" '
                     f'dur="{total}s" repeatCount="indefinite" calcMode="spline" '
                     f'keySplines="0 0 1 1;.6 0 .2 1;0 0 1 1;0 0 1 1;.6 0 .2 1"/>{"".join(sub.body)}</g>')
    s.add(rise(0.2) + f'<g clip-path="url(#tc)">{"".join(words)}</g></g>')

    cx = 72 + l2 + 56
    cw = W - 72 - cx
    T = 8
    s.add(rise(0.45))
    code_window(s, cx, 150, cw, 182, t, theme, T)
    s.add("</g>")
    toast(s, cx + cw - 300, 300, t, theme, 3.6, 7.4, T)

    s.add(rise(0.55))
    s.text(72, 440, "Kurs · Lernplattform · Coaching · Code-Reviews", "sans400", 16, t["muted"])
    lab = "Lektionen aus Produktion"
    dot_x = W - 72 - measure(lab, "mono500", 13) - 14
    s.add(f'<circle cx="{dot_x}" cy="435.5" r="4" fill="{BRAND["success"]}"/>'
          f'<circle cx="{dot_x}" cy="435.5" r="4" fill="none" stroke="{BRAND["success"]}">'
          f'<animate attributeName="r" values="4;11" dur="2s" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" values=".6;0" dur="2s" repeatCount="indefinite"/></circle>')
    s.text(W - 72, 440, lab, "mono500", 13, t["muted"], anchor="end")
    s.add("</g>")
    return s.render()


# ---------------------------------------------------------------- shared

def heading(s: Svg, num, title, headline, t, delay=0.0):
    s.add(rise(delay))
    label(s, 0, 18, num, title, t)
    s.text(0, 66, headline, "sans800", 40, t["text"], tracking=-0.045)
    s.add("</g>")


def pulse_dot(s: Svg, x, y, color, r=4):
    s.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>'
          f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{color}">'
          f'<animate attributeName="r" values="{r};{r * 2.8}" dur="2s" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" values=".7;0" dur="2s" repeatCount="indefinite"/></circle>')


# ---------------------------------------------------------------- 01 über mich

VALUES = [
    ("Wert 01", "Präzision statt Annahmen.", "Jede Aussage ist belegbar. Keine Garantien, keine erfundenen Zahlen."),
    ("Wert 02", "Lieber richtig als schnell.", "Sauberer Code, klare Schichten, strikte Typen, auch im Unterricht."),
    ("Wert 03", "Aus echten Projekten.", "Jede Lektion stammt aus einem System, das wirklich läuft."),
]


def build_about(t, theme):
    W = 1000
    cw, gap, top, ch = 322, 17, 200, 312
    s = Svg(W, top + ch + 2)
    heading(s, "01", "Über mich", "Wissen aus Produktion. Für Entwickler.", t)
    body = ("Ich bin Mario, Entwickler aus Hannover. Ich leite die Entwicklung von District Roleplay und baue mit "
            "edify studio Software für Kunden. Was ich dort in Produktion lerne, gebe ich auf skurllex.com weiter.")
    s.add(rise(0.12))
    for i, line in enumerate(wrap(body, "sans400", 18, 900)):
        s.text(0, 112 + i * 29, line, "sans400", 18, t["muted"])
    s.add("</g>")
    fills = [(t["v1"], t["border"] if theme == "dark" else None, t["v1_text"], t["v1_muted"], t["v1_label"]),
             (BRAND["blue"], None, BRAND["white"], "#DCE5FF", "#DCE5FF"),
             (t["v3"], t["border"] if theme == "light" else None, t["v3_text"], t["v3_muted"], t["accent"])]
    T = 6
    for i, ((lab, head, txt), (fill, stroke, fg, mut, labc)) in enumerate(zip(VALUES, fills)):
        x = i * (cw + gap)
        s.add(rise(0.25 + i * 0.14))
        card(s, x, top, cw, ch, fill, stroke, r=24)
        if i == 1:
            cid = uid("vc")
            s.defs.append(f'<clipPath id="{cid}"><rect x="{x}" y="{top}" width="{cw}" height="{ch}" rx="24"/></clipPath>')
            s.add(f'<g clip-path="url(#{cid})">')
            dots(s, x, top, cw, ch, 22, BRAND["white"], 0.18)
            glows(s, [(x + cw - 40, top + 40, 90, BRAND["blue_light"], -60, 50, 9), (x + 40, top + ch, 90, BRAND["violet"], 60, -40, 11)],
                  0.6, uid("vg"))
            s.add("</g>")
        s.text(x + 32, top + 48, lab, "mono500", 13, labc)
        for j, ln in enumerate(wrap(head, "sans800", 26, cw - 64)):
            s.text(x + 32, top + 96 + j * 30, ln, "sans800", 26, fg, tracking=-0.03)
        for j, ln in enumerate(wrap(txt, "sans400", 16, cw - 64)):
            s.text(x + 32, top + 176 + j * 25, ln, "sans400", 16, mut)
        by = top + ch - 34
        line_col = "#ffffff22" if i < 2 or theme == "dark" else BRAND["border"]
        s.add(f'<path d="M{x + 32} {by - 28.5}H{x + cw - 32}" stroke="{line_col}"/>')
        if i == 0:
            typed(s, x + 32, by, '$ grep -ri "garantiert"', "mono400", 13, t["v1_muted"], 0.5, T, 0.045, cursor=t["v1_label"], hold_until=1.6)
            s.add(f'<g opacity="0">{win(1.7, T - 0.3, T, 0.2)}')
            s.text(x + cw - 32, by, "0 Treffer", "mono600", 13, t["v1_label"], anchor="end")
            s.add("</g>")
        elif i == 1:
            s.text(x + 32, by, '"strict": true', "mono400", 13, "#DCE5FF")
            pw = measure("aktiv", "sans600", 12) + 20
            s.add(f'<g opacity="0">{win(1.0, T - 0.3, T, 0.2)}'
                  f'<rect x="{x + cw - 32 - pw:.0f}" y="{by - 17}" width="{pw:.0f}" height="24" rx="12" fill="{BRAND["white"]}"/>')
            s.text(x + cw - 32 - pw + 10, by, "aktiv", "sans600", 12, BRAND["blue"])
            s.add("</g>")
        else:
            pulse_dot(s, x + 36, by - 4.5, BRAND["success"])
            s.text(x + 50, by, "läuft in Produktion", "mono400", 13, mut)
        s.add("</g>")
    return s.render()


# ---------------------------------------------------------------- 02 projekte

PROJECTS = [
    ("01", "District Roleplay", ("In Entwicklung", "soft"),
     "FiveM-Roleplay-Plattform, deren Entwicklung ich leite. TypeScript-Server, Lua-Clients, Vue-NUI und ein Next.js-Webpanel in einem Monorepo.",
     ["TypeScript", "Lua", "Vue 3", "Prisma"], "log"),
    ("02", "skurllex.com", ("Lernplattform", "solid"),
     "Kurse, Coaching und Code-Reviews. Jede Lektion stammt aus einem System, das wirklich läuft.",
     ["Kurse", "Coaching", "Code-Reviews"], "progress"),
    ("03", "edify studio", ("Studio", "soft"),
     "Mein Solo-Softwarestudio. Web, SaaS, Mobile und Game-Dev, von einer Person gebaut und betreut.",
     ["Next.js", "SaaS", "DevOps"], "pipeline"),
    ("04", "FiveM-Scripts", ("Abgeschlossen", "success"),
     "Über 2.000 Server haben meine Scripts genutzt. Heute fließt diese Erfahrung in District und in die Kurse.",
     ["Lua", "ESX", "QBCore", "ox_lib"], "diff"),
]


def build_projects_label(t, theme):
    s = Svg(1000, 82)
    heading(s, "02", "Projekte", "Echte Systeme. Echter Betrieb.", t)
    return s.render()


def visual(s: Svg, kind, x, y, w, h, t, theme):
    box = t["surface"] if theme == "light" else "#1B2A44"
    T = 7
    if kind == "diff":
        s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{BRAND["navy"] if theme == "light" else "#0B1424"}"/>')
        red, green = "#F87171", "#4ADE80"
        ly = y + 38
        s.add(f'<g>{win(0.3, T - 0.3, T, 0.25)}')
        s.text(x + 18, ly, "- const data: any = await res.json()", "mono400", 13, red)
        lw = measure("- const data: any = await res.json()", "mono400", 13)
        s.add(f'<rect x="{x + 18}" y="{ly - 5}" height="1.5" width="0" fill="{red}">'
              f'<animate attributeName="width" values="0;0;{lw:.0f};{lw:.0f}" keyTimes="0;{1.0 / T:.4f};{1.6 / T:.4f};1" dur="{T}s" repeatCount="indefinite"/></rect>')
        typed(s, x + 18, ly + 28, "+ const data = Schema.parse(await res.json())", "mono400", 13, green, 1.9, T, 0.03,
              cursor=green, hold_until=3.4)
        s.add(f'<g opacity="0">{win(3.6, T - 0.3, T, 0.2)}')
        s.text(x + w - 16, y + h - 14, "Kein any. Nie.", "sans700", 13, "#FFFFFF", anchor="end")
        s.add("</g></g>")
        return
    s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{box}"/>')
    if kind == "log":
        lines = [("ensure district-core", "Ressource gestartet"), ("pg-boss · pulse", "Jobs verbunden"), ("webpanel", "online")]
        for i, (a, b) in enumerate(lines):
            t0 = 0.4 + i * 0.9
            ly = y + 28 + i * 24
            s.add(f'<g opacity="0">{win(t0, T - 0.4, T, 0.2)}')
            s.add(f'<circle cx="{x + 20}" cy="{ly - 4.5}" r="3.5" fill="{BRAND["success"]}"/>')
            s.text(x + 32, ly, a, "mono400", 12.5, t["text"])
            s.text(x + w - 16, ly, b, "mono400", 12.5, t["muted"], anchor="end")
            s.add("</g>")
    elif kind == "progress":
        s.text(x + 16, y + 30, "Lektion 03 · Server Actions", "mono500", 12.5, t["text"])
        frames_p = ["380 P", "400 P"]
        s.add(f'<g>{win(0.01, 3.4, T, 0.01)}')
        s.text(x + w - 16, y + 30, frames_p[0], "mono600", 12.5, t["accent"], anchor="end")
        s.add(f'</g><g opacity="0">{win(3.4, T - 0.01, T, 0.01)}')
        s.text(x + w - 16, y + 30, frames_p[1], "mono600", 12.5, t["accent"], anchor="end")
        s.add("</g>")
        bw = w - 32
        track = BRAND["border"] if theme == "light" else "#24344F"
        s.add(f'<rect x="{x + 16}" y="{y + 44}" width="{bw}" height="8" rx="4" fill="{track}"/>'
              f'<rect x="{x + 16}" y="{y + 44}" width="0" height="8" rx="4" fill="{BRAND["blue"]}">'
              f'<animate attributeName="width" values="{bw * 0.2:.0f};{bw * 0.2:.0f};{bw:.0f};{bw:.0f}" '
              f'keyTimes="0;{0.4 / T:.4f};{3.2 / T:.4f};1" dur="{T}s" repeatCount="indefinite" calcMode="spline" '
              f'keySplines="0 0 1 1;.4 0 .2 1;0 0 1 1"/></rect>')
        steps_lbl = "Video · Übung · Review"
        s.text(x + 16, y + h - 14, steps_lbl, "sans400", 12.5, t["muted"])
        pw = measure("+20 P", "mono600", 12) + 18
        s.add(f'<g opacity="0">{win(3.3, T - 0.4, T, 0.2)}'
              f'<rect x="{x + w - 16 - pw:.0f}" y="{y + h - 32}" width="{pw:.0f}" height="24" rx="8" fill="{BRAND["success"]}"/>')
        s.text(x + w - 16 - pw + 9, y + h - 15, "+20 P", "mono600", 12, BRAND["white"])
        s.add("</g>")
    elif kind == "pipeline":
        names = ["Build", "Test", "Deploy"]
        n = len(names)
        seg = (w - 32) / n
        cy = y + 34
        track = BRAND["border"] if theme == "light" else "#24344F"
        s.add(f'<path d="M{x + 16 + 14} {cy}H{x + w - 16 - 14}" stroke="{track}" stroke-width="2"/>'
              f'<rect x="{x + 30}" y="{cy - 1}" width="0" height="2" fill="{BRAND["blue"]}">'
              f'<animate attributeName="width" values="0;0;{w - 60:.0f};{w - 60:.0f}" keyTimes="0;{0.4 / T:.4f};{3.4 / T:.4f};1" '
              f'dur="{T}s" repeatCount="indefinite"/></rect>')
        for i, nm in enumerate(names):
            px = x + 16 + 14 + i * (w - 60) / (n - 1)
            t_on = 0.4 + i * 1.5
            s.add(f'<circle cx="{px:.0f}" cy="{cy}" r="11" fill="{box}" stroke="{track}" stroke-width="2"/>')
            s.add(f'<g opacity="0">{win(t_on, T - 0.3, T, 0.15)}<circle cx="{px:.0f}" cy="{cy}" r="11" fill="{BRAND["success"]}"/>'
                  f'<path d="M{px - 4.5:.1f} {cy}l3 3 6-6.5" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>')
            s.text(px, cy + 30, nm, "mono500", 12, t["muted"], anchor="middle")
        s.add(f'<g opacity="0">{win(3.6, T - 0.3, T, 0.2)}')
        pulse_dot(s, x + w - 16 - measure("live", "mono600", 12) - 10, y + h - 16.5, BRAND["success"], 3.5)
        s.text(x + w - 16, y + h - 12, "live", "mono600", 12, t["text"], anchor="end")
        s.add("</g>")


def build_project(t, theme, p, idx=0):
    num, title, (badge, kind), desc, tags, vis = p
    W, H = 492, 400
    s = Svg(W, H)
    s.add(rise(0.1 + idx * 0.1))
    card(s, 0, 0, W, H, t["card"], t["border"], r=24)
    s.text(32, 48, f"{num} —", "mono500", 13, t["accent"])
    bw = measure(badge, "sans600", 13) + 24
    pill(s, W - 32 - bw, 28, badge, t, kind)
    s.text(32, 96, title, "sans700", 24, t["text"], tracking=-0.03)
    for i, ln in enumerate(wrap(desc, "sans400", 16, W - 64)):
        s.text(32, 134 + i * 25, ln, "sans400", 16, t["muted"])
    visual(s, vis, 32, 214, W - 64, 104, t, theme)
    x = 32
    for tag in tags:
        x += pill(s, x, H - 58, tag, t, "outline", "sans600", 13) + 8
    s.add("</g>")
    return s.render()


# ---------------------------------------------------------------- 03 aktivität

def load_calendar():
    path = ROOT / "data" / "contributions.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return data["weeks"], data["total"], True
    rng = random.Random(42)
    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday() + 1 + 52 * 7)
    weeks = []
    for w in range(53):
        week = []
        for d in range(7):
            day = start + dt.timedelta(days=w * 7 + d)
            if day > today:
                continue
            base = 0.55 + 0.45 * math.sin(w / 6.0)
            n = 0 if rng.random() > base else int(rng.expovariate(0.22))
            week.append({"date": day.isoformat(), "count": n})
        weeks.append(week)
    return weeks, sum(d["count"] for wk in weeks for d in wk), False


def streaks(weeks):
    days = [d["count"] for wk in weeks for d in wk]
    best = run = 0
    for c in days:
        run = run + 1 if c else 0
        best = max(best, run)
    cur = 0
    for c in reversed(days):
        if not c:
            break
        cur += 1
    return cur, best


MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]


def counter(s: Svg, x, y, value: int, key, size, fill, suffix="", start=0.3, dur=1.4, steps=14, anchor=None):
    vals = [round(value * (1 - (1 - k / steps) ** 3)) for k in range(steps + 1)]
    fmt = lambda v: f"{v:,}".replace(",", ".") + suffix
    for k, v in enumerate(vals):
        t0 = start + dur * k / steps
        t1 = start + dur * (k + 1) / steps
        if k == steps:
            s.add(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t0:.2f}s" fill="freeze"/>')
        elif k == 0:
            s.add(f'<g><set attributeName="opacity" to="0" begin="{t1:.2f}s" fill="freeze"/>')
        else:
            s.add(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t0:.2f}s"/>'
                  f'<set attributeName="opacity" to="0" begin="{t1:.2f}s" fill="freeze"/>')
        s.text(x, y, fmt(v), key, size, fill, anchor=anchor)
        s.add("</g>")
    return measure(fmt(value), key, size)


def build_activity(t, theme, cal):
    weeks, total, live = cal
    W, H = 1000, 380
    s = Svg(W, H)
    heading(s, "03", "Aktivität", "Jeden Tag ein Commit weiter.", t)
    top = 100
    s.add(rise(0.15))
    card(s, 0, top, W, H - top, t["card"], t["border"], r=24)
    counts = sorted(d["count"] for wk in weeks for d in wk if d["count"])
    q = [counts[int(len(counts) * f)] if counts else 1 for f in (0.25, 0.5, 0.75)]
    level = lambda c: 0 if not c else 1 + sum(c > x for x in q)
    x0, y0, step = 80, top + 66, 16.4
    last = None
    for wi, wk in enumerate(weeks):
        if not wk:
            continue
        m = dt.date.fromisoformat(wk[0]["date"]).month
        if m != last and wi < len(weeks) - 2:
            s.text(x0 + wi * step - 5, y0 - 18, MONTHS[m - 1], "mono400", 11, t["muted"])
            last = m
    for d, name in ((0, "Mo"), (2, "Mi"), (4, "Fr")):
        s.text(32, y0 + d * step + 4, name, "mono400", 11, t["muted"])
    cells = []
    last_cell = None
    for wi, wk in enumerate(weeks):
        for day in wk:
            dow = dt.date.fromisoformat(day["date"]).weekday()
            cx, cy = x0 + wi * step, y0 + dow * step
            delay = 0.3 + wi * 0.022 + dow * 0.01
            cells.append(f'<rect x="{cx - 6:.1f}" y="{cy - 6:.1f}" width="12" height="12" rx="3.5" fill="{t["heat"][level(day["count"])]}" '
                         f'opacity="0"><set attributeName="opacity" to="1" begin="{delay:.2f}s" fill="freeze"/></rect>')
            last_cell = (cx, cy, level(day["count"]))
    s.add("".join(cells))
    if last_cell:
        cx, cy, lv = last_cell
        col = t["accent"]
        s.add(f'<rect x="{cx - 6:.1f}" y="{cy - 6:.1f}" width="12" height="12" rx="3.5" fill="none" stroke="{col}" stroke-width="1.5">'
              f'<animate attributeName="opacity" values="1;.2;1" dur="1.8s" repeatCount="indefinite"/></rect>')
        s.add(f'<rect x="{cx - 6:.1f}" y="{cy - 6:.1f}" width="12" height="12" rx="3.5" fill="none" stroke="{col}">'
              f'<animate attributeName="x" values="{cx - 6:.1f};{cx - 12:.1f}" dur="1.8s" repeatCount="indefinite"/>'
              f'<animate attributeName="y" values="{cy - 6:.1f};{cy - 12:.1f}" dur="1.8s" repeatCount="indefinite"/>'
              f'<animate attributeName="width" values="12;24" dur="1.8s" repeatCount="indefinite"/>'
              f'<animate attributeName="height" values="12;24" dur="1.8s" repeatCount="indefinite"/>'
              f'<animate attributeName="rx" values="3.5;7" dur="1.8s" repeatCount="indefinite"/>'
              f'<animate attributeName="opacity" values=".7;0" dur="1.8s" repeatCount="indefinite"/></rect>')
    cur, best = streaks(weeks)
    fy = H - 40
    s.add(f'<path d="M32 {fy - 30.5}H{W - 32}" stroke="{t["border"]}"/>')
    x = 32
    for val, suf, lab in ((total, "", "Beiträge im letzten Jahr"), (best, " Tage", "längste Serie"), (cur, " Tage", "aktuelle Serie")):
        x += counter(s, x, fy, val, "mono600", 14, t["text"], suf, start=0.6, dur=1.5) + 8
        x += s.text(x, fy, lab, "sans400", 15, t["muted"]) + 32
    lx = W - 32 - measure("mehr", "mono400", 11) - 8
    s.text(W - 32, fy, "mehr", "mono400", 11, t["muted"], anchor="end")
    for i in range(4, -1, -1):
        s.add(f'<rect x="{lx - 12}" y="{fy - 11}" width="12" height="12" rx="3.5" fill="{t["heat"][i]}"/>')
        lx -= 16
    s.text(lx - 4, fy, "weniger", "mono400", 11, t["muted"], anchor="end")
    if not live:
        s.text(W - 32, top + 34, "Vorschau-Daten", "mono400", 11, t["muted"], anchor="end")
    s.add("</g>")
    return s.render()


# ---------------------------------------------------------------- 04 stack

STACK = [
    ("Produkt", ["TypeScript", "React", "Next.js", "Tailwind", "Vue 3"]),
    ("Backend", ["Node.js", "Prisma", "Drizzle", "PostgreSQL", "WebSockets"]),
    ("FiveM", ["Lua", "ESX", "QBCore", "ox_lib", "NUI"]),
    ("Infra", ["Linux", "Docker", "Hetzner", "Coolify", "Dokploy", "Cloudflare"]),
    ("KI", ["Claude Code", "MCP", "OpenAI", "ElevenLabs"]),
]


def build_stack(t, theme):
    W = 1000
    row = 60
    top = 100
    H = top + 24 + row * len(STACK) + 12
    s = Svg(W, H)
    heading(s, "04", "Stack", "Werkzeuge, die täglich laufen.", t)
    s.add(rise(0.1))
    card(s, 0, top, W, H - top, t["card"], t["border"], r=24)
    s.add("</g>")
    all_pills = []
    for i, (k, items) in enumerate(STACK):
        y = top + 24 + i * row
        s.add(rise(0.2 + i * 0.1))
        if i:
            s.add(f'<path d="M32 {y - 0.5}H{W - 32}" stroke="{t["border"]}"/>')
        s.text(32, y + 35, f"0{i + 1}", "mono500", 13, t["accent"])
        s.text(72, y + 36, k, "sans700", 17, t["text"], tracking=-0.02)
        x = 200
        for it in items:
            w = pill(s, x, y + 16, it, t, "outline")
            all_pills.append((x, y + 16, w, it))
            x += w + 8
        s.add("</g>")
    step, T = 0.42, None
    T = round(len(all_pills) * step + 1.2, 2)
    for j, (x, y, w, it) in enumerate(all_pills):
        t0 = 0.6 + j * step
        t1 = t0 + 0.9
        if t1 >= T:
            continue
        s.add(f'<g opacity="0">{win(t0, t1, T, 0.18)}'
              f'<rect x="{x + .5:.1f}" y="{y + .5}" width="{w - 1:.1f}" height="27" rx="13.5" fill="{BRAND["blue"]}"/>')
        s.text(x + 12, y + 18.5, it, "sans600", 13, BRAND["white"])
        s.add("</g>")
    return s.render()


# ---------------------------------------------------------------- 05 kontakt

def build_contact(t, theme):
    W, H = 1000, 330
    s = Svg(W, H)
    s.defs.append(f'<clipPath id="cc"><rect x="0" y="0" width="{W}" height="{H}" rx="32"/></clipPath>')
    s.add(rise(0.05))
    card(s, 0, 0, W, H, BRAND["blue"], None, r=32)
    s.add('<g clip-path="url(#cc)">')
    glows(s, [(900, 40, 160, BRAND["blue_light"], -80, 50, 12), (760, 320, 140, BRAND["violet"], 70, -40, 15)], 0.55, "cg")
    step = 22
    T = 4.0
    cols = []
    for ci, cx in enumerate(range(step // 2, W, step)):
        pts = "".join(f'<circle cx="{cx}" cy="{cy}" r="1.1"/>' for cy in range(step // 2, H, step))
        d = (ci * 0.045) % T
        cols.append(f'<g opacity=".18"><animate attributeName="opacity" values=".18;.18;.6;.18;.18" keyTimes="0;.0;.12;.3;1" '
                    f'dur="{T}s" begin="{d:.2f}s" repeatCount="indefinite"/>{pts}</g>')
    s.add(f'<g fill="{BRAND["white"]}">{"".join(cols)}</g>')
    s.add("</g>")
    s.text(56, 70, "05 — Kontakt", "mono500", 13, "#DCE5FF")
    s.text(56, 132, "Gute Ideen.", "sans800", 48, BRAND["white"], tracking=-0.045)
    s.text(56, 184, "Fangen mit Hallo an.", "sans800", 48, BRAND["white"], tracking=-0.045)
    s.text(56, 226, "Ich schaue mir jede Anfrage selbst an. Für Projekte, Coaching und Code-Reviews.", "sans400", 17, "#DCE5FF")
    btn = "Schreib mir"
    bw = measure(btn, "sans600", 17) + 32 + 44
    s.add(f'<rect x="56" y="250" width="{bw:.0f}" height="56" rx="14" fill="{BRAND["navy"]}"/>')
    s.defs.append(f'<clipPath id="bt"><rect x="60" y="256" width="{bw - 60:.0f}" height="44"/></clipPath>')
    TB = 4.5
    roll = (f'<animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 -36;0 36;0 0;0 0" '
            f'keyTimes="0;{3.2 / TB:.4f};{3.5 / TB:.4f};{3.5001 / TB:.4f};{3.8 / TB:.4f};1" dur="{TB}s" repeatCount="indefinite"/>')
    sub = Svg(1, 1)
    sub.text(72, 284, btn, "sans600", 17, BRAND["white"])
    s.used.add("sans600")
    s.add(f'<g clip-path="url(#bt)"><g>{roll}{"".join(sub.body)}</g></g>')
    s.add(f'<rect x="{56 + bw - 48:.0f}" y="258" width="40" height="40" rx="10" fill="#26344D"/>')
    s.add(f'<g><animateTransform attributeName="transform" type="translate" values="0 0;4 0;0 0" dur="1.6s" repeatCount="indefinite" '
          f'calcMode="spline" keySplines=".4 0 .2 1;.4 0 .2 1"/>')
    s.text(56 + bw - 28, 285, "→", "sans600", 18, BRAND["white"], anchor="middle")
    s.add("</g>")
    mx = 56 + bw + 24
    mw = s.text(mx, 284, PROFILE["mail"], "mono500", 15, BRAND["white"])
    s.add(f'<rect x="{mx + mw + 3:.1f}" y="{284 - 13}" width="8" height="16" fill="{BRAND["white"]}" class="bl"/>')
    s.add("</g>")
    return s.render()




# ---------------------------------------------------------------- cta

def build_cta(t, theme):
    W, H = 1000, 96
    s = Svg(W, H)
    s.add(rise(0.5))
    card(s, 0, 0, W, H, t["card"], t["border"], r=22)
    s.text(32, 41, "Interaktive Version", "mono500", 13, t["accent"])
    s.text(32, 70, "Terminal, Filter, Punkte-System und Live-Heatmap zum Ausprobieren.", "sans400", 16, t["muted"])
    btn = "Öffnen"
    bw = measure(btn, "sans600", 17) + 32 + 44
    bx = W - 24 - bw
    s.add(f'<rect x="{bx:.0f}" y="20" width="{bw:.0f}" height="56" rx="14" fill="{BRAND["blue"]}"/>')
    s.defs.append(f'<clipPath id="ctb"><rect x="{bx + 4:.0f}" y="26" width="{bw - 56:.0f}" height="44"/></clipPath>')
    TB = 4.0
    roll = (f'<animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 -36;0 36;0 0;0 0" '
            f'keyTimes="0;{2.8 / TB:.4f};{3.1 / TB:.4f};{3.1001 / TB:.4f};{3.4 / TB:.4f};1" dur="{TB}s" repeatCount="indefinite"/>')
    sub = Svg(1, 1)
    sub.text(bx + 18, 54, btn, "sans600", 17, BRAND["white"])
    s.used.add("sans600")
    s.add(f'<g clip-path="url(#ctb)"><g>{roll}{"".join(sub.body)}</g></g>')
    s.add(f'<rect x="{bx + bw - 48:.0f}" y="28" width="40" height="40" rx="10" fill="#FFFFFF" fill-opacity=".16"/>'
          f'<g><animateTransform attributeName="transform" type="translate" values="0 0;4 0;0 0" dur="1.6s" repeatCount="indefinite" '
          f'calcMode="spline" keySplines=".4 0 .2 1;.4 0 .2 1"/>')
    s.text(bx + bw - 28, 55, "→", "sans600", 18, BRAND["white"], anchor="middle")
    s.add("</g>")
    url = PROFILE["pages"].replace("https://", "").rstrip("/")
    s.text(bx - 24, 54, url, "mono400", 13, t["muted"], anchor="end")
    s.add("</g>")
    return s.render()


def build_faq_label(t, theme):
    s = Svg(1000, 82)
    heading(s, "06", "FAQ", "Häufige Fragen. Klare Antworten.", t)
    return s.render()

README = """<a href="https://{site}"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/hero.svg"><img src="assets/light/hero.svg" width="100%" alt="~/skurllex – Lerne TypeScript, Next.js, FiveM, DevOps und Lua. Aus echten Projekten."></picture></a>

<a href="{pages}"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/cta.svg"><img src="assets/light/cta.svg" width="100%" alt="Interaktive Version öffnen: Terminal, Filter, Punkte-System und Live-Heatmap"></picture></a>

<br><br>

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/about.svg"><img src="assets/light/about.svg" width="100%" alt="01 – Über mich: Wissen aus Produktion. Für Entwickler."></picture>

<br><br>

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/projects.svg"><img src="assets/light/projects.svg" width="100%" alt="02 – Projekte"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/project-district.svg"><img src="assets/light/project-district.svg" width="49%" alt="District Roleplay"></picture> <a href="https://{site}"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/project-skurllex.svg"><img src="assets/light/project-skurllex.svg" width="49%" alt="skurllex.com Lernplattform"></picture></a>
<a href="https://{studio}"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/project-edify.svg"><img src="assets/light/project-edify.svg" width="49%" alt="edify studio"></picture></a> <picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/project-scripts.svg"><img src="assets/light/project-scripts.svg" width="49%" alt="FiveM-Scripts, abgeschlossen"></picture>

<br><br>

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/activity.svg"><img src="assets/light/activity.svg" width="100%" alt="03 – Aktivität: GitHub-Beiträge im letzten Jahr"></picture>

<br><br>

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/stack.svg"><img src="assets/light/stack.svg" width="100%" alt="04 – Stack"></picture>

<br><br>

<a href="mailto:{mail}"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/contact.svg"><img src="assets/light/contact.svg" width="100%" alt="05 – Kontakt: Gute Ideen. Fangen mit Hallo an. {mail}"></picture></a>

<br><br>

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/faq.svg"><img src="assets/light/faq.svg" width="100%" alt="06 – Häufige Fragen. Klare Antworten."></picture>

<details>
<summary><b>01 — Was ist skurllex?</b></summary>
<br>
Meine Lern- und Coaching-Marke. Ich gebe weiter, was in echten Systemen wie District Roleplay täglich funktionieren muss: Kurse, Coaching und Code-Reviews. Mehr auf <a href="https://{site}">{site}</a>.
<br><br>
</details>

<details>
<summary><b>02 — Für wen sind die Kurse?</b></summary>
<br>
Für Entwickler, die über Tutorials hinaus wollen und wissen möchten, wie Systeme im Betrieb gebaut werden: TypeScript, Next.js, FiveM und Lua, DevOps.
<br><br>
</details>

<details>
<summary><b>03 — Machst du auch Code-Reviews für eigene Projekte?</b></summary>
<br>
Ja. Schreib mir kurz, worum es geht, an <a href="mailto:{mail}">{mail}</a>. Ich schaue mir jede Anfrage selbst an.
<br><br>
</details>

<details>
<summary><b>04 — Arbeitest du auch für Kunden?</b></summary>
<br>
Ja, über mein Studio <a href="https://{studio}">edify studio</a>: Web, SaaS, Mobile und Game-Dev, von einer Person gebaut und betreut.
<br><br>
</details>

<details>
<summary><b>05 — Wann startet District Roleplay?</b></summary>
<br>
Das Release-Datum steht intern fest und wird bald angekündigt.
<br><br>
</details>

<br>

<p align="center"><sub><a href="{pages}">Interaktive Version</a> &nbsp;·&nbsp; <a href="https://{site}">{site}</a> &nbsp;·&nbsp; <a href="mailto:{mail}">{mail}</a> &nbsp;·&nbsp; <a href="https://{studio}">{studio}</a> &nbsp;·&nbsp; Aus Hannover</sub></p>
"""


def main():
    cal = load_calendar()
    slugs = ["district", "skurllex", "edify", "scripts"]
    for theme, t in THEMES.items():
        out = ROOT / "assets" / theme
        out.mkdir(parents=True, exist_ok=True)
        files = {
            "hero.svg": build_hero(t, theme),
            "about.svg": build_about(t, theme),
            "projects.svg": build_projects_label(t, theme),
            "activity.svg": build_activity(t, theme, cal),
            "stack.svg": build_stack(t, theme),
            "contact.svg": build_contact(t, theme),
            "cta.svg": build_cta(t, theme),
            "faq.svg": build_faq_label(t, theme),
        }
        for k, (slug, p) in enumerate(zip(slugs, PROJECTS)):
            files[f"project-{slug}.svg"] = build_project(t, theme, p, k)
        for name, content in files.items():
            (out / name).write_text(content, encoding="utf-8")
    (ROOT / "README.md").write_text(README.format(**PROFILE), encoding="utf-8")
    src = ROOT / "data" / "contributions.json"
    if src.exists():
        (ROOT / "docs").mkdir(exist_ok=True)
        (ROOT / "docs" / "contributions.json").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


if __name__ == "__main__":
    main()
