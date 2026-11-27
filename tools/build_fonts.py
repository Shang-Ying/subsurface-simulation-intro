#!/usr/bin/env python3
"""Build small Noto Sans TC web-font subsets for the embedded pages.

Usage (from the repo root):
    python3 tools/build_fonts.py            # rebuild subsets whose characters changed
    python3 tools/build_fonts.py --check    # exit 1 if a page needs a rebuild

build_news.py runs this automatically, so a News update never needs a separate step.

Why: loading Noto Sans TC from Google Fonts makes a page download dozens of
font slices (Chinese is split into ~100 slices per weight), which makes the
Google Sites embeds slow. Instead each page gets its own font containing only
the characters that page uses, in weights 400 / 500 / 700 (600 renders as 700,
as it did with Google Fonts):

    webfont/<page>-<weight>.<sig>.woff2     e.g. webfont/home-400.1a2b3c4d5e.woff2

The @font-face rules go in <style id="webfont"> in the page's <head>, under the
family name 'Noto Sans TC Sub', with a unicode-range listing exactly the
characters the subset contains. The page's font stack is
'Source Sans 3', 'Noto Sans TC Sub', 'Noto Sans TC', … and Google's Noto Sans TC
is still linked (without blocking rendering) as a fallback: a character that is
not in the subset, e.g. text added by hand without rebuilding, is still drawn in
Noto Sans TC, only fetched from Google.

<sig> is a hash of the page's character set, so the file name changes whenever
the characters change (no stale browser cache), and --check needs no font tools.

The source font (variable NotoSansTC[wght].ttf, SIL Open Font License, from the
google/fonts repository) is downloaded once into tools/.fontsrc/ (git-ignored).
Requires: pip install fonttools brotli
"""
import hashlib
import html
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "webfont"
SRC_DIR = ROOT / "tools" / ".fontsrc"
SRC = SRC_DIR / "NotoSansTC[wght].ttf"
SRC_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanstc/NotoSansTC%5Bwght%5D.ttf"
LICENSE_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanstc/OFL.txt"

PAGES = ["home", "news", "members", "cv"]
WEIGHTS = (400, 500, 700)
FAMILY = "Noto Sans TC Sub"
VERSION = "3"  # bump to force a rebuild of every subset

BLOCK_RE = re.compile(r'<style id="webfont">.*?</style>', re.S)
SIG_RE = re.compile(r"sig ([0-9a-f]{10})")
ANCHOR_RE = re.compile(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/css2\?family=Source\+Sans\+3[^>]*>')


def page_path(name):
    return ROOT / name / "index.html"


def page_chars(text):
    """Every non-ASCII character the page can show, including the full-width space U+3000 (text, attributes and JS strings),
    plus printable ASCII: while Source Sans 3 is still loading the browser draws Latin text with
    the next font in the stack, and without ASCII here that would pull Google's Noto slices."""
    text = html.unescape(BLOCK_RE.sub("", text))
    return ({c for c in text if ord(c) > 127 and (c.isprintable() or c == "　")}
            | {chr(i) for i in range(0x21, 0x7F)})


def signature(chars):
    s = VERSION + "|" + ",".join(map(str, WEIGHTS)) + "|" + "".join(sorted(chars))
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:10]


def current_sig(text):
    m = BLOCK_RE.search(text)
    m = m and SIG_RE.search(m.group(0))
    return m.group(1) if m else None


def files_for(name, sig):
    return [OUT / f"{name}-{w}.{sig}.woff2" for w in WEIGHTS]


def stale_pages():
    out = []
    for name in PAGES:
        text = page_path(name).read_text(encoding="utf-8")
        sig = signature(page_chars(text))
        if current_sig(text) != sig or not all(f.exists() for f in files_for(name, sig)):
            out.append(name)
    return out


def check():
    """Return the pages whose font subset is out of date (and print the result)."""
    stale = stale_pages()
    for name in PAGES:
        print(f"webfont {name}: {'out of date' if name in stale else 'up to date'}")
    return [f"webfont/{n}" for n in stale]


def unicode_range(cps):
    cps = sorted(cps)
    parts, i = [], 0
    while i < len(cps):
        j = i
        while j + 1 < len(cps) and cps[j + 1] == cps[j] + 1:
            j += 1
        parts.append(f"U+{cps[i]:X}" if i == j else f"U+{cps[i]:X}-{cps[j]:X}")
        i = j + 1
    return ",".join(parts)


def ensure_source():
    if SRC.exists():
        return
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    print(f"downloading {SRC_URL}")
    tmp = SRC.with_suffix(".part")
    urllib.request.urlretrieve(SRC_URL, tmp)
    tmp.replace(SRC)


def subset_font(font, chars, flavor=None):
    from fontTools import subset
    opts = subset.Options()
    opts.hinting = False
    opts.desubroutinize = True
    opts.flavor = flavor
    # fontTools' default feature list (kern, liga, locl, …); "*" would pull in every alternate glyph
    s = subset.Subsetter(opts)
    s.populate(unicodes=[ord(c) for c in chars])
    s.subset(font)
    return font


def build():
    stale = stale_pages()
    if not stale:
        print("webfont: up to date")
        return
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    import io

    ensure_source()
    OUT.mkdir(exist_ok=True)
    lic = OUT / "OFL.txt"
    if not lic.exists():
        urllib.request.urlretrieve(LICENSE_URL, lic)

    texts = {n: page_path(n).read_text(encoding="utf-8") for n in stale}
    chars = {n: page_chars(t) for n, t in texts.items()}
    union = set().union(*chars.values())

    # cut the 10+ MB variable font down to the needed glyphs once, then make one static instance per weight
    var = subset_font(TTFont(SRC), union)
    buf = io.BytesIO()
    var.save(buf)
    statics = {}
    for w in WEIGHTS:
        buf.seek(0)
        statics[w] = instancer.instantiateVariableFont(TTFont(buf), {"wght": w})

    for name in stale:
        sig = signature(chars[name])
        rules = []
        for w, path in zip(WEIGHTS, files_for(name, sig)):
            sb = io.BytesIO()
            statics[w].save(sb)
            sb.seek(0)
            f = subset_font(TTFont(sb), chars[name], flavor="woff2")
            covered = {cp for cp in f.getBestCmap() if chr(cp) in chars[name]}
            f.save(path)
            rules.append(f"@font-face{{font-family:'{FAMILY}';font-style:normal;font-weight:{w};font-display:swap;"
                         f"src:url(../webfont/{path.name}) format('woff2');unicode-range:{unicode_range(covered)}}}")
            print(f"wrote webfont/{path.name} ({path.stat().st_size // 1024} KB, {len(covered)} chars)")
        for old in OUT.glob(f"{name}-*.woff2"):
            if old.name not in {p.name for p in files_for(name, sig)}:
                old.unlink()
        block = (f'<style id="webfont">/* generated by tools/build_fonts.py, sig {sig} */\n'
                 + "\n".join(rules) + "</style>")
        text = texts[name]
        if BLOCK_RE.search(text):
            text = BLOCK_RE.sub(lambda _: block, text, count=1)
        else:
            m = ANCHOR_RE.search(text)
            if not m:
                raise SystemExit(f"{name}/index.html: no Source Sans 3 stylesheet link to put the fonts after")
            text = text[:m.end()] + "\n" + block + text[m.end():]
        page_path(name).write_text(text, encoding="utf-8")
        print(f"wrote {name}/index.html")


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(1 if check() else 0)
    build()
