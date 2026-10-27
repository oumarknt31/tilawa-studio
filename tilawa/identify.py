"""Find which surahs and verses are recited, without being told (like Tarteel).

The recitation model writes down what it hears (greedy CTC decoding: the most
likely letter of every frame). track() follows those letters through the whole
Quran: windows of heard letters are located by letter n-grams voting for a
place, compared letter by letter with it, and chained by a Viterbi search, so a
recording holding several passages (a prayer: Al-Fatiha, then another surah;
the last three surahs in a row; a surah recited again) is found passage by
passage. The precise forced alignment (align.py) runs afterwards on them.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache

import numba
import numpy as np

from . import quran

N = 5  # letters per n-gram
COMMON = 300  # n-grams found more often than this in the Quran say nothing about the place
SHORT, SHORT_TOP = 4, 3  # and the best places of shorter ones (more survive letters misheard)


def _letters(text: str) -> str:
    return quran.skeleton(text).replace(" ", "").replace("|", "")


@lru_cache(maxsize=2)
def _index(basmala: bool = False):
    """Skeleton of the whole Quran in one string, the verse owning each letter,
    and the positions of every n-gram. basmala: the basmala said before each surah
    (but At-Tawbah; Al-Fatiha's is its verse 1) is in the text too, as verse 0."""
    align = quran._sources()[1]
    parts, owner = [], []
    bas = _letters(quran.BASMALA)
    for (s, a), text in sorted(align.items()):
        if basmala and a == 1 and s not in (1, 9):
            parts.append(bas)
            owner.extend([(s, 0)] * len(bas))
        sk = _letters(text)
        parts.append(sk)
        owner.extend([(s, a)] * len(sk))
    full = "".join(parts)
    grams = defaultdict(list)
    for i in range(len(full) - N + 1):
        grams[full[i:i + N]].append(i)
    return full, owner, {g: np.array(p) for g, p in grams.items()}


def transcript(em: np.ndarray, model) -> str:
    """What the model hears: most likely letter per frame, repeats and blanks removed."""
    inv = {v: k for k, v in model.vocab.items()}
    out, prev = [], -1
    for i in em.argmax(axis=1):
        if i != prev and i != model.blank:
            out.append(inv[int(i)])
        prev = i
    return "".join(out).replace("|", " ")


# ---------------------------------------------------------------- following a whole recording

W = 32  # letters per window
STEP = 8  # letters between windows
MIN_FIT = 0.62  # a window matching the Quran less than this is not a recitation
FIT_GAIN = 10.0  # weight of the match of each window
COST_ENTER = 4.0  # recitation starts after something else (or stops)
COST_BACK = 3.0  # the reciter goes back (repeats)
COST_SKIP = 3.0  # letters missed by the model
COST_JUMP = 9.0  # another place of the Quran
BACK_LIMIT = 900  # letters: how far back a repeat may go
SKIP_LIMIT = 160
GAP_LETTERS = 12  # letters before or after the passages listened to again (a short verse)
GAP_LETTERS_IN = 6  # (further in: "fi 'amadin mumaddadah" has 10, the model heard 7 past the window)
GAP_SHARE = 0.5  # share of its verses' letters a passage found there must have heard


@dataclass
class Passage:
    surah: int
    first: int  # verses heard
    last: int
    t0: float  # first and last letter heard (s)
    t1: float
    letters: int  # heard letters matched with it
    fit: float  # how well they match (0..1)
    marks: list = field(default_factory=list)  # (time s, verse) of letters heard: where each verse is

    def to_dict(self) -> dict:
        return {"surah": self.surah, "first": self.first, "last": self.last, "t0": round(self.t0, 2),
                "t1": round(self.t1, 2), "coverage": round(self.fit, 3)}


@lru_cache(maxsize=1)
def _codes():
    """The Quran's letters as small integers (and the letter -> integer table)."""
    full, owner, _ = _index(True)
    table = {c: i + 1 for i, c in enumerate(sorted(set(full)))}
    return np.array([table[c] for c in full], dtype=np.int16), table


def heard(em: np.ndarray, model) -> tuple[np.ndarray, np.ndarray]:
    """The letters the model hears (as _codes integers) and the frame of each."""
    _, table = _codes()
    inv = {v: k for k, v in model.vocab.items()}
    codes, frames, prev = [], [], -1
    for t, i in enumerate(em.argmax(axis=1)):
        if i != prev and i != model.blank:
            for c in quran.skeleton(inv[int(i)]):
                if c in table:
                    codes.append(table[c])
                    frames.append(t)
        prev = i
    return np.array(codes, dtype=np.int16), np.array(frames, dtype=np.int64)


@numba.njit(cache=True)
def _fit(q, text):
    """Local alignment of q with text (Smith-Waterman: only the stretch of q that reads like
    some stretch of text counts; letters before or after it, such as speech that is not the
    Quran, are left out). Returns the letters of q matched, the first and last of them (index
    in q) and where they are in text."""
    n, m = len(q), len(text)
    H = np.zeros((n + 1, m + 1), dtype=np.int32)
    best, bi, bj = 0, 0, 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            v = H[i - 1, j - 1] + (2 if q[i - 1] == text[j - 1] else -1)
            v = max(v, H[i - 1, j] - 1, H[i, j - 1] - 1, 0)
            H[i, j] = v
            if v > best:
                best, bi, bj = v, i, j
    # trace back
    i, j, matched = bi, bj, 0
    first_q, last_q, first_t, last_t = -1, -1, -1, -1
    while i > 0 and j > 0 and H[i, j] > 0:
        if H[i, j] == H[i - 1, j - 1] + (2 if q[i - 1] == text[j - 1] else -1):
            if q[i - 1] == text[j - 1]:
                matched += 1
                if last_q < 0:
                    last_q, last_t = i - 1, j - 1
                first_q, first_t = i - 1, j - 1
            i -= 1
            j -= 1
        elif H[i, j] == H[i - 1, j] - 1:
            i -= 1
        else:
            j -= 1
    return matched, first_q, last_q, first_t, last_t


def _place(q: np.ndarray, guess: int, slack: int = 12):
    """Where window q reads best around Quran position guess: (fit 0..1, start, details)."""
    codes, _ = _codes()
    lo, hi = max(0, guess - slack), min(len(codes), guess + len(q) + slack)
    if hi - lo < len(q) // 2:
        return 0.0, guess, None
    matched, fq, lq, ft, lt = _fit(q, codes[lo:hi])
    if fq < 0:
        return 0.0, guess, None
    start = lo + ft - fq  # where q's first letter would be
    return matched / len(q), start, (fq, lq, lo + ft, lo + lt)


@lru_cache(maxsize=1)
def _short_grams() -> dict:
    """The positions of every SHORT-gram (see _vote)."""
    full = _index(True)[0]
    grams = defaultdict(list)
    for i in range(len(full) - SHORT + 1):
        grams[full[i:i + SHORT]].append(i)
    return {g: np.array(p) for g, p in grams.items()}


def _vote(q: np.ndarray, top: int, n: int = N) -> list[int]:
    """Quran positions where window q may start, by its rarest letter groups (of n letters)."""
    full, owner, grams = _index(True)
    if n != N:
        grams = _short_grams()
    _, table = _codes()
    inv = {v: k for k, v in table.items()}
    s = "".join(inv[int(c)] for c in q)
    votes: dict[int, float] = defaultdict(float)
    for i in range(len(s) - n + 1):
        pos = grams.get(s[i:i + n])
        if pos is None or len(pos) > COMMON:
            continue
        w = 1.0 / len(pos)
        for b in set(((pos - i) // 8).tolist()):
            votes[b] += w
    out = []
    for b, _ in sorted(votes.items(), key=lambda kv: -kv[1]):
        if all(abs(b - o) > 2 for o in out):
            out.append(b)
        if len(out) == top:
            break
    return [b * 8 for b in out]


def _cost(p: int, q: int, step: int = STEP) -> float:
    """Moving from Quran position p (one window) to q (the next)."""
    d = q - p
    if step * 0.25 - 4 <= d <= step * 2 + 4:
        return 0.0
    if -BACK_LIMIT <= d < 0:
        return COST_BACK
    if 0 < d <= SKIP_LIMIT:
        return COST_SKIP
    return COST_JUMP


def track(em: np.ndarray, model, beam: int = 8, top: int = 6) -> list[Passage]:
    """The passages recited, in the order heard."""
    codes, frames = heard(em, model)
    if len(codes) < W // 2:
        return []
    out = _track(codes, frames, W, STEP, beam, top)
    if not out and len(codes) < 3 * W:  # a short verse said twice is shorter than a window
        return _track(codes, frames, W // 2, STEP // 2, beam, top)
    # letters before the first passage or after the last (a short verse before or after another
    # surah: every window there reads half of each; the passage's edge window may already reach
    # into it), listened to again with smaller windows
    t = frames * 0.02
    more = []
    if out:
        lo = int(np.searchsorted(t, out[0].t0)) + STEP
        hi = int(np.searchsorted(t, max(p.t1 for p in out), side="right")) - STEP
        # (after the last one, from where its last window went on or a little further in: half of
        # each verse in one small window may be too little of the short one; not so before the
        # first, where it is more often talk)
        for edges in ([(0, lo)], [(hi + d, len(codes)) for d in (0, STEP // 2, STEP)]):
            for a, b in edges:
                a = max(a, _after_istiadha(codes, a, b))  # (it reads like the end of 16:98)
                enough = GAP_LETTERS if (a, b) == edges[0] else GAP_LETTERS_IN
                found = _track(codes[a:b], frames[a:b], W // 2, STEP // 2, beam, top) if b - a >= enough else []
                if found:
                    more += found
                    break
        # most of what they claim heard (a talk before a recitation quotes pieces of long verses)
        vs = _verses()
        more = [p for p in more if p.letters >= GAP_SHARE * sum(vs[(p.surah, a)][1] for a in range(p.first, p.last + 1))]
    return _clean(sorted(out + more, key=lambda p: p.t0), keep={id(p) for p in more}) if more else out


def _after_istiadha(codes, a: int, b: int) -> int:
    """Where the letters [a, b) go on after an isti'adha said among them (a if there is none)."""
    _, table = _codes()
    ist = np.array([table[c] for c in _letters(quran.ISTIADHA)], dtype=np.int16)
    matched, _fq, _lq, _ft, lt = _fit(ist, codes[a:b]) if b - a >= len(ist) // 2 else (0, 0, 0, 0, 0)
    return a + lt + 1 if matched >= 0.8 * len(ist) else a


def _track(codes, frames, w: int, step: int, beam: int, top: int) -> list[Passage]:
    starts = list(range(0, max(1, len(codes) - w + 1), step))
    if starts[-1] + w < len(codes):
        starts.append(len(codes) - w)
    # Viterbi over windows: each state is a Quran position (or -1: not the Quran)
    layers = []  # per window: list of (position, score, back index, fit, details)
    prev = [(-1, 0.0, -1, 0.0, None)]
    for k, s0 in enumerate(starts):
        q = codes[s0:s0 + w]
        guesses = _vote(q, top)
        guesses += [g for g in _vote(q, SHORT_TOP, SHORT) if all(abs(g - h) > 16 for h in guesses)]
        ranked = sorted(range(len(prev)), key=lambda i: -prev[i][1])[:beam]
        guesses += [prev[i][0] + step for i in ranked if prev[i][0] >= 0]
        cands = []
        for g in guesses:
            f, start, det = _place(q, g)
            if det is not None and all(abs(start - c[0]) > 2 for c in cands):
                cands.append((start, f, det))
        layer = []
        # not the Quran
        best, arg = -1e18, 0
        for i, (p, sc, *_r) in enumerate(prev):
            v = sc - (0 if p < 0 else COST_ENTER / 2)
            if v > best:
                best, arg = v, i
        layer.append((-1, best, arg, 0.0, None))
        for start, f, det in cands:
            gain = FIT_GAIN * (f - MIN_FIT)
            best, arg = -1e18, 0
            for i, (p, sc, *_r) in enumerate(prev):
                # at the very start, half (as for stopping): a short clip is one window, it must be able to win
                v = sc - ((COST_ENTER / 2 if k == 0 else COST_ENTER) if p < 0 else _cost(p, start, step))
                if v > best:
                    best, arg = v, i
            layer.append((start, best + gain, arg, f, det))
        layers.append(layer)
        prev = layer
    # best path
    i = max(range(len(prev)), key=lambda j: prev[j][1])
    path = []
    for k in range(len(layers) - 1, -1, -1):
        path.append((k, layers[k][i]))
        i = layers[k][i][2]
    path.reverse()
    return _passages(path, starts, codes, frames, w, step)


def _passages(path, starts, codes, frames, w: int = W, step: int = STEP) -> list[Passage]:
    """Runs of windows reading on in the Quran -> passages (one per surah)."""
    full, owner, _ = _index(True)
    runs, cur = [], []
    for k, (pos, _sc, _b, f, det) in path:
        if pos < 0:
            if cur:
                runs.append(cur)
            cur = []
            continue
        if cur and _cost(cur[-1][1], pos, step) >= COST_JUMP:
            runs.append(cur)
            cur = []
        cur.append((k, pos, f, det))
    if cur:
        runs.append(cur)
    out: list[Passage] = []
    out_runs = []
    for run in runs:
        fit = float(np.mean([f for _, _, f, _ in run]))
        # the letters matched in each window, in the order heard (heard index, Quran position);
        # a window that crosses into the next surah is split where it does (in Quran order: 113
        # then 114, the basmala between them belonging to 114)
        pieces = []
        for k, pos, f, (fq, lq, ft, lt) in run:
            h0, h1 = starts[k] + fq, starts[k] + lq
            q = ft
            while q <= lt:
                s = owner[q][0]
                q_end = q
                while q_end + 1 <= lt and owner[q_end + 1][0] == s:
                    q_end += 1
                a = h0 + (h1 - h0) * (q - ft) / max(1, lt - ft)
                b = h0 + (h1 - h0) * (q_end - ft) / max(1, lt - ft)
                pieces.append((int(round(a)), int(round(b)), q, q_end))
                q = q_end + 1
        # a passage: the same surah, read on (or going back a verse at most: the aligner follows
        # that); another surah, or the same surah again from further back, is a new passage
        cur = None
        for a, b, q, q_end in pieces:
            s = owner[q][0]
            if cur and cur["s"] == s and q >= _verse_start(s, owner[cur["q"]][1] - 1) - w:
                cur["h1"], cur["q"] = max(cur["h1"], b), max(cur["q"], q_end)
                cur["ps"].append((a, b, q, q_end))
            else:
                cur = {"s": s, "q": q_end, "h0": a, "h1": b, "ps": [(a, b, q, q_end)]}
                out_runs.append((cur, fit))
    for cur, fit in out_runs:
        heard_at: dict[int, set] = defaultdict(set)  # verse -> its letters matched
        for _a, _b, q0, q1 in cur["ps"]:
            for q in range(q0, q1 + 1):
                heard_at[owner[q][1]].add(q)
        verses = sorted(heard_at)
        # a verse at either end counts if enough of it was heard (not the last letters of the
        # previous verse, which read like the start of this passage: the aligner looks one
        # verse back anyway)
        enough = lambda v: len(heard_at[v]) >= min(24, 0.3 * _verses()[(cur["s"], v)][1])
        while len(verses) > 1 and not enough(verses[0]):
            verses.pop(0)
        while len(verses) > 1 and not enough(verses[-1]):
            verses.pop()
        said = sum(len(heard_at[v]) for v in verses if v > 0)  # letters of verses
        if verses[-1] == 0:  # only the basmala: said before the next surah, not a passage
            continue
        marks = sorted((float(frames[a]) * 0.02, owner[q][1]) for a, _b, q, _e in cur["ps"])
        out.append(Passage(cur["s"], max(1, verses[0]), verses[-1], float(frames[cur["h0"]]) * 0.02,
                           float(frames[cur["h1"]] + 1) * 0.02, said, fit, marks))
    out.sort(key=lambda p: p.t0)
    return _clean(out)


@lru_cache(maxsize=None)
def _verses() -> dict:
    """(surah, verse) -> (where it starts in the tracker's text, its number of letters); verse 0: the basmala."""
    full, owner, _ = _index(True)
    out = {}
    for i, key in enumerate(owner):
        start, n = out.get(key, (i, 0))
        out[key] = (start, n + 1)
    return out


def _verse_start(s: int, a: int) -> int:
    """Where verse s:a starts in the tracker's text (before the first verse: the surah's start)."""
    vs = _verses()
    return vs.get((s, a), vs.get((s, 0), vs.get((s, 1))))[0]


def _clean(ps: list[Passage], keep=frozenset()) -> list[Passage]:
    """Drop what is not a passage of its own: a basmala before a surah reads like 1:1
    (or 27:30), and a few letters matching by chance (but in keep: a short verse found at an
    edge, which matched most of its letters)."""
    out = []
    for i, p in enumerate(ps):
        basmala = (p.surah, p.first, p.last) in ((1, 1, 1), (27, 30, 30))
        if basmala and (i + 1 < len(ps) or len(ps) > 1):
            continue
        if p.letters < 14 and len(ps) > 1 and id(p) not in keep:
            continue
        out.append(p)
    # the same passage going on after a long pause: one passage
    merged = []
    for p in out:
        q = merged[-1] if merged else None
        if q and q.surah == p.surah and q.last - 1 <= p.first <= q.last + 2:  # reading on after a pause
            q.first, q.last = min(q.first, p.first), max(q.last, p.last)
            q.t1, q.letters, q.marks = max(q.t1, p.t1), q.letters + p.letters, sorted(q.marks + p.marks)
        else:
            merged.append(p)
    return merged
