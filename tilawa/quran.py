"""Quran text access.

Sources (bundled verbatim in tilawa/data, see README for licences):
  quran-uthmani.txt       Tanzil Uthmani text            -> what is displayed
  quran-align.txt         text the alignment model knows -> what is aligned
  en.transliteration.txt  Tanzil transliteration         -> phonetic line, "tanzil" convention
                          (the other conventions are made from the Arabic: translit.py)
  trans/*.txt             Tanzil and QuranEnc translations -> translation line (see LANGS, EDITIONS)

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

from . import translit as _translit
from .i18n import UserError

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


# typos of the Tanzil transliteration (as written -> as it should be)
# (in the file's own markup)
TANZIL_TRANSLIT_FIXES = {(114, 6): ("s<b>m</b>", "s<b>i</b>"), (10, 94): ("anzalnn<u>a</u>", "anzaln<u>a</u>"),
                         (3, 180): ("t<u>a</u>hummu", "t<u>a</u>humu")}


def _load(name: str) -> dict[tuple[int, int], str]:
    out = {}
    with open(DATA / name, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("|", 2)
            if len(parts) == 3 and parts[0].isdigit():
                out[(int(parts[0]), int(parts[1]))] = parts[2].rstrip("|")  # one Tanzil line has a stray "|"
    return out


@lru_cache(maxsize=None)
def _sources():
    return (
        _load("quran-uthmani.txt"),
        _load("quran-align.txt"),
        _translit_fixed(),
        translation_table("fr"),
    )


def _translit_fixed() -> dict[tuple[int, int], str]:
    t = _load("en.transliteration.txt")
    for key, (bad, good) in TANZIL_TRANSLIT_FIXES.items():
        t[key] = t[key].replace(bad, good)
    return t


# code -> (name, Tanzil file of the default translation, its translator, right-to-left)
LANGS = {
    "fr": ("Français", "fr.hamidullah", "Muhammad Hamidullah", False),
    "en": ("English", "en.sahih", "Saheeh International", False),
    "es": ("Español", "es.cortes", "Julio Cortés", False),
    "de": ("Deutsch", "de.bubenheim", "Bubenheim & Elyas", False),
    "it": ("Italiano", "it.piccardo", "Hamza Roberto Piccardo", False),
    "pt": ("Português", "pt.elhayek", "Samir El-Hayek", False),
    "nl": ("Nederlands", "nl.siregar", "Sofian S. Siregar", False),
    "sv": ("Svenska", "sv.bernstrom", "Knut Bernström", False),
    "tr": ("Türkçe", "tr.diyanet", "Diyanet İşleri", False),
    "id": ("Bahasa Indonesia", "id.indonesian", "Kementerian Agama RI", False),
    "ms": ("Bahasa Melayu", "ms.basmeih", "Abdullah Muhammad Basmeih", False),
    "bs": ("Bosanski", "bs.korkut", "Besim Korkut", False),
    "sq": ("Shqip", "sq.ahmeti", "Sherif Ahmeti", False),
    "ru": ("Русский", "ru.kuliev", "Elmir Kuliev", False),
    "ur": ("اردو", "ur.jalandhry", "Fateh Muhammad Jalandhry", True),
    "none": ("Sans traduction (arabe seul)", None, "", False),
}

# Isti'adha (not a verse, so not in the translations)
ISTIADHA_TRANSLATION = {
    "fr": "Je cherche refuge auprès d'Allah contre Satan le lapidé.",
    "en": "I seek refuge in Allah from Satan, the accursed.",
    "es": "Me refugio en Alá de Satanás, el maldito.",
    "de": "Ich suche Zuflucht bei Allah vor dem verfluchten Satan.",
    "it": "Mi rifugio in Allah contro Satana il lapidato.",
    "pt": "Busco refúgio em Allah contra Satanás, o maldito.",
    "nl": "Ik zoek mijn toevlucht bij Allah tegen de vervloekte satan.",
    "sv": "Jag söker skydd hos Gud mot den förbannade Satan.",
    "tr": "Kovulmuş şeytandan Allah'a sığınırım.",
    "id": "Aku berlindung kepada Allah dari godaan setan yang terkutuk.",
    "ms": "Aku berlindung kepada Allah daripada syaitan yang direjam.",
    "bs": "Utječem se Allahu od prokletog šejtana.",
    "sq": "Kërkoj mbrojtje te Allahu nga shejtani i mallkuar.",
    "ru": "Прибегаю к защите Аллаха от проклятого сатаны.",
    "ur": "میں شیطان مردود سے اللہ کی پناہ مانگتا ہوں۔",
    "none": "",
}


# Languages with a choice of translations: the most read ones that may be
# republished, the most used first (the default). Masson (French) and Khattab's
# Clear Quran (English) are widely read too, but under copyright.
EDITIONS = {
    "fr": [("fr.hamidullah", "Muhammad Hamidullah"), ("fr.maach", "Rachid Maach"),
           ("fr.noor", "Centre international Noor (ex-Montada)")],
    "en": [("en.sahih", "Saheeh International"), ("en.yusufali", "Abdullah Yusuf Ali"),
           ("en.pickthall", "Marmaduke Pickthall")],
}


def editions(lang: str) -> list[tuple[str, str]]:
    """(file, translator) of the translations of a language, the default first."""
    if lang in EDITIONS:
        return EDITIONS[lang]
    file = LANGS.get(lang, (None, None))[1]
    return [(file, LANGS[lang][2])] if file else []


def edition(lang: str, chosen: str | None = None) -> str | None:
    """The translation file to use: the one chosen if it is of this language, else the default."""
    files = [f for f, _ in editions(lang)]
    return chosen if chosen in files else (files[0] if files else None)


@lru_cache(maxsize=None)
def translation_table(lang: str, chosen: str | None = None) -> dict[tuple[int, int], str]:
    file = edition(lang, chosen)
    return _load(f"trans/{file}.txt") if file else {}


def translation(lang: str, s: int, a: int, chosen: str | None = None) -> str:
    if lang not in LANGS:
        raise ValueError(f"Unknown language {lang}")
    return translation_table(lang, chosen).get((s, a), "")


def languages() -> list[dict]:
    return [{"code": k, "name": v[0], "translator": v[2], "rtl": v[3],
             "editions": [{"id": f, "translator": t} for f, t in editions(k)]} for k, v in LANGS.items()]


@lru_cache(maxsize=None)
def surahs() -> list[dict]:
    return json.loads((DATA / "surahs.json").read_text(encoding="utf-8"))


def surah(n: int) -> dict:
    if not 1 <= n <= 114:
        raise UserError("bad_surah")
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

    def phonetic(self, a0: int, a1: int, style: str = "simple") -> list[str]:
        """One transliterated word per align word of [a0, a1), recited in a row.
        "tanzil": the Tanzil transliteration; else made from the Arabic (translit.py)."""
        if style == "tanzil":
            return [self.translit_text(k, k + 1) if k else self.translit_text(0, 1) for k in range(a0, a1)]
        return _translit.transliterate(self.align[a0:a1], style, start_of_verse=a0 == 0)


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
        raise UserError("bad_verse", s=s, a=a)
    display = _split_display(uth[(s, a)], strip_basmala=(a == 1 and s not in (1, 9)))
    align = ali[(s, a)].split()
    v = Verse(s, a, display, align, _clean_translit(trl[(s, a)]), fr[(s, a)])
    v.align_to_display = _boundary_map(align, display)
    return v


def verses(s: int, first: int, last: int | None = None) -> list[Verse]:
    total = surah(s)["verses"]
    last = total if last is None else min(last, total)
    if not 1 <= first <= last:
        raise UserError("bad_range", first=first, last=last, total=total)
    return [verse(s, a) for a in range(first, last + 1)]
