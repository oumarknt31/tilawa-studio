"""Command line.

  tilawa                      open the app in the browser
  tilawa desktop              open the app in its own window
  tilawa make SOURCE [--surah 23 --from 84] --reciter "Muhammad Dibirov" [--format 16:9 --lang en]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

HOME = Path(os.environ.get("TILAWA_HOME") or Path.home() / "Tilawa Studio")


def _bar(stage: str, f: float, _state={"t": 0.0}):
    now = time.time()
    if f < 1 and now - _state["t"] < 0.2:
        return
    _state["t"] = now
    n = int(f * 30)
    sys.stderr.write(f"\r  {stage:<10} [{'#' * n}{'.' * (30 - n)}] {f * 100:5.1f}%")
    if f >= 1:
        sys.stderr.write("\n")


def make(args) -> int:
    from . import project, render
    from .library import Library

    lib = Library(HOME)
    render.USER_FONTS = lib.fonts_dir
    render.USER_LOGO, render.LOGO_AUTO = lib.logo_file, lib.settings().get("logo_auto", True)
    slug = re.sub(r"[^\w-]+", "-", f"{args.surah or 'auto'}-{args.first}-{time.strftime('%Y%m%d-%H%M%S')}")
    folder = (Path(args.out) if args.out else HOME) / "projects" / slug
    print(f"Project: {folder}")
    p = project.create(folder, args.source, args.surah, args.first, args.last, args.reciter, args.title or "", _bar,
                       args.format, args.lang, lib.style(args.style))
    p.render.update({k: v for k, v in (("size", args.size), ("quality", args.quality), ("fit", args.fit)) if v})
    project.analyze(p, _bar)
    print(f"Surah {p.surah}, verses {project.found_verses(p)}")
    for b in p.blocks:
        label = f"{b['ayah']:>3}" if b["kind"] == "verse" else b["kind"][:3]
        print(f"  {b['start']:6.2f}-{b['end']:6.2f}  [{label}] {b['fr'][:70]}")
    out = project.make_video(p, Path(args.out) if args.out else HOME, _bar)
    print(f"\nDone: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tilawa", description="Quran recitation videos with Arabic, French and phonetic subtitles.")
    sub = ap.add_subparsers(dest="cmd")
    app = sub.add_parser("app", help="open the app (default)")
    app.add_argument("--port", type=int, default=8765)
    app.add_argument("--no-browser", action="store_true")
    d = sub.add_parser("desktop", help="open the app in its own window")
    d.add_argument("--port", type=int, default=8765)
    m = sub.add_parser("make", help="make a video without the editor")
    m.add_argument("source", help="video file or link (YouTube, Instagram, TikTok...)")
    m.add_argument("--surah", type=int, default=0, help="found in the recitation if omitted")
    m.add_argument("--from", dest="first", type=int, default=1, help="first verse recited")
    m.add_argument("--to", dest="last", type=int, help="last verse (found automatically if omitted)")
    m.add_argument("--reciter", default="")
    m.add_argument("--title", help='defaults to "SOURATE <NAME>"')
    m.add_argument("--format", default="9:16", choices=["9:16", "16:9", "1:1", "4:5"])
    m.add_argument("--lang", default="fr", help="translation: fr, en, es, de, it, pt, nl, sv, tr, id, ms, bs, sq, ru, ur, none")
    m.add_argument("--style", help="style preset id (pieux, mushaf, moderne, doux, elegant, calligraphie; "
                   "for 16:9: cinema, pieux-youtube, bandeau, bandeau-titre, cinema-dore, minimal)")
    m.add_argument("--size", choices=["auto", "hd", "2k", "4k"])
    m.add_argument("--quality", choices=["max", "high", "hevc", "prores", "studio"])
    m.add_argument("--fit", choices=["auto", "crop", "blur", "pad"])
    m.add_argument("--out", help=f"output folder (default: {HOME})")
    args = ap.parse_args(argv)
    if args.cmd == "make":
        return make(args)
    if args.cmd == "desktop":
        from . import desktop

        desktop.run(port=args.port)
        return 0
    from . import server

    server.run(port=getattr(args, "port", 8765), open_browser=not getattr(args, "no_browser", False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
