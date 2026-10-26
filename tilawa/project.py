"""A project = one source video + its subtitle blocks + settings, saved as
JSON so it can be reviewed and edited before rendering."""

from __future__ import annotations

import difflib
import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from . import align, basmala, detect, identify, media, quran, render, segment, translit
from .i18n import UserError

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
    detected: dict | None = None  # the passages heard (detect.py): {"matches": [...]}
    surahs: list[int] = field(default_factory=list)  # every surah recited, in order (several: a prayer...)
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
        p = Project(**{k: v for k, v in d.items() if k in Project.__dataclass_fields__})
        if p.blocks and "translit" not in p.segment:
            p.segment["translit"] = "tanzil"  # made before the other conventions: its phonetic is Tanzil's
        return p


def create(folder: Path, source: str, surah: int, first_verse: int, last_verse: int | None = None,
           reciter: str = "", title: str = "", progress: Progress | None = None,
           fmt: str = "9:16", lang: str = "fr", style: dict | None = None, translit: str = "simple",
           translation: str = "") -> Project:
    """Copy (or download) the source into the project folder. surah 0: find it in the audio."""
    progress = progress or (lambda s, f: None)
    folder.mkdir(parents=True, exist_ok=True)
    if surah:
        quran.verse(surah, first_verse)  # validates
    if fmt not in render.FORMATS or lang not in quran.LANGS:
        raise UserError("bad_format_lang")
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
    p.segment.update(lang=lang, translit=translit, translation=quran.edition(lang, translation) or "")
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
    opt = segment.Options(**{k: v for k, v in p.segment.items() if k in segment.Options.__dataclass_fields__})
    opt.lang = p.lang
    blocks, found = detect.detect(em, audio, model, opt, p.surah, p.first_verse, p.last_verse)
    p.detected = {"matches": found}
    if not blocks or not any(b.kind == "verse" for b in blocks):
        raise UserError("no_verse" if p.surah else "not_recognized")
    auto_title = not p.title or p.title in (titles(p.lang, [p.surah] if p.surah else []), titles(p.lang, p.surahs))
    p.blocks = [b.to_dict() for b in blocks]
    p.surahs = surahs_of(p.blocks)
    if p.surah not in p.surahs:
        p.surah = p.surahs[0]
        p.first_verse = next(b["ayah"] for b in p.blocks if b["kind"] == "verse" and b["surah"] == p.surah)
    if auto_title:
        p.title = titles(p.lang, p.surahs)
    p.save()
    progress("done", 1.0)
    return p


def surahs_of(blocks: list[dict]) -> list[int]:
    """The surahs of the verse blocks, in the order recited."""
    out = []
    for b in blocks:
        if b["kind"] == "verse" and b["surah"] not in out:
            out.append(b["surah"])
    return out


def titles(lang: str, surahs: list[int]) -> str:
    """The title of a recitation of one surah or several."""
    if len(surahs) <= 1:
        return render.surah_title(surahs[0], lang) if surahs else ""
    return render.surahs_title(surahs, lang)


def header_titles(p: Project) -> list[tuple[float, str]] | None:
    """A recitation of several surahs whose title is the automatic one: each surah's own title,
    from its first subtitle (its basmala, if said) on. (Same as headerTitles() in index.html.)"""
    surahs = surahs_of(p.blocks)
    if len(surahs) < 2 or p.title != titles(p.lang, surahs):
        return None
    out, before = [], None  # before: a basmala / isti'adha said just before the next verse
    for b in p.blocks:
        if b["kind"] != "verse":
            before = b["start"] if before is None else before
            continue
        if not out or out[-1][1] != b["surah"]:
            out.append((0.0 if not out else before if before is not None else b["start"], b["surah"]))
        before = None
    return [(t, render.surah_title(s, p.lang)) for t, s in out]


def passages(p: Project) -> list[tuple[int, int, int]]:
    """(surah, first verse, last verse) of each surah recited, in order."""
    out = []
    for s in surahs_of(p.blocks):
        ayahs = [b["ayah"] for b in p.blocks if b["kind"] == "verse" and b["surah"] == s]
        out.append((s, min(ayahs), max(ayahs)))
    return out


def found_verses(p: Project) -> tuple[int, int] | None:
    ayahs = [b["ayah"] for b in p.blocks if b["kind"] == "verse"]
    return (min(ayahs), max(ayahs)) if ayahs else None


def output_name(p: Project) -> str:
    parts = []
    for s, lo, hi in passages(p) or [(p.surah, 0, 0)]:
        parts += [quran.surah(s)["name"].replace("'", "").replace(" ", "-"), f"{lo}-{hi}" if lo != hi else f"{lo}" if lo else ""]
    reciter = re.sub(r"[^\w-]+", "-", p.reciter).strip("-")  # also keeps "/" and ".." out of the file name
    return "_".join(x for x in (*parts, reciter) if x)


def youtube_style(p: Project) -> bool:
    """A 16:9 video in one of the YouTube arrangements (not a horizontal Short)."""
    look = lambda k: str(p.style.get(k) or "").strip('"')
    return p.format == "16:9" and (look("--layout") in ("cinema", "band") or look("--header-mode") == "intro")


def basmala_state(p: Project) -> dict:
    """Whether a basmala by another reciter can go before the recitation, and why (or why not).
    reason: "said" (the reciter says it) | "tawbah" | "fatiha" (it is the first verse) |
            "start" (the surah starts without it: recommended) | "middle" (optional)"""
    blocks = p.blocks
    first = next((b for b in blocks if b["kind"] == "verse"), None)
    if any(b["kind"] == "basmala" for b in blocks):
        reason = "said"
    elif p.surah == 9:
        reason = "tawbah"
    elif p.surah == 1:
        reason = "fatiha"
    else:
        reason = "start" if first and first["ayah"] == 1 else "middle"
    return {"available": youtube_style(p), "reason": reason, "possible": reason in ("start", "middle")}


def basmala_payload(p: Project) -> dict:
    """The subtitle of the basmala, in the project's translation and transliteration."""
    b = segment.Block("basmala", 0, 0, 0, 4, 0, 0, quran.BASMALA_UTHMANI,
                      segment.translation(quran.verse(1, 1), p.lang, p.segment.get("translation")),
                      " ".join(segment.phonetic("basmala", None, 0, 0, p.segment.get("translit", "simple"))))
    return render.block_payload(b, p.lang)


def make_video(p: Project, out_dir: Path | None = None, progress: Progress | None = None) -> Path:
    opt = render.RenderOptions(**{k: v for k, v in p.render.items() if k in render.RenderOptions.__dataclass_fields__})
    blocks = [segment.Block.from_dict(b) for b in p.blocks]
    out_dir = out_dir or p.folder
    out_dir.mkdir(parents=True, exist_ok=True)
    extra = None
    state = basmala_state(p)
    if opt.basmala and state["available"] and state["possible"] and basmala.HOME:
        if progress:
            progress("prepare", 0.0)
        extra = {"file": basmala.ensure(basmala.HOME, opt.basmala), "payload": basmala_payload(p)}
    times = render.repeats(opt, p.format)
    name = output_name(p) + (f"_x{times}" if times > 1 else "")
    return render.render(p.video_path, blocks, p.title, p.reciter, out_dir / name, opt, p.style, progress,
                         p.get_background(), p.media_dir, p.format, p.lang, p.surah, extra, header_titles(p))


def make_still(p: Project, t: float, out_dir: Path, progress: Progress | None = None) -> Path:
    """Full-resolution PNG of the video at time t (for a thumbnail or a post)."""
    opt = render.RenderOptions(**{k: v for k, v in p.render.items() if k in render.RenderOptions.__dataclass_fields__})
    opt.quality, opt.trim_start, opt.trim_end = "png", max(0.0, t), None
    blocks = [segment.Block.from_dict(b) for b in p.blocks]
    name = f"{output_name(p)}_{t:.1f}s"
    return render.render(p.video_path, blocks, p.title, p.reciter, out_dir / name, opt, p.style, progress,
                         p.get_background(), p.media_dir, p.format, p.lang, p.surah, titles=header_titles(p))


POSITION_KEYS = ("--header-top", "--header-x", "--block-top", "--block-x", "--band-top", "--logo-x", "--logo-y")


def convert_format(p: Project, fmt: str) -> None:
    """Switch the project to another format: texts go back to that format's
    places, backgrounds that filled the frame fill the new one."""
    if fmt not in render.FORMATS:
        raise UserError("bad_format")
    old = p.format
    p.format = fmt
    p.style = {k: v for k, v in p.style.items() if k not in POSITION_KEYS}
    if p.style.get("--logo-pos") == "custom":  # dragged by hand: the new format's best corner
        del p.style["--logo-pos"]
    if p.background:
        for c in p.background["clips"] + p.background.get("spare", []):
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


def set_language(p: Project, lang: str, chosen: str | None = None) -> None:
    """Translation in another language (or another translation of it), cut like the Arabic."""
    if lang not in quran.LANGS:
        raise UserError("bad_format_lang")
    edition = quran.edition(lang, chosen) or ""
    blocks = [segment.Block.from_dict(b) for b in p.blocks]
    segment.retranslate(blocks, lang, edition)
    surahs = surahs_of(p.blocks) or ([p.surah] if p.surah else [])
    if surahs and p.title == titles(p.lang, surahs):
        p.title = titles(lang, surahs)
    p.lang = lang
    p.segment["lang"], p.segment["translation"] = lang, edition
    p.blocks = [b.to_dict() for b in blocks]


def set_translit(p: Project, style: str) -> None:
    """Write the phonetic line of every subtitle in another convention."""
    if style not in translit.STYLES and style != "tanzil":
        raise UserError("bad_format_lang")
    blocks = [segment.Block.from_dict(b) for b in p.blocks]
    segment.rephonetize(blocks, style)
    p.segment["translit"] = style
    p.blocks = [b.to_dict() for b in blocks]


# ---------------------------------------------------------------- a verse heard as another one
#
# Many verses are repeated word for word (Ar-Rahman's refrain, 31 times) or
# nearly, in the same surah or elsewhere: the aligner may give a recitation the
# number of the wrong one. These find the verses that read the same as a
# subtitle, check each against the audio, and re-align that stretch of the
# recitation with the one chosen.

def occurrence(p: Project, i: int) -> tuple[int, int]:
    """Blocks [j0, j1) of the recitation of the verse that block i is part of
    (its parts in a row, repeats included: the aligner follows repeats)."""
    bl = p.blocks
    if not 0 <= i < len(bl) or bl[i]["kind"] != "verse":
        raise UserError("not_a_verse")
    def same(x, y):  # y goes on x's recitation: same verse, and not a new one after a complete one
        return (x["kind"] == y["kind"] == "verse" and (x["surah"], x["ayah"]) == (y["surah"], y["ayah"])
                and not (y["a0"] == 0 and x["a1"] >= len(quran.verse(x["surah"], x["ayah"]).align)))
    j0, j1 = i, i + 1
    while j0 > 0 and same(bl[j0 - 1], bl[j0]):
        j0 -= 1
    while j1 < len(bl) and same(bl[j1 - 1], bl[j1]):
        j1 += 1
    return j0, j1


def _window(p: Project, j0: int, j1: int) -> tuple[float, float]:
    """The stretch of audio of blocks [j0, j1), with a little margin (not into the neighbours' voice)."""
    bl = p.blocks
    lo = bl[j0 - 1]["voice_end"] if j0 > 0 else 0.0
    hi = bl[j1]["voice_start"] if j1 < len(bl) else p.duration
    return max(lo, bl[j0]["voice_start"] - 0.3), min(hi, bl[j1 - 1]["voice_end"] + 0.3)


def _heard(em: np.ndarray, model, v: quran.Verse, t0: float, t1: float) -> list:
    """The verse aligned on [t0, t1] of the recitation (word timings on the whole video's clock)."""
    f0, f1 = int(t0 / align.FRAME_S), int(np.ceil(t1 / align.FRAME_S))
    occ = align.align(em[f0:f1], model, [v], prefixes=False)
    return [align.WordTiming(o.word, o.start + f0 * align.FRAME_S, o.end + f0 * align.FRAME_S, o.score) for o in occ]


def verse_candidates(p: Project, i: int, progress: Progress | None = None, limit: int = 6) -> dict:
    """Verses the recitation of block i's verse could be, the most likely first."""
    progress = progress or (lambda s, f: None)
    j0, j1 = occurrence(p, i)
    blocks = p.blocks[j0:j1]
    cur = (blocks[0]["surah"], blocks[0]["ayah"])
    heard = quran.skeleton(" ".join(w["w"] for b in blocks for w in b["words"])).replace(" ", "")
    prev = next((b for b in reversed(p.blocks[:j0]) if b["kind"] == "verse"), None)
    after_prev = (prev["surah"], prev["ayah"] + 1) if prev else None
    # verses reading the same: letter groups of the subtitle found in them
    full, owner, grams = identify._index()
    votes: dict[tuple[int, int], float] = {}
    n = identify.N
    for k in range(0, max(1, len(heard) - n + 1)):
        for pos in grams.get(heard[k:k + n], [])[:400]:
            votes[owner[pos]] = votes.get(owner[pos], 0) + 1
    near = sorted(votes, key=lambda key: -votes[key])[:40]
    for key in (cur, after_prev, (cur[0], cur[1] - 1), (cur[0], cur[1] + 1)):  # and the verses around
        if key and 1 <= key[1] <= quran.surah(key[0])["verses"] and key not in near:
            near.append(key)
    def letters(key):
        return quran.skeleton(" ".join(quran.verse(*key).align)).replace(" ", "")

    alike = []
    for key in near:
        sm = difflib.SequenceMatcher(None, heard, letters(key), autojunk=False)
        alike.append((sum(m.size for m in sm.get_matching_blocks()) / max(1, len(heard)), key))
    alike.sort(key=lambda x: (-x[0], x[1] != cur, x[1] != after_prev))
    picks = [key for c, key in alike if c >= 0.6][:limit] or [key for _, key in alike[:limit]]
    # what the audio says: the letters the model hears on this stretch, compared with each verse
    progress("listening", 0.3)
    model = align.get_model()
    em = np.load(p.folder / "emissions.npy")
    t0, t1 = _window(p, j0, j1)
    said = identify._letters(identify.transcript(em[int(t0 / align.FRAME_S):int(np.ceil(t1 / align.FRAME_S))], model))
    # the part of each verse this recitation covers (a clip may stop mid-verse)
    part = (blocks[-1]["a1"] - blocks[0]["a0"]) / max(1, len(quran.verse(*cur).align))
    out = []
    for key in picks:
        text = letters(key)
        m = sum(b.size for b in difflib.SequenceMatcher(None, said, text, autojunk=False).get_matching_blocks())
        expect = len(text) * (part if key == cur or len(text) > len(heard) * 1.2 else 1.0)
        out.append({"surah": key[0], "ayah": key[1], "name": quran.surah(key[0])["name"],
                    "ar": quran.verse(*key).display_text(), "same_text": text == letters(cur),
                    "audio": round(2 * m / max(1, len(said) + expect), 3), "current": key == cur, "follows": key == after_prev})
    out.sort(key=lambda c: (-round(c["audio"], 2), not c["follows"], not c["current"]))
    return {"index": j0, "parts": j1 - j0, "current": {"surah": cur[0], "ayah": cur[1]}, "candidates": out}


def set_verse(p: Project, i: int, s: int, a: int, progress: Progress | None = None) -> None:
    """Give the recitation of block i's verse to verse s:a: that stretch is aligned again with it."""
    progress = progress or (lambda st, f: None)
    j0, j1 = occurrence(p, i)
    v = quran.verse(s, a)
    progress("aligning", 0.2)
    t0, t1 = _window(p, j0, j1)
    occ = _heard(np.load(p.folder / "emissions.npy"), align.get_model(), v, t0, t1)
    if not occ:
        raise UserError("no_verse")
    opt = segment.Options(**{k: x for k, x in p.segment.items() if k in segment.Options.__dataclass_fields__})
    opt.lang = p.lang
    progress("aligning", 0.6)
    new = segment.build_blocks(occ, [v], media.load_audio(p.video_path), p.duration, opt)
    new = [b for b in new if b.kind == "verse"]
    if not new:
        raise UserError("no_verse")
    # the new parts take the place of the old ones on screen
    new[0].start, new[-1].end = p.blocks[j0]["start"], p.blocks[j1 - 1]["end"]
    p.blocks[j0:j1] = [b.to_dict() for b in new]


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
