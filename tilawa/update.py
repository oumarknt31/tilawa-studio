"""Version of the installed app and updates from GitHub, from inside the app.

The installer writes the commit it installed to `.version` in the app folder.
An update downloads the latest code over the app folder (projects, videos and
the Python environment are elsewhere or kept), refreshes the components with
uv, and the app restarts."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

REPO = "oumarknt31/tilawa-studio"
APP_DIR = Path(__file__).resolve().parent.parent
VERSION_FILE = APP_DIR / ".version"
_cache: dict = {}


def _get(url: str, timeout: float = 10) -> bytes:
    import certifi
    import ssl

    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(url, headers={"User-Agent": "tilawa-studio", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read()


def current() -> str | None:
    """Commit installed, or None for a development copy (a git checkout)."""
    if (APP_DIR / ".git").exists():
        return None
    try:
        return VERSION_FILE.read_text().strip() or None
    except OSError:
        return None


def latest() -> dict:
    """Newest commit on GitHub (cached for an hour): {sha, date, message}."""
    if _cache.get("t", 0) > time.time() - 3600:
        return _cache["latest"]
    c = json.loads(_get(f"https://api.github.com/repos/{REPO}/commits/main"))
    info = {"sha": c["sha"], "date": c["commit"]["committer"]["date"], "message": c["commit"]["message"].split("\n")[0]}
    _cache.update(t=time.time(), latest=info)
    return info


def check() -> dict:
    cur = current()
    if cur is None:
        return {"available": False, "dev": True}
    try:
        new = latest()
    except Exception:
        return {"available": False, "offline": True, "current": cur}
    return {"available": new["sha"] != cur, "current": cur, **new}


def _uv() -> str:
    for c in (shutil.which("uv"), Path.home() / ".local" / "bin" / ("uv.exe" if os.name == "nt" else "uv")):
        if c and Path(c).exists():
            return str(c)
    raise RuntimeError("uv not found")


def apply(progress) -> str:
    """Download and install the latest version; returns its commit."""
    if current() is None:
        raise RuntimeError("development copy: update with git")
    new = latest()
    progress("fetch_update", 0.1)
    data = _get(f"https://codeload.github.com/{REPO}/tar.gz/{new['sha']}", timeout=120)
    progress("fetch_update", 0.5)
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        for m in tar.getmembers():
            parts = Path(m.name).parts[1:]  # drop the "repo-sha/" top folder
            if not parts or ".." in parts or m.issym() or m.islnk():
                continue
            dst = APP_DIR.joinpath(*parts)
            if m.isdir():
                dst.mkdir(parents=True, exist_ok=True)
            elif m.isfile():
                dst.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(m) as src, open(dst, "wb") as out:
                    shutil.copyfileobj(src, out)
                os.chmod(dst, m.mode & 0o777 | 0o600)
    progress("install", 0.7)
    subprocess.run([_uv(), "sync", "--no-dev"], cwd=APP_DIR, check=True, capture_output=True)
    VERSION_FILE.write_text(new["sha"])
    if sys.platform == "darwin":  # refresh the app in the Applications folder (icon, launcher)
        from . import shortcuts

        shortcuts.install()
    progress("done", 1.0)
    return new["sha"]


def restart() -> None:
    """Start the app again in a new process (once this one has freed the port) and leave."""
    args = [sys.executable, "-m", "tilawa.cli", *sys.argv[1:]]
    if os.name == "nt":
        subprocess.Popen(["cmd", "/c", "timeout /t 2 >nul & " + subprocess.list2cmdline(args)], cwd=APP_DIR,
                         creationflags=0x08000000)  # no console window
    else:
        subprocess.Popen(["/bin/sh", "-c", 'sleep 2; exec "$@"', "sh", *args], cwd=APP_DIR, start_new_session=True)
    os._exit(0)
