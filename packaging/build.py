"""Build the desktop app: a self-contained folder with its own Python and
every component installed, zipped for a GitHub Release.

    python packaging/build.py [--version v1.2.0]

macOS:   dist/Tilawa Studio.app      -> dist/TilawaStudio-macOS.zip
Windows: dist/Tilawa Studio/          -> dist/TilawaStudio-Windows.zip

The Python is a relocatable build (python-build-standalone, through uv), so
the folder works wherever it is copied. Nothing is compiled or resolved on
the user's computer; the recognition model (1.2 GB) and the browser that
draws the text are downloaded once by `tilawa setup` (run by the installer),
and kept across updates.
"""

from __future__ import annotations

import argparse
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
NAME = "Tilawa Studio"
PY = "3.12"
MAC = sys.platform == "darwin"
WIN = os.name == "nt"


def run(*cmd, **kw):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def run_py(py: Path, *args, **kw):
    """The app's Python, isolated (-I): it sees only what is installed in it, never this source folder."""
    return run(py, "-I", *args, cwd=DIST, **kw)


def python_home() -> Path:
    """A fresh relocatable Python, copied from uv's managed builds."""
    run("uv", "python", "install", PY)
    exe = Path(subprocess.run(["uv", "python", "find", "--managed-python", PY], capture_output=True, text=True,
                              check=True).stdout.strip())
    home = exe.parent.parent if not WIN else exe.parent
    return home.resolve()


def build(version: str) -> Path:
    shutil.rmtree(DIST, ignore_errors=True)
    if MAC:
        app = DIST / f"{NAME}.app"
        contents = app / "Contents"
        py_dir = contents / "Resources" / "python"
    else:
        app = DIST / NAME
        py_dir = app / "python"
    shutil.copytree(python_home(), py_dir, symlinks=True)
    for f in py_dir.rglob("EXTERNALLY-MANAGED"):  # uv's mark: this copy is ours to install into
        f.unlink()
    py = py_dir / ("python.exe" if WIN else "bin/python3")

    # the exact versions of uv.lock, then the app itself
    req = DIST / "requirements.txt"
    run("uv", "export", "--frozen", "--no-dev", "--no-hashes", "--no-emit-project", "-o", req, cwd=ROOT)
    run("uv", "pip", "install", "--python", py, "--break-system-packages", "-r", req)
    run("uv", "pip", "install", "--python", py, "--break-system-packages", "--no-deps", ROOT)
    req.unlink()
    site = Path(run_py(py, "-c", "import tilawa, pathlib; print(pathlib.Path(tilawa.__file__).parent.parent)",
                       capture_output=True, text=True).stdout.strip())
    assert py_dir in site.parents, site  # the installed copy, not the sources
    (site / "tilawa" / "VERSION").write_text(version)
    # ffmpeg inside the app (static build, with VideoToolbox on macOS)
    run_py(py, "-c", "from tilawa import media; print(media.tools())")
    if WIN:
        vc_runtime(site)
    prune(site)
    run_py(py, "-m", "compileall", "-q", "-j", "0", site)

    if MAC:
        mac_bundle(app, contents, version)
    else:
        (app / "VERSION").write_text(version)
    return app


def vc_runtime(site: Path) -> None:
    """PyTorch on Windows needs Microsoft's C++ runtime: its DLLs go next to torch's (allowed by
    Microsoft for apps), so a friend's computer does not need it installed."""
    system = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
    for dll in ("msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll", "vcruntime140.dll", "vcruntime140_1.dll",
                "concrt140.dll", "vcomp140.dll"):
        src, dst = system / dll, site / "torch" / "lib" / dll
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)


def prune(site: Path) -> None:
    """What a running app never uses: headers, tests, caches (smaller download, shorter paths on Windows)."""
    for pattern in ("torch/include", "torch/share", "torch/test", "torch/testing/_internal/data", "caffe2",
                    "numpy/*/tests", "*/tests", "pip", "setuptools"):
        for p in site.glob(pattern):
            if p.is_dir() and p.name not in ("site-packages",):
                shutil.rmtree(p, ignore_errors=True)
    for p in site.rglob("__pycache__"):
        shutil.rmtree(p, ignore_errors=True)


def mac_bundle(app: Path, contents: Path, version: str) -> None:
    macos = contents / "MacOS"
    macos.mkdir(parents=True)
    shutil.copy2(ROOT / "tilawa" / "assets" / "icon.icns", contents / "Resources" / "icon.icns")
    # the Python executable inside Contents/MacOS: macOS then sees the app itself running
    # (its name and icon in the Dock and the menu bar), not "Python"
    py_bin = contents / "Resources" / "python" / "bin"
    real = (py_bin / "python3").resolve()
    shutil.copy2(real, macos / "tilawa-python")
    launcher = macos / NAME
    launcher.write_text(f"""#!/bin/bash
# {NAME} {version}: the app's own Python, started from inside the app
DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONHOME="$DIR/../Resources/python" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
mkdir -p "$HOME/{NAME}/logs"
exec "$DIR/tilawa-python" -m tilawa.cli desktop "$@" >> "$HOME/{NAME}/logs/app.log" 2>&1
""")
    launcher.chmod(0o755)
    plist = {
        "CFBundleName": NAME, "CFBundleDisplayName": NAME, "CFBundleIdentifier": "org.tilawastudio.app",
        "CFBundleExecutable": NAME, "CFBundleIconFile": "icon", "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": version.lstrip("v"), "CFBundleVersion": version.lstrip("v"),
        "LSMinimumSystemVersion": "12.0", "NSHighResolutionCapable": True,
        "LSApplicationCategoryType": "public.app-category.video", "LSArchitecturePriority": ["arm64"],
        "NSMicrophoneUsageDescription": "Tilawa Studio does not use the microphone.",
    }
    with open(contents / "Info.plist", "wb") as f:
        plistlib.dump(plist, f)


def package(app: Path) -> Path:
    if MAC:
        out = DIST / "TilawaStudio-macOS.zip"
        run("ditto", "-c", "-k", "--keepParent", app, out)
    else:
        out = DIST / "TilawaStudio-Windows.zip"
        shutil.make_archive(str(out.with_suffix("")), "zip", DIST, app.name)
    print(out, f"{out.stat().st_size / 1e6:.0f} MB")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="dev")
    ap.add_argument("--no-zip", action="store_true")
    a = ap.parse_args()
    app = build(a.version)
    if not a.no_zip:
        package(app)
