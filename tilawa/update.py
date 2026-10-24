"""Version of the app and updates from GitHub Releases, from inside the app.

The app is built by the release workflow (packaging/build.py): a folder with
its own Python, which writes its version to tilawa/VERSION. An update
downloads the new build next to the installed one, checks it against the
release's SHA256SUMS.txt, and when the app quits a small script swaps the two
folders and opens the new version. Projects, videos, the model and the logo
are in the home folder and the caches, outside the app: they stay.

Copies installed the old way (the source code with a uv environment, in
~/Tilawa Studio/Application) move to the built app the same way; a git
checkout is a development copy and is never updated."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import zipfile
from pathlib import Path

REPO = "oumarknt31/tilawa-studio"
PKG = Path(__file__).resolve().parent
NAME = "Tilawa Studio"
MAC, WIN = sys.platform == "darwin", os.name == "nt"
ASSET = "TilawaStudio-macOS.zip" if MAC else "TilawaStudio-Windows.zip"
_cache: dict = {}
_pending: dict = {}  # an update ready to be swapped in when the app quits
_applying = threading.Lock()  # one download at a time: a second one would delete the staged build


def _get(url: str, timeout: float = 15):
    import certifi
    import ssl

    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(url, headers={"User-Agent": "tilawa-studio", "Accept": "application/vnd.github+json"})
    return urllib.request.urlopen(req, timeout=timeout, context=ctx)


def kind() -> str:
    """"app" (built release), "legacy" (installed from the source code), or "dev" (a git checkout)."""
    if (PKG / "VERSION").exists():
        return "app"
    if (PKG.parent / ".git").exists():
        return "dev"
    return "legacy"


def current() -> str | None:
    if kind() == "app":
        return (PKG / "VERSION").read_text().strip()
    if kind() == "legacy":
        try:
            return (PKG.parent / ".version").read_text().strip()[:7] or "legacy"
        except OSError:
            return "legacy"
    return None


def app_path() -> Path:
    """The installed app: Tilawa Studio.app (macOS) or the Tilawa Studio folder (Windows)."""
    exe = Path(sys.executable).resolve()
    if kind() == "app":
        return exe.parents[2] if MAC else exe.parents[1]
    # an old install moves to the usual place
    if MAC:
        return Path.home() / "Applications" / f"{NAME}.app"
    return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Programs" / NAME


def _version_key(v: str) -> tuple:
    return tuple(int(x) if x.isdigit() else 0 for x in v.lstrip("v").split("-")[0].split("."))


def latest() -> dict:
    """The newest release (cached for an hour): {tag, date, message, assets}."""
    if _cache.get("t", 0) > time.time() - 3600:
        return _cache["latest"]
    with _get(f"https://api.github.com/repos/{REPO}/releases/latest") as r:
        rel = json.load(r)
    info = {"tag": rel["tag_name"], "date": rel.get("published_at"), "message": rel.get("name") or rel["tag_name"],
            "assets": {a["name"]: a["browser_download_url"] for a in rel.get("assets", [])}}
    _cache.update(t=time.time(), latest=info)
    return info


def check() -> dict:
    k = kind()
    if k == "dev" or not (MAC or WIN):
        return {"available": False, "dev": True}
    try:
        new = latest()
    except Exception:
        return {"available": False, "offline": True, "current": current()}
    available = ASSET in new["assets"] and (k == "legacy" or _version_key(new["tag"]) > _version_key(current() or "0"))
    return {"available": available, "current": current(), **{x: new[x] for x in ("tag", "date", "message")}}


def apply(progress) -> str:
    """Download the new version next to the installed one; it is swapped in when the app quits (restart())."""
    if kind() == "dev":
        raise RuntimeError("development copy: update with git")
    if not _applying.acquire(blocking=False):
        raise RuntimeError("an update is already downloading")
    try:
        return _apply(progress)
    finally:
        _applying.release()


def _apply(progress) -> str:
    new = latest()
    if _pending.get("tag") == new["tag"] and _pending["built"].exists():
        progress("done", 1.0)
        return new["tag"]
    url, sums_url = new["assets"].get(ASSET), new["assets"].get("SHA256SUMS.txt")
    if not url:
        raise RuntimeError("no build for this computer in the latest release")
    target = app_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = target.parent / f".{NAME}-update"
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir()
    archive = stage / ASSET
    h = hashlib.sha256()
    with _get(url, timeout=60) as r, open(archive, "wb") as f:
        size, done = int(r.headers.get("Content-Length") or 0), 0
        while chunk := r.read(1 << 20):
            f.write(chunk)
            h.update(chunk)
            done += len(chunk)
            if size:
                progress("fetch_update", 0.85 * done / size)
    if sums_url:
        with _get(sums_url) as r:
            sums = dict(line.split()[::-1] for line in r.read().decode().splitlines() if line.strip())
        if sums.get(ASSET) != h.hexdigest():
            shutil.rmtree(stage, ignore_errors=True)
            raise RuntimeError("the download is damaged (checksum mismatch), try again")
    progress("install", 0.9)
    if MAC:  # ditto keeps the app's permissions and links
        subprocess.run(["ditto", "-x", "-k", str(archive), str(stage)], check=True)
    else:
        with zipfile.ZipFile(archive) as z:
            z.extractall(stage)
    archive.unlink()
    built = stage / (f"{NAME}.app" if MAC else NAME)
    if not built.exists():
        raise RuntimeError("the download does not contain the app")
    _pending.update(built=built, target=target, stage=stage, tag=new["tag"])
    progress("done", 1.0)
    return new["tag"]


def restart() -> None:
    """Quit; a script waits for this process to end, puts the new version in place (if one is
    ready) and opens the app."""
    pid = os.getpid()
    built, target, stage = _pending.get("built"), _pending.get("target") or app_path(), _pending.get("stage")
    # the old install (source code + uv environment) is removed once replaced: on macOS only, where
    # the old installer always put it in ~/Tilawa Studio/Application (on Windows it is wherever it was unzipped)
    old = PKG.parent
    legacy = old if kind() == "legacy" and MAC and old.name == "Application" and old.parent.name == NAME else None
    if WIN:
        exe = target / "python" / "pythonw.exe"
        swap = ""
        if built:
            swap = (f"if (Test-Path '{built}') {{ "
                    f"if (Test-Path '{target}') {{ Rename-Item '{target}' '{target}.old' }}; "
                    f"try {{ Move-Item '{built}' '{target}' -EA Stop; Remove-Item '{target}.old','{stage}' -Recurse -Force -EA SilentlyContinue }} "
                    f"catch {{ if (Test-Path '{target}.old') {{ Rename-Item '{target}.old' '{target}' }} }}; "
                    f"& '{target / 'python' / 'python.exe'}' -m tilawa.shortcuts }}; ")
        if legacy and built:
            swap += f"if (Test-Path '{target}') {{ Remove-Item '{legacy}' -Recurse -Force -EA SilentlyContinue }}; "
        script = (f"while (Get-Process -Id {pid} -EA SilentlyContinue) {{ Start-Sleep -Milliseconds 300 }}; {swap}"
                  f"Start-Process '{exe}' -ArgumentList '-m','tilawa.cli','desktop' -WorkingDirectory '{target}'")
        subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", script],
                         creationflags=0x08000000)
    else:
        swap = ""
        if built:
            swap = (f'if [ -d "{built}" ]; then rm -rf "{target}.old"; [ -e "{target}" ] && mv "{target}" "{target}.old"; '
                    f'if mv "{built}" "{target}"; then rm -rf "{target}.old" "{stage}"; else mv "{target}.old" "{target}"; fi; '
                    f'xattr -dr com.apple.quarantine "{target}" 2>/dev/null; fi; ')
        if legacy and built:
            swap += f'[ -d "{target}" ] && rm -rf "{legacy}"; '
        opener = f'open "{target}"' if MAC and (built or kind() == "app") else \
            subprocess.list2cmdline([sys.executable, "-m", "tilawa.cli", *sys.argv[1:]])
        subprocess.Popen(["/bin/sh", "-c", f"while kill -0 {pid} 2>/dev/null; do sleep 0.3; done; {swap}{opener}"],
                         start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os._exit(0)
