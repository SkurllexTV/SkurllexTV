import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

import gen
from gen import BRAND, Svg, measure

OUT = gen.ROOT / "brand"


def mark(s: Svg, cx, cy, size, tilde_col, cursor_col, with_tilde=True):
    tw = measure("~/", "mono600", size) if with_tilde else 0
    cw, ch = size * 0.5, size * 0.98
    gap = size * 0.06 if with_tilde else 0
    total = tw + gap + cw
    x = cx - total / 2
    base = cy + ch / 2 - size * 0.2
    if with_tilde:
        s.text(x, base, "~/", "mono600", size, tilde_col)
    s.add(f'<rect x="{x + tw + gap:.1f}" y="{base - size * 0.78:.1f}" width="{cw:.1f}" height="{ch:.1f}" fill="{cursor_col}"/>')


def avatar(variant):
    s = Svg(1024, 1024)
    if variant == "navy":
        s.add(f'<rect width="1024" height="1024" fill="{BRAND["navy"]}"/>')
        mark(s, 512, 512, 330, BRAND["blue_light"], BRAND["blue_light"])
    elif variant == "blue":
        s.add(f'<rect width="1024" height="1024" fill="{BRAND["blue"]}"/>')
        mark(s, 512, 512, 330, BRAND["navy"], BRAND["white"])
    else:
        s.add(f'<rect width="1024" height="1024" fill="{BRAND["white"]}"/>')
        mark(s, 512, 512, 330, BRAND["blue"], BRAND["blue"])
    return s.render()


def gradient_bg(s: Svg, w, h, uid, step):
    s.defs.append(
        f'<linearGradient id="{uid}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="#7FA2FF"/><stop offset=".4" stop-color="#2B5BE0"/>'
        f'<stop offset=".75" stop-color="#5B4BD6"/><stop offset="1" stop-color="#16264A"/></linearGradient>'
    )
    s.add(f'<rect width="{w}" height="{h}" fill="url(#{uid})"/>')
    gen.grid(s, w, h, step, "#FFFFFF", uid + "m", cx=0.45, cy=0.4, r=0.9)
    s.body[-1] = s.body[-1].replace('stroke="#FFFFFF"', 'stroke="#FFFFFF" stroke-opacity=".16"')


def discord_banner():
    w, h = 1360, 480
    s = Svg(w, h)
    gradient_bg(s, w, h, "db", 56)
    x = w - 72 - 0
    tw = measure("~/skurllex", "mono600", 34)
    lx = w - 72 - tw - 34 * 0.56
    s.text(lx, 104, "~/", "mono600", 34, BRAND["navy"])
    s.text(lx + measure("~/", "mono600", 34), 104, "skurllex", "mono600", 34, BRAND["white"])
    s.add(f'<rect x="{lx + tw + 34 * 0.06:.1f}" y="{104 - 34 * 0.78:.1f}" width="{34 * 0.5:.1f}" height="{34 * 0.98:.1f}" fill="{BRAND["white"]}"/>')
    s.text(w - 72, 400, "Wissen aus Produktion. Für Entwickler.", "sans800", 40, BRAND["white"], tracking=-0.045, anchor="end")
    return s.render(), w, h


def server_banner():
    w, h = 960, 540
    s = Svg(w, h)
    gradient_bg(s, w, h, "sb", 48)
    return s.render(), w, h


async def render(items):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome")
        for name, markup, w, h in items:
            svg = OUT / f"{name}.svg"
            svg.write_text(markup, encoding="utf-8")
            pg = await b.new_page(viewport={"width": w, "height": h})
            await pg.goto(svg.as_uri())
            await pg.wait_for_timeout(500)
            await pg.screenshot(path=str(OUT / f"{name}.png"), clip={"x": 0, "y": 0, "width": w, "height": h})
            await pg.close()
        await b.close()


def main():
    OUT.mkdir(exist_ok=True)
    db, dw, dh = discord_banner()
    sb, sw, sh = server_banner()
    items = [(f"avatar-{v}", avatar(v), 1024, 1024) for v in ("navy", "blue", "white")]
    items += [("discord-banner", db, dw, dh), ("discord-server-banner", sb, sw, sh)]
    asyncio.run(render(items))


if __name__ == "__main__":
    main()
