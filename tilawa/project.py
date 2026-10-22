"""A project = one source video + its subtitle blocks + settings, saved as
JSON so it can be reviewed and edited before rendering."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from . import align, identify, media, quran, render, segment

Progress = Callable[[str, float], None]


@dataclass
class Project:
    folder: Path
    video: str  # file name inside the folder
    surah: int  # 0 = not known yet: found in the audio (identify.py)
    first_verse: int
    last_verse: int | None = None
    reciter: str = ""
    title: str = ""
    duration: float = 0.0
    width: int = 0  # source picture size (rotation applied)
    height: int = 0
    blocks: list[dict] = field(default_factory=list)
    render: dict = field(default_factory=lambda: asdict(render.RenderOptions()))
    segment: dict = field(default_factory=lambda: asdict(segment.Options()))
    style: dict = field(default_factory=dict)  # CSS variables of the overlay (text positions and sizes)
    background: dict | None = None  # see render.default_background; None = the original video alone
    media: list[dict] = field(default_factory=list)  # imported photos/videos: {file, name, kind, w, h, dur}
    format: str = "9:16"  # render.FORMATS
    lang: str = "fr"  # translation language (quran.LANGS)
    detected: dict | None = None  # what identify.py heard: {"matches": [...]}
    audio_only: bool = False  # made from a sound file: the picture is a plain frame

    @property
    def media_dir(self) -> Path:
        return self.folder / "media"

    def ensure_size(self) -> None:
        """Projects made before width/height were stored."""
        if not self.width:
            info = media.probe(self.video_path)
            self.width, self.height = info.width, info.height
            self.save()

    def get_background(self) -> dict:
        self.ensure_size()
        return self.background or render.default_background(self.width, self.height, self.render.get("fit", "auto"),
                                                            self.format)

    @property
    def video_path(self) -> Path:
        return self.folder / self.video

    @property
    def file(self) -> Path:
        return self.folder / "project.json"

    def save(self) -> None:
        d = asdict(self)
        d["folder"] = None
        self.file.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    @staticmethod
    def load(folder: Path) -> "Project":
        d = json.loads((folder / "project.json").read_text(encoding="utf-8"))
        d["folder"] = folder
        return Project(**{k: v for k, v in d.items() if k in Project.__dataclass_fields__})


def create(folder: Path, source: str, surah: int, first_verse: int, last_verse: int | None = None,
           reciter: str = "", title: str = "", progress: Progress | None = None,
           fmt: str = "9:16", lang: str = "fr", style: dict | None = None) -> Project:
    """Copy (or download) the source into the project folder. surah 0: find it in the audio."""
    progress = progress or (lambda s, f: None)
    folder.mkdir(parents=True, exist_ok=True)
    if surah:
        quran.verse(surah, first_verse)  # validates
    if fmt not in render.FORMATS or lang not in quran.LANGS:
        raise ValueError("Unknown format or language")
    if source.startswith(("http://", "https://")):
        path = media.download(source, folder, lambda f: progress("download", f))
    else:
        src = Path(source).expanduser()
        if not src.is_file():
            raise FileNotFoundError(source)
        path = folder / f"source{src.suffix.lower()}"
        if src.resolve() != path.resolve():
            shutil.copy2(src, path)
    audio_only = not media.has_video(path)
    if audio_only:  # just the recitation: a plain picture, for the user's photos and videos
        cw, ch = render.FORMATS[fmt]
        sound = path
        path = media.audio_to_video(sound, folder / "source.mp4", cw, ch)
        sound.unlink(missing_ok=True)
    info = media.probe(path)
    progress("preview", 0.5)
    media.make_preview(path, folder / "preview.mp4")
    thumbnail(folder)
    p = Project(folder, path.name, surah, first_verse or 1, last_verse, reciter.strip(),
                title.strip() or (render.surah_title(surah, lang) if surah else ""), info.duration, info.width, info.height,
                format=fmt, lang=lang, style=dict(style or {}), audio_only=audio_only)
    p.segment["lang"] = lang
    p.save()
    return p


def thumbnail(folder: Path) -> Path:
    """Small picture of the video for the project list."""
    out = folder / "thumb.jpg"
    src = folder / "preview.mp4"
    dur = media.probe(src).duration
    # the most representative of ~4 s of frames (skips black intros and blurred frames)
    subprocess.run([media.tools()[0], "-y", "-v", "error", "-ss", f"{min(3.0, dur * 0.15):.2f}", "-i", str(src),
                    "-frames:v", "1", "-vf", "thumbnail=120,scale='if(gt(iw,ih),480,-2)':'if(gt(iw,ih),-2,480)'",
                    "-q:v", "4", str(out)], check=True)
    return out


def analyze(p: Project, progress: Progress | None = None) -> Project:
    """Find the verses in the audio and build the subtitle blocks."""
    progress = progress or (lambda s, f: None)
    progress("audio", 0.0)
    audio = media.load_audio(p.video_path)
    progress("model", 0.1)
    model = align.get_model()
    cache = p.folder / "emissions.npy"
    if cache.exists():
        em = np.load(cache)
    else:
        progress("listening", 0.3)
        em = model.emissions(audio)
        np.save(cache, em)
    progress("identify", 0.65)
    matches = identify.identify(em, model)
    p.detected = {"matches": [m.to_dict() for m in matches]}
    found_range = None
    if not p.surah:
        if not matches:
            raise ValueError("Je n'ai pas reconnu de passage du Coran dans cette vidéo. "
                             "Choisis la sourate et le premier verset à la main.")
        best = matches[0]
        p.surah, p.first_verse = best.surah, best.first
        found_range = (best.first, best.last)
        if not p.title:
            p.title = render.surah_title(p.surah, p.lang)
    elif matches and matches[0].surah == p.surah and abs(matches[0].first - p.first_verse) <= 6:
        found_range = (matches[0].first, matches[0].last)
    progress("aligning", 0.7)
    total = quran.surah(p.surah)["verses"]
    if found_range and not p.last_verse:
        last = min(total, found_range[1] + 1)
    else:
        last = p.last_verse or min(total, p.first_verse - 1 + align.max_verses_for(len(audio) / align.SR, total))
    # the starting verse is a hint: a few earlier verses are considered too
    first = max(1, p.first_verse - align.LOOKBACK_VERSES)
    verses = quran.verses(p.surah, first, last)
    occ = align.align(em, model, verses, hint=p.first_verse - first)
    if not any(o.word.unit == "verse" for o in occ):
        raise ValueError("No verse of the chosen range was found in this audio. Check the surah and starting verse.")
    opt = segment.Options(**{k: v for k, v in p.segment.items() if k in segment.Options.__dataclass_fields__})
    opt.lang = p.lang
    blocks = segment.build_blocks(occ, verses, audio, len(audio) / align.SR, opt)
    p.blocks = [b.to_dict() for b in blocks]
    p.save()
    progress("done", 1.0)
    return p


def found_verses(p: Project) -> tuple[int, int] | None:
    ayahs = [b["ayah"] for b in p.blocks if b["kind"] == "verse"]
    return (min(ayahs), max(ayahs)) if ayahs else None


def output_name(p: Project) -> str:
    rng = found_verses(p)
    name = quran.surah(p.surah)["name"].replace("'", "").replace(" ", "-")
    verses = f"{rng[0]}-{rng[1]}" if rng and rng[0] != rng[1] else f"{rng[0]}" if rng else ""
    reciter = re.sub(r"[^\w-]+", "-", p.reciter).strip("-")  # also keeps "/" and ".." out of the file name
    return "_".join(x for x in (name, verses, reciter) if x)


def make_video(p: Project, out_dir: Path | None = None, progress: Progress | None = None) -> Path:
    opt = render.RenderOptions(**{k: v for k, v in p.render.items() if k in render.RenderOptions.__dataclass_fields__})
    blocks = [segment.Block.from_dict(b) for b in p.blocks]
    out_dir = out_dir or p.folder
    out_dir.mkdir(parents=True, exist_ok=True)
    return render.render(p.video_path, blocks, p.title, p.reciter, out_dir / output_name(p), opt, p.style, progress,
                         p.get_background(), p.media_dir, p.format, p.lang)


def make_still(p: Project, t: float, out_dir: Path, progress: Progress | None = None) -> Path:
    """Full-resolution PNG of the video at time t (for a thumbnail or a post)."""
    opt = render.RenderOptions(**{k: v for k, v in p.render.items() if k in render.RenderOptions.__dataclass_fields__})
    opt.quality, opt.trim_start, opt.trim_end = "png", max(0.0, t), None
    blocks = [segment.Block.from_dict(b) for b in p.blocks]
    name = f"{output_name(p)}_{t:.1f}s"
    return render.render(p.video_path, blocks, p.title, p.reciter, out_dir / name, opt, p.style, progress,
                         p.get_background(), p.media_dir, p.format, p.lang)


POSITION_KEYS = ("--header-top", "--header-x", "--block-top", "--block-x")


def convert_format(p: Project, fmt: str) -> None:
    """Switch the project to another format: texts go back to that format's
    places, backgrounds that filled the frame fill the new one."""
    if fmt not in render.FORMATS:
        raise ValueError("Unknown format")
    old = p.format
    p.format = fmt
    p.style = {k: v for k, v in p.style.items() if k not in POSITION_KEYS}
    if p.background:
        for c in p.background["clips"]:
            if c["src"] == "original":
                sw, sh = p.width, p.height
            else:
                m = next((m for m in p.media if m["file"] == c["src"]), None)
                if not m:
                    continue
                sw, sh = m["w"], m["h"]
            z_old, z_new = render.cover_zoom(sw, sh, old), render.cover_zoom(sw, sh, fmt)
            if abs(float(c.get("zoom") or 1) - z_old) < 0.02:
                c["zoom"] = round(z_new, 4)  # filled the frame: keeps filling it


def set_language(p: Project, lang: str) -> None:
    """Translation in another language, cut like the Arabic."""
    if lang not in quran.LANGS:
        raise ValueError("Unknown language")
    blocks = [segment.Block.from_dict(b) for b in p.blocks]
    segment.retranslate(blocks, lang)
    if p.surah and p.title == render.surah_title(p.surah, p.lang):
        p.title = render.surah_title(p.surah, lang)
    p.lang = lang
    p.segment["lang"] = lang
    p.blocks = [b.to_dict() for b in blocks]


def add_media(p: Project, src: Path, name: str) -> dict:
    """Import a photo or video to use as background."""
    import uuid

    p.media_dir.mkdir(exist_ok=True)
    stem = "m" + uuid.uuid4().hex[:10]
    ext = src.suffix.lower()
    if ext in media.IMAGE_EXTS:
        dst = p.media_dir / f"{stem}.png"
        w, h = media.import_image(src, dst)
        item = {"file": dst.name, "name": name, "kind": "image", "w": w, "h": h, "dur": 0.0}
    else:
        dst = p.media_dir / f"{stem}{ext}"
        shutil.copy2(src, dst)
        info = media.probe(dst)
        # the editor plays a light H.264 copy; the render uses the original
        media.make_preview(dst, p.media_dir / f"{stem}.preview.mp4")
        item = {"file": dst.name, "name": name, "kind": "video", "w": info.width, "h": info.height,
                "dur": round(info.duration, 3)}
    p.media.append(item)
    p.save()
    return item


def waveform(p: Project, per_second: int = 50) -> list[float]:
    """Peak level (0..1) of the audio, `per_second` values per second, for the timeline."""
    cache = p.folder / "waveform.json"
    if cache.exists():
        return json.loads(cache.read_text())
    audio = media.load_audio(p.video_path, 8000)
    hop = 8000 // per_second
    n = len(audio) // hop
    peaks = np.abs(audio[: n * hop]).reshape(n, hop).max(axis=1) if n else np.zeros(0)
    peaks = peaks / max(1e-6, float(np.percentile(peaks, 99.5)) if n else 1.0)
    out = [round(min(1.0, float(x)), 3) for x in peaks]
    cache.write_text(json.dumps(out))
    return out
