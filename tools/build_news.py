#!/usr/bin/env python3
"""Rebuild the News timeline in news/index.html from news/news.yaml.

Usage (from the repo root):
    python3 tools/build_news.py            # rewrite news/index.html
    python3 tools/build_news.py --check    # exit 1 if index.html is out of date

Only two regions of news/index.html are regenerated: the year-jump links
(<div class="yj">…</div>) and the timeline (<main …>…</main>). The <head>,
CSS, header card, filter chips and scripts are left exactly as they are.

Data format (news/news.yaml): a list of items, newest first.

  - ym: 2026-11              # year-month the item is filed under
    to: 8                    # optional: end month for a range (e.g. Jul–Aug)
    cat: teach               # paper | talk | conf | teach | service | award | visit | project
    title: 水文地質學|課程|參訪 <span class="at">@ 雲林縣|口湖鄉</span>
    link: https://doi.org/…  # optional: adds the "Link ↗" pill after the title
    body:                    # optional lines under the title, in order
      - kv_t: [題目：, Paper title]     # key/value, title style
      - kv:   [期刊：, Journal name]
      - li:   numbered list line (numbers are automatic)
      - ln:   plain line
    photos:                  # optional; files live in news/img/
      - s: 2026-11_hydrogeo_field_1.jpg   # full size; <name>_s.jpg is the 900 px copy
        w: 1130
        h: 929
        c: caption shown under the photo (may be empty)
        a: alt text (defaults to the caption, or the title without tags)

Text fields are inline HTML. A "|" marks a <wbr> (allowed line-break point)
between Chinese words, so titles wrap at word boundaries on narrow screens.
"""
import html
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "news" / "index.html"
DATA = ROOT / "news" / "news.yaml"

CATS = {
    "paper":   ("論文", "Publication", "#1F3A5F"),
    "talk":    ("演講", "Talk", "#8A5A2B"),
    "conf":    ("研討會", "Conference", "#2F6F6A"),
    "teach":   ("教學", "Teaching", "#5B4B8A"),
    "service": ("服務", "Service", "#4F6475"),
    "award":   ("獲獎", "Award", "#A3781A"),
    "visit":   ("交流", "Visit", "#3F74A3"),
    "project": ("計畫", "Project", "#7A4E5C"),
}
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
I_CAP = 8  # entrance-animation index is capped at 8

PHOTO_ICON = ('<svg class="pic" viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="3" width="12" '
              'height="10" rx="1.5"/><circle cx="6" cy="6.6" r="1.2"/><path d="m2.8 12 3.6-3.4 2.4 '
              '2.2 1.8-1.6 2.6 2.4"/></svg>')
CHEVRON = '<svg class="chv" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>'


def wbr(s):
    return str(s).replace("|", "<wbr>")


def plain(s):
    return re.sub(r"<[^>]+>", "", str(s)).replace("|", "")


def render_photos(photos, title):
    ps = []
    for p in photos:
        c = str(p.get("c", "") or "")
        a = p.get("a") or plain(c) or plain(title).strip()
        ps.append({"s": "img/" + p["s"], "c": plain(c), "a": a, "w": int(p["w"]), "h": int(p["h"]),
                   "_c": c})
    key = Path(photos[0]["s"]).stem.replace("-", "")
    pid = "ph" + key
    sar = sum(p["w"] / p["h"] for p in ps)
    data = json.dumps([{k: p[k] for k in ("s", "c", "a", "w", "h")} for p in ps], ensure_ascii=False)
    out = [f'<div class="phw"><button class="pht" type="button" aria-expanded="false" '
           f'aria-controls="{pid}">{PHOTO_ICON}<span>照片</span>{CHEVRON}</button>'
           f'<div class="phc" id="{pid}"><div class="phi">'
           f'<figure class="ph n{len(ps)}" data-set="{html.escape(data, quote=True)}">'
           f'<div class="pg" style="--sar:{sar:.4f};--n:{len(ps)}">']
    for i, p in enumerate(ps):
        ar = p["w"] / p["h"]
        stem, ext = p["s"].rsplit(".", 1)
        small = f"{stem}_s.{ext}"
        label = "檢視照片" + (f"：{p['c']}" if p["c"] else "")
        if p["w"] > 900:
            img = (f'<img src="{small}" srcset="{small} 900w, {p["s"]} {p["w"]}w" '
                   f'sizes="(max-width:640px) 92vw, 600px" ')
        else:
            img = f'<img src="{p["s"]}" '
        img += (f'width="{p["w"]}" height="{p["h"]}" loading="lazy" decoding="async" '
                f'alt="{html.escape(p["a"], quote=True)}">')
        out.append(f'<button class="pt" type="button" data-i="{i}" style="--ar:{ar:.4f}" '
                   f'aria-label="{html.escape(label, quote=True)}">{img}</button>')
    out.append("</div>")
    caps = [p["_c"] for p in ps if p["_c"]]
    if caps:
        out.append(f"<figcaption>{wbr(' / '.join(caps))}</figcaption>")
    out.append("</figure></div></div></div>")
    return "".join(out)


def render_item(it, gi, first, last):
    cat = it["cat"]
    zh, en, col = CATS[cat]
    ym = str(it["ym"])
    y, m = ym.split("-")
    m = int(m)
    cls = ["it"]
    if gi == 0:
        cls.append("lead")
    if last:
        cls.append("lv")
    cls.append("hv")
    if first:
        cls.append("f1")
    to = it.get("to")
    if to:
        t = (f'<time class="dt" datetime="{ym}" title="{y} 年 {m}-{to} 月"><b class="num rg">{m}'
             f'<span class="dash">–</span>{to}</b><span class="mz">月</span>'
             f'<em>{MON[m-1]}–{MON[int(to)-1]}</em></time>')
    else:
        t = (f'<time class="dt" datetime="{ym}" title="{y} 年 {m} 月"><b class="num">{m}</b>'
             f'<span class="mz">月</span><em>{MON[m-1]}</em></time>')
    title = wbr(it["title"])
    if it.get("link"):
        title += (f'<a class="pill" href="{it["link"]}" target="_blank" rel="noopener" '
                  f'aria-label="開啟連結（新分頁）">Link<span aria-hidden="true">↗</span></a>')
    body = [f'<p class="meta"><span class="tag" style="--c:{col}"><i></i>{zh}<span class="te"> {en}'
            f'</span></span><span class="new" hidden>NEW</span></p><h3 class="tt">{title}</h3>']
    n = 0
    for line in it.get("body") or []:
        (k, v), = line.items()
        if k == "li":
            n += 1
            body.append(f'<p class="li"><span class="n num">{n}.</span><span>{wbr(v)}</span></p>')
        elif k == "ln":
            body.append(f'<p class="ln">{wbr(v)}</p>')
        elif k in ("kv", "kv_t"):
            c = "kv kv-t" if k == "kv_t" else "kv"
            body.append(f'<p class="{c}"><span class="k">{wbr(v[0])}</span>'
                        f'<span class="v">{wbr(v[1])}</span></p>')
        else:
            raise ValueError(f"unknown body line type {k!r} in {ym} {plain(it['title'])}")
    if it.get("photos"):
        body.append(render_photos(it["photos"], it["title"]))
    return (f'<article class="{" ".join(cls)}" data-cat="{cat}" data-ym="{ym}" '
            f'style="--i:{min(gi, I_CAP)};--c:{col}">{t}<div class="bd">{"".join(body)}</div></article>')


def render(items):
    for it in items:
        it["ym"] = str(it["ym"])
        if it["cat"] not in CATS:
            raise ValueError(f"unknown cat {it['cat']!r}")
    years = []
    for it in items:
        y = it["ym"][:4]
        if not years or years[-1] != y:
            years.append(y)
    secs, gi = [], 0
    for y in years:
        ys = [it for it in items if it["ym"][:4] == y]
        arts = []
        for k, it in enumerate(ys):
            arts.append(render_item(it, gi, k == 0, k == len(ys) - 1))
            gi += 1
        secs.append(f'<section class="yr" id="y{y}" data-y="{y}" aria-labelledby="yh{y}">'
                    f'<h2 class="yh" id="yh{y}"><span class="num">{y}</span></h2>'
                    f'<div class="its">{"".join(arts)}</div></section>')
    main = '<main class="news sheet" id="main">' + "".join(secs) + "</main>"
    yj = ('<div class="yj" aria-label="年份">'
          + "".join(f'<a href="#y{y}" data-y="{y}" class="num">{y}</a>' for y in years) + "</div>")
    return main, yj


def build(page_html, items):
    main, yj = render(items)
    page_html, n1 = re.subn(r'<main class="news sheet" id="main">.*?</main>', lambda _: main,
                            page_html, count=1, flags=re.S)
    page_html, n2 = re.subn(r'<div class="yj" aria-label="年份">.*?</div>', lambda _: yj,
                            page_html, count=1, flags=re.S)
    if n1 != 1 or n2 != 1:
        raise SystemExit("could not find the <main> or year-jump block in news/index.html")
    return page_html


def main():
    items = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    old = PAGE.read_text(encoding="utf-8")
    new = build(old, items)
    if "--check" in sys.argv:
        if new != old:
            print("news/index.html is out of date: run python3 tools/build_news.py")
            sys.exit(1)
        print("news/index.html is up to date")
        return
    if new == old:
        print("no change")
        return
    PAGE.write_text(new, encoding="utf-8")
    print(f"wrote {PAGE.relative_to(ROOT)} ({len(items)} items)")


if __name__ == "__main__":
    main()
