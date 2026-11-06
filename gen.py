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
        style = f"<style>{faces}.bl{{animation:bl 1.06s steps(1) infinite}}@keyframes bl{{50%{{opacity:0}}}}</style>"
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


def build_hero(t, theme):
    W, H = 1200, 520
    s = Svg(W, H)
    card(s, 0, 0, W, H, t["bg"], t["border"], r=28)
    s.defs.append(f'<clipPath id="hc"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="27"/></clipPath>')
    s.add('<g clip-path="url(#hc)">')
    if theme == "light":
        glows(s, [(1010, 110, 190, BRAND["blue_light"], -60, 40, 18), (880, 230, 120, BRAND["blue"], 50, -30, 22),
                  (140, 470, 150, BRAND["violet"], 70, -20, 20)], 0.42, "hg")
        grid(s, W, H, 64, t["grid"], "hm", cx=0.35, cy=0.45, r=0.8)
    else:
        glows(s, [(1020, 80, 220, BRAND["blue"], -70, 50, 18), (820, 260, 140, BRAND["violet"], 50, -40, 22),
                  (80, 500, 180, "#5B4BD6", 80, -30, 20)], 0.55, "hg")
        grid(s, W, H, 56, t["grid"], "hm", cx=0.4, cy=0.45, r=0.85)
    s.add("</g>")
    logo(s, 72, 92, 26, t)
    s.text(W - 72, 92, f"{PROFILE['city'].lower()} · {PROFILE['site']}", "mono400", 14, t["muted"], anchor="end")

    size, tr = 76, -0.05
    base1, base2 = 278, 360
    lerne = "Lerne "
    lw = measure(lerne, "sans800", size, tr) + tr * size
    s.text(72, base1, lerne, "sans800", size, t["text"], tracking=tr)
    s.text(72, base2, "Aus echten Projekten.", "sans800", size, t["text"], tracking=tr)

    n, hold, move = len(TOPICS), 2.2, 0.45
    period = hold + move
    total = n * period
    s.defs.append(f'<clipPath id="tc"><rect x="{72 + lw - 4}" y="{base1 - size * 0.95}" width="700" height="{size * 1.17}"/></clipPath>')
    words = []
    for i, word in enumerate(TOPICS):
        t_in = i * period
        k = lambda v: f"{(v % total) / total:.4f}"
        if i == 0:
            vals, kts = f"0 0;0 0;0 {-size * 1.3};0 {-size * 1.3};0 {size * 1.3};0 0", \
                f"0;{k(hold)};{k(hold + move)};{(total - move - 0.001) / total:.4f};{(total - move) / total:.4f};1"
        else:
            a, b = t_in - move, t_in
            vals = f"0 {size * 1.3};0 {size * 1.3};0 0;0 0;0 {-size * 1.3};0 {-size * 1.3}"
            kts = f"0;{a / total:.4f};{b / total:.4f};{(b + hold) / total:.4f};{(b + hold + move) / total:.4f};1"
        init = "0 0" if i == 0 else f"0 {size * 1.3}"
        sub = Svg(1, 1)
        sub.text(72 + lw, base1, word, "sans800", size, t["accent"], tracking=tr)
        s.used.add("sans800")
        words.append(
            f'<g transform="translate({init})"><animateTransform attributeName="transform" type="translate" values="{vals}" '
            f'keyTimes="{kts}" dur="{total}s" repeatCount="indefinite" calcMode="linear"/>{"".join(sub.body)}</g>'
        )
    s.add(f'<g clip-path="url(#tc)">{"".join(words)}</g>')

    s.text(72, 440, "Kurs · Lernplattform · Coaching · Code-Reviews", "sans400", 16, t["muted"])
    dot_x = W - 72 - measure("Lektionen aus Produktion", "mono500", 13) - 18
    s.add(f'<circle cx="{dot_x + 4}" cy="{435.5}" r="4" fill="{BRAND["success"]}"/>')
    s.text(W - 72, 440, "Lektionen aus Produktion", "mono500", 13, t["muted"], anchor="end")
    return s.render()


# ---------------------------------------------------------------- 01 über mich

VALUES = [
    ("Wert 01", "Präzision statt Annahmen.", "Jede Aussage ist belegbar. Keine Garantien, keine erfundenen Zahlen."),
    ("Wert 02", "Lieber richtig als schnell.", "Sauberer Code, klare Schichten, strikte Typen, auch im Unterricht."),
    ("Wert 03", "Aus echten Projekten.", "Jede Lektion stammt aus einem System, das wirklich läuft."),
]


def build_about(t, theme):
    W = 1000
    s = Svg(W, 470)
    label(s, 0, 18, "01", "Über mich", t)
    s.text(0, 66, "Wissen aus Produktion. Für Entwickler.", "sans800", 40, t["text"], tracking=-0.045)
    body = ("Ich bin Mario, Entwickler aus Hannover. Ich leite die Entwicklung von District Roleplay und baue mit "
            "edify studio Software für Kunden. Was ich dort in Produktion lerne, gebe ich auf skurllex.com weiter.")
    for i, line in enumerate(wrap(body, "sans400", 18, 900)):
        s.text(0, 112 + i * 29, line, "sans400", 18, t["muted"])
    cw, gap, top, ch = 322, 17, 200, 262
    fills = [(t["v1"], None, t["v1_text"], t["v1_muted"], t["v1_label"]),
             (BRAND["blue"], None, BRAND["white"], "#DCE5FF", "#DCE5FF"),
             (t["v3"], t["border"] if theme == "light" else None, t["v3_text"], t["v3_muted"], t["accent"])]
    for i, ((lab, head, txt), (fill, stroke, fg, mut, labc)) in enumerate(zip(VALUES, fills)):
        x = i * (cw + gap)
        card(s, x, top, cw, ch, fill, stroke or (t["border"] if theme == "dark" and i == 0 else None), r=24)
        s.text(x + 32, top + 48, lab, "mono500", 13, labc)
        for j, ln in enumerate(wrap(head, "sans800", 26, cw - 64)):
            s.text(x + 32, top + 96 + j * 30, ln, "sans800", 26, fg, tracking=-0.03)
        for j, ln in enumerate(wrap(txt, "sans400", 16, cw - 64)):
            s.text(x + 32, top + 176 + j * 25, ln, "sans400", 16, mut)
    return s.render()


# ---------------------------------------------------------------- 02 projekte

PROJECTS = [
    ("01", "District Roleplay", ("In Entwicklung", "soft"),
     "FiveM-Roleplay-Plattform, deren Entwicklung ich leite. TypeScript-Server, Lua-Clients, Vue-NUI und ein Next.js-Webpanel in einem Monorepo.",
     ["TypeScript", "Lua", "Vue 3", "Prisma"]),
    ("02", "skurllex.com", ("Lernplattform", "solid"),
     "Kurse, Coaching und Code-Reviews. Jede Lektion stammt aus einem System, das wirklich läuft.",
     ["Kurse", "Coaching", "Code-Reviews"]),
    ("03", "edify studio", ("Studio", "soft"),
     "Mein Solo-Softwarestudio. Web, SaaS, Mobile und Game-Dev, von einer Person gebaut und betreut.",
     ["Next.js", "SaaS", "DevOps"]),
    ("04", "FiveM-Scripts", ("Abgeschlossen", "success"),
     "Über 2.000 Server haben meine Scripts genutzt. Heute fließt diese Erfahrung in District und in die Kurse.",
     ["Lua", "ESX", "QBCore", "ox_lib"]),
]


def build_projects_label(t, theme):
    s = Svg(1000, 82)
    label(s, 0, 18, "02", "Projekte", t)
    s.text(0, 66, "Echte Systeme. Echter Betrieb.", "sans800", 40, t["text"], tracking=-0.045)
    return s.render()


def build_project(t, theme, p):
    num, title, (badge, kind), desc, tags = p
    W, H = 492, 300
    s = Svg(W, H)
    card(s, 0, 0, W, H, t["card"], t["border"], r=24)
    s.text(32, 48, f"{num} —", "mono500", 13, t["accent"])
    bw = measure(badge, "sans600", 13) + 24
    pill(s, W - 32 - bw, 28, badge, t, kind)
    s.text(32, 96, title, "sans700", 24, t["text"], tracking=-0.03)
    for i, ln in enumerate(wrap(desc, "sans400", 16, W - 64)):
        s.text(32, 134 + i * 25, ln, "sans400", 16, t["muted"])
    x = 32
    for tag in tags:
        x += pill(s, x, H - 60, tag, t, "outline", "sans600", 13) + 8
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


def build_activity(t, theme, cal):
    weeks, total, live = cal
    W, H = 1000, 380
    s = Svg(W, H)
    label(s, 0, 18, "03", "Aktivität", t)
    s.text(0, 66, "Jeden Tag ein Commit weiter.", "sans800", 40, t["text"], tracking=-0.045)
    top = 100
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
    for wi, wk in enumerate(weeks):
        for day in wk:
            dow = dt.date.fromisoformat(day["date"]).weekday()
            cells.append(f'<rect x="{x0 + wi * step - 6:.1f}" y="{y0 + dow * step - 6:.1f}" width="12" height="12" rx="3.5" '
                         f'fill="{t["heat"][level(day["count"])]}"/>')
    gw = len(weeks) * step + 20
    s.defs.append(f'<clipPath id="rv"><rect x="{x0 - 10}" y="{y0 - 12}" height="{7 * step + 16}" width="0">'
                  f'<animate attributeName="width" from="0" to="{gw:.0f}" dur="1.4s" begin="0.2s" fill="freeze" '
                  f'calcMode="spline" keyTimes="0;1" keySplines=".2 .7 .3 1"/></rect></clipPath>')
    s.add(f'<g clip-path="url(#rv)">{"".join(cells)}</g>')
    cur, best = streaks(weeks)
    fy = H - 40
    s.add(f'<path d="M32 {fy - 30.5}H{W - 32}" stroke="{t["border"]}"/>')
    x = 32
    for val, lab in ((f"{total:,}".replace(",", "."), "Beiträge im letzten Jahr"), (f"{best} Tage", "längste Serie"),
                     (f"{cur} Tage", "aktuelle Serie")):
        x += s.text(x, fy, val, "mono600", 14, t["text"]) + 8
        x += s.text(x, fy, lab, "sans400", 15, t["muted"]) + 32
    lx = W - 32 - measure("mehr", "mono400", 11) - 8
    s.text(W - 32, fy, "mehr", "mono400", 11, t["muted"], anchor="end")
    for i in range(4, -1, -1):
        s.add(f'<rect x="{lx - 12}" y="{fy - 11}" width="12" height="12" rx="3.5" fill="{t["heat"][i]}"/>')
        lx -= 16
    s.text(lx - 4, fy, "weniger", "mono400", 11, t["muted"], anchor="end")
    if not live:
        s.text(W - 32, top + 34, "Vorschau-Daten", "mono400", 11, t["muted"], anchor="end")
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
    label(s, 0, 18, "04", "Stack", t)
    s.text(0, 66, "Werkzeuge, die täglich laufen.", "sans800", 40, t["text"], tracking=-0.045)
    card(s, 0, top, W, H - top, t["card"], t["border"], r=24)
    for i, (k, items) in enumerate(STACK):
        y = top + 24 + i * row
        if i:
            s.add(f'<path d="M32 {y - 0.5}H{W - 32}" stroke="{t["border"]}"/>')
        s.text(32, y + 35, f"0{i + 1}", "mono500", 13, t["accent"])
        s.text(72, y + 36, k, "sans700", 17, t["text"], tracking=-0.02)
        x = 200
        for it in items:
            x += pill(s, x, y + 16, it, t, "outline") + 8
    return s.render()


# ---------------------------------------------------------------- 05 kontakt

def build_contact(t, theme):
    W, H = 1000, 330
    s = Svg(W, H)
    s.defs.append(f'<clipPath id="cc"><rect x="0" y="0" width="{W}" height="{H}" rx="32"/></clipPath>')
    card(s, 0, 0, W, H, BRAND["blue"], None, r=32)
    s.add('<g clip-path="url(#cc)">')
    dots(s, 0, 0, W, H, 22, BRAND["white"], 0.22)
    glows(s, [(900, 40, 160, BRAND["blue_light"], -40, 30, 16), (760, 320, 140, BRAND["violet"], 40, -20, 20)], 0.55, "cg")
    s.add("</g>")
    s.text(56, 70, "05 — Kontakt", "mono500", 13, "#DCE5FF")
    s.text(56, 132, "Gute Ideen.", "sans800", 48, BRAND["white"], tracking=-0.045)
    s.text(56, 184, "Fangen mit Hallo an.", "sans800", 48, BRAND["white"], tracking=-0.045)
    s.text(56, 226, "Ich schaue mir jede Anfrage selbst an. Für Projekte, Coaching und Code-Reviews.", "sans400", 17, "#DCE5FF")
    btn = "Schreib mir"
    bw = measure(btn, "sans600", 17) + 32 + 44
    s.add(f'<rect x="56" y="250" width="{bw:.0f}" height="56" rx="14" fill="{BRAND["navy"]}"/>')
    s.text(72, 284, btn, "sans600", 17, BRAND["white"])
    s.add(f'<rect x="{56 + bw - 48:.0f}" y="258" width="40" height="40" rx="10" fill="#26344D"/>')
    s.text(56 + bw - 28, 285, "→", "sans600", 18, BRAND["white"], anchor="middle")
    s.text(56 + bw + 24, 284, PROFILE["mail"], "mono500", 15, BRAND["white"])
    return s.render()


README = """<a href="https://{site}"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/hero.svg"><img src="assets/light/hero.svg" width="100%" alt="~/skurllex – Lerne TypeScript, Next.js, FiveM, DevOps und Lua. Aus echten Projekten."></picture></a>

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

<p align="center"><sub><a href="https://{site}">{site}</a> &nbsp;·&nbsp; <a href="mailto:{mail}">{mail}</a> &nbsp;·&nbsp; <a href="https://{studio}">{studio}</a> &nbsp;·&nbsp; Aus Hannover</sub></p>
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
        }
        for slug, p in zip(slugs, PROJECTS):
            files[f"project-{slug}.svg"] = build_project(t, theme, p)
        for name, content in files.items():
            (out / name).write_text(content, encoding="utf-8")
    (ROOT / "README.md").write_text(README.format(**PROFILE), encoding="utf-8")


if __name__ == "__main__":
    main()
