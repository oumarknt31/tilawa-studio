"""Find which surah and verses are recited, without being told (like Tarteel).

The recitation model writes down what it hears (greedy CTC decoding: the most
likely letter of every frame). That rough transcript is located in the whole
Quran by letter n-grams voting for an offset, then the best candidates are
compared letter by letter. The precise forced alignment (align.py) runs
afterwards on the verses found.
"""

from __future__ import annotations

import difflib
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from . import quran

N = 5  # letters per n-gram
COMMON = 300  # n-grams found more often than this in the Quran say nothing about the place
BIN = 40  # letters: tolerance of the offset vote (transcription slips, missed letters)
MIN_COVERAGE = 0.45  # share of the transcript that must match the Quran


@dataclass
class Match:
    surah: int
    first: int  # first verse heard
    last: int  # last verse heard
    coverage: float  # 0..1, share of the transcript found in the Quran text

    def to_dict(self) -> dict:
        return {"surah": self.surah, "first": self.first, "last": self.last, "coverage": round(self.coverage, 3)}


def _letters(text: str) -> str:
    return quran.skeleton(text).replace(" ", "").replace("|", "")


@lru_cache(maxsize=1)
def _index():
    """Skeleton of the whole Quran in one string, the verse owning each letter,
    and the positions of every n-gram."""
    align = quran._sources()[1]
    parts, owner = [], []
    for (s, a), text in sorted(align.items()):
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


def identify(em: np.ndarray, model, top: int = 3) -> list[Match]:
    """Best guesses for the recited passage, most likely first (empty if none)."""
    heard = _letters(transcript(em, model))
    if len(heard) < 2 * N:
        return []
    full, owner, grams = _index()
    votes: dict[int, float] = defaultdict(float)
    for i in range(len(heard) - N + 1):
        pos = grams.get(heard[i:i + N])
        if pos is None or len(pos) > COMMON:
            continue
        w = 1.0 / len(pos)
        for b in set(((pos - i) // BIN).tolist()):
            votes[b] += w
    tried, out = set(), []
    for b, _ in sorted(votes.items(), key=lambda kv: -kv[1])[:12]:
        if b in tried or b - 1 in tried or b + 1 in tried:
            continue
        tried.add(b)
        lo = max(0, b * BIN - 2 * BIN)
        hi = min(len(full), b * BIN + len(heard) + 3 * BIN)
        sm = difflib.SequenceMatcher(None, heard, full[lo:hi], autojunk=False)
        blocks = [m for m in sm.get_matching_blocks() if m.size >= 3]
        if not blocks:
            continue
        matched = sum(m.size for m in blocks)
        first = owner[lo + blocks[0].b]
        last = owner[lo + blocks[-1].b + blocks[-1].size - 1]
        if last[0] != first[0]:  # crosses into the next surah: keep the surah heard most
            per = defaultdict(int)
            for m in blocks:
                per[owner[lo + m.b][0]] += m.size
            s = max(per, key=per.get)
            inside = [m for m in blocks if owner[lo + m.b][0] == s]
            first = owner[lo + inside[0].b]
            last = owner[lo + inside[-1].b + inside[-1].size - 1]
        out.append(Match(first[0], first[1], last[1], matched / len(heard)))
    out = [m for m in out if m.coverage >= MIN_COVERAGE]
    out.sort(key=lambda m: -m.coverage)
    # the same passage found twice (repeated verses in the Quran) stays listed once
    seen, uniq = set(), []
    for m in out:
        if (m.surah, m.first) not in seen:
            seen.add((m.surah, m.first))
            uniq.append(m)
    return uniq[:top]
