"""The app in its own window (no browser, no Terminal).

The local server runs in a background thread and the interface is shown in a
native web view (WebKit on macOS, Edge WebView2 on Windows). Closing the
window quits the app.
"""

from __future__ import annotations

import sys
import threading
import time
import urllib.request
from pathlib import Path

PKG = Path(__file__).parent


def _wait_until_up(url: str, timeout: float = 30) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(f"{url}/api/languages", timeout=1):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def _mac_identity() -> None:
    """Name and icon of the app in the menu bar and the Dock (the process is Python)."""
    try:
        from AppKit import NSApplication, NSImage
        from Foundation import NSBundle

        info = NSBundle.mainBundle().infoDictionary()
        info["CFBundleName"] = info["CFBundleDisplayName"] = "Tilawa Studio"
        icon = PKG / "assets" / "icon.png"
        if icon.exists():
            NSApplication.sharedApplication().setApplicationIconImage_(NSImage.alloc().initWithContentsOfFile_(str(icon)))
    except Exception:
        pass


def run(port: int = 8765) -> None:
    import webview

    from . import server

    url = f"http://127.0.0.1:{port}"
    server.DESKTOP = True
    if not server._already_running(url):
        threading.Thread(target=server.run, kwargs={"port": port, "open_browser": False}, daemon=True).start()
        _wait_until_up(url)
    if sys.platform == "darwin":
        _mac_identity()
    webview.settings["ALLOW_DOWNLOADS"] = True
    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True
    window = webview.create_window("Tilawa Studio", url, width=1440, height=900, min_size=(1100, 700),
                                   background_color="#0a0e11", text_select=True)

    def closing():
        # an export or analysis is running: quitting would lose it
        if server.busy():
            fr = (server.LIB.settings().get("ui") or "fr") == "fr"
            return window.create_confirmation_dialog(
                "Tilawa Studio",
                "Une vidéo est en cours de création. Quitter quand même ?" if fr
                else "A video is being made. Quit anyway?")
        return True

    window.events.closing += closing
    webview.start()
    _quit()


def _quit() -> None:
    """Stop the encodes still running and leave at once (the server thread is a daemon)."""
    import os

    from . import render

    for proc in list(render.RUNNING):
        proc.terminate()
    os._exit(0)
