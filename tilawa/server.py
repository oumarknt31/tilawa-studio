"""Local web app: import -> review/edit -> render.

Everything runs on this computer; the browser is only the interface.
Heavy work (analysis, rendering) runs one job at a time in a worker thread.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import uuid
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

from contextvars import ContextVar, copy_context

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import basmala, media, project, quran, render, segment
from .cli import HOME
from .i18n import UI_LANGS, UserError
from .library import Library

PKG = Path(__file__).parent
PROJECTS = HOME / "projects"
VIDEOS = HOME / "Videos"
LIB = Library(HOME)
render.USER_FONTS = LIB.fonts_dir
render.USER_LOGO = LIB.logo_file
render.LOGO_AUTO = LIB.settings().get("logo_auto", True)
basmala.HOME = HOME
LIB.fonts_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Tilawa Studio")
app.mount("/fonts", StaticFiles(directory=PKG / "fonts"), name="fonts")
app.mount("/userfonts", StaticFiles(directory=LIB.fonts_dir), name="userfonts")
app.mount("/assets", StaticFiles(directory=PKG / "assets"), name="assets")
_pool = ThreadPoolExecutor(max_workers=1)
_jobs: dict[str, dict] = {}
_lock = threading.Lock()
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".3gp"}
DESKTOP = False  # running in the app's own window (desktop.py), not in a browser
LANG: ContextVar[str] = ContextVar("lang", default="fr")  # language of the interface making the request


def _msg(e: Exception) -> str:
    return e.text(LANG.get()) if isinstance(e, UserError) else str(e)


@app.exception_handler(UserError)
async def user_error(request: Request, e: UserError):
    return JSONResponse({"detail": e.text(LANG.get())}, status_code=400)


@app.middleware("http")
async def local_only(request: Request, call_next):
    # other websites open in the browser can reach 127.0.0.1 too: refuse DNS-rebound hosts and cross-site writes
    local = ("127.0.0.1", "localhost")
    if (request.headers.get("host") or "").rsplit(":", 1)[0] not in local:
        return PlainTextResponse("Forbidden", 403)
    lang = request.headers.get("x-lang", "")
    LANG.set(lang if lang in UI_LANGS else "fr")
    origin = request.headers.get("origin")
    if request.method not in ("GET", "HEAD") and origin and origin.split("://", 1)[-1].rsplit(":", 1)[0] not in local:
        return PlainTextResponse("Forbidden", 403)
    return await call_next(request)


# ---------------------------------------------------------------- jobs

def _job(kind: str, project_id: str, fn) -> str:
    jid = uuid.uuid4().hex[:10]
    lang = LANG.get()
    job = {"id": jid, "kind": kind, "project": project_id, "stage": "queued", "progress": 0.0,
           "status": "running", "error": None, "result": None, "started": time.time(), "cancel": False}
    with _lock:
        _jobs[jid] = job

    def progress(stage: str, f: float):
        if job["cancel"]:
            raise Cancelled()  # stops the job at its next step (the renderer stops ffmpeg)
        job["stage"], job["progress"] = stage, round(float(f), 4)

    def run():
        try:
            if job["cancel"]:
                raise Cancelled()
            job["result"] = fn(progress)
            job["status"] = "done"
        except Cancelled:
            job["status"] = "cancelled"
        except Exception as e:  # report to the UI
            traceback.print_exc()
            job["status"], job["error"] = "error", (e.text(lang) if isinstance(e, UserError) else str(e)) or e.__class__.__name__

    _pool.submit(copy_context().run, run)  # with the request's project reading (quran.use_reading)
    return jid


class Cancelled(Exception):
    """The user stopped the job."""


@app.get("/api/jobs/{jid}")
def job_status(jid: str):
    if jid not in _jobs:
        raise HTTPException(404)
    return _jobs[jid]


@app.post("/api/jobs/{jid}/cancel")
def cancel_job(jid: str):
    if jid not in _jobs:
        raise HTTPException(404)
    _jobs[jid]["cancel"] = True
    return {"ok": True}


# ---------------------------------------------------------------- projects

def _folder(pid: str) -> Path:
    if not re.fullmatch(r"[\w-]+", pid):
        raise HTTPException(400, "bad id")
    f = PROJECTS / pid
    if not (f / "project.json").exists():
        raise HTTPException(404, "project not found")
    return f


def _public(p: project.Project) -> dict:
    d = asdict(p)
    d["folder"] = None
    d["id"] = p.folder.name
    d["surah_info"] = quran.surah(p.surah) if p.surah else None
    d["surahs"] = project.surahs_of(p.blocks)
    d["auto_title"] = project.titles(p.lang, d["surahs"])  # the title made from the surahs (headerTitles)
    d["surah_titles"] = {s: render.surah_title(s, p.lang) for s in d["surahs"]}
    d["background"] = p.get_background()
    d["verse_counts"] = [quran.verse_count(s) for s in range(1, 115)]  # as the project's reading counts them
    if p.surah:  # the verses asked for, numbered as the reading numbers them
        first = quran.verse(p.surah, p.first_verse)
        d["first_number"] = first.number(0) or 1
        d["last_number"] = quran.verse(p.surah, p.last_verse).numbers[-1] if p.last_verse else None
    d["width"], d["height"] = p.width, p.height
    for b, raw in zip(d["blocks"], p.blocks):  # the verse numbers shown, and the ornament in the preview
        x = segment.Block.from_dict(raw)
        b["num"], b["num_end"] = project.numbers(raw) if x.kind == "verse" else (0, 0)
        b["ends_verse"] = render.ends_verse(x)
    d["exports"] = _exports(p)
    d["basmala"] = project.basmala_state(p) | {"payload": project.basmala_payload(p)}
    return d


def _exports(p: project.Project) -> list[dict]:
    """Videos and images already made from this project, newest first."""
    if not p.surah or not VIDEOS.exists():
        return []
    stem = project.output_name(p)
    files = [f for f in VIDEOS.iterdir() if f.name.startswith(stem) and f.suffix in (".mp4", ".mov", ".png")]
    return [{"name": f.name, "size": f.stat().st_size, "time": f.stat().st_mtime}
            for f in sorted(files, key=lambda f: -f.stat().st_mtime)]


@app.get("/api/surahs")
def surahs():
    from . import warsh
    return [s | {"verses_warsh": warsh.verse_count(s["n"])} for s in quran.surahs()]


@app.get("/api/projects")
def list_projects():
    out = []
    for f in sorted(PROJECTS.glob("*/project.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            p = project.Project.load(f.parent)
            rng = project.found_verses(p)
            out.append({"id": f.parent.name, "title": p.title, "reciter": p.reciter, "surah": p.surah,
                        "surah_name": quran.surah(p.surah)["name"] if p.surah else "",
                        "verses": list(rng) if rng else None, "passages": project.passages(p), "first_verse": p.first_verse, "blocks": len(p.blocks),
                        "format": p.format, "lang": p.lang, "duration": p.duration,
                        "thumb": (f.parent / "preview.mp4").exists(), "modified": f.stat().st_mtime})
        except Exception:
            continue
    return out


@app.post("/api/projects")
async def new_project(surah: int = Form(0), first_verse: int = Form(1), last_verse: int | None = Form(None),
                      reciter: str = Form(""), title: str = Form(""), url: str = Form(""),
                      format: str = Form("9:16"), lang: str = Form("fr"), style: str = Form(""), translation: str = Form(""),
                      reading: str = Form("auto"), file: UploadFile | None = File(None)):
    """surah 0: the surah and verses are found in the recitation."""
    reading = reading if reading in quran.READINGS else "auto"
    try:
        if surah:  # verses numbered as the chosen reading numbers them
            quran.use_reading(reading)
            first_verse = quran.key_of(surah, first_verse)[1]
            last_verse = quran.key_of(surah, last_verse, end=True)[1] if last_verse else None
            quran.verse(surah, first_verse)
        if format not in render.FORMATS or lang not in quran.LANGS:
            raise UserError("bad_format_lang")
    except ValueError as e:
        raise HTTPException(400, _msg(e))
    if not url and not file:
        raise UserError("need_source")
    if url and not file and not url.strip().startswith(("http://", "https://")):
        raise UserError("need_https")
    if file and Path(file.filename or "").suffix.lower() not in VIDEO_EXTS | media.AUDIO_EXTS:
        raise UserError("bad_source", exts=", ".join(sorted(VIDEO_EXTS | media.AUDIO_EXTS)))
    name = f"{quran.surah(surah)['name']}-{first_verse}" if surah else "recitation"
    slug = re.sub(r"[^\w-]+", "-", f"{name}-{time.strftime('%Y%m%d-%H%M%S')}")
    folder = PROJECTS / slug
    folder.mkdir(parents=True, exist_ok=True)
    source = url.strip()
    if file:
        dst = folder / f"upload{Path(file.filename).suffix.lower()}"
        with dst.open("wb") as f:
            shutil.copyfileobj(file.file, f, length=8 << 20)
        source = str(dst)

    settings = LIB.update_settings({"format": format, "lang": lang, "style": style, "reading": reading})
    look = LIB.style(style)
    translit = settings.get("translit", "simple")
    translation = translation or (settings.get("translations") or {}).get(lang, "")
    if translation:  # the one chosen in the form is remembered for this language
        LIB.update_settings({"translations": {**(settings.get("translations") or {}), lang: translation}})

    def work(progress):
        p = project.create(folder, source, surah, first_verse, last_verse, reciter, title, progress, format, lang, look,
                           translit, translation, reading)
        if file:
            Path(source).unlink(missing_ok=True)
        project.analyze(p, progress)
        return slug

    return {"id": slug, "job": _job("analyze", slug, work)}


@app.get("/api/projects/{pid}")
def get_project(pid: str):
    return _public(project.Project.load(_folder(pid)))


@app.put("/api/projects/{pid}")
def save_project(pid: str, body: dict):
    p = project.Project.load(_folder(pid))
    for key in ("title", "reciter", "blocks", "render", "style", "segment"):
        if key in body:
            setattr(p, key, body[key])
    for b in p.blocks:
        for k in ("ends_verse", "num", "num_end"):
            b.pop(k, None)
    if "background" in body:
        known = {m["file"] for m in p.media} | {"original"}
        bg = body["background"]
        bg["clips"] = [c for c in bg.get("clips", []) if c.get("src") in known] or p.get_background()["clips"]
        bg["spare"] = [c for c in bg.get("spare", []) if c.get("src") in known]  # set aside, not in the video
        p.background = bg
    p.save()
    return _public(p)


@app.post("/api/projects/{pid}/analyze")
def reanalyze(pid: str, body: dict):
    p = project.Project.load(_folder(pid))
    if body.get("reading") in (*quran.READINGS, "auto"):
        p.reading = body["reading"]
        quran.use_reading(p.reading)
    if body.get("auto"):
        p.surah, p.first_verse, p.last_verse = 0, 1, None
    if body.get("surah"):
        p.surah = int(body["surah"])
    # verses numbered as the project's reading numbers them
    if "first_verse" in body and p.surah:
        p.first_verse = quran.key_of(p.surah, int(body["first_verse"]))[1]
        quran.verse(p.surah, p.first_verse)
    if "last_verse" in body:
        p.last_verse = quran.key_of(p.surah, int(body["last_verse"]), end=True)[1] if body["last_verse"] else None
    if "segment" in body:
        p.segment.update(body["segment"])
    p.save()
    return {"job": _job("analyze", pid, lambda progress: project.analyze(p, progress) and pid)}


@app.post("/api/projects/{pid}/split")
def split(pid: str, body: dict):
    p = project.Project.load(_folder(pid))
    blocks = [segment.Block.from_dict(b) for b in p.blocks]
    try:
        segment.split_block(blocks, int(body["index"]), int(body["word"]), p.lang, p.segment.get("translit", "simple"))
    except (ValueError, IndexError) as e:
        raise HTTPException(400, _msg(e))
    p.blocks = [b.to_dict() for b in blocks]
    p.save()
    return _public(p)


@app.post("/api/projects/{pid}/merge")
def merge(pid: str, body: dict):
    p = project.Project.load(_folder(pid))
    blocks = [segment.Block.from_dict(b) for b in p.blocks]
    try:
        segment.merge_blocks(blocks, int(body["index"]), p.segment.get("translit", "simple"))
    except (ValueError, IndexError) as e:
        raise HTTPException(400, _msg(e))
    p.blocks = [b.to_dict() for b in blocks]
    p.save()
    return _public(p)


@app.post("/api/projects/{pid}/restore")
def restore_text(pid: str, body: dict):
    """Undo hand corrections of a verse block's Arabic and phonetic text."""
    p = project.Project.load(_folder(pid))
    b = segment.Block.from_dict(p.blocks[int(body["index"])])
    if b.kind == "verse":
        segment.verse_texts(b, p.segment.get("translit", "simple"))
        p.blocks[int(body["index"])] = b.to_dict()
        p.save()
    return _public(p)


@app.post("/api/projects/{pid}/retime")
def retime(pid: str):
    """Recompute on-screen times from the voice timings (undo manual timing edits)."""
    p = project.Project.load(_folder(pid))
    blocks = [segment.Block.from_dict(b) for b in p.blocks]
    segment.retime(blocks, p.duration)
    p.blocks = [b.to_dict() for b in blocks]
    p.save()
    return _public(p)


@app.post("/api/projects/{pid}/language")
def set_language(pid: str, body: dict):
    p = project.Project.load(_folder(pid))
    try:
        project.set_language(p, body["lang"], body.get("translation"))
    except (ValueError, KeyError) as e:
        raise HTTPException(400, _msg(e))
    p.save()
    # the translation chosen for a language is the one new videos get
    LIB.update_settings({"translations": {**(LIB.settings().get("translations") or {}), p.lang: p.segment["translation"]}})
    return _public(p)


@app.post("/api/projects/{pid}/translit")
def set_translit(pid: str, body: dict):
    """Write the phonetic line in another convention (and new videos too)."""
    p = project.Project.load(_folder(pid))
    try:
        project.set_translit(p, str(body.get("style", "")))
    except ValueError as e:
        raise HTTPException(400, _msg(e))
    p.save()
    LIB.update_settings({"translit": p.segment["translit"]})
    return _public(p)


@app.post("/api/projects/{pid}/verse-candidates")
def verse_candidates(pid: str, body: dict):
    """The verses the recitation of a subtitle could be, checked against the audio (a job: it listens)."""
    p = project.Project.load(_folder(pid))
    i = int(body["index"])
    project.occurrence(p, i)  # not a verse: refused now
    return {"job": _job("verse", pid, lambda progress: project.verse_candidates(p, i, progress))}


@app.post("/api/projects/{pid}/set-verse")
def set_verse(pid: str, body: dict):
    """Give the recitation of a subtitle to another verse: aligned again with it (a job)."""
    folder = _folder(pid)
    project.Project.load(folder)  # its reading
    i, s = int(body["index"]), int(body["surah"])
    # a verse picked in the list (its Hafs key), or typed (numbered as the reading numbers it)
    a = int(body["ayah"]) if "ayah" in body else quran.key_of(s, int(body["number"]))[1]
    quran.verse(s, a)  # validates

    def work(progress):
        p = project.Project.load(folder)
        project.set_verse(p, i, s, a, progress)
        p.save()
        return True

    return {"job": _job("verse", pid, work)}


@app.post("/api/projects/{pid}/format")
def set_format(pid: str, body: dict):
    """Change the format, or (copy=true) make a copy of the project in that format."""
    folder = _folder(pid)
    fmt = body.get("format")
    if fmt not in render.FORMATS:
        raise UserError("bad_format")
    if body.get("copy"):
        slug = re.sub(r"[^\w-]+", "-", f"{pid.rsplit('-', 2)[0]}-{fmt.replace(':', 'x')}-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copytree(folder, PROJECTS / slug)
        folder = PROJECTS / slug
    p = project.Project.load(folder)
    project.convert_format(p, fmt)
    p.save()
    return _public(p)


@app.post("/api/projects/{pid}/still")
def make_still(pid: str, body: dict):
    p = project.Project.load(_folder(pid))
    t = float(body.get("t", 0))
    return {"job": _job("still", pid, lambda progress: project.make_still(p, t, VIDEOS, progress).name)}


@app.get("/api/projects/{pid}/thumb")
def thumb(pid: str):
    folder = _folder(pid)
    f = folder / "thumb.jpg"
    if not f.exists():
        try:
            project.thumbnail(folder)
        except Exception:
            raise HTTPException(404)
    return FileResponse(f, headers={"Cache-Control": "max-age=60"})


@app.post("/api/projects/{pid}/render")
def start_render(pid: str):
    p = project.Project.load(_folder(pid))
    if not p.blocks:
        raise UserError("nothing_to_render")
    return {"job": _job("render", pid, lambda progress: project.make_video(p, VIDEOS, progress).name)}


@app.delete("/api/projects/{pid}")
def delete_project(pid: str):
    shutil.rmtree(_folder(pid))
    return {"ok": True}


@app.post("/api/projects/{pid}/media")
def add_media(pid: str, file: UploadFile = File(...)):
    """Import a photo or video to use as background (runs in the request: a few seconds)."""
    folder = _folder(pid)
    ext = Path(file.filename or "").suffix.lower()
    if ext not in VIDEO_EXTS | media.IMAGE_EXTS:
        raise UserError("bad_media")
    tmp = folder / f"import{ext}"
    with tmp.open("wb") as f:
        shutil.copyfileobj(file.file, f, length=8 << 20)
    try:
        p = project.Project.load(folder)
        return project.add_media(p, tmp, Path(file.filename).name)
    except Exception:
        traceback.print_exc()
        raise UserError("unreadable_media")
    finally:
        tmp.unlink(missing_ok=True)


@app.delete("/api/projects/{pid}/media/{name}")
def delete_media(pid: str, name: str):
    p = project.Project.load(_folder(pid))
    p.media = [m for m in p.media if m["file"] != name]
    if p.background:
        p.background["clips"] = [c for c in p.background["clips"] if c["src"] != name] or None
        p.background["spare"] = [c for c in p.background.get("spare", []) if c["src"] != name]
        if p.background["clips"] is None:
            p.background = None
    p.save()
    for f in p.media_dir.glob(Path(name).stem + "*"):
        f.unlink()
    return _public(p)


@app.get("/api/projects/{pid}/media/{name}")
def get_media(pid: str, name: str, pp: bool = False):
    """Media for the editor (light H.264 copy of videos; `pp`: its forward +
    backward cycle, made on first use)."""
    folder = _folder(pid) / "media"
    f = folder / Path(name).name
    preview = folder / f"{f.stem}.preview.mp4"
    if pp and preview.exists():
        cycle = folder / f"{f.stem}.pp.preview.mp4"
        if not cycle.exists():
            media.pingpong(preview, cycle, preview=True)
        preview = cycle
    f = preview if preview.exists() else f
    if not f.is_file():
        raise HTTPException(404)
    return FileResponse(f)


@app.get("/api/projects/{pid}/waveform")
def waveform(pid: str):
    return project.waveform(project.Project.load(_folder(pid)))


@app.get("/api/projects/{pid}/preview")
def preview(pid: str):
    return FileResponse(_folder(pid) / "preview.mp4", media_type="video/mp4")


@app.get("/api/output/{name}")
def output(name: str, download: bool = False):
    f = VIDEOS / Path(name).name
    if not f.exists():
        raise HTTPException(404)
    return FileResponse(f, filename=f.name if download else None)


@app.get("/api/info")
def info():
    from . import update

    return {"desktop": DESKTOP, "version": update.current(), "platform": sys.platform}


@app.post("/api/open/{name}")
def open_file(name: str):
    """Open an exported video or image in the computer's own player / viewer."""
    f = VIDEOS / Path(name).name
    if not f.exists():
        raise HTTPException(404)
    if sys.platform == "darwin":
        subprocess.run(["open", str(f)])
    elif sys.platform == "win32":
        os.startfile(str(f))  # noqa: S606 - a file the app made
    else:
        subprocess.run(["xdg-open", str(f)])
    return {"ok": True}


@app.post("/api/notify")
def notify(body: dict):
    """System notification (the app window has none of its own)."""
    title, text = str(body.get("title", ""))[:80], str(body.get("text", ""))[:200]
    if sys.platform == "darwin":
        esc = lambda x: x.replace("\\", "\\\\").replace('"', '\\"')
        subprocess.run(["osascript", "-e", f'display notification "{esc(text)}" with title "{esc(title)}" sound name "Glass"'],
                       capture_output=True)
    return {"ok": True}


@app.get("/api/update")
def update_check():
    from . import update

    return update.check()


@app.post("/api/update")
def update_apply():
    from . import update

    return {"job": _job("update", "", update.apply)}


@app.post("/api/restart")
def restart():
    from . import update

    threading.Timer(0.3, update.restart).start()
    return {"ok": True}


def busy() -> bool:
    """An analysis, export or update is running."""
    return any(j["status"] == "running" for j in _jobs.values())


@app.post("/api/reveal/{name}")
def reveal(name: str):
    """Show the rendered file in Finder / Explorer."""
    f = VIDEOS / Path(name).name
    if sys.platform == "darwin":
        subprocess.run(["open", "-R", str(f)])
    elif sys.platform == "win32":
        subprocess.run(["explorer", "/select,", str(f)])
    else:
        subprocess.run(["xdg-open", str(f.parent)])
    return {"ok": True}


@app.get("/api/languages")
def languages():
    return quran.languages()


@app.get("/api/settings")
def get_settings():
    return LIB.settings()


@app.put("/api/settings")
def put_settings(body: dict):
    s = LIB.update_settings({k: v for k, v in body.items() if k in ("format", "lang", "style", "reciters", "tour", "ui", "logo_auto")})
    render.LOGO_AUTO = s.get("logo_auto", True)
    return s


@app.get("/api/styles")
def styles():
    return LIB.styles()


@app.post("/api/styles")
def save_style(body: dict):
    return LIB.save_style(str(body.get("name", "")), dict(body.get("style") or {}))


@app.delete("/api/styles/{sid}")
def delete_style(sid: str):
    LIB.delete_style(sid)
    return {"ok": True}


@app.get("/api/fonts")
def fonts():
    return LIB.fonts()


@app.post("/api/fonts")
def add_font(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".ttf", ".otf"):
        raise UserError("bad_font")
    LIB.fonts_dir.mkdir(parents=True, exist_ok=True)
    tmp = LIB.fonts_dir / f".import{ext}"
    with tmp.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        return LIB.add_font(tmp, Path(file.filename).name)
    except Exception:
        traceback.print_exc()
        raise UserError("unreadable_font")
    finally:
        tmp.unlink(missing_ok=True)


@app.delete("/api/fonts/{family}")
def delete_font(family: str):
    LIB.delete_font(family)
    return {"ok": True}


@app.post("/api/logo")
def set_logo(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in media.IMAGE_EXTS:
        raise UserError("bad_logo")
    tmp = HOME / f".logo-import{ext}"
    HOME.mkdir(parents=True, exist_ok=True)
    with tmp.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        return LIB.set_logo(tmp)
    except Exception:
        traceback.print_exc()
        raise UserError("unreadable_media")
    finally:
        tmp.unlink(missing_ok=True)


@app.delete("/api/logo")
def delete_logo():
    return LIB.delete_logo()


@app.get("/userlogo/logo.png")
def logo():
    if not LIB.logo_file.is_file():
        raise HTTPException(404)
    return FileResponse(LIB.logo_file, media_type="image/png", headers={"Cache-Control": "no-cache"})


@app.get("/api/basmala")
def basmala_list():
    """Reciters whose basmala can go before a recitation (YouTube styles)."""
    return basmala.listing(HOME)


@app.get("/api/basmala/{rid}.wav")
def basmala_audio(rid: str):
    if rid not in basmala.RECITERS:
        raise HTTPException(404)
    try:
        f = basmala.ensure(HOME, rid)  # downloaded the first time it is listened to
    except OSError:
        raise UserError("download_failed")
    return FileResponse(f, media_type="audio/wav")


@app.get("/overlay.html")
def overlay():
    return FileResponse(PKG / "web" / "overlay.html", media_type="text/html")


@app.get("/")
def index():
    return HTMLResponse((PKG / "web" / "index.html").read_text(encoding="utf-8"))


def run(port: int = 8765, open_browser: bool = True):
    import uvicorn

    PROJECTS.mkdir(parents=True, exist_ok=True)
    VIDEOS.mkdir(parents=True, exist_ok=True)
    url = f"http://127.0.0.1:{port}"
    if _already_running(url):
        # launched twice: reuse the running app instead of failing on the busy port
        print(f"\n  Tilawa Studio est déjà ouvert / is already open: {url}\n")
        if open_browser:
            webbrowser.open(url)
        return
    print(f"\n  Tilawa Studio : {url}\n  Vidéos / Videos : {VIDEOS}\n"
          "  Laisse cette fenêtre ouverte, ferme-la pour quitter.\n  Keep this window open; close it to quit.\n")
    if open_browser:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    # warm the model up in the job queue so the first analysis is quick
    _pool.submit(_warmup)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def _already_running(url: str) -> bool:
    import urllib.request

    try:
        with urllib.request.urlopen(f"{url}/api/surahs", timeout=2) as r:
            return r.status == 200
    except OSError:
        return False


def _warmup():
    try:
        from . import align, firstrun

        firstrun.ensure_browser()  # an update may need another version of it
        align.get_model()
    except Exception:
        traceback.print_exc()
