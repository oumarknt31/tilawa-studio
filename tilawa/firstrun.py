"""What the app needs besides itself, downloaded once and kept across updates:
the browser that draws the text (Playwright's headless Chromium) and the
recitation model (1.2 GB). `tilawa setup` gets both (the installer runs it);
`tilawa smoke` checks that a built app works (the release workflow runs it).
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

BROWSER = "chromium-headless-shell"  # what render.OverlayRenderer launches (headless)


def _say(fr: str, en: str) -> None:
    print(f"-> {fr} / {en}", flush=True)


def browser_ready() -> bool:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            return Path(pw.chromium.executable_path).exists() or _headless_shell_exists(pw)
    except Exception:
        return False


def _headless_shell_exists(pw) -> bool:
    try:
        b = pw.chromium.launch()
        b.close()
        return True
    except Exception:
        return False


def install_browser() -> None:
    subprocess.run([sys.executable, "-m", "playwright", "install", BROWSER], check=True)


def ensure_browser() -> None:
    """Get the browser if it is missing (a new version of the app may need another one)."""
    if not browser_ready():
        install_browser()


def setup() -> int:
    _say("Moteur de dessin du texte", "Text drawing engine")
    ensure_browser()
    _say("ffmpeg", "ffmpeg")
    from . import media

    media.tools()
    _say("Modèle de reconnaissance de la récitation (~1,2 Go, une seule fois)",
         "Recitation recognition model (~1.2 GB, once)")
    from . import align

    align.get_model()
    _say("Prêt", "Ready")
    return 0


def smoke() -> int:
    """Start the server, draw a subtitle, encode a short video: the parts a broken build would break."""
    from . import align, media, render, server  # noqa: F401  (imports torch and transformers too)

    ff, fp = media.tools()
    subprocess.run([ff, "-hide_banner", "-version"], check=True, capture_output=True)
    # the link downloader merges video and audio with that same ffmpeg
    import yt_dlp
    from yt_dlp.postprocessor.ffmpeg import FFmpegPostProcessor

    with yt_dlp.YoutubeDL({"ffmpeg_location": str(Path(ff).parent), "quiet": True}) as ydl:
        assert FFmpegPostProcessor(ydl).available, "yt-dlp does not find ffmpeg"
    ensure_browser()
    tmp = Path(tempfile.mkdtemp())
    r = render.OverlayRenderer(1080, 1920)
    try:
        png, _ = r.png(tmp / "header.png", {}, {"title": "SOURATE AL-FATIHA", "reciter": "Test", "visible": True})
    finally:
        r.close()
    assert png.stat().st_size > 1000, "overlay not drawn"
    info_args, ext, pix = render._encode_args(None, render.RenderOptions())
    out = tmp / f"test{ext}"
    subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=640x360:d=1",
                    "-pix_fmt", pix, *info_args, str(out)], check=True)
    assert out.stat().st_size > 1000, "video not encoded"
    os.environ.setdefault("TILAWA_HOME", str(tmp / "home"))
    port = 8799
    threading.Thread(target=server.run, kwargs={"port": port, "open_browser": False}, daemon=True).start()
    for _ in range(100):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/languages", timeout=1) as resp:
                assert resp.status == 200
                break
        except OSError:
            time.sleep(0.2)
    else:
        raise AssertionError("server did not start")
    import torch

    print(f"smoke test passed (torch {torch.__version__}, ffmpeg {Path(ff).name}, encoder {info_args[1]})", flush=True)
    os._exit(0)  # without waiting for the server thread (it would start loading the model)
