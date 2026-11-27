#!/usr/bin/env python3
"""Prepare a photo for a News item and print the YAML lines to paste.

Usage (from the repo root):
    python3 tools/prep_photo.py ~/Downloads/IMG_1234.jpg 2026-12_some_event_1 [--caption "合影"]

Writes news/img/<name>.jpg (long side at most 1800 px) and, when wider than
900 px, news/img/<name>_s.jpg (900 px wide). Rotation from the camera is
applied and all metadata (EXIF, GPS location) is removed.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "news" / "img"


def save(im, path):
    im.convert("RGB").save(path, "JPEG", quality=85, optimize=True, progressive=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("name", help="file stem, e.g. 2026-12_some_event_1 (YYYY-MM_topic_N)")
    ap.add_argument("--caption", default="")
    a = ap.parse_args()

    im = ImageOps.exif_transpose(Image.open(a.src))
    im.thumbnail((1800, 1800), Image.LANCZOS)
    OUT.mkdir(parents=True, exist_ok=True)
    save(im, OUT / f"{a.name}.jpg")
    w, h = im.size
    if w > 900:
        s = im.resize((900, round(h * 900 / w)), Image.LANCZOS)
        save(s, OUT / f"{a.name}_s.jpg")
    print("  photos:")
    print(f"  - s: {a.name}.jpg")
    print(f"    w: {w}")
    print(f"    h: {h}")
    if a.caption:
        print(f"    c: {a.caption}")


if __name__ == "__main__":
    main()
