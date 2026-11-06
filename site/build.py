import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FACES = [("Geist", 400, "Geist-Regular"), ("Geist", 600, "Geist-SemiBold"), ("Geist", 700, "Geist-Bold"), ("Geist", 800, "Geist-ExtraBold"),
         ("Geist Mono", 400, "GeistMono-Regular"), ("Geist Mono", 500, "GeistMono-Medium"), ("Geist Mono", 600, "GeistMono-SemiBold")]


def main():
    css = "".join(
        f"@font-face{{font-family:'{fam}';font-weight:{w};font-display:swap;src:url(data:font/woff2;base64,"
        f"{base64.b64encode((ROOT / 'fonts' / f'{name}.woff2').read_bytes()).decode()}) format('woff2')}}"
        for fam, w, name in FACES
    )
    html = (ROOT / "site" / "template.html").read_text(encoding="utf-8").replace("/*FONTS*/", css)
    out = ROOT / "docs" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(out, len(html) // 1024, "KB")


if __name__ == "__main__":
    main()
