"""Things shared by all projects: style presets, fonts imported by the user,
and a few remembered settings. Kept in the app's home folder (cli.HOME)."""

from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path

PKG = Path(__file__).parent

# placement depends on the format: a style preset never carries it
# a font's family name comes from inside the imported file and ends up in CSS
# and in the page: only plain names are accepted
_SAFE_FAMILY = re.compile(r"^[\w .-]{1,60}$")

POSITION_KEYS = ("--header-top", "--header-x", "--block-top", "--block-x", "--header-zoom", "--block-zoom", "--band-top")


def _grad(a: str, b: str) -> str:
    return f"linear-gradient(90deg, {a} 0%, {b} 100%)"


BUILTIN_STYLES = [
    {"id": "pieux", "name": "Le Chemin des Pieux", "builtin": True, "style": {}},
    {"id": "mushaf", "name": "Mushaf doré", "builtin": True, "style": {
        "--arabic": '"Scheherazade New"', "--ayah-mark": "circle", "--ar-size": "50px", "--num-display": "none",
        "--title-font": '"Cinzel"', "--text-font": '"Lora"',
        "--title-c1": "#f5d77a", "--title-c2": "#fff4cf", "--title-grad": _grad("#f5d77a", "#fff4cf"),
        "--reciter-c1": "#e9d8a6", "--reciter-c2": "#ffffff", "--reciter-grad": _grad("#e9d8a6", "#ffffff"),
        "--ar-color": "#fbf1d3", "--fr-color": "#ffffff", "--tr-color": "#e8c872"}},
    {"id": "moderne", "name": "Moderne", "builtin": True, "style": {
        "--arabic": '"Noto Naskh Arabic"', "--ayah-mark": "circle", "--title-font": '"Poppins"', "--text-font": '"Poppins"',
        "--title-c1": "#ffffff", "--title-c2": "#ffffff", "--title-grad": _grad("#ffffff", "#ffffff"),
        "--reciter-c1": "#b9f3ec", "--reciter-c2": "#b9f3ec", "--reciter-grad": _grad("#b9f3ec", "#b9f3ec"),
        "--fr-color": "#ffffff", "--tr-color": "#9be7ff", "--outline": "#000000", "--fr-size": "33px", "--tr-size": "27px"}},
    {"id": "doux", "name": "Douceur", "builtin": True, "style": {
        "--ayah-mark": "brackets", "--title-font": '"Nunito"', "--text-font": '"Nunito"',
        "--title-c1": "#a8e6cf", "--title-c2": "#dcedc1", "--title-grad": _grad("#a8e6cf", "#dcedc1"),
        "--reciter-c1": "#ffd3b6", "--reciter-c2": "#ffaaa5", "--reciter-grad": _grad("#ffd3b6", "#ffaaa5"),
        "--fr-color": "#fffaf0", "--tr-color": "#ffd3b6", "--outline": "#26323a"}},
    {"id": "elegant", "name": "Élégant", "builtin": True, "style": {
        "--arabic": '"Amiri"', "--ayah-mark": "circle", "--title-font": '"Playfair Display"', "--text-font": '"Playfair Display"',
        "--title-c1": "#ffffff", "--title-c2": "#d4af37", "--title-grad": _grad("#ffffff", "#d4af37"),
        "--reciter-c1": "#d4af37", "--reciter-c2": "#d4af37", "--reciter-grad": _grad("#d4af37", "#d4af37"),
        "--tr-color": "#d4af37", "--num-color": "#d4af37"}},
    {"id": "calligraphie", "name": "Calligraphie", "builtin": True, "style": {
        "--arabic": '"Aref Ruqaa"', "--ar-size": "48px", "--ayah-mark": "circle", "--title-font": '"Cinzel"', "--text-font": '"Lora"',
        "--title-c1": "#e0c3fc", "--title-c2": "#8ec5fc", "--title-grad": _grad("#e0c3fc", "#8ec5fc"),
        "--reciter-c1": "#8ec5fc", "--reciter-c2": "#e0c3fc", "--reciter-grad": _grad("#8ec5fc", "#e0c3fc")}},
    # for YouTube (16:9), from the layouts of popular recitation channels: shown for that format only
    {"id": "cinema", "name": "Cinéma", "builtin": True, "formats": ["16:9"], "style": {
        "--layout": "cinema", "--header-mode": "corner", "--emph": "bold", "--emph-weight": "600", "--stroke": "0",
        "--outline": "#000000", "--arabic": '"Amiri Quran"', "--ayah-mark": "circle", "--ar-size": "66px",
        "--title-font": '"Poppins"', "--text-font": '"Poppins"', "--fr-case": "uppercase", "--fr-size": "42px",
        "--tr-weight": "300", "--tr-size": "33px", "--title-size": "22px", "--reciter-size": "22px",
        "--title-c1": "#ffffff", "--title-c2": "#ffffff", "--title-grad": _grad("#ffffff", "#ffffff"),
        "--reciter-c1": "#ffffff", "--reciter-c2": "#ffffff", "--reciter-grad": _grad("#ffffff", "#ffffff"),
        "--fr-color": "#ffffff", "--num-color": "#ffffff", "--tr-color": "#e6e6e6", "--logo-pos": "tr"}},
    {"id": "pieux-youtube", "name": "Le Chemin des Pieux — YouTube", "builtin": True, "formats": ["16:9"], "style": {
        "--layout": "band", "--header-mode": "intro", "--emph": "color", "--stroke": "0", "--outline": "#000000",
        "--title-font": '"Cinzel"', "--text-font": '"Open Sans"', "--fr-variant": "small-caps", "--fr-weight": "500",
        "--fr-spacing": "1.5px", "--fr-size": "54px", "--num-font": '"Cinzel"', "--num-weight": "700", "--num-size": "60px",
        "--num-color": "#e9c35b", "--arabic": '"Amiri"', "--ar-size": "54px", "--ar-color": "#ffffff",
        "--tr-font": '"Cinzel"', "--tr-weight": "700", "--tr-size": "38px", "--tr-spacing": "1px", "--tr-color": "#e2b85a",
        "--title-size": "58px", "--title-c1": "#7fe3f0", "--title-c2": "#7fe3f0", "--title-grad": _grad("#7fe3f0", "#7fe3f0"),
        "--reciter-c1": "#7fe3f0", "--reciter-c2": "#7fe3f0", "--reciter-grad": _grad("#7fe3f0", "#7fe3f0"),
        "--intro-accent": "#7fe3f0", "--band-bg": "rgba(0, 0, 0, .3)", "--logo-pos": "tr", "--logo-size": "190px"}},
    {"id": "bandeau", "name": "Bandeau classique", "builtin": True, "formats": ["16:9"], "style": {
        "--layout": "band", "--header-mode": "intro", "--emph": "bold", "--stroke": "0", "--outline": "#000000",
        "--title-font": '"Arimo"', "--text-font": '"Arimo"', "--fr-case": "uppercase", "--fr-size": "52px",
        "--num-size": "64px", "--arabic": '"Amiri"', "--ar-size": "54px", "--ar-color": "#ffffff", "--tr-weight": "700",
        "--tr-size": "42px", "--tr-color": "#f6c945", "--fr-color": "#ffffff", "--num-color": "#ffffff",
        "--title-size": "56px", "--title-c1": "#ff2bd6", "--title-c2": "#ff2bd6", "--title-grad": _grad("#ff2bd6", "#ff2bd6"),
        "--reciter-c1": "#ff2bd6", "--reciter-c2": "#ff2bd6", "--reciter-grad": _grad("#ff2bd6", "#ff2bd6"),
        "--intro-accent": "#ffffff", "--band-bg": "rgba(0, 0, 0, .32)", "--logo-pos": "tr"}},
    {"id": "bandeau-titre", "name": "Bandeau titre", "builtin": True, "formats": ["16:9"], "style": {
        "--layout": "band", "--header-mode": "intro", "--stroke": "0", "--outline": "#000000", "--num-display": "none",
        "--title-font": '"Oswald"', "--text-font": '"Oswald"', "--fr-case": "uppercase", "--fr-weight": "700",
        "--fr-size": "60px", "--fr-color": "#eef6f7", "--arabic": '"Noto Naskh Arabic"', "--ar-size": "50px",
        "--tr-font": '"Lora"', "--tr-size": "38px", "--tr-color": "#f3d27a",
        "--title-size": "60px", "--title-c1": "#eef6f7", "--title-c2": "#eef6f7", "--title-grad": _grad("#eef6f7", "#eef6f7"),
        "--reciter-c1": "#f3d27a", "--reciter-c2": "#f3d27a", "--reciter-grad": _grad("#f3d27a", "#f3d27a"),
        "--intro-accent": "#f3d27a", "--band-bg": "rgba(0, 0, 0, .45)", "--logo-pos": "tr"}},
    {"id": "cinema-dore", "name": "Cinéma doré", "builtin": True, "formats": ["16:9"], "style": {
        "--layout": "cinema", "--header-mode": "intro", "--emph": "color", "--emph-colors": "#f7d98b #ffffff",
        "--stroke": "0", "--outline": "#000000", "--arabic": '"Scheherazade New"', "--ayah-mark": "circle", "--ar-size": "66px",
        "--ar-color": "#fbf1d3", "--title-font": '"Cinzel"', "--text-font": '"Cinzel"', "--fr-size": "40px", "--fr-weight": "600",
        "--fr-color": "#f5ecd7", "--num-color": "#f7d98b", "--tr-font": '"Lora"', "--tr-size": "32px", "--tr-color": "#d9c38f",
        "--title-size": "58px", "--title-c1": "#f7d98b", "--title-c2": "#fff4cf", "--title-grad": _grad("#f7d98b", "#fff4cf"),
        "--reciter-c1": "#fff4cf", "--reciter-c2": "#f7d98b", "--reciter-grad": _grad("#fff4cf", "#f7d98b"),
        "--intro-accent": "#f7d98b"}},
    {"id": "minimal", "name": "Minimal", "builtin": True, "formats": ["16:9"], "style": {
        "--layout": "cinema", "--header-mode": "corner", "--stroke": "0", "--outline": "#000000",
        "--arabic": '"Scheherazade New"', "--ayah-mark": "brackets", "--ar-size": "76px", "--text-font": '"Lora"',
        "--title-font": '"Lora"', "--fr-size": "38px", "--fr-color": "#f2f2f2", "--num-color": "#f2f2f2", "--tr-display": "none",
        "--title-size": "22px", "--reciter-size": "22px",
        "--title-c1": "#ffffff", "--title-c2": "#ffffff", "--title-grad": _grad("#ffffff", "#ffffff"),
        "--reciter-c1": "#ffffff", "--reciter-c2": "#ffffff", "--reciter-grad": _grad("#ffffff", "#ffffff")}},
]


class Library:
    def __init__(self, home: Path):
        self.home = home
        self.styles_dir = home / "styles"
        self.fonts_dir = home / "fonts"
        self.settings_file = home / "settings.json"
        self.logo_file = home / "logo.png"

    # ------------------------------------------------------------ settings
    def settings(self) -> dict:
        try:
            return json.loads(self.settings_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def update_settings(self, changes: dict) -> dict:
        s = self.settings() | changes
        self.home.mkdir(parents=True, exist_ok=True)
        self.settings_file.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
        return s

    # ------------------------------------------------------------ styles
    def styles(self) -> list[dict]:
        out = list(BUILTIN_STYLES)
        for f in sorted(self.styles_dir.glob("*.json")):
            try:
                out.append(json.loads(f.read_text(encoding="utf-8")) | {"id": f.stem, "builtin": False})
            except ValueError:
                continue
        return out

    def style(self, sid: str | None) -> dict:
        return next((s["style"] for s in self.styles() if s["id"] == sid), {})

    def save_style(self, name: str, style: dict) -> dict:
        self.styles_dir.mkdir(parents=True, exist_ok=True)
        sid = re.sub(r"[^\w-]+", "-", name.lower()).strip("-")[:40] or "style"
        if any(s["id"] == sid for s in BUILTIN_STYLES) or (self.styles_dir / f"{sid}.json").exists():
            sid += "-" + uuid.uuid4().hex[:4]
        data = {"name": name.strip()[:60] or "Mon style",
                "style": {k: str(v) for k, v in style.items() if k.startswith("--") and k not in POSITION_KEYS}}
        (self.styles_dir / f"{sid}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        return data | {"id": sid, "builtin": False}

    def delete_style(self, sid: str) -> None:
        f = self.styles_dir / f"{Path(sid).name}.json"
        f.unlink(missing_ok=True)

    # ------------------------------------------------------------ logo
    def set_logo(self, src: Path) -> dict:
        """The user's logo (channel, page...), shown on the videos whose style places it."""
        import pillow_heif
        from PIL import Image, ImageOps

        pillow_heif.register_heif_opener()
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im).convert("RGBA")  # transparency kept
            im.thumbnail((1024, 1024))
            self.home.mkdir(parents=True, exist_ok=True)
            im.save(self.logo_file, "PNG")
        return self.update_settings({"logo": self.logo_file.stat().st_mtime_ns})

    def delete_logo(self) -> dict:
        self.logo_file.unlink(missing_ok=True)
        return self.update_settings({"logo": None})

    # ------------------------------------------------------------ fonts
    def fonts(self) -> list[dict]:
        bundled = json.loads((PKG / "fonts" / "fonts.json").read_text(encoding="utf-8"))
        return [f | {"user": False} for f in bundled] + [f | {"user": True} for f in self.user_fonts()]

    def user_fonts(self) -> list[dict]:
        try:
            fonts = json.loads((self.fonts_dir / "fonts.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        return [f for f in fonts if _SAFE_FAMILY.match(str(f.get("family", "")))
                and all(re.match(r"^[\w.-]+$", str(file)) for file, _ in f.get("files", []))]

    def add_font(self, src: Path, filename: str) -> dict:
        """Import a .ttf / .otf font (e.g. the King Fahd Complex mushaf font)."""
        from PIL import ImageFont

        family, _ = ImageFont.truetype(str(src), 20).getname()
        family = re.sub(r"[^\w .-]+", "", family or "").strip()[:60] or "Police importée"
        self.fonts_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(filename).suffix.lower()
        dst = self.fonts_dir / (re.sub(r"[^\w-]+", "-", Path(filename).stem)[:50] + ext)
        shutil.copy2(src, dst)
        arabic = _has_arabic(dst)
        entry = {"family": family, "label": f"{family} (importée)", "script": "arabic" if arabic else "latin",
                 "ornament": False, "files": [[dst.name, "100 900"]]}
        fonts = [f for f in self.user_fonts() if f["family"] != family] + [entry]
        (self.fonts_dir / "fonts.json").write_text(json.dumps(fonts, ensure_ascii=False, indent=1), encoding="utf-8")
        return entry

    def delete_font(self, family: str) -> None:
        keep = []
        for f in self.user_fonts():
            if f["family"] == family:
                for file, _ in f["files"]:
                    (self.fonts_dir / Path(file).name).unlink(missing_ok=True)
            else:
                keep.append(f)
        (self.fonts_dir / "fonts.json").write_text(json.dumps(keep, ensure_ascii=False, indent=1), encoding="utf-8")


def _has_arabic(font: Path) -> bool:
    """Whether the font draws Arabic letters (alif and lam differ from a missing glyph)."""
    from PIL import Image, ImageDraw, ImageFont

    f = ImageFont.truetype(str(font), 40)

    def ink(ch):
        im = Image.new("L", (80, 80))
        ImageDraw.Draw(im).text((10, 10), ch, font=f, fill=255)
        return im.tobytes()

    missing = ink("￿")
    return ink("ب") != missing and ink("ل") != missing
