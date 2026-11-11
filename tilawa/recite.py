"""Recitations recorded in the app (or imported), the verses recognised in them, and the two streaks:
the recitation streak (a day with at least one verse recited) and the creation streak (a day with a
video exported). The day is the computer's own (from midnight to midnight where the user lives).

Each recitation is a folder in Tilawa Studio/Récitations/<id>/: recitation.wav (16 kHz mono) and
recitation.json. Nothing leaves the computer."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
import wave
from pathlib import Path

import numpy as np

from . import media, quran
from .i18n import UserError

RATE = 16000


# ---------------------------------------------------------------- recording from the microphone

def _mic() -> list[str]:
    """ffmpeg's input for the default microphone of the system (TILAWA_MIC: another input, for tests)."""
    if os.environ.get("TILAWA_MIC"):
        return ["-re", "-f", "lavfi", "-i", os.environ["TILAWA_MIC"]]
    if sys.platform == "darwin":
        return ["-f", "avfoundation", "-i", ":default"]
    if sys.platform == "win32":
        out = subprocess.run([media.tools()[0], "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
                             capture_output=True, text=True, errors="replace").stderr
        names = re.findall(r'"([^"]+)"\s*\(audio\)', out)
        if not names:
            raise UserError("no_microphone")
        return ["-f", "dshow", "-i", f"audio={names[0]}"]
    return ["-f", "pulse", "-i", "default"]


class Recorder:
    """The microphone recorded into a WAV file, its level readable while it records."""

    def __init__(self, out: Path):
        self.out, self.level, self.seconds, self.error = out, 0.0, 0.0, ""
        out.parent.mkdir(parents=True, exist_ok=True)
        self.proc = subprocess.Popen([media.tools()[0], "-hide_banner", "-loglevel", "error", *_mic(),
                                      "-ac", "1", "-ar", str(RATE), "-f", "s16le", "pipe:1"],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.wav = wave.open(str(out), "wb")
        self.wav.setnchannels(1); self.wav.setsampwidth(2); self.wav.setframerate(RATE)
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()

    def _read(self):
        frames = 0
        while chunk := self.proc.stdout.read(RATE // 10 * 2):  # a tenth of a second
            self.wav.writeframes(chunk)
            x = np.frombuffer(chunk, np.int16).astype(np.float32) / 32768
            # loudness shown from -50 dB (silence) to 0 dB
            self.level = float(np.clip((20 * np.log10(np.sqrt(np.mean(x * x)) + 1e-9) + 50) / 50, 0, 1)) if len(x) else 0.0
            frames += len(x)
            self.seconds = frames / RATE

    def stop(self) -> Path:
        try:
            self.proc.stdin.write(b"q"); self.proc.stdin.flush()
        except OSError:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.thread.join(timeout=5)
        self.wav.close()
        if self.seconds < 0.5:  # no sound came: no microphone, or not allowed to use it
            err = self.proc.stderr.read().decode(errors="replace").strip().splitlines()
            raise UserError("mic_failed", err=(err[-1] if err else "")[:200])
        return self.out

    def cancel(self):
        self.proc.kill()
        self.thread.join(timeout=5)
        self.wav.close()
        self.out.unlink(missing_ok=True)


# ---------------------------------------------------------------- the verses recited

def folder(home: Path) -> Path:
    return Path(home) / "Récitations"


def new_id() -> str:
    return time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4]


def recognise(wav: Path, progress=lambda s, f: None) -> dict:
    """Which verses are recited: [[surah, first, last], ...] as the reading numbers them, their Hafs keys
    in order, and the reading heard."""
    from . import align, detect, project, segment, warsh

    progress("audio", 0.05)
    audio = media.load_audio(wav)
    progress("model", 0.15)
    model = align.get_model()
    progress("listening", 0.3)
    em = model.emissions(audio)
    short = model.emissions(audio, detect.SHORT_CHUNK_S, detect.SHORT_CONTEXT_S)
    progress("identify", 0.7)
    opt = segment.Options()
    quran.use_reading("hafs")
    blocks, _ = detect.detect(em, audio, model, opt, 0, 1, None, short)
    reading = warsh.reading_heard(em, model, blocks)
    if reading == "warsh":
        quran.use_reading("warsh")
        blocks, _ = detect.detect(em, audio, model, opt, 0, 1, None, short)
    verses = [b for b in blocks if b.kind == "verse"]
    if not verses:  # too short for the passage tracker (a single short verse): compared with every verse
        return _short(em, model, len(audio))
    keys, passages = [], []
    for b in verses:
        if [b.surah, b.ayah] not in keys:
            keys.append([b.surah, b.ayah])
        first, last = project.numbers(b.to_dict())
        first, last = first or 1, last or first or 1
        if passages and passages[-1][0] == b.surah and passages[-1][1] <= first <= passages[-1][2] + 1:
            passages[-1][2] = max(passages[-1][2], last)
        else:
            passages.append([b.surah, first, last])
    progress("done", 1.0)
    return {"passages": passages, "keys": keys, "verses": len({(p[0], n) for p in passages for n in range(p[1], p[2] + 1)}),
            "reading": reading, "duration": round(len(audio) / RATE, 1)}


SHORT_HEARD = 0.75  # share of the letters heard that must read like the verses found
SHORT_VERSES = 0.6  # share of those verses' letters that must be heard


def _short(em: np.ndarray, model, samples: int) -> dict:
    """A short recitation (a verse or a few): the verses whose letters read best like the letters heard,
    when most of what is heard matches them and most of them is heard. Verses that read the same
    (a refrain) give the first of them."""
    from . import identify

    out = {"passages": [], "keys": [], "verses": 0, "reading": "hafs", "duration": round(samples / RATE, 1)}
    q, _ = identify.heard(em, model)
    if len(q) < 4:
        return out
    codes, _ = identify._codes()
    owner = identify._index(True)[1]
    best = None
    for (s, a), (start, n) in identify._verses().items():
        if a == 0:
            continue
        text = codes[start:start + n + 2 * len(q)]  # the verse, and what follows it (a few verses)
        matched, fq, lq, ft, lt = identify._fit(q, text)
        if fq < 0:
            continue
        span = [k for k in dict.fromkeys(owner[start + ft:start + lt + 1]) if k[1]]
        letters = sum(identify._verses()[k][1] for k in span)
        if matched >= SHORT_HEARD * len(q) and matched >= SHORT_VERSES * letters:
            score = (matched, -len(span))
            if not best or score > best[0]:
                best = (score, span)
    if best:
        span = best[1]
        out["keys"] = [list(k) for k in span]
        out["passages"] = [[span[0][0], span[0][1], span[-1][1]]] if len({k[0] for k in span}) == 1 else [[s, a, a] for s, a in span]
        out["verses"] = len(span)
    return out


def label(passages: list[list[int]]) -> str:
    """"Al-Mulk 1–10 · Al-Ikhlas 1–4"."""
    return " · ".join(f"{quran.surah(s)['name']} {a}" + (f"–{b}" if b != a else "") for s, a, b in passages)


def save(home: Path, rid: str, wav: Path, found: dict, imported: bool = False) -> dict:
    d = folder(home) / rid
    d.mkdir(parents=True, exist_ok=True)
    if wav.resolve() != (d / "recitation.wav").resolve():
        shutil.move(str(wav), d / "recitation.wav")
    now = dt.datetime.now()
    rec = {"id": rid, "day": now.date().isoformat(), "time": now.strftime("%H:%M"), "imported": imported,
           **found, "label": label(found["passages"])}
    (d / "recitation.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


def recitations(home: Path) -> list[dict]:
    out = []
    for f in folder(home).glob("*/recitation.json"):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
    return sorted(out, key=lambda r: r["id"], reverse=True)


# ---------------------------------------------------------------- streaks

def log_export(home: Path, project_id: str, file: str) -> None:
    """A video exported today: a day of the creation streak."""
    f = Path(home) / "activity.json"
    try:
        log = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        log = []
    log.append({"day": dt.date.today().isoformat(), "kind": "export", "project": project_id, "file": file})
    f.write_text(json.dumps(log[-5000:], ensure_ascii=False, indent=0), encoding="utf-8")


def export_days(home: Path, videos: Path) -> set[str]:
    """Days a video was exported: the log, and the videos already in the folder (made before the log)."""
    days = set()
    try:
        days |= {x["day"] for x in json.loads((Path(home) / "activity.json").read_text(encoding="utf-8")) if x.get("kind") == "export"}
    except (OSError, ValueError):
        pass
    if videos.exists():
        days |= {dt.date.fromtimestamp(f.stat().st_mtime).isoformat() for f in videos.iterdir() if f.suffix in (".mp4", ".mov")}
    return days


def streak(days: set[str], today: dt.date | None = None) -> dict:
    """Days in a row up to today (today not done yet: up to yesterday, the streak is still alive),
    the best ever, and the last 7 days."""
    today = today or dt.date.today()
    done = lambda d: d.isoformat() in days
    start = today if done(today) else today - dt.timedelta(days=1)
    n = 0
    while done(start - dt.timedelta(days=n)):
        n += 1
    best, run, prev = 0, 0, None
    for d in sorted(dt.date.fromisoformat(x) for x in days):
        run = run + 1 if prev and (d - prev).days == 1 else 1
        best, prev = max(best, run), d
    return {"current": n, "best": max(best, n), "today": done(today),
            "week": [{"day": (today - dt.timedelta(days=k)).isoformat(), "done": done(today - dt.timedelta(days=k))} for k in range(6, -1, -1)]}
