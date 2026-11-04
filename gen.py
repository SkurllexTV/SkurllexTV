import base64
import datetime as dt
import json
import io
import math
import random
import string
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent
FONTS = ROOT / "fonts"
OUT = ROOT

PROFILE = {
    "handle": "skurllex",
    "name": "mario stirbu",
    "host": "edify",
    "city": "hannover",
    "site": "edifystudios.de",
    "mail": "hi@edifystudios.de",
    "shop": "https://b-development.tebex.io/",
}

THEMES = {
    "dark": dict(bg="#000000", border="#262626", dim="#3d3d3d", mid="#7d7d7d", fg="#ededed", acc="#C8FF3C"),
    "light": dict(bg="#ffffff", border="#e3e3e3", dim="#bdbdbd", mid="#6e6e6e", fg="#0a0a0a", acc="#5a7300"),
}

EXTRA_GLYPHS = "▁▂▃▄▅▆▇█●─░▒▓·✓→"


def font_b64(name: str) -> str:
    font = TTFont(FONTS / name)
    opts = Options()
    opts.flavor = "woff2"
    opts.layout_features = []
    sub = Subsetter(opts)
    sub.populate(text=string.printable + EXTRA_GLYPHS)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


FONT_CSS = (
    "@font-face{font-family:'JBM';font-weight:400;src:url(data:font/woff2;base64,%s) format('woff2')}"
    "@font-face{font-family:'JBM';font-weight:700;src:url(data:font/woff2;base64,%s) format('woff2')}"
    % (font_b64("JetBrainsMonoNL-Regular.woff2"), font_b64("JetBrainsMonoNL-Bold.woff2"))
)
STYLE = (
    "<style>" + FONT_CSS +
    ".m{font-family:'JBM',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;white-space:pre}"
    ".b{font-weight:700}"
    ".bl{animation:bl 1.1s steps(1) infinite}@keyframes bl{50%{opacity:0}}"
    "</style>"
)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def svg(w: int, h: int, body: str, defs: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'fill="none" xml:space="preserve">{STYLE}<defs>{defs}</defs>{body}</svg>'
    )


def text(x, y, size, spans, anchor=None, extra=""):
    if isinstance(spans, tuple):
        spans = [spans]
    inner = "".join(
        f'<tspan fill="{c}"{" font-weight=\"700\"" if b else ""}>{esc(t)}</tspan>' for t, c, b in spans
    )
    a = f' text-anchor="{anchor}"' if anchor else ""
    return f'<text x="{x}" y="{y}" class="m" font-size="{size}"{a}{extra}>{inner}</text>'


def frames(inner: list[str], starts: list[float], dur: float) -> str:
    kt = ";".join(f"{s:.4f}" for s in starts)
    out = []
    for i, content in enumerate(inner):
        vals = ";".join("1" if j == i else "0" for j in range(len(inner)))
        out.append(
            f'<g opacity="{1 if i == 0 else 0}">{content}'
            f'<animate attributeName="opacity" values="{vals}" keyTimes="{kt}" dur="{dur}s" '
            f'calcMode="discrete" repeatCount="indefinite"/></g>'
        )
    return "".join(out)


def scramble(target: str, ratio: float, rng: random.Random) -> str:
    pool = "!#$%&*+-/:;<=>?@[]^_{|}~0123456789abcdef"
    return "".join(ch if (ch == " " or rng.random() > ratio) else rng.choice(pool) for ch in target)


def label(num: str, title: str, t) -> str:
    x2 = round(len(f"// {num}  {title}") * 7.2 + 14)
    body = text(0, 16, 12, [("// ", t["dim"], False), (num, t["acc"], True), (f"  {title}", t["mid"], False)])
    body += f'<line x1="{x2}" y1="12" x2="1000" y2="12" stroke="{t["border"]}"/>'
    return body


def write(theme: str, name: str, content: str):
    path = OUT / "assets" / theme / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_label(t):
    return svg(1000, 24, label("02", "work", t))


def build_whoami(t):
    h = PROFILE
    rows = [
        ("cmd", "whoami"),
        ("out", [(h["name"], t["fg"], True), (f"  ·  developer & creator  ·  {h['city']}", t["mid"], False)]),
        ("cmd", "cat focus"),
        ("out", [("fivem        ", t["fg"], False), ("roleplay platforms, lua + typescript", t["mid"], False)]),
        ("out", [("product      ", t["fg"], False), ("next.js, react and prisma, idea to shipped", t["mid"], False)]),
        ("out", [("infra        ", t["fg"], False), ("self-hosted on hetzner, docker, coolify", t["mid"], False)]),
        ("out", [("content      ", t["fg"], False), ("skurllextv, dev courses and build videos", t["mid"], False)]),
        ("cmd", "cat ~/.customers"),
        ("out", [("2000+", t["fg"], True), ("   # fivem script customers and counting.", t["dim"], False)]),
        ("idle", None),
    ]
    return terminal(t, "01", "whoami", rows)


def terminal(t, num, title, rows):
    h = PROFILE
    prompt = [(f"{h['handle']}@{h['host']}", t["acc"], True), (" ~ ", t["mid"], False), ("$ ", t["mid"], False)]
    cmd_x = 26 + len(f"{h['handle']}@{h['host']} ~ $ ") * 9
    defs, body = "", ""
    clock, y = 0.40, 116
    for i, (kind, payload) in enumerate(rows):
        if kind == "cmd":
            n = len(payload) + 1
            type_start, step = clock + 0.20, 0.055
            type_dur = n * step
            ws = ";".join(f"{k * 9:.2f}" for k in range(n))
            xs = ";".join(f"{cmd_x + k * 9:.2f}" for k in range(n))
            kt = ";".join(f"{k / n:.4f}" for k in range(n))
            defs += (
                f'<clipPath id="c{i}"><rect x="{cmd_x}" y="{y - 17}" height="24" width="0">'
                f'<animate attributeName="width" values="{ws}" keyTimes="{kt}" dur="{type_dur:.2f}s" '
                f'begin="{type_start:.2f}s" calcMode="discrete" fill="freeze"/></rect></clipPath>'
            )
            body += (
                f'<g opacity="0"><set attributeName="opacity" to="1" begin="{clock:.2f}s" fill="freeze"/>'
                + text(26, y, 15, prompt)
                + f'<g clip-path="url(#c{i})">{text(cmd_x, y, 15, (payload, t["fg"], False))}</g>'
                f'<rect x="{cmd_x}" y="{y - 13}" width="9.0" height="17" fill="{t["acc"]}" opacity="0">'
                f'<animate attributeName="x" values="{xs}" keyTimes="{kt}" dur="{type_dur:.2f}s" '
                f'begin="{type_start:.2f}s" calcMode="discrete" fill="freeze"/>'
                f'<set attributeName="opacity" to="1" begin="{clock:.2f}s"/>'
                f'<set attributeName="opacity" to="0" begin="{type_start + type_dur:.2f}s"/></rect></g>'
            )
            clock = type_start + type_dur + 0.18
        elif kind == "out":
            body += (
                f'<g opacity="0"><set attributeName="opacity" to="1" begin="{clock:.2f}s" fill="freeze"/>'
                + text(26, y, 15, payload) + "</g>"
            )
            clock += 0.08
        else:
            body += (
                f'<g opacity="0"><set attributeName="opacity" to="1" begin="{clock + 0.15:.2f}s" fill="freeze"/>'
                + text(26, y, 15, prompt)
                + f'<rect x="{cmd_x}" y="{y - 13}" width="9.0" height="17" fill="{t["acc"]}" class="bl"/></g>'
            )
        y += 26
    height = y + 4
    frame = (
        label(num, title, t)
        + f'<rect x=".5" y="40.5" width="999" height="{height - 41}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>'
        + f'<path d="M1 80.5H999" stroke="{t["border"]}"/>'
        + text(24, 65, 11, ("● ● ●", t["dim"], False))
        + text(500, 65, 12, (f"─ zsh ─ {h['handle']}@{h['host']} ─", t["mid"], False), anchor="middle")
    )
    return svg(1000, height, frame + body, defs)


def card_shell(t, num, name, kind, demo, desc, tags):
    body = (
        f'<rect x=".5" y=".5" width="491" height="285" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>'
        + text(24, 40, 17, [(f"[{num}] ", t["dim"], False), (name, t["fg"], True)])
        + text(468, 40, 12, (kind, t["mid"], False), anchor="end")
        + f'<path d="M24 58.5H468" stroke="{t["border"]}" stroke-dasharray="2 4"/>'
        + demo
    )
    for i, line in enumerate(desc):
        body += text(24, 188 + i * 21, 13.5, (line, t["mid"], False))
    body += f'<path d="M24 242.5H468" stroke="{t["border"]}"/>'
    body += text(24, 267, 12, (tags, t["dim"], False))
    return svg(492, 286, body)


def build_card_district(t):
    lines = [
        [("> ensure ", t["mid"], False), ("district-core", t["fg"], False)],
        [("> services ", t["mid"], False), ("61 loaded  ·  43 schemas", t["fg"], False)],
        [("> webpanel ", t["mid"], False), ("212 api routes", t["fg"], False), ("  [ok]", t["acc"], True)],
    ]
    demo = text(24, 92, 12, ("[ fxserver · boot ]", t["dim"], False))
    for i, spans in enumerate(lines):
        s = 0.083 + i * 0.167
        demo += (
            f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" '
            f'keyTimes="0;{s:.3f};{s + 0.008:.3f};.92;1" dur="6.0s" repeatCount="indefinite"/>'
            + text(24, 116 + i * 19, 13, spans) + "</g>"
        )
    return card_shell(
        t, "01", "district", "fivem rp platform", demo,
        ["FiveM roleplay platform I lead. TypeScript server,", "Lua clients, Vue NUI and a Next.js webpanel in", "one monorepo."],
        "typescript · lua · vue 3 · prisma",
    )


def build_card_edify(t):
    steps = [("build", 0), ("build", 1), ("test", 2), ("test", 3), ("deploy", 4), ("live", 5)]
    inner = []
    for stage, k in steps:
        bar = "█" * (k * 6) + "░" * (30 - k * 6)
        done = k == 5
        inner.append(
            text(24, 92, 12, ("[ deploy · production ]", t["dim"], False))
            + text(24, 122, 11, (bar, t["acc"] if done else t["fg"], False))
            + text(24, 146, 13, [("> ", t["mid"], False), (stage, t["fg"], False)]
                   + ([("  [ok]", t["acc"], True)] if done else []))
        )
    starts = [0.0, 0.12, 0.24, 0.36, 0.48, 0.60]
    return card_shell(
        t, "02", "edify studio", "software studio", frames(inner, starts, 5.0),
        ["My solo software studio. Web, SaaS, mobile and", "game dev, built and shipped by one person", "instead of an agency."],
        "next.js · saas · mobile · devops",
    )


def build_card_skurllextv(t):
    inner = []
    total = 12
    for k in range(1, 7):
        bar = "▓" * (k * 2) + "░" * (total - k * 2)
        inner.append(
            text(24, 92, 12, ("[ course · fivem / lua ]", t["dim"], False))
            + text(24, 122, 15, [(bar, t["fg"], False), (f"  {k * 2:02d}/{total}", t["mid"], False)])
            + text(24, 146, 13, [("> unlocked ", t["mid"], False), (f"lesson {k * 2:02d}", t["fg"], False)]
                   + ([("  [done]", t["acc"], True)] if k == 6 else []))
        )
    starts = [i / 6 for i in range(6)]
    return card_shell(
        t, "03", "skurllextv", "dev education", frames(inner, starts, 4.8),
        ["Courses and build videos for developers. FiveM,", "Lua and full-stack, step by step or self-paced."],
        "courses · fivem · full-stack",
    )


def build_card_fxserver(t):
    rng = random.Random(7)
    src = ['Citizen.CreateThread(function()', '  TriggerServerEvent("core:x")']
    prot = ['[ dump detected · decoy served ]', '  resource stream  ·  blocked']
    seq = []
    seq.append(("[ resource ]", src, t["fg"]))
    for r in (0.6, 0.45, 0.3, 0.15):
        seq.append(("[ dump attempt ]", [scramble(x, r, rng) for x in src], t["mid"]))
    seq.append(("[ protected ]", prot, t["acc"]))
    for r in (0.3, 0.55, 0.75):
        seq.append(("[ resource ]", [scramble(x, r, rng) for x in src], t["mid"]))
    inner = [
        text(24, 92, 12, (head, t["dim"], False))
        + "".join(text(24, 116 + i * 19, 14, (ln, col, False)) for i, ln in enumerate(lines))
        for head, lines, col in seq
    ]
    starts = [0.0, 0.4415, 0.4592, 0.4768, 0.4945, 0.5121, 0.9536, 0.9691, 0.9845]
    return card_shell(
        t, "04", "fxserver", "resource protection", frames(inner, starts, 4.53),
        ["Custom FXServer built from source. Dump", "detection, bytecode protection and decoy", "resources against leaks."],
        "c++ · lua · linux",
    )


def build_stack(t):
    rows = [
        ("product", "typescript · react · next.js · tailwind · vue 3"),
        ("backend", "node · prisma · drizzle · postgresql · websockets"),
        ("fivem", "lua · esx · qbcore · ox_lib · nui · fxserver"),
        ("infra", "linux · docker · hetzner · coolify · dokploy · cloudflare"),
        ("ai", "claude code · mcp · openai · elevenlabs"),
    ]
    row_h = 46
    height = 41 + row_h * len(rows) + 1
    body = label("04", "stack", t)
    body += f'<rect x=".5" y="40.5" width="999" height="{height - 42}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>'
    body += f'<path d="M150.5 40V{height - 2}" stroke="{t["border"]}"/>'
    for i, (k, v) in enumerate(rows):
        y = 69 + i * row_h
        body += text(24, y, 14, [("$ ", t["dim"], False), (k, t["fg"], True)])
        body += text(174, y, 14, (v, t["mid"], False))
        if i < len(rows) - 1:
            body += f'<path d="M1 {86.5 + i * row_h}H999" stroke="{t["border"]}"/>'
    return svg(1000, height, body)


def build_signoff(t):
    p = PROFILE
    rows = [
        ("cmd", "./hire --one-dev-not-an-agency"),
        ("out", [("scope        ", t["fg"], False), ("web · saas · mobile · fivem · devops", t["mid"], False)]),
        ("out", [("delivery     ", t["fg"], False), ("concept to production, one point of contact", t["mid"], False)]),
        ("out", [("status       ", t["fg"], False), ("open for projects", t["fg"], True), ("  [ok]", t["acc"], True)]),
        ("out", [("contact      ", t["fg"], False), (p["mail"], t["acc"], True)]),
        ("idle", None),
    ]
    return terminal(t, "05", "eof", rows)


def load_calendar():
    path = ROOT / "data" / "contributions.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return data["weeks"], data["total"], True
    rng = random.Random(42)
    start = dt.date.today() - dt.timedelta(days=dt.date.today().weekday() + 1 + 52 * 7)
    weeks = []
    for w in range(53):
        week = []
        for d in range(7):
            day = start + dt.timedelta(days=w * 7 + d)
            if day > dt.date.today():
                continue
            base = 0.55 + 0.45 * math.sin(w / 6.0)
            n = 0 if rng.random() > base else int(rng.expovariate(0.22))
            week.append({"date": day.isoformat(), "count": n})
        weeks.append(week)
    return weeks, sum(d["count"] for wk in weeks for d in wk), False


def streaks(weeks):
    days = [d["count"] for wk in weeks for d in wk]
    best = cur = run = 0
    for c in days:
        run = run + 1 if c else 0
        best = max(best, run)
    for c in reversed(days):
        if not c:
            break
        cur += 1
    return cur, best


def build_activity(t, cal):
    weeks, total, live = cal
    counts = sorted(d["count"] for wk in weeks for d in wk if d["count"])
    q = [counts[int(len(counts) * f)] if counts else 1 for f in (0.25, 0.5, 0.75)]

    def level(c):
        if not c:
            return 0
        return 1 + sum(c > x for x in q)

    chars = ["··", "░░", "▒▒", "▓▓", "██"]
    cell, x0, y0, rh = 16.8, 74, 110, 17
    body = label("03", "activity", t)
    height = 40 + 70 + 7 * rh + 62
    body += f'<rect x=".5" y="40.5" width="999" height="{height - 41}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>'
    body += text(24, 72, 12, [("$ ", t["dim"], False), ("git log --since=1.year --author=", t["mid"], False),
                              (PROFILE["handle"], t["fg"], True)])
    body += text(976, 72, 12, ("live" if live else "preview data", t["dim"], False), anchor="end")
    last_month = None
    for wi, wk in enumerate(weeks):
        if not wk:
            continue
        m = dt.date.fromisoformat(wk[0]["date"]).strftime("%b").lower()
        if m != last_month and wi < len(weeks) - 2:
            body += text(round(x0 + wi * cell, 1), y0 - 14, 11, (m, t["dim"], False))
            last_month = m
    for d, name in ((1, "mon"), (3, "wed"), (5, "fri")):
        body += text(24, y0 + 8 + d * rh, 11, (name, t["dim"], False))
    grid = ""
    for d in range(7):
        y = y0 + 8 + d * rh
        for wi, wk in enumerate(weeks):
            day = next((x for x in wk if dt.date.fromisoformat(x["date"]).weekday() == (d + 6) % 7), None)
            if day is None:
                continue
            lv = level(day["count"])
            col = t["dim"] if lv == 0 else t["acc"]
            grid += f'<text x="{x0 + wi * cell:.1f}" y="{y}" class="m" font-size="12" fill="{col}">{chars[lv]}</text>'
    gw = len(weeks) * cell + 10
    body += (f'<defs><clipPath id="rv"><rect x="{x0 - 4}" y="{y0}" height="{7 * rh + 10}" width="0">'
             f'<animate attributeName="width" from="0" to="{gw:.0f}" dur="1.6s" begin="0.3s" fill="freeze"/></rect></clipPath></defs>'
             f'<g clip-path="url(#rv)">{grid}</g>')
    cur, best = streaks(weeks)
    fy = y0 + 7 * rh + 36
    body += f'<path d="M1 {fy - 22.5}H999" stroke="{t["border"]}"/>'
    body += text(24, fy, 13, [(f"{total:,}", t["fg"], True), (" contributions", t["mid"], False),
                              ("   ·   ", t["dim"], False), (f"{best}d", t["fg"], True), (" longest streak", t["mid"], False),
                              ("   ·   ", t["dim"], False), (f"{cur}d", t["acc"], True), (" current", t["mid"], False)])
    body += text(976, fy, 13, [("less ", t["dim"], False)] + [(c + " ", t["dim"] if i == 0 else t["acc"], False) for i, c in enumerate(chars)]
                 + [(" more", t["dim"], False)], anchor="end")
    return svg(1000, height, body)


def build_card_scripts(t):
    w, h = 1000, 252
    body = (
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>'
        + text(24, 40, 17, [("[05] ", t["dim"], False), ("fivem scripts", t["fg"], True)])
        + text(976, 40, 12, ("store · " + PROFILE["shop"], t["mid"], False), anchor="end")
        + f'<path d="M24 58.5H976" stroke="{t["border"]}" stroke-dasharray="2 4"/>'
        + f'<path d="M500.5 76V190" stroke="{t["border"]}"/>'
    )
    counts = ["1,994", "1,995", "1,996", "1,997", "1,998", "1,999", "2,000+"]
    inner = []
    for i, c in enumerate(counts):
        done = i == len(counts) - 1
        inner.append(text(24, 132, 40, (c, t["acc"] if done else t["fg"], True)))
    starts = [0.0, 0.07, 0.14, 0.21, 0.28, 0.35, 0.42]
    body += text(24, 92, 12, ("[ customers ]", t["dim"], False)) + frames(inner, starts, 6.0)
    body += text(24, 166, 13, [("> frameworks ", t["mid"], False), ("esx · qbcore · standalone", t["fg"], False)])
    body += text(24, 186, 13, [("> delivery   ", t["mid"], False), ("instant", t["fg"], False), ("  [ok]", t["acc"], True)])
    desc = ["Paid FiveM scripts, sold to over 2,000 servers.", "Clean configs, protected builds and support",
            "included. From weapon skin shops to full systems."]
    for i, line in enumerate(desc):
        body += text(524, 104 + i * 21, 13.5, (line, t["mid"], False))
    body += text(524, 180, 13.5, [("> ", t["dim"], False), ("browse the store", t["fg"], True), ("  →", t["acc"], False)])
    body += f'<path d="M24 212.5H976" stroke="{t["border"]}"/>'
    body += text(24, 237, 12, ("lua · esx · qbcore · ox_lib · nui · tebex", t["dim"], False))
    return svg(w, h, body)


def glyph_paths(word: str, font_path: Path, target_w: float, cx: float, baseline: float, tracking: float, ys: float = 1.55):
    font = TTFont(font_path)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    names = [cmap[ord(c)] for c in word]
    adv = [gs[n].width for n in names]
    raw_w = sum(adv) + tracking * upm * (len(word) - 1)
    scale = target_w / raw_w
    x = cx - target_w / 2
    paths = []
    for n, a in zip(names, adv):
        pen = SVGPathPen(gs)
        gs[n].draw(TransformPen(pen, (scale, 0, 0, -scale * ys, x, baseline)))
        paths.append(pen.getCommands())
        x += (a + tracking * upm) * scale
    cap = font["OS/2"].sCapHeight * scale * ys
    return " ".join(paths), cap


def ascii_field(w, h, t, seed):
    rng = random.Random(seed)
    ramp = " .:-=+*#%"
    blobs = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(50, 130)) for _ in range(16)]
    rows = []
    cw, rh = 5.4, 9
    for r in range(int(h / rh) + 1):
        y = r * rh + 8
        line = []
        for c in range(int(w / cw) + 1):
            x = c * cw
            v = max(math.exp(-((x - bx) ** 2 + (y - by) ** 2) / (2 * s * s)) for bx, by, s in blobs)
            v += 0.18 * math.sin(x * 0.021 + y * 0.013) * math.sin(y * 0.05)
            v = max(0.0, min(0.999, (v - 0.25) * 1.35 + rng.uniform(-0.1, 0.1)))
            line.append(ramp[int(v * len(ramp))])
        rows.append(f'<text x="0" y="{y}" class="m" font-size="9" fill="{t["dim"]}">{esc("".join(line))}</text>')
    return f'<g opacity="{0.55 if t["bg"] == "#000000" else 0.75}">' + "".join(rows) + "</g>"


def build_hero(t, dark: bool):
    w, h = 1400, 504
    d, cap = glyph_paths("SKURLLEX", FONTS / "syne-latin-800-normal.woff2",
                         1180, w / 2, 0, 0.02)
    baseline = h / 2 + cap / 2
    d, cap = glyph_paths("SKURLLEX", FONTS / "syne-latin-800-normal.woff2",
                         1180, w / 2, baseline, 0.02)
    top = baseline - cap
    if dark:
        face = [(0, "#ffffff"), (0.30, "#c9c9c9"), (0.47, "#4a4a4a"), (0.50, "#0d0d0d"), (0.53, "#26300a"),
                (0.66, "#8a8a8a"), (0.86, "#e6e6e6"), (1, "#ffffff")]
        side_a, side_b, glow_op = "#2a2a2a", "#050505", 0.22
    else:
        face = [(0, "#f2f2f2"), (0.30, "#9a9a9a"), (0.47, "#262626"), (0.50, "#050505"), (0.53, "#1d2508"),
                (0.66, "#5e5e5e"), (0.86, "#cfcfcf"), (1, "#f5f5f5")]
        side_a, side_b, glow_op = "#3a3a3a", "#0a0a0a", 0.0
    stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in face)
    defs = (
        f'<linearGradient id="face" x1="0" y1="{top}" x2="0" y2="{baseline}" gradientUnits="userSpaceOnUse">{stops}</linearGradient>'
        f'<linearGradient id="side" x1="0" y1="{top}" x2="0" y2="{baseline + 20}" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{side_a}"/><stop offset="1" stop-color="{side_b}"/></linearGradient>'
        f'<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".30" stop-color="#fff" stop-opacity=".22"/>'
        f'<stop offset=".36" stop-color="#fff" stop-opacity="0"/><stop offset=".66" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".71" stop-color="#fff" stop-opacity=".16"/><stop offset=".76" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="sweep" x1="0" y1="0" x2="1" y2=".35">'
        f'<stop offset=".2" stop-color="#000" stop-opacity="0"/><stop offset=".4" stop-color="#000" stop-opacity=".35"/>'
        f'<stop offset=".5" stop-color="#fff" stop-opacity=".95"/><stop offset=".6" stop-color="#000" stop-opacity=".35"/>'
        f'<stop offset=".8" stop-color="#000" stop-opacity="0"/></linearGradient>'
        f'<radialGradient id="glow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{THEMES["dark"]["acc"]}" stop-opacity="1"/>'
        f'<stop offset="1" stop-color="{THEMES["dark"]["acc"]}" stop-opacity="0"/></radialGradient>'
        f'<filter id="shadow" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur stdDeviation="14"/></filter>'
        f'<clipPath id="txt"><path d="{d}"/></clipPath>'
    )
    body = f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{t["bg"]}" stroke="{t["border"]}"/>'
    body += ascii_field(w, h, t, 3)
    if glow_op:
        body += f'<ellipse cx="{w / 2}" cy="{baseline + 26}" rx="560" ry="46" fill="url(#glow)" opacity="{glow_op}"/>'
    else:
        body += f'<path d="{d}" fill="#000" opacity=".28" filter="url(#shadow)" transform="translate(6 18)"/>'
    depth = 16
    for i in range(depth, 0, -1):
        body += f'<path d="{d}" fill="url(#side)" transform="translate({i * 0.55:.2f} {i * 0.9:.2f})"/>'
    body += f'<path d="{d}" fill="url(#face)"/>'
    body += f'<g clip-path="url(#txt)"><rect x="0" y="{top - 10}" width="{w}" height="{cap + 20}" fill="url(#sheen)"/>'
    body += (f'<rect x="0" y="{top - 10}" width="300" height="{cap + 40}" fill="url(#sweep)">'
             f'<animateTransform attributeName="transform" type="translate" values="-500 0;{w + 80} 0;{w + 80} 0" '
             f'keyTimes="0;0.28;1" dur="7s" begin="1.2s" repeatCount="indefinite"/></rect></g>')
    for cx, cy in ((22, 22), (w - 22, 22), (22, h - 22), (w - 22, h - 22)):
        body += f'<path d="M{cx - 5} {cy}H{cx + 5}M{cx} {cy - 5}V{cy + 5}" stroke="{t["dim"]}"/>'
    p = PROFILE
    body += text(48, 60, 15, [(p["handle"], t["fg"], True), ("  /  ", t["dim"], False), (p["name"], t["mid"], False)])
    body += text(w - 48, 60, 15, (f"{p['city']}, de", t["mid"], False), anchor="end")
    body += text(48, h - 44, 15, [("[ ", t["mid"], False), ("●", t["acc"], False), (" status: online ]", t["mid"], False)])
    body += text(w - 48, h - 44, 15, (f"[ {p['site']} ]", t["mid"], False), anchor="end")
    return svg(w, h, body, defs)


README = """<a href="https://{site}"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/hero.svg"><source media="(prefers-color-scheme: light)" srcset="assets/light/hero.svg"><img src="assets/dark/hero.svg" width="100%" alt="SKURLLEX in 3D chrome. Mario Stirbu, Hannover."></picture></a>

<br>

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/whoami.svg"><source media="(prefers-color-scheme: light)" srcset="assets/light/whoami.svg"><img src="assets/dark/whoami.svg" width="100%" alt="whoami: Mario Stirbu, developer and creator in Hannover. FiveM, product, infrastructure and content."></picture>

<br>

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/label-work.svg"><source media="(prefers-color-scheme: light)" srcset="assets/light/label-work.svg"><img src="assets/dark/label-work.svg" width="100%" alt="02 work"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/card-district.svg"><source media="(prefers-color-scheme: light)" srcset="assets/light/card-district.svg"><img src="assets/dark/card-district.svg" width="49%" alt="District: FiveM roleplay platform"></picture> <a href="https://{site}"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/card-edify.svg"><source media="(prefers-color-scheme: light)" srcset="assets/light/card-edify.svg"><img src="assets/dark/card-edify.svg" width="49%" alt="edify studio: solo software studio"></picture></a>
<picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/card-skurllextv.svg"><source media="(prefers-color-scheme: light)" srcset="assets/light/card-skurllextv.svg"><img src="assets/dark/card-skurllextv.svg" width="49%" alt="SkurllexTV: developer courses and build videos"></picture> <picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/card-fxserver.svg"><source media="(prefers-color-scheme: light)" srcset="assets/light/card-fxserver.svg"><img src="assets/dark/card-fxserver.svg" width="49%" alt="FXServer: custom build for resource protection"></picture>

<a href="https://{shop}"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/card-scripts.svg"><source media="(prefers-color-scheme: light)" srcset="assets/light/card-scripts.svg"><img src="assets/dark/card-scripts.svg" width="100%" alt="FiveM scripts: sold to over 2,000 servers"></picture></a>

<br>

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/activity.svg"><source media="(prefers-color-scheme: light)" srcset="assets/light/activity.svg"><img src="assets/dark/activity.svg" width="100%" alt="GitHub activity over the last year as an ASCII heatmap"></picture>

<br>

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/stack.svg"><source media="(prefers-color-scheme: light)" srcset="assets/light/stack.svg"><img src="assets/dark/stack.svg" width="100%" alt="Stack: product, backend, FiveM, infrastructure and AI."></picture>

<br>

<a href="mailto:{mail}"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/signoff.svg"><source media="(prefers-color-scheme: light)" srcset="assets/light/signoff.svg"><img src="assets/dark/signoff.svg" width="100%" alt="Hire: web, SaaS, mobile, FiveM. Open for projects. Contact: {mail}"></picture></a>

<p align="center"><sub><a href="mailto:{mail}">{mail}</a> &nbsp;·&nbsp; <a href="https://{site}">{site}</a> &nbsp;·&nbsp; discord: skurllex</sub></p>
"""


def main():
    builders = {
        "whoami.svg": build_whoami,
        "label-work.svg": build_label,
        "card-district.svg": build_card_district,
        "card-edify.svg": build_card_edify,
        "card-skurllextv.svg": build_card_skurllextv,
        "card-fxserver.svg": build_card_fxserver,
        "card-scripts.svg": build_card_scripts,
        "stack.svg": build_stack,
        "signoff.svg": build_signoff,
    }
    cal = load_calendar()
    for theme, t in THEMES.items():
        for name, fn in builders.items():
            write(theme, name, fn(t))
        write(theme, "activity.svg", build_activity(t, cal))
        write(theme, "hero.svg", build_hero(t, theme == "dark"))
    (OUT / "README.md").write_text(README.format(**PROFILE), encoding="utf-8")
    print("ok", file=sys.stderr)


if __name__ == "__main__":
    main()
