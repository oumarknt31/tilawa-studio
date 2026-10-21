"""A project = one source video + its subtitle blocks + settings, saved as
JSON so it can be reviewed and edited before rendering."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from . import align, media, quran, render, segment

Progress = Callable[[str, float], None]


@dataclass
class Project:
    folder: Path
    video: str  # file name inside the folder
    surah: int
    first_verse: int
    last_verse: int | None = None
    reciter: str = ""
    title: str = ""
    duration: float = 0.0
    blocks: list[dict] = field(default_factory=list)
    render: dict = field(default_factory=lambda: asdict(render.RenderOptions()))
    segment: dict = field(default_factory=lambda: asdict(segment.Options()))
    style: dict = field(default_factory=dict)

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
           reciter: str = "", title: str = "", progress: Progress | None = None) -> Project:
    """Copy (or download) the source into the project folder."""
    progress = progress or (lambda s, f: None)
    folder.mkdir(parents=True, exist_ok=True)
    quran.verse(surah, first_verse)  # validates
    if source.startswith(("http://", "https://")):
        path = media.download(source, folder, lambda f: progress("download", f))
    else:
        src = Path(source).expanduser()
        if not src.is_file():
            raise FileNotFoundError(source)
        path = folder / f"source{src.suffix.lower()}"
        if src.resolve() != path.resolve():
            shutil.copy2(src, path)
    info = media.probe(path)
    progress("preview", 0.5)
    media.make_preview(path, folder / "preview.mp4")
    p = Project(folder, path.name, surah, first_verse, last_verse, reciter.strip(),
                title.strip() or render.surah_title(surah), info.duration)
    p.save()
    return p


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
    progress("aligning", 0.7)
    total = quran.surah(p.surah)["verses"]
    last = p.last_verse or min(total, p.first_verse - 1 + align.max_verses_for(len(audio) / align.SR, total))
    # the starting verse is a hint: a few earlier verses are considered too
    first = max(1, p.first_verse - align.LOOKBACK_VERSES)
    verses = quran.verses(p.surah, first, last)
    occ = align.align(em, model, verses, hint=p.first_verse - first)
    if not any(o.word.unit == "verse" for o in occ):
        raise ValueError("No verse of the chosen range was found in this audio. Check the surah and starting verse.")
    opt = segment.Options(**{k: v for k, v in p.segment.items() if k in segment.Options.__dataclass_fields__})
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
    reciter = p.reciter.replace(" ", "-")
    return "_".join(x for x in (name, verses, reciter) if x)


def make_video(p: Project, out_dir: Path | None = None, progress: Progress | None = None) -> Path:
    opt = render.RenderOptions(**{k: v for k, v in p.render.items() if k in render.RenderOptions.__dataclass_fields__})
    blocks = [segment.Block.from_dict(b) for b in p.blocks]
    out_dir = out_dir or p.folder
    out_dir.mkdir(parents=True, exist_ok=True)
    return render.render(p.video_path, blocks, p.title, p.reciter, out_dir / output_name(p), opt, p.style, progress)
