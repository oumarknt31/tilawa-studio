"""Benchmark of the automatic detection (which surahs and verses, and when).

Not a unit test (it needs the model and downloads recordings): run it by hand
after touching identify.py, align.py or the detection in project.py:

    uv run python tests/detection_bench.py [case names...]

Each case is a recitation stitched from EveryAyah's verse-by-verse recordings,
so the truth is known exactly: several surahs in a row, a basmala or an
isti'adha before them, a clip cut in the middle of a verse, silence, noise or
speech that is not the Quran, repeated verses. The recordings have no
published licence: they are downloaded into a cache folder, never committed.

A case passes when the verses found are exactly the ones recited, in order,
each found within 0.6 s of when it starts, and nothing is shown over audio
that is not the Quran."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tilawa import align, detect, media, quran, segment  # noqa: E402

CACHE = Path(os.environ.get("TILAWA_BENCH", Path.home() / ".cache" / "tilawa-bench"))
SR = 16000
R = {  # EveryAyah folders
    "alafasy": "Alafasy_128kbps", "husary": "Husary_128kbps", "minshawi": "Minshawy_Murattal_128kbps",
    "abdulbasit": "Abdul_Basit_Murattal_192kbps", "muaiqly": "MaherAlMuaiqly128kbps",
    "dossari": "Yasser_Ad-Dussary_128kbps", "shuraim": "Saood_ash-Shuraym_128kbps",
    "shatri": "Abu_Bakr_Ash-Shaatree_128kbps", "qatami": "Nasser_Alqatami_128kbps",
    "sudais": "Abdurrahmaan_As-Sudais_192kbps",
}
HAS_PREFIXES = {"alafasy", "husary", "shuraim", "shatri"}  # their own bismillah.mp3 / audhubillah.mp3


def V(s, a, b=None):  # verses s:a..b
    return [("v", s, x) for x in range(a, (b or a) + 1)]


B, I = [("basmala",)], [("istiadha",)]


def gap(sec, kind="silence"):
    return [(kind, sec)]


def cut(s, a, start=0.0, end=1.0):  # part of a verse's recording (fractions of its length)
    return [("v", s, a, start, end)]


# name: (reciter, pieces)
CASES = {
    # several surahs
    "fatiha+kursi": ("alafasy", V(1, 1, 7) + gap(1.5) + V(2, 255, 257)),
    "ikhlas-falaq-nas": ("husary", B + V(112, 1, 4) + gap(1) + B + V(113, 1, 5) + gap(1) + B + V(114, 1, 6)),
    "asr+kawthar": ("shuraim", V(103, 1, 3) + gap(1.2) + V(108, 1, 3)),
    "fatiha+qadr": ("minshawi", V(1, 1, 7) + gap(2) + B + V(97, 1, 5)),
    "yasin+mulk": ("abdulbasit", V(36, 1, 6) + gap(1.5) + V(67, 1, 4)),
    "nas+fatiha": ("dossari", V(114, 1, 6) + gap(1) + V(1, 1, 7)),
    "duha-sharh-tin": ("muaiqly", V(93, 1, 11) + B + V(94, 1, 8) + gap(1) + B + V(95, 1, 8)),
    "baqara-end+imran": ("shatri", V(2, 285, 286) + gap(1) + B + V(3, 1, 4)),
    "rahman+waqia": ("qatami", V(55, 1, 13) + gap(1.5) + B + V(56, 1, 7)),
    "istiadha+fatiha+kahf": ("alafasy", I + V(1, 1, 7) + gap(1) + V(18, 1, 4)),
    "fatiha+ikhlas": ("sudais", V(1, 1, 7) + gap(1.5) + V(112, 1, 4)),
    "falaq+talk+nas": ("husary", V(113, 1, 5) + gap(6, "speech") + V(114, 1, 6)),
    "baqara-two-places": ("shatri", V(2, 1, 5) + gap(2) + V(2, 255, 256)),
    "prayer-fatiha+baqara": ("shuraim", V(1, 1, 7) + gap(2) + V(2, 54, 57)),
    # the start of the recitation
    "cut-ahzab35": ("husary", cut(33, 35, 0.12) + V(33, 36)),
    "duha-intro": ("shuraim", gap(5) + I + B + V(93, 1, 11)),
    "music-baqara153": ("sudais", gap(4, "noise") + V(2, 153, 156)),
    "muminun34": ("abdulbasit", V(23, 34, 40)),
    "yasin-start": ("minshawi", V(36, 1, 8)),
    "maryam-start": ("alafasy", V(19, 1, 5)),
    "alif-lam-mim": ("husary", B + V(2, 1, 5)),
    "rahman-refrain-start": ("dossari", V(55, 13, 20)),
    "cut-naba-half": ("qatami", cut(78, 1, 0.5) + V(78, 2, 10)),
    "talk+kursi": ("alafasy", gap(8, "speech") + V(2, 255)),
    "short-verse-first": ("muaiqly", V(74, 1, 7)),
    "cut-kahf-word": ("shatri", cut(18, 10, 0.3) + V(18, 11, 12)),
    # repeats, ends, long
    "ikhlas-repeat": ("shatri", V(112, 1) + V(112, 1, 4)),
    "repeat-verse": ("husary", V(2, 255) + V(2, 255) + V(2, 256)),
    "end-cut": ("sudais", V(2, 284, 285) + cut(2, 286, 0, 0.55)),
    "mulk-long": ("husary", V(67, 1, 15)),
    "muzzammil": ("shuraim", V(73, 1, 10)),
}


def _file(reciter: str, name: str) -> Path:
    out = CACHE / "everyayah" / R[reciter] / name
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        import certifi
        import ssl

        ctx = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(f"https://everyayah.com/data/{R[reciter]}/{name}", timeout=60, context=ctx) as r:
            out.write_bytes(r.read())
    return out


def _speech() -> np.ndarray:
    """Arabic speech that is not the Quran (a talk), for the "not a recitation" cases."""
    f = CACHE / "speech.wav"
    if not f.exists():
        import yt_dlp

        tmp = CACHE / "speech-src"
        with yt_dlp.YoutubeDL({"format": "bestaudio", "outtmpl": str(tmp) + ".%(ext)s", "quiet": True,
                               "ffmpeg_location": str(Path(media.tools()[0]).parent),
                               "download_ranges": yt_dlp.utils.download_range_func(None, [(120, 180)])}) as y:
            info = y.extract_info("ytsearch1:محاضرة قصيرة عن الصبر", download=True)
        src = next(CACHE.glob("speech-src.*"))
        subprocess.run([media.tools()[0], "-v", "error", "-y", "-i", str(src), "-ac", "1", "-ar", str(SR), str(f)], check=True)
        print("speech from:", info["entries"][0]["title"])
    return media.load_audio(f)


def _onset(x: np.ndarray) -> tuple[float, float]:
    """Where the voice starts and stops in a recording (s)."""
    hop = SR // 100
    n = len(x) // hop
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    loud = np.nonzero(db > db.max() - 28)[0]  # (lower picks up breaths and room noise)
    return (loud[0] / 100, (loud[-1] + 1) / 100) if len(loud) else (0.0, len(x) / SR)


def build(name: str) -> tuple[np.ndarray, list[dict]]:
    """The case's audio and its truth: [{kind, surah, ayah, t0, t1, whole_start}]."""
    reciter, pieces = CASES[name]
    out, truth, t = [], [], 0.0
    rng = np.random.default_rng(len(name))
    for p in pieces:
        kind = p[0]
        if kind == "v":
            x = media.load_audio(_file(reciter, f"{p[1]:03d}{p[2]:03d}.mp3"))
            f0, f1 = (p[3], p[4]) if len(p) > 3 else (0.0, 1.0)
            o0, o1 = _onset(x)
            if f0 or f1 < 1:  # a cut: fractions of the voiced part
                a, b = int((o0 + f0 * (o1 - o0)) * SR), int((o0 + f1 * (o1 - o0)) * SR)
                x = x[a:b]
                o0, o1 = 0.0, len(x) / SR
            truth.append({"kind": "verse", "surah": p[1], "ayah": p[2], "t0": t + o0, "t1": t + o1,
                          "cut_start": f0 > 0, "cut_end": f1 < 1})
        elif kind in ("basmala", "istiadha"):
            own = reciter in HAS_PREFIXES  # the others: the basmala is their 1:1, the isti'adha Alafasy's
            if kind == "basmala":
                x = media.load_audio(_file(reciter, "bismillah.mp3" if own else "001001.mp3"))
            else:
                x = media.load_audio(_file(reciter if own else "alafasy", "audhubillah.mp3"))
            o0, o1 = _onset(x)
            truth.append({"kind": kind, "t0": t + o0, "t1": t + o1})
        else:
            sec = p[1]
            if kind == "silence":
                x = np.zeros(int(sec * SR), np.float32)
            elif kind == "noise":  # music-like: chords and noise
                tt = np.arange(int(sec * SR)) / SR
                x = sum(0.08 * np.sin(2 * np.pi * f * tt) for f in (220, 277, 330, 440)) + 0.02 * rng.standard_normal(len(tt))
                x = x.astype(np.float32)
            else:
                sp = _speech()
                x = sp[: int(sec * SR)]
            truth.append({"kind": kind, "t0": t, "t1": t + len(x) / SR})
        out.append(x)
        pause = np.zeros(int(0.35 * SR), np.float32)  # breath between recordings
        out.append(pause)
        t += (len(x) + len(pause)) / SR
    return np.concatenate(out), truth


def emissions(name: str, audio: np.ndarray) -> np.ndarray:
    f = CACHE / "cases" / f"{name}.npy"
    if f.exists():
        em = np.load(f)
        if len(em) == len(audio) // 320:  # else the case changed
            return em
    f.parent.mkdir(parents=True, exist_ok=True)
    em = align.get_model().emissions(audio)
    np.save(f, em)
    return em


def evaluate(blocks: list[segment.Block], truth: list[dict]) -> dict:
    """Compare the subtitles with the truth."""
    verses = [b for b in blocks if b.kind == "verse"]
    # each truth verse: the blocks of the same verse that start around it
    got_seq, last, prev = [], [], None
    for b in verses:  # a new recitation of a verse: another verse, or the same again from its start
        if not prev or (prev.surah, prev.ayah) != (b.surah, b.ayah) or b.a0 == 0 and prev.a1 >= len(quran.verse(b.surah, b.ayah).align):
            got_seq.append(((b.surah, b.ayah), b))
            last.append(b)
        last[-1] = b
        prev = b
    want = [((x["surah"], x["ayah"]), x) for x in truth if x["kind"] == "verse"]
    problems = []
    if [k for k, _ in got_seq] != [k for k, _ in want]:
        problems.append(f"verses {_fmt([k for k, _ in got_seq])} instead of {_fmt([k for k, _ in want])}")
    else:
        for (k, b), end, (_, x) in zip(got_seq, last, want):
            if not x["cut_end"] and end.a1 < len(quran.verse(*k).align):
                problems.append(f"{k[0]}:{k[1]} shown up to word {end.a1} of {len(quran.verse(*k).align)}")
            if not x["cut_start"] and abs(b.voice_start - x["t0"]) > 0.6:
                problems.append(f"{k[0]}:{k[1]} starts at {b.voice_start:.1f}s instead of {x['t0']:.1f}s")
            if x["cut_start"] is False and b.a0 != 0:
                problems.append(f"{k[0]}:{k[1]} shown from word {b.a0 + 1}")
        first, b0 = want[0][1], got_seq[0][1]
        if first["cut_start"] and (b0.a0 != 0 or b0.start > 0.05):
            problems.append(f"cut clip: first verse shown from word {b0.a0 + 1} at {b0.start:.1f}s, not the start at 0s")
    # nothing over what is not the Quran
    for x in truth:
        if x["kind"] in ("silence", "noise", "speech"):
            for b in blocks:
                ov = min(b.voice_end, x["t1"]) - max(b.voice_start, x["t0"])
                if ov > 0.5:
                    problems.append(f"{b.kind} {b.surah}:{b.ayah} shown over {x['kind']} ({ov:.1f}s)")
    return {"ok": not problems, "problems": problems, "got": _fmt([k for k, _ in got_seq])}


def _fmt(seq):
    out = []
    for s, a in seq:
        if out and out[-1][0] == s and out[-1][2] == a - 1:
            out[-1][2] = a
        else:
            out.append([s, a, a])
    return " ".join(f"{s}:{a}" + (f"-{b}" if b != a else "") for s, a, b in out)


def main(names: list[str]) -> None:
    names = names or list(CASES)
    model = align.get_model()
    ok = 0
    t_all = time.time()
    for name in names:
        audio, truth = build(name)
        em = emissions(name, audio)
        t = time.time()
        blocks, _ = detect.detect(em, audio, model, segment.Options())
        res = evaluate(blocks, truth)
        ok += res["ok"]
        print(f"{'ok  ' if res['ok'] else 'FAIL'} {name:24s} {time.time() - t:5.1f}s  {res['got']}")
        for pr in res["problems"]:
            print("       -", pr)
    print(f"\n{ok}/{len(names)} cases pass ({time.time() - t_all:.0f}s)")


if __name__ == "__main__":
    main(sys.argv[1:])
