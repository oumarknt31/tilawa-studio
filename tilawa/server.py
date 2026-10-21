"""Local web app: import -> review/edit -> render.

Everything runs on this computer; the browser is only the interface.
Heavy work (analysis, rendering) runs one job at a time in a worker thread.
"""

from __future__ import annotations

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

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import media, project, quran, render, segment
from .cli import HOME

PKG = Path(__file__).parent
PROJECTS = HOME / "projects"
VIDEOS = HOME / "Videos"

app = FastAPI(title="Tilawa Studio")
app.mount("/fonts", StaticFiles(directory=PKG / "fonts"), name="fonts")
_pool = ThreadPoolExecutor(max_workers=1)
_jobs: dict[str, dict] = {}
_lock = threading.Lock()
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".3gp"}


@app.middleware("http")
async def local_only(request: Request, call_next):
    # other websites open in the browser can reach 127.0.0.1 too: refuse DNS-rebound hosts and cross-site writes
    local = ("127.0.0.1", "localhost")
    if (request.headers.get("host") or "").rsplit(":", 1)[0] not in local:
        return PlainTextResponse("Forbidden", 403)
    origin = request.headers.get("origin")
    if request.method not in ("GET", "HEAD") and origin and origin.split("://", 1)[-1].rsplit(":", 1)[0] not in local:
        return PlainTextResponse("Forbidden", 403)
    return await call_next(request)


# ---------------------------------------------------------------- jobs

def _job(kind: str, project_id: str, fn) -> str:
    jid = uuid.uuid4().hex[:10]
    job = {"id": jid, "kind": kind, "project": project_id, "stage": "queued", "progress": 0.0,
           "status": "running", "error": None, "result": None, "started": time.time()}
    with _lock:
        _jobs[jid] = job

    def progress(stage: str, f: float):
        job["stage"], job["progress"] = stage, round(float(f), 4)

    def run():
        try:
            job["result"] = fn(progress)
            job["status"] = "done"
        except Exception as e:  # report to the UI
            traceback.print_exc()
            job["status"], job["error"] = "error", str(e) or e.__class__.__name__

    _pool.submit(run)
    return jid


@app.get("/api/jobs/{jid}")
def job_status(jid: str):
    if jid not in _jobs:
        raise HTTPException(404)
    return _jobs[jid]


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
    d["surah_info"] = quran.surah(p.surah)
    d["background"] = p.get_background()
    d["width"], d["height"] = p.width, p.height
    out = VIDEOS / (project.output_name(p) + (".mov" if p.render.get("quality") == "prores" else ".mp4"))
    d["output"] = out.name if out.exists() else None
    return d


@app.get("/api/surahs")
def surahs():
    return quran.surahs()


@app.get("/api/projects")
def list_projects():
    out = []
    for f in sorted(PROJECTS.glob("*/project.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            p = project.Project.load(f.parent)
            out.append({"id": f.parent.name, "title": p.title, "reciter": p.reciter, "surah": p.surah,
                        "first_verse": p.first_verse, "blocks": len(p.blocks), "modified": f.stat().st_mtime})
        except Exception:
            continue
    return out


@app.post("/api/projects")
async def new_project(surah: int = Form(...), first_verse: int = Form(...), last_verse: int | None = Form(None),
                      reciter: str = Form(""), title: str = Form(""), url: str = Form(""),
                      file: UploadFile | None = File(None)):
    try:
        quran.verse(surah, first_verse)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not url and not file:
        raise HTTPException(400, "Choisis un fichier vidéo ou colle un lien.")
    if url and not file and not url.strip().startswith(("http://", "https://")):
        raise HTTPException(400, "Le lien doit commencer par https://")
    if file and Path(file.filename or "").suffix.lower() not in VIDEO_EXTS:
        raise HTTPException(400, "Format non reconnu : choisis une vidéo (" + ", ".join(sorted(VIDEO_EXTS)) + ").")
    slug = re.sub(r"[^\w-]+", "-", f"{quran.surah(surah)['name']}-{first_verse}-{time.strftime('%Y%m%d-%H%M%S')}")
    folder = PROJECTS / slug
    folder.mkdir(parents=True, exist_ok=True)
    source = url.strip()
    if file:
        dst = folder / f"upload{Path(file.filename).suffix.lower()}"
        with dst.open("wb") as f:
            shutil.copyfileobj(file.file, f, length=8 << 20)
        source = str(dst)

    def work(progress):
        p = project.create(folder, source, surah, first_verse, last_verse, reciter, title, progress)
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
    if "background" in body:
        known = {m["file"] for m in p.media} | {"original"}
        bg = body["background"]
        bg["clips"] = [c for c in bg.get("clips", []) if c.get("src") in known] or p.get_background()["clips"]
        p.background = bg
    p.save()
    return _public(p)


@app.post("/api/projects/{pid}/analyze")
def reanalyze(pid: str, body: dict):
    p = project.Project.load(_folder(pid))
    if "first_verse" in body:
        quran.verse(p.surah, int(body["first_verse"]))
        p.first_verse = int(body["first_verse"])
    if "last_verse" in body:
        p.last_verse = int(body["last_verse"]) if body["last_verse"] else None
    if "segment" in body:
        p.segment.update(body["segment"])
    p.save()
    return {"job": _job("analyze", pid, lambda progress: project.analyze(p, progress) and pid)}


@app.post("/api/projects/{pid}/split")
def split(pid: str, body: dict):
    p = project.Project.load(_folder(pid))
    blocks = [segment.Block.from_dict(b) for b in p.blocks]
    try:
        segment.split_block(blocks, int(body["index"]), int(body["word"]))
    except (ValueError, IndexError) as e:
        raise HTTPException(400, str(e))
    p.blocks = [b.to_dict() for b in blocks]
    p.save()
    return _public(p)


@app.post("/api/projects/{pid}/merge")
def merge(pid: str, body: dict):
    p = project.Project.load(_folder(pid))
    blocks = [segment.Block.from_dict(b) for b in p.blocks]
    try:
        segment.merge_blocks(blocks, int(body["index"]))
    except (ValueError, IndexError) as e:
        raise HTTPException(400, str(e))
    p.blocks = [b.to_dict() for b in blocks]
    p.save()
    return _public(p)


@app.post("/api/projects/{pid}/restore")
def restore_text(pid: str, body: dict):
    """Undo hand corrections of a verse block's Arabic and phonetic text."""
    p = project.Project.load(_folder(pid))
    b = segment.Block.from_dict(p.blocks[int(body["index"])])
    if b.kind == "verse":
        segment.verse_texts(b)
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


@app.post("/api/projects/{pid}/render")
def start_render(pid: str):
    p = project.Project.load(_folder(pid))
    if not p.blocks:
        raise HTTPException(400, "Rien à rendre")
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
        raise HTTPException(400, "Format non reconnu : choisis une photo (jpg, png, heic…) ou une vidéo.")
    tmp = folder / f"import{ext}"
    with tmp.open("wb") as f:
        shutil.copyfileobj(file.file, f, length=8 << 20)
    try:
        p = project.Project.load(folder)
        return project.add_media(p, tmp, Path(file.filename).name)
    except Exception:
        traceback.print_exc()
        raise HTTPException(400, "Impossible de lire ce fichier (photo ou vidéo abîmée, ou format non pris en charge).")
    finally:
        tmp.unlink(missing_ok=True)


@app.delete("/api/projects/{pid}/media/{name}")
def delete_media(pid: str, name: str):
    p = project.Project.load(_folder(pid))
    p.media = [m for m in p.media if m["file"] != name]
    if p.background:
        p.background["clips"] = [c for c in p.background["clips"] if c["src"] != name] or None
        if p.background["clips"] is None:
            p.background = None
    p.save()
    for f in p.media_dir.glob(Path(name).stem + "*"):
        f.unlink()
    return _public(p)


@app.get("/api/projects/{pid}/media/{name}")
def get_media(pid: str, name: str):
    """Media for the editor (light H.264 copy of videos)."""
    folder = _folder(pid) / "media"
    f = folder / Path(name).name
    preview = folder / f"{f.stem}.preview.mp4"
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
        print(f"\n  Tilawa Studio est déjà ouvert : {url}\n")
        if open_browser:
            webbrowser.open(url)
        return
    print(f"\n  Tilawa Studio : {url}\n  Vidéos : {VIDEOS}\n  (laisse cette fenêtre ouverte, ferme-la pour quitter)\n")
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
        from . import align

        align.get_model()
    except Exception:
        traceback.print_exc()
