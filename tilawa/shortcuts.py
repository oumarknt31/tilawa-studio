"""Make the app open like any other: "Tilawa Studio" in the Applications folder
(Mac: Launchpad, Spotlight, Dock) or in the Start menu and on the desktop
(Windows). Created on the user's computer by the installer, so macOS does not
block it as a download from the internet."""

from __future__ import annotations

import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
ASSETS = Path(__file__).resolve().parent / "assets"
NAME = "Tilawa Studio"


def _python() -> Path:
    venv = APP_DIR / ".venv"
    return venv / ("Scripts/pythonw.exe" if os.name == "nt" else "bin/python")


def mac_app(dest: Path | None = None) -> Path:
    """~/Applications/Tilawa Studio.app: starts the app in its own window."""
    dest = dest or Path.home() / "Applications"
    app = dest / f"{NAME}.app"
    shutil.rmtree(app, ignore_errors=True)
    (app / "Contents" / "MacOS").mkdir(parents=True)
    (app / "Contents" / "Resources").mkdir()
    shutil.copy2(ASSETS / "icon.icns", app / "Contents" / "Resources" / "icon.icns")
    plist = {
        "CFBundleName": NAME, "CFBundleDisplayName": NAME, "CFBundleIdentifier": "org.tilawastudio.app",
        "CFBundleExecutable": "tilawa-studio", "CFBundleIconFile": "icon", "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "1.0", "CFBundleVersion": "1", "LSMinimumSystemVersion": "11.0",
        "NSHighResolutionCapable": True, "LSApplicationCategoryType": "public.app-category.video",
        # Python may be a universal binary: run it natively, not under Rosetta
        "LSArchitecturePriority": ["arm64", "x86_64"], "LSRequiresNativeExecution": True,
    }
    with open(app / "Contents" / "Info.plist", "wb") as f:
        plistlib.dump(plist, f)
    logs = Path.home() / "Tilawa Studio" / "logs"
    launcher = app / "Contents" / "MacOS" / "tilawa-studio"
    launcher.write_text(f"""#!/bin/bash
# Tilawa Studio: opens the app installed in {APP_DIR}
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
mkdir -p "{logs}"
cd "{APP_DIR}" || exit 1
# a universal Python started from an app may pick Intel (Rosetta): ask for Apple Silicon
if [ "$(sysctl -n hw.optional.arm64 2>/dev/null)" = "1" ]; then ARCH=(arch -arm64); else ARCH=(); fi
exec "${{ARCH[@]}}" "{_python()}" -m tilawa.cli desktop >> "{logs}/app.log" 2>&1
""")
    launcher.chmod(0o755)
    # tell Finder / Launchpad about the new (or changed) app
    subprocess.run(["/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister",
                    "-f", str(app)], capture_output=True)
    subprocess.run(["touch", str(app)], capture_output=True)
    return app


def windows_shortcuts() -> list[Path]:
    """Start menu and desktop shortcuts that start the app without a console window."""
    targets = []
    appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    for folder in (appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs", Path.home() / "Desktop"):
        if folder.exists():
            targets.append(folder / f"{NAME}.lnk")
    for lnk in targets:
        ps = (f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}'); "
              f"$s.TargetPath = '{_python()}'; $s.Arguments = '-m tilawa.cli desktop'; "
              f"$s.WorkingDirectory = '{APP_DIR}'; $s.IconLocation = '{ASSETS / 'icon.ico'}'; $s.Save()")
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)
    return targets


def install() -> list[Path]:
    if sys.platform == "darwin":
        return [mac_app()]
    if os.name == "nt":
        return windows_shortcuts()
    return []


if __name__ == "__main__":
    for p in install():
        print(p)
