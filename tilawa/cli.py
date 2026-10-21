"""Command line.

  tilawa                      open the app in the browser
  tilawa make SOURCE --surah 23 --from 84 --reciter "Muhammad Dibirov"
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
    from . import project

    slug = re.sub(r"[^\w-]+", "-", f"{args.surah}-{args.first}-{time.strftime('%Y%m%d-%H%M%S')}")
    folder = (Path(args.out) if args.out else HOME) / "projects" / slug
    print(f"Project: {folder}")
    p = project.create(folder, args.source, args.surah, args.first, args.last, args.reciter, args.title or "", _bar)
    p.render.update({k: v for k, v in (("size", args.size), ("quality", args.quality), ("fit", args.fit)) if v})
    project.analyze(p, _bar)
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
    m = sub.add_parser("make", help="make a video without the editor")
    m.add_argument("source", help="video file or link (YouTube, Instagram, TikTok...)")
    m.add_argument("--surah", type=int, required=True)
    m.add_argument("--from", dest="first", type=int, required=True, help="first verse recited")
    m.add_argument("--to", dest="last", type=int, help="last verse (found automatically if omitted)")
    m.add_argument("--reciter", default="")
    m.add_argument("--title", help='defaults to "SOURATE <NAME>"')
    m.add_argument("--size", choices=["auto", "1080x1920", "1440x2560", "2160x3840"])
    m.add_argument("--quality", choices=["max", "high", "hevc", "prores"])
    m.add_argument("--fit", choices=["auto", "crop", "blur", "pad"])
    m.add_argument("--out", help=f"output folder (default: {HOME})")
    args = ap.parse_args(argv)
    if args.cmd == "make":
        return make(args)
    from . import server

    server.run(port=getattr(args, "port", 8765), open_browser=not getattr(args, "no_browser", False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
