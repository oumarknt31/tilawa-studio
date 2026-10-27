"""Accuracy benchmark: hundreds of generated cases, to measure the detection honestly.

detection_bench.py holds 31 hand-made cases, good for finding bugs; this one says how often
the detection is right, on recordings like the ones users bring:

    uv run python tests/accuracy_bench.py               # the dev cases (work on these)
    uv run python tests/accuracy_bench.py --split sealed  # score only (measure a version)
    uv run python tests/accuracy_bench.py --cases 12 40   # some cases, with their problems

A case number always gives the same case (generated from it):
- quran.com full-surah recordings (12 recitations, with the time of every verse): real
  continuous recitation, clipped as users clip it (a Short, from the surah start, up to its
  end, cut mid-verse), Al-Fatiha then a surah as in a prayer, two surahs, a verse said twice;
- EveryAyah verse-by-verse files (about 45 reciters), stitched: basmala, isti'adha, speech or
  music before, repeats, a second surah. Warsh reciters are scored apart (the text is Hafs);
- about half of them degraded: mosque reverb, room noise, phone sound, faster or slower.

30% of the case numbers are sealed: never look at them while fixing, or the score stops
meaning anything; --split sealed prints only the score. A case passes as in
detection_bench.evaluate. The recordings have no published licence: they are downloaded
into the cache folder, never committed."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import tempfile
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import detection_bench as db  # noqa: E402
from tilawa import align, detect, media, quran, segment  # noqa: E402

SR = db.SR
HOME = db.CACHE / "accuracy"
QDC = {97: "dossari", 2: "abdulbasit", 3: "sudais", 4: "shatri", 5: "rifai", 6: "husary", 10: "shuraim",
       161: "tunaiji", 1: "abdulbasit-mujawwad", 7: "alafasy", 9: "minshawi", 12: "husary-muallim"}
# (173, Alafasy "streaming", has broken timings)
# quran.com verse times are often over a second off, sometimes many: the boundaries come from
# forced alignment of the text (_bounds); a fit worse than this (mean log-prob) is not the verses
FORCE_MIN = -2.0
VOICE_HOLD = 0.15  # the voice proper lasts this long (a click before it does not)
EA = ["Abdul_Basit_Murattal_192kbps", "Abdul_Basit_Mujawwad_128kbps", "Abdullah_Basfar_192kbps",
      "Abdurrahmaan_As-Sudais_192kbps", "AbdulSamad_64kbps_QuranExplorer.Com", "Abu_Bakr_Ash-Shaatree_128kbps",
      "Ahmed_ibn_Ali_al-Ajamy_128kbps_ketaballah.net", "Alafasy_128kbps", "Ghamadi_40kbps", "Hani_Rifai_192kbps",
      "Husary_128kbps", "Husary_128kbps_Mujawwad", "Hudhaify_128kbps", "MaherAlMuaiqly128kbps", "Menshawi_32kbps", "Minshawy_Mujawwad_192kbps", "Minshawy_Murattal_128kbps",
      "Mohammad_al_Tablaway_128kbps", "Muhammad_Ayyoub_128kbps", "Muhammad_Jibreel_128kbps", "Mustafa_Ismail_48kbps",
      "Saood_ash-Shuraym_128kbps", "Parhizgar_48kbps", "Salaah_AbdulRahman_Bukhatir_128kbps",
      "Muhsin_Al_Qasim_192kbps", "Salah_Al_Budair_128kbps",
      "Abdullah_Matroud_128kbps", "Ahmed_Neana_128kbps", "Muhammad_AbdulKareem_128kbps", "khalefa_al_tunaiji_64kbps",
      "mahmoud_ali_al_banna_32kbps", "Karim_Mansoori_40kbps", "Husary_Muallim_128kbps",
      "Khaalid_Abdullaah_al-Qahtaanee_192kbps", "Yasser_Ad-Dussary_128kbps", "Nasser_Alqatami_128kbps",
      "Ali_Hajjaj_AlSuesy_128kbps", "Sahl_Yassin_128kbps", "aziz_alili_128kbps", "Yaser_Salamah_128kbps",
      "Akram_AlAlaqimy_128kbps", "Ali_Jaber_64kbps", "Fares_Abbad_64kbps", "Ayman_Sowaid_64kbps"]
WARSH = ["warsh/warsh_ibrahim_aldosary_128kbps", "warsh/warsh_yassin_al_jazaery_64kbps", "warsh/warsh_Abdul_Basit_128kbps"]
EA_PREFIXES = {"Alafasy_128kbps", "Husary_128kbps", "Saood_ash-Shuraym_128kbps", "Abu_Bakr_Ash-Shaatree_128kbps"}
# their 001001.mp3 is the isti'adha then the basmala: not a basmala, and Al-Fatiha starts at 1:2
EA_ISTIADHA_IN_1 = {"Mustafa_Ismail_48kbps", "Parhizgar_48kbps", "mahmoud_ali_al_banna_32kbps",
                    "Karim_Mansoori_40kbps", "Ali_Jaber_64kbps"}
# their verse 1 files hold the basmala too: no basmala added, and that verse's start is unknown
EA_BASMALA_IN_V1 = {"AbdulSamad_64kbps_QuranExplorer.Com", "Ahmed_ibn_Ali_al-Ajamy_128kbps_ketaballah.net",
                    "Menshawi_32kbps", "Mustafa_Ismail_48kbps", "Parhizgar_48kbps", "Muhammad_AbdulKareem_128kbps",
                    "mahmoud_ali_al_banna_32kbps", "warsh/warsh_yassin_al_jazaery_64kbps"}
# live recordings (the audience is as loud as the reciter): only the verses are checked, not when
EA_NO_TIMING = {"Abdul_Basit_Mujawwad_128kbps", "Husary_128kbps_Mujawwad", "Minshawy_Mujawwad_192kbps",
                "Mustafa_Ismail_48kbps"}
UNKNOWN = (-1e9, 1e9)
MIN_CASE_S = 12.0  # shorter than any Short
LONG_FILE_S = 2400  # a surah recording longer than this is picked less often (big download)


def sealed(i: int) -> bool:
    return (i * 7919 + 13) % 10 < 3


# ---------------------------------------------------------------- sources

def _get(url: str, out: Path) -> Path:
    if not out.exists():
        import certifi
        import ssl

        out.parent.mkdir(parents=True, exist_ok=True)
        ctx = ssl.create_default_context(cafile=certifi.where())
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TilawaStudio-bench"})  # (urllib's is refused)
        with urllib.request.urlopen(req, timeout=120, context=ctx) as r:
            data = r.read()
        tmp = out.with_suffix(out.suffix + ".part")
        tmp.write_bytes(data)
        tmp.rename(out)
    return out


def _qdc_info(rid: int, surah: int) -> dict:
    f = _get(f"https://api.qurancdn.com/api/qdc/audio/reciters/{rid}/audio_files?chapter={surah}&segments=true",
             HOME / "qdc" / str(rid) / f"{surah}.json")
    a = json.loads(f.read_text())["audio_files"][0]
    dur = a["duration"] / 1000
    verses = []
    for v in a["verse_timings"]:
        f, t = v["timestamp_from"] / 1000, min(dur, v["timestamp_to"] / 1000)
        segs = [s for s in v.get("segments") or [] if len(s) >= 3]
        verses.append({"ayah": int(v["verse_key"].split(":")[1]), "from": f, "to": t,
                       "w0": segs[0][1] / 1000 if segs else f})  # its first word (often closer than "from")
    return {"url": a["audio_url"], "duration": dur, "verses": verses}


def _decode(path: Path, t0: float, t1: float) -> np.ndarray:
    out = subprocess.run([media.tools()[0], "-v", "error", "-ss", f"{t0:.3f}", "-i", str(path), "-t", f"{t1 - t0:.3f}",
                          "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def _between(path: Path, vs: list[dict], k: int) -> float:
    """Where to cut between verse k-1 and verse k: the quietest moment around their boundary
    (quran.com's times can be a second off, and a cut in a word leaves a syllable of the
    other verse in the clip)."""
    v, p = vs[k], vs[k - 1]
    lo, hi = max(p["w0"] + 0.3, min(v["from"], v["w0"]) - 1.2), max(v["from"], v["w0"]) + 0.3
    lo, hi = (_bounds(path, vs, [k]).get(k) or (lo, hi))[:2]
    if hi - lo < 0.5:
        return (lo + hi) / 2
    x = _decode(path, lo - 0.5, hi)[int(0.5 * SR):]  # (a seek starts with a few ms of zeros)
    hop = SR // 100
    n = len(x) // hop
    if n < 30:
        return v["from"]
    level = np.convolve(20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(axis=1)) + 1e-9),
                        np.ones(20) / 20, mode="same")
    return lo + (10 + int(np.argmin(level[10:-10]))) / 100


def _ea(folder: str, name: str) -> np.ndarray:
    return media.load_audio(_get(f"https://everyayah.com/data/{folder}/{name}", HOME / "everyayah" / folder / name))


def _surah(rng) -> int:
    """Mostly what people recite in Shorts and prayers (Juz 'Amma, Al-Fatiha), but every surah."""
    r = rng.random()
    if r < 0.12:
        return 1
    if r < 0.5:
        return int(rng.integers(78, 115))
    return int(rng.integers(1, 115))


def _length(rng) -> float:
    r = rng.random()
    return rng.uniform(15, 60) if r < 0.45 else rng.uniform(60, 180) if r < 0.8 else rng.uniform(180, 420)


# ---------------------------------------------------------------- building

class Case:
    def __init__(self):
        self.parts: list[np.ndarray] = []
        self.truth: list[dict] = []
        self.t = 0.0

    def add(self, x: np.ndarray, truth: list[dict] = ()):
        for e in truth:
            self.truth.append({**e, **{k: self.t + e[k] for k in ("t0", "t1", "t0_lo", "t0_hi") if k in e}})
        self.parts.append(x.astype(np.float32))
        self.t += len(x) / SR

    def gap(self, sec: float, kind: str = "silence", rng=None):
        if kind == "silence":
            x = np.zeros(int(sec * SR), np.float32)
        elif kind == "noise":  # music-like: chords and noise
            tt = np.arange(int(sec * SR)) / SR
            x = sum(0.08 * np.sin(2 * np.pi * f * tt) for f in (220, 277, 330, 440)) + 0.02 * rng.standard_normal(len(tt))
        else:
            sp = db._speech()
            a = int(rng.integers(0, max(1, len(sp) - int(sec * SR))))
            x = sp[a:a + int(sec * SR)]
        self.add(x, [{"kind": kind, "t0": 0.0, "t1": len(x) / SR}])

    def audio(self) -> np.ndarray:
        return np.concatenate(self.parts) if self.parts else np.zeros(SR, np.float32)


def _verse_truth(x: np.ndarray, surah: int, ayah: int, t0: float, t1: float, cut_start=False, cut_end=False,
                 word_start: float | None = None, timing: bool = True) -> dict:
    """A verse inside x between t0 and t1 (s): where the voice is. The start is known within a
    range: from the loudness (the first sound, which can be a breath or the echo of the verse
    before, up to the voice proper, 20 dB below the loudest) and quran.com's first word (which
    can be a second off) when there is one; no range at all when timing is False."""
    a, b = int(t0 * SR), max(int(t0 * SR) + 1, int(t1 * SR))
    o0, o1 = (0.0, (b - a) / SR) if cut_start and cut_end else db._onset(x[a:b])
    if cut_start:
        o0 = 0.0
    if cut_end:
        o1 = (b - a) / SR
    start = t0 + o0
    known = [start] + ([] if cut_start else [t0 + db._onset(x[a:b], 20, VOICE_HOLD)[0]])
    known += [min(max(word_start, t0), t1)] if word_start is not None and not cut_start else []
    lo, hi = (min(known), max(known)) if timing else UNKNOWN
    return {"kind": "verse", "surah": surah, "ayah": ayah, "t0": start, "t1": t0 + o1, "t0_lo": lo, "t0_hi": hi,
            "cut_start": cut_start, "cut_end": cut_end}


_model = None


def _bounds(path: Path, vs: list[dict], ks=()) -> dict[int, list | None]:
    """Where verse k-1 ends and verse k starts in a quran.com recording: {k: [end, start,
    clean]}, None where forced alignment does not find the verses around quran.com's times;
    clean is False when over a second of voice lies between them (a verse said again, or half
    of it, that the timings do not know). The boundaries ks are found together (the verses
    from k-1 to the last k, aligned at once over their stretch); cached."""
    global _model
    cache = path.with_name(f"{path.stem}.bounds.json")
    out = {int(k): b for k, b in json.loads(cache.read_text()).items()} if cache.exists() else {}
    ks = sorted(k for k in ks if 0 < k < len(vs) and k not in out)
    if not ks:
        return out
    _model = _model or align.get_model()
    surah, first, last = int(path.stem), ks[0] - 1, ks[-1]
    toks = [[t for w in quran.verse(surah, vs[j]["ayah"]).align for t in _model.tokens(w)] for j in range(first, last + 1)]
    end = vs[last + 1]["from"] if last + 1 < len(vs) else vs[-1]["to"]
    found = None
    for pad in (20.0, 60.0):  # (the times drift: up to 17 s seen)
        a = max(0.0, vs[first]["from"] - pad)
        x = _decode(path, a, end + pad)
        chunk = 4 * SR  # one pass of detection's two (longer windows go deaf to 82:17-18, alike)
        em = _model._pass(x, list(range(0, len(x), chunk)), chunk, SR, len(x) // 320)
        frames, ends, score = _force(em, [t for v in toks for t in v], _model)
        if score >= FORCE_MIN:
            found = a, x, frames, ends
            break
    for k in ks:
        out[k] = None
    if found:
        a, x, frames, ends = found
        hop = SR // 100
        n = len(x) // hop
        level = 10 * np.log10((x[:n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
        edges = np.cumsum([0] + [len(v) for v in toks])  # first token of each verse
        for k in ks:
            j = k - first
            e, s_ = a + (ends[edges[j] - 1] + 1) * align.FRAME_S, a + frames[edges[j]] * align.FRAME_S
            voice = np.count_nonzero(level[int((e - a) * 100):int((s_ - a) * 100)] > level.max() - 20) / 100
            out[k] = [float(e), float(s_), bool(voice < 1.0)]
    cache.write_text(json.dumps(out))
    return out


def _force(em: np.ndarray, toks: list[int], model) -> tuple[np.ndarray, np.ndarray, float]:
    """Strict CTC alignment of toks (every one, in order; word separators count as blank)
    with anything before and after them: (first frame of each token, last frame of each
    token, mean log-prob of the tokens there)."""
    em = em.astype(np.float64)
    T, L = len(em), len(toks)
    S = 2 * L + 1  # blank, token, blank, ..., blank
    tok = np.array(toks)
    is_tok = np.arange(S) % 2 == 1
    col = np.where(is_tok, tok[np.clip((np.arange(S) - 1) // 2, 0, L - 1)], 0)
    blank = np.logaddexp(em[:, model.blank], em[:, model.sep])
    # silence costs nothing outside the verses and a little inside them, else they spread over it
    filler = np.maximum(em.max(axis=1) - align.FILLER_PENALTY, blank)
    blank = blank - 0.02
    skip = np.zeros(S, dtype=bool)  # s-2 -> s: a token unlike the one before
    skip[3::2] = tok[1:] != tok[:-1]
    skip[1] = True
    NEG = -1e18
    # states: 0 before, 1..S the CTC states, S+1 after
    dp = np.full(S + 2, NEG)
    back = np.zeros((T, S + 2), dtype=np.int8)
    emit = lambda t: np.where(is_tok, em[t, col], blank[t])
    e0 = emit(0)
    dp[0], dp[1], dp[2] = filler[0], e0[0], e0[1]
    for t in range(1, T):
        prev, cur = dp, np.full(S + 2, NEG)
        cur[0] = prev[0] + filler[t]
        stay = prev[1:S + 1]
        step = np.concatenate(([prev[0]], prev[1:S]))
        jump = np.where(skip, np.concatenate(([NEG, prev[0]], prev[1:S - 1])), NEG)
        cand = np.stack([stay, step, jump])
        k = cand.argmax(axis=0)
        cur[1:S + 1] = cand[k, np.arange(S)] + emit(t)
        back[t, 1:S + 1] = k
        last = max(prev[S - 1], prev[S])
        if prev[S + 1] >= last:
            cur[S + 1], back[t, S + 1] = prev[S + 1] + filler[t], 0
        else:
            cur[S + 1], back[t, S + 1] = last + filler[t], 1 if prev[S] >= prev[S - 1] else 2
        dp = cur
    s = int(np.argmax([dp[S - 1], dp[S], dp[S + 1]])) + S - 1
    frames, ends = np.full(L, -1, dtype=np.int64), np.full(L, -1, dtype=np.int64)
    if dp[s] <= NEG / 2:
        return frames, ends, -1e9
    for t in range(T - 1, -1, -1):
        if 1 <= s <= S and s % 2 == 0:  # (state s is CTC index s-1: odd = a token)
            frames[(s - 2) // 2] = t  # (going back: ends at the token's first frame)
            if ends[(s - 2) // 2] < 0:
                ends[(s - 2) // 2] = t
        if t == 0:
            break
        k = int(back[t, s])
        if s == S + 1:
            s = S + 1 if k == 0 else S + 1 - k
        elif s > 0:
            s -= k
    if (frames < 0).any():
        return frames, ends, -1e9
    return frames, ends, float(np.mean(em[frames, tok]))


def _heard_from(path: Path, vs: list[dict], k: int, cut: float) -> int | None:
    """Verse k of a quran.com recording cut at `cut` (s): its first word heard whole (the
    words before it are not heard, or only their end); None where its stretch is not known."""
    global _model
    b0, b1 = _bounds(path, vs, [k, k + 1]).get(k), _bounds(path, vs, [k + 1]).get(k + 1)
    start = vs[0]["w0"] if k == 0 else b0 and b0[1]
    end = vs[-1]["to"] if k + 1 == len(vs) else b1 and b1[0]
    if start is None or end is None:
        return None
    words = quran.verse(int(path.stem), vs[k]["ayah"]).align
    _model = _model or align.get_model()
    toks = [_model.tokens(w) for w in words]
    a = max(0.0, start - 0.5)
    x = _decode(path, a, end + 0.5)
    chunk = 4 * SR
    em = _model._pass(x, list(range(0, len(x), chunk)), chunk, SR, len(x) // 320)
    frames, _, score = _force(em, [t for w in toks for t in w], _model)
    if score < FORCE_MIN:
        return None
    firsts = np.cumsum([0] + [len(w) for w in toks])[:-1]
    return next((w for w, f in enumerate(firsts) if a + frames[f] * align.FRAME_S >= cut), len(words) - 1)


def _start_known(path: Path, vs: list[dict], k: int, t0: float) -> tuple[float | None, bool]:
    """(word_start, timing) for _verse_truth, verse k of a quran.com recording cut at t0: where
    forced alignment starts it (the verses may be joined without a pause: the end of the one
    before, "-un", after the cut), unknown where it did not find the boundary or where
    something lies between the verses; quran.com's first word for a surah's first verse."""
    if k == 0:
        return vs[0]["w0"] - t0, True
    b = _bounds(path, vs, [k]).get(k)
    return (b[1] - t0 if b else None), bool(b and b[2])


def _qdc_clip(c: Case, rid: int, surah: int, rng, mode: str, target: float):
    """mode: start (the surah's start), end (up to its end), any; cuts mid-verse sometimes,
    otherwise in the pause between two verses."""
    info = _qdc_info(rid, surah)
    path = _get(info["url"], HOME / "qdc" / str(rid) / f"{surah}.mp3")
    vs = info["verses"]
    if mode == "start":
        i0 = 0
    elif mode == "end":
        acc, i0 = 0.0, len(vs) - 1
        while i0 > 0 and acc < target:
            acc += vs[i0]["to"] - vs[i0]["from"]
            i0 -= 1
    else:
        i0 = int(rng.integers(0, len(vs)))
    i1 = i0
    while i1 + 1 < len(vs) and vs[i1]["to"] - vs[i0]["from"] < target:
        i1 += 1
    cut_start = mode != "start" and rng.random() < 0.2
    cut_end = mode != "end" and i1 + 1 < len(vs) and rng.random() < 0.12
    _bounds(path, vs, range(i0, i1 + 2))
    cuts = [0.0 if i0 == 0 else _between(path, vs, i0)] + [_between(path, vs, k) for k in range(i0 + 1, i1 + 1)] + \
        [info["duration"] if i1 + 1 == len(vs) else _between(path, vs, i1 + 1)]
    if cut_start:
        cuts[0] = cuts[0] + rng.uniform(0.15, 0.6) * (cuts[1] - cuts[0])
    if cut_end:
        cuts[-1] = cuts[-2] + rng.uniform(0.4, 0.85) * (cuts[-1] - cuts[-2])
    t0 = cuts[0]
    x = _decode(path, t0, cuts[-1])
    truth = []
    for j, k in enumerate(range(i0, i1 + 1)):
        truth.append(_verse_truth(x, surah, vs[k]["ayah"], cuts[j] - t0, cuts[j + 1] - t0, cut_start and j == 0,
                                  cut_end and k == i1, *_start_known(path, vs, k, t0)))
    if cut_start:
        truth[0]["heard_from"] = _heard_from(path, vs, i0, cuts[0])
    c.add(x, truth)


def _qdc_repeat(c: Case, rid: int, surah: int, rng):
    """A few verses, one of them said twice in a row (a reciter going back)."""
    info = _qdc_info(rid, surah)
    path = _get(info["url"], HOME / "qdc" / str(rid) / f"{surah}.mp3")
    vs = info["verses"]
    i0 = int(rng.integers(0, len(vs)))
    i1 = min(len(vs) - 1, i0 + int(rng.integers(1, 4)))
    rep = int(rng.integers(i0, i1 + 1))
    cut = lambda k: 0.0 if k == 0 else info["duration"] if k == len(vs) else _between(path, vs, k)
    _bounds(path, vs, range(i0, i1 + 2))
    for k in list(range(i0, rep + 1)) + list(range(rep, i1 + 1)):
        a, b = cut(k), cut(k + 1)
        x = _decode(path, a, b)
        c.add(x, [_verse_truth(x, surah, vs[k]["ayah"], 0.0, len(x) / SR, False, False, *_start_known(path, vs, k, a))])


def _ea_run(c: Case, folder: str, surah: int, rng, target: float, warsh: bool):
    n = quran.surah(surah)["verses"]
    a = 1 if rng.random() < 0.4 else int(rng.integers(1, n + 1))
    if surah == 1 and a == 1 and folder in EA_ISTIADHA_IN_1:
        a = 2
    r = rng.random()
    if not warsh and surah not in (1, 9) and a == 1 and r < 0.6 and folder not in EA_ISTIADHA_IN_1 | EA_BASMALA_IN_V1:
        own = folder in EA_PREFIXES
        x = _ea(folder, "bismillah.mp3" if own else "001001.mp3")
        o0, o1 = db._onset(x)
        c.add(x, [{"kind": "basmala", "t0": o0, "t1": o1}])
        c.gap(0.35)
    rep = int(rng.integers(a, n + 1)) if rng.random() < 0.15 else None
    v, start = a, c.t
    while v <= n and (c.t - start < target or v == a):
        x = _ea(folder, f"{surah:03d}{v:03d}.mp3")
        timing = folder not in EA_NO_TIMING and not (v == 1 and surah != 1 and folder in EA_BASMALA_IN_V1)
        lead, cuts = _ea_lead(folder, surah, v, x)  # (the verses before, said again first)
        cuts = [0.0] + cuts + [len(x) / SR]
        for _ in range(2 if v == rep else 1):
            c.add(x, [_verse_truth(x, surah, u, cuts[j], cuts[j + 1], timing=timing) for j, u in enumerate(lead + [v])])
            c.gap(0.35)
        v += 1


EA_LEAD_MAX = 3  # verses before a verse a recording of it may start with (mujawwad: the one before, again)
EA_LEAD_LOSS = 0.3  # their letters must fit about as well as the verse's own (mean log-prob)


def _ea_lead(folder: str, surah: int, v: int, x: np.ndarray) -> tuple[list[int], list[float]]:
    """An EveryAyah recording of verse v that starts with the verses before it said again
    (Minshawi's mujawwad: "al-hamdu... ar-rahmani r-rahim" in 1:3's file): (those verses,
    where each next one starts, s), found by forced alignment; cached."""
    global _model
    if v == 1:
        return [], []
    cache = HOME / "everyayah" / folder / "lead.json"
    known = json.loads(cache.read_text()) if cache.exists() else {}
    key = f"{surah:03d}{v:03d}"
    if key not in known:
        _model = _model or align.get_model()
        chunk = 4 * SR
        em = _model._pass(x, list(range(0, len(x), chunk)), chunk, SR, len(x) // 320)
        toks = lambda u: [t for w in quran.verse(surah, u).align for t in _model.tokens(w)]
        own = _force(em, toks(v), _model)[2]
        best = ([], [])
        for k in range(1, min(EA_LEAD_MAX, v - 1) + 1):
            us = list(range(v - k, v + 1))
            parts = [toks(u) for u in us]
            frames, ends, score = _force(em, [t for q in parts for t in q], _model)
            if score < max(FORCE_MIN, own - EA_LEAD_LOSS):
                break
            edges = np.cumsum([0] + [len(q) for q in parts])
            cuts = [float((ends[edges[j] - 1] + 1 + frames[edges[j]]) / 2 * align.FRAME_S) for j in range(1, len(us))]
            best = (us[:-1], cuts)
        known[key] = best
        cache.write_text(json.dumps(known))
    return [int(u) for u in known[key][0]], [float(t) for t in known[key][1]]


def build(i: int) -> tuple[np.ndarray, list[dict], dict]:
    """Case i: (audio, truth, meta). Cached."""
    f = HOME / "cases" / f"{i}.npz"
    if f.exists():
        z = np.load(f, allow_pickle=False)
        return z["audio"].astype(np.float32) / 32767, json.loads(str(z["truth"])), json.loads(str(z["meta"]))
    for attempt in range(20):  # a reciter without that surah, a download refused: another draw
        rng = np.random.default_rng([i, attempt])
        try:
            audio, truth, meta = _generate(rng)
            break
        except (urllib.error.HTTPError, KeyError, IndexError, ValueError, subprocess.CalledProcessError):
            continue
    else:
        raise RuntimeError(f"case {i}: no source")
    audio, meta = _augment(audio, truth, meta, rng)
    f.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(f, audio=(np.clip(audio, -1, 1) * 32767).astype(np.int16),
                        truth=json.dumps(truth), meta=json.dumps(meta))
    return audio, truth, meta


def _generate(rng) -> tuple[np.ndarray, list[dict], dict]:
    c = Case()
    r = rng.random()
    if r < 0.6:  # quran.com, continuous
        rid = int(rng.choice(list(QDC)))
        surah = _surah(rng)
        while _qdc_info(rid, surah)["duration"] > LONG_FILE_S and rng.random() < 0.6:
            surah = _surah(rng)
        meta = {"source": "quran.com", "reciter": QDC[rid]}
        k = rng.random()
        lead = rng.random()
        if lead < 0.08:
            c.gap(rng.uniform(2, 8), "speech", rng)
        elif lead < 0.14:
            c.gap(rng.uniform(2, 6), "noise", rng)
        if k < 0.45:
            meta["kind"] = "clip"
            _qdc_clip(c, rid, surah, rng, ["start", "end", "any"][int(rng.choice(3, p=[0.3, 0.25, 0.45]))], _length(rng))
        elif k < 0.7:
            meta["kind"] = "prayer"
            _qdc_clip(c, rid, 1, rng, "start", 999)
            c.gap(rng.uniform(1, 3))
            other = surah if surah != 1 else int(rng.integers(78, 115))
            _qdc_clip(c, rid, other, rng, "start" if rng.random() < 0.5 else "any", rng.uniform(20, 120))
        elif k < 0.88:
            meta["kind"] = "two-surahs"
            s1 = surah if surah < 114 else 113
            s2 = s1 + 1 if rng.random() < 0.6 else _surah(rng)
            if s2 == s1:
                s2 = s1 % 114 + 1
            _qdc_clip(c, rid, s1, rng, "end" if rng.random() < 0.5 else "any", rng.uniform(15, 90))
            c.gap(rng.uniform(0.8, 2.5))
            _qdc_clip(c, rid, s2, rng, "start", rng.uniform(15, 90))
        else:
            meta["kind"] = "repeat"
            _qdc_repeat(c, rid, surah, rng)
    else:  # EveryAyah, stitched
        warsh = rng.random() < 0.08
        folder = str(rng.choice(WARSH if warsh else EA))
        meta = {"source": "everyayah", "reciter": folder.split("/")[-1], "kind": "stitched", "warsh": warsh}
        lead = rng.random()
        if lead < 0.1:
            c.gap(rng.uniform(2, 8), "speech", rng)
        elif lead < 0.18:
            c.gap(rng.uniform(2, 6), "noise", rng)
        elif lead < 0.3 and folder in EA_PREFIXES:
            x = _ea(folder, "audhubillah.mp3")
            o0, o1 = db._onset(x)
            c.add(x, [{"kind": "istiadha", "t0": o0, "t1": o1}])
            c.gap(0.35)
        _ea_run(c, folder, _surah(rng), rng, _length(rng) / 2, warsh)
        if rng.random() < 0.2:
            meta["kind"] = "stitched-two"
            c.gap(rng.uniform(0.8, 2.5))
            _ea_run(c, folder, _surah(rng), rng, rng.uniform(15, 60), warsh)
    if c.t < MIN_CASE_S:
        raise ValueError("too short")
    return c.audio(), c.truth, meta


# ---------------------------------------------------------------- degradation

def _ffmpeg(x: np.ndarray, *args: str) -> np.ndarray:
    out = subprocess.run([media.tools()[0], "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                          *args, "-f", "f32le", "-ar", str(SR), "-ac", "1", "-"],
                         input=x.astype(np.float32).tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def _reverb(x: np.ndarray, rng) -> np.ndarray:
    """A mosque or a hall: decaying noise as the room's response."""
    rt60, wet = rng.uniform(0.8, 2.5), rng.uniform(0.25, 0.6)
    n = int(rt60 * SR)
    ir = rng.standard_normal(n) * np.exp(-6.9 * np.arange(n) / n)
    ir[0] = 0.0
    ir /= np.sqrt((ir ** 2).sum())
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    out = (1 - wet) * x + wet * y * (np.abs(x).max() / (np.abs(y).max() + 1e-9))
    return out.astype(np.float32)


def _noise(x: np.ndarray, rng) -> np.ndarray:
    """Room noise (pink-ish) at 8 to 20 dB below the recitation."""
    w = np.fft.irfft(np.fft.rfft(rng.standard_normal(len(x))) / np.sqrt(np.arange(len(x) // 2 + 1) + 1), len(x))
    voiced = x[np.abs(x) > 0.02 * np.abs(x).max()]
    level = np.sqrt((voiced ** 2).mean()) if len(voiced) else 0.05
    snr = rng.uniform(8, 20)
    return (x + w / np.sqrt((w ** 2).mean()) * level / 10 ** (snr / 20)).astype(np.float32)


def _augment(audio: np.ndarray, truth: list[dict], meta: dict, rng) -> tuple[np.ndarray, dict]:
    if rng.random() < 0.5:
        meta["degraded"] = []
        return audio, meta
    kinds = list(rng.choice(["reverb", "noise", "phone", "speed"], size=int(rng.integers(1, 3)), replace=False))
    for k in kinds:
        if k == "reverb":
            audio = _reverb(audio, rng)
        elif k == "noise":
            audio = _noise(audio, rng)
        elif k == "phone":
            with tempfile.TemporaryDirectory() as d:
                ogg = Path(d) / "phone.ogg"
                subprocess.run([media.tools()[0], "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                                "-af", "highpass=f=300,lowpass=f=3400", "-c:a", "libopus", "-b:a", "12k", str(ogg)],
                               input=audio.astype(np.float32).tobytes(), check=True)
                audio = media.load_audio(ogg)
        else:
            speed = float(rng.uniform(0.92, 1.08))
            audio = _ffmpeg(audio, "-af", f"atempo={speed:.4f}")
            for e in truth:
                for key in ("t0", "t1", "t0_lo", "t0_hi"):
                    if key in e:
                        e[key] /= speed
    meta["degraded"] = sorted(kinds)
    return audio, meta


# ---------------------------------------------------------------- running

def emissions(i: int, audio: np.ndarray, model, short: bool = False) -> np.ndarray:
    """The model's letters (short: with detect's short windows), cached."""
    f = HOME / "cases" / f"{i}.{'em2' if short else 'em'}.npy"
    if f.exists():
        em = np.load(f)
        if len(em) == len(audio) // 320:
            return em
    em = model.emissions(audio, detect.SHORT_CHUNK_S, detect.SHORT_CONTEXT_S) if short else model.emissions(audio)
    np.save(f, em)
    return em


def lower_bound(ok: int, n: int, conf: float = 0.95) -> float:
    """Clopper-Pearson: the true pass rate is at least this, with this confidence."""
    if n == 0 or ok == 0:
        return 0.0
    if ok == n:
        return (1 - conf) ** (1 / n)

    def tail(p):  # P(X >= ok)
        return sum(math.exp(math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
                            + k * math.log(p) + (n - k) * math.log1p(-p)) for k in range(ok, n + 1))
    lo, hi = 0.0, ok / n
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if tail(mid) < 1 - conf else (lo, mid)
    return lo


def categories(meta: dict) -> list[str]:
    out = [f"source:{meta['source']}", f"kind:{meta['kind']}", f"reciter:{meta['reciter']}"]
    out += [f"degraded:{d}" for d in meta.get("degraded", [])] or ["degraded:none"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400, help="case numbers 0..n-1")
    ap.add_argument("--split", choices=["dev", "sealed", "all"], default="dev")
    ap.add_argument("--cases", type=int, nargs="*", help="only these case numbers (shows their problems)")
    ap.add_argument("--build-only", action="store_true", help="download, build and listen; no detection")
    args = ap.parse_args()
    ids = args.cases or [i for i in range(args.n) if args.split == "all" or sealed(i) == (args.split == "sealed")]
    quiet = args.split == "sealed" and not args.cases
    model = align.get_model()
    results, t_all = [], time.time()
    for i in ids:
        audio, truth, meta = build(i)
        em, short = emissions(i, audio, model), emissions(i, audio, model, short=True)
        if args.build_only:
            print(f"built {i} ({len(audio) / SR:.0f}s)", flush=True)
            continue
        blocks, _ = detect.detect(em, audio, model, segment.Options(), short=short)
        res = db.evaluate(blocks, truth)
        res.update(case=i, meta=meta, duration=round(len(audio) / SR, 1))
        results.append(res)
        if not quiet:
            want = db._fmt([(x["surah"], x["ayah"]) for x in truth if x["kind"] == "verse"])
            print(f"{'ok  ' if res['ok'] else 'FAIL'} {i:4d} {meta['kind']:12s} {meta['reciter'][:22]:22s} "
                  f"{'+'.join(meta.get('degraded', [])) or '-':14s} {res['duration']:6.0f}s  {want}", flush=True)
            for p in res["problems"] if not res["ok"] else []:
                print("        -", p)
            for n in res["notes"]:
                print("        note:", n)
    if args.build_only:
        return
    scored = [r for r in results if not r["meta"].get("warsh")]
    ok = sum(r["ok"] for r in scored)
    print(f"\n{args.split}: {ok}/{len(scored)} cases pass ({100 * ok / max(1, len(scored)):.1f}%), "
          f"at least {100 * lower_bound(ok, len(scored)):.1f}% with 95% confidence ({time.time() - t_all:.0f}s)")
    noted = sum(r["ok"] and bool(r["notes"]) for r in scored)
    if noted:
        print(f"  ({noted} of them with a repeat the truth does not know, inside a verse's recording: check by ear)")
    warsh = [r for r in results if r["meta"].get("warsh")]
    if warsh:
        print(f"warsh (not supported, apart): {sum(r['ok'] for r in warsh)}/{len(warsh)}")
    if not quiet:
        by = defaultdict(lambda: [0, 0])
        for r in scored:
            for c in categories(r["meta"]):
                by[c][0] += r["ok"]
                by[c][1] += 1
        print("\nby category (failures first):")
        for c, (k, n) in sorted(by.items(), key=lambda x: (x[1][0] / x[1][1], x[0])):
            if not c.startswith("reciter:") or k < n:
                print(f"  {c:40s} {k:4d}/{n:<4d} {100 * k / n:5.1f}%")
    out = HOME / "results" / f"{args.split}-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps([{k: v for k, v in r.items()} for r in results], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
