"""Quran text access.

Sources (bundled verbatim in tilawa/data, see README for licences):
  quran-uthmani.txt       Tanzil Uthmani text            -> what is displayed
  quran-align.txt         text the alignment model knows -> what is aligned
  en.transliteration.txt  Tanzil transliteration         -> phonetic line
  fr.hamidullah.txt       Hamidullah French translation  -> French line

The aligned text and the displayed text split some words differently
(e.g. "يَا أَيُّهَا" vs "يَـٰٓأَيُّهَا"), so every verse carries a map from
alignment-word boundaries to display-word boundaries.
"""

from __future__ import annotations

import difflib
import html
import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).parent / "data"

# Pause marks (waqf) that appear as standalone tokens in the Uthmani text.
WAQF_MARKS = set("ۖۗۚۛۜۘۙ")
DECORATIONS = set("۞۩")
# Strength of each mark as a place to cut a long verse (higher = better).
WAQF_STRENGTH = {"ۘ": 3, "ۗ": 3, "ۚ": 3, "ۖ": 2, "ۛ": 1, "ۙ": 0, "ۜ": 1}

ISTIADHA = "أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ"
BASMALA = "بِسْمِ اللَّهِ الرَّحْمَـٰنِ الرَّحِيمِ"
BASMALA_UTHMANI = "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ"

_HARAKAT = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_ALEF = str.maketrans({"ٱ": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي", "ء": ""})


def skeleton(word: str) -> str:
    """Bare consonant skeleton used to compare the two Arabic spellings."""
    return _HARAKAT.sub("", word).translate(_ALEF)


def _load(name: str) -> dict[tuple[int, int], str]:
    out = {}
    with open(DATA / name, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("|")
            if len(parts) == 3 and parts[0].isdigit():
                out[(int(parts[0]), int(parts[1]))] = parts[2]
    return out


@lru_cache(maxsize=None)
def _sources():
    return (
        _load("quran-uthmani.txt"),
        _load("quran-align.txt"),
        _load("en.transliteration.txt"),
        _load("fr.hamidullah.txt"),
    )


@lru_cache(maxsize=None)
def surahs() -> list[dict]:
    return json.loads((DATA / "surahs.json").read_text(encoding="utf-8"))


def surah(n: int) -> dict:
    if not 1 <= n <= 114:
        raise ValueError(f"Surah must be between 1 and 114, got {n}")
    return surahs()[n - 1]


@dataclass
class DisplayWord:
    text: str
    waqf: str = ""  # pause mark that follows this word, if any


@dataclass
class Verse:
    surah: int
    ayah: int
    display: list[DisplayWord]  # Uthmani words with their pause marks
    align: list[str]  # words the model aligns against
    translit: list[str]  # one entry per align word when counts match
    french: str
    # boundary i of the align words (0..len(align)) -> boundary in display words
    align_to_display: list[int] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.surah}:{self.ayah}"

    def display_text(self, start: int = 0, end: int | None = None) -> str:
        """Uthmani text for display words [start, end), pause marks included."""
        words = self.display[start:end]
        out = []
        for i, w in enumerate(words):
            out.append(w.text)
            # a pause mark at the very end of a part is dropped (it marks the cut itself)
            if w.waqf and i < len(words) - 1:
                out.append(w.waqf)
        return " ".join(out)

    def translit_text(self, a0: int, a1: int) -> str:
        """Transliteration for align words [a0, a1)."""
        n = len(self.align)
        if len(self.translit) == n:
            words = self.translit[a0:a1]
        else:  # rare count mismatch: proportional slice
            m = len(self.translit)
            words = self.translit[round(a0 * m / n): round(a1 * m / n)]
        text = " ".join(words)
        return text[:1].upper() + text[1:] if a0 == 0 else text


def _clean_translit(text: str) -> list[str]:
    return html.unescape(re.sub(r"<[^>]+>", "", text)).split()


def _split_display(uthmani: str, strip_basmala: bool) -> list[DisplayWord]:
    words: list[DisplayWord] = []
    for tok in uthmani.split():
        if all(c in WAQF_MARKS for c in tok):
            if words:
                words[-1].waqf = tok
        elif all(c in DECORATIONS for c in tok):
            continue
        else:
            words.append(DisplayWord(tok))
    return words[4:] if strip_basmala else words


def _boundary_map(align: list[str], display: list[DisplayWord]) -> list[int]:
    """Map each align-word boundary to the closest display-word boundary.

    Both texts are reduced to their consonant skeletons and matched
    character by character, which absorbs spelling differences."""
    a_sk = [skeleton(w) for w in align]
    d_sk = [skeleton(w.text) for w in display]
    a_str, d_str = "".join(a_sk), "".join(d_sk)
    sm = difflib.SequenceMatcher(None, a_str, d_str, autojunk=False)
    # char position map a_str -> d_str
    pos = [0] * (len(a_str) + 1)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        for k in range(i1, i2 + 1):
            pos[k] = j1 + (round((k - i1) * (j2 - j1) / (i2 - i1)) if i2 > i1 else 0)
    d_bounds = [0]
    for s in d_sk:
        d_bounds.append(d_bounds[-1] + len(s))
    out, acc = [], 0
    for i in range(len(align) + 1):
        if i:
            acc += len(a_sk[i - 1])
        target = pos[acc]
        out.append(min(range(len(d_bounds)), key=lambda j: abs(d_bounds[j] - target)))
    out[0], out[-1] = 0, len(display)
    for i in range(1, len(out)):  # keep it monotonic
        out[i] = max(out[i], out[i - 1])
    return out


@lru_cache(maxsize=4096)
def verse(s: int, a: int) -> Verse:
    uth, ali, trl, fr = _sources()
    if (s, a) not in uth:
        raise ValueError(f"Verse {s}:{a} does not exist")
    display = _split_display(uth[(s, a)], strip_basmala=(a == 1 and s not in (1, 9)))
    align = ali[(s, a)].split()
    v = Verse(s, a, display, align, _clean_translit(trl[(s, a)]), fr[(s, a)])
    v.align_to_display = _boundary_map(align, display)
    return v


def verses(s: int, first: int, last: int | None = None) -> list[Verse]:
    total = surah(s)["verses"]
    last = total if last is None else min(last, total)
    if not 1 <= first <= last:
        raise ValueError(f"Invalid verse range {first}-{last} for surah {s} ({total} verses)")
    return [verse(s, a) for a in range(first, last + 1)]
