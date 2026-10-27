"""The Warsh 'an Nafi' reading, laid out on the Hafs verses the rest of the app uses.

data/quran-warsh.txt is Qur'anpedia.net's Warsh mushaf (the King Fahd Complex's printed
one), verbatim. Warsh counts the verses its own way (6214, al-Madani al-akhir): a Warsh
verse can cover two Hafs verses (2:1 "Alif Lam Mim" with 2:2) and a Hafs verse can hold
two Warsh verses (1:7). Translations, the detection and the projects all know a verse
by its Hafs number, so the Warsh text is cut back into Hafs verses, and each verse says
where its Warsh verses end and their numbers: what the reader sees.

The text uses the King Fahd Complex's own signs (tanween forms, undotted final ya, a dot
for the hamzat al-wasl, imala): they are turned into the usual codepoints for display
(display_word), and into the plain spelling the recognition model reads (spoken), where
a word spelled differently but said the same as in Hafs gets the Hafs spelling, the one
the model knows."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from functools import lru_cache

from . import quran

PAUSE = "ۖۗۚۛۜۘۙ"  # pause marks, written on the word in this text
VOWELS = "َُِ"  # fatha damma kasra
# the King Fahd Complex's signs, in the codepoints the Arabic fonts draw
DISPLAY = str.maketrans({"ے": "ى", "ٗ": "ً", "ٞ": "ٌ", "ٖ": "ٍ",
                         "‏": None, "۩": None, "۞": None})


@dataclass
class Text:
    """One Hafs verse, in Warsh."""
    display: list[quran.DisplayWord]
    align: list[str]
    align_to_display: list[int]
    numbers: list[int]  # Warsh verse number of each align word (0: the basmala, not a verse)
    ends: dict[int, int]  # align boundary -> number of the Warsh verse ending there


def display_word(word: str) -> tuple[str, str]:
    """(word as the fonts draw it, the pause mark written on it)."""
    w = word.translate(DISPLAY)
    pause = "".join(c for c in w if c in PAUSE)
    return "".join(c for c in w if c not in PAUSE), pause[:1]


def naql(word: str) -> bool:
    """A word starting with a hamza whose vowel Warsh moves onto the word before ("qada flaha"):
    written as an alif with a vowel and no hamza."""
    return bool(re.match(f"^ا[{VOWELS}](?![ٰ۪۬۟])", word))


def spoken(word: str, starts_verse: bool = False) -> str:
    """A Warsh word in the plain spelling the model reads (that of quran-align.txt)."""
    w = word.replace("ے", "ي").translate(DISPLAY)
    w = "".join(c for c in w if c not in PAUSE)
    if starts_verse and naql(w):  # after a stop, the hamza is said
        w = ("إ" if w[1] == "ِ" else "أ") + w[1:]
    # an alif starting a word with no hamza is not said: hamzat al-wasl (its dot), or naql
    w = re.sub(f"^ا[{VOWELS}]?[۪۬۟]?(?!ٰ)", "ا", w)
    w = re.sub("^اٰ", "آ", w)
    w = re.sub(f"يـ+([{VOWELS}]?)ٔ", "ئ\\1", w)  # hamza on a tatweel after a ya: its seat
    w = re.sub(f"ـ+([{VOWELS}]?)[ٕٔ]", "ء\\1", w)  # hamza on a tatweel
    w = re.sub(f"ـ*([{VOWELS}]?)ۧ", "ي\\1", w)  # small high ya: a ya said (النَّبِيٓـِٕۧنَ)
    w = w.replace("ـ", "")
    w = w.replace("أٓ", "آ")  # hamza then a long a
    w = w.replace("ٰ۪", "َا").replace("۪", "َ")  # imala, written where the fatha is
    w = re.sub("([وي])ٰ", "ا", w)  # a waw or ya carrying a long a: salaat, tawraat
    w = w.replace("ىٰ", "ى")
    w = re.sub(f"[{VOWELS}]?ٰ", "َا", w)  # dagger alif: a long a
    w = re.sub("وُۥ", "وُو", w)  # dawuud
    w = re.sub("[ٓۥۦۨۢ۬۟]", "", w)  # madd, silat, iqlab, tashil, silent signs
    w = re.sub("([اوى])ْ", "\\1", w)  # a silent alif (كَفَرُواْ)
    w = re.sub("^((?:[وفبل][َِ])?)ال(?=يْل)", "\\1الل", w)  # al-layl, written with one lam
    return w


_HAMZA = str.maketrans({"أ": "ء", "إ": "ء", "ؤ": "ء", "ئ": "ء", "ٔ": "ء", "ٕ": "ء",
                        "ٱ": "ا", "ى": "ي", "ة": "ه"})


def same_key(word: str) -> str:
    """What two spellings of a word said the same share: its letters, hamzas and long
    vowels (not its short vowels, shadda or sukun)."""
    w = word.replace("آ", "ءا").replace("ـٰ", "ا").replace("ىٰ", "ى").replace("ٰ", "ا").translate(_HAMZA)
    return re.sub("ء+", "ء", re.sub("[ً-ٓۥۦـ]", "", w))


@lru_cache(maxsize=1)
def source() -> tuple[str, dict[int, list[tuple[int, list[int], str]]]]:
    """(basmala, surah -> [(Warsh verse, Hafs verses it covers, text)])."""
    basmala, out = "", {}
    with open(quran.DATA / "quran-warsh.txt", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("# basmala|"):
                basmala = line.split("|", 1)[1]
            elif line and line[0].isdigit():
                s, a, hafs, text = line.split("|", 3)
                out.setdefault(int(s), []).append((int(a), [int(x) for x in hafs.split(",")], text))
    return basmala, out


def verse_count(s: int) -> int:
    return len(source()[1][s])


@lru_cache(maxsize=None)
def surah(s: int) -> dict[int, Text]:
    """The Warsh text of every Hafs verse of surah s."""
    basmala, src = source()
    align = quran._sources()[1]
    n_hafs = quran.surah(s)["verses"]
    # every Warsh word, with its verse and the Hafs verses that verse covers
    words = [(w, a, hafs) for a, hafs, text in src[s] for w in text.split() if w.translate(DISPLAY).strip(PAUSE)]
    hafs_words = [(w, h) for h in range(1, n_hafs + 1) if (s, h) != (1, 1) for w in align[(s, h)].split()]
    said = [spoken(w, k == 0 or words[k - 1][1] != a) for k, (w, a, _) in enumerate(words)]
    a_keys, h_keys = [same_key(w) for w in said], [same_key(w) for w, _ in hafs_words]
    ops = difflib.SequenceMatcher(None, a_keys, h_keys, autojunk=False).get_opcodes()

    # the Hafs verse of each Warsh word: its verse's, or when that verse covers several,
    # the one of the Hafs word it lines up with
    pos = [0] * len(words)  # Warsh word -> index of its Hafs word
    for tag, i1, i2, j1, j2 in ops:
        for k in range(i1, i2):
            pos[k] = min(j1 + (k - i1) * max(j2 - j1, 1) // max(i2 - i1, 1), len(hafs_words) - 1)
    owner = []
    for k, (_, _, hafs) in enumerate(words):
        h = hafs_words[pos[k]][1]
        owner.append(hafs[0] if len(hafs) == 1 else min(max(h, hafs[0]), hafs[-1]))
    for k in range(1, len(owner)):  # in order
        owner[k] = max(owner[k], owner[k - 1])

    # where a Warsh word is the same as its Hafs word(s), the Hafs spelling
    use = {}  # Warsh word -> Hafs words
    for tag, i1, i2, j1, j2 in ops:
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for k in range(i2 - i1):
                hw, h = hafs_words[j1 + k]
                # the same word, or spelled letters (Alif Lam Mim), written bare in Hafs
                same = tag == "equal" or (not re.search("[ً-ْ]", hw)
                                          and quran.skeleton(words[i1 + k][0]) == quran.skeleton(hw))
                # (not the word a hamza's vowel moves onto, nor a mim Warsh lengthens: said otherwise)
                nxt = words[i1 + k + 1] if i1 + k + 1 < len(words) else None
                moved = nxt is not None and nxt[1] == words[i1 + k][1] and naql(nxt[0])
                if same and h == owner[i1 + k] and not moved and "مُۥ" not in words[i1 + k][0]:
                    use[i1 + k] = [hw]
        elif tag == "replace" and i2 - i1 == 1 and j2 - j1 > 1 and a_keys[i1] == "".join(h_keys[j1:j2]) \
                and {h for _, h in hafs_words[j1:j2]} == {owner[i1]}:  # يَٰٓأَيُّهَا = يَا أَيُّهَا
            use[i1] = [w for w, _ in hafs_words[j1:j2]]

    out: dict[int, Text] = {}
    for h in range(1, n_hafs + 1):
        ks = [k for k in range(len(words)) if owner[k] == h]
        if (s, h) == (1, 1):  # Al-Fatiha's basmala: said, not counted as a verse in Warsh
            display = [quran.DisplayWord(display_word(w)[0]) for w in basmala.split()]
            out[h] = Text(display, quran.BASMALA.split(), list(range(5)), [0] * 4, {})
            continue
        assert ks, f"no Warsh word for {s}:{h}"
        t = Text([], [], [], [], {})
        for k in ks:
            w, a, _ = words[k]
            text, pause = display_word(w)
            t.display.append(quran.DisplayWord(text, pause))
            for x in use.get(k, [said[k]]):
                t.align.append(x)
                t.numbers.append(a)
            if k + 1 == len(words) or words[k + 1][1] != a:  # the last word of its Warsh verse
                t.ends[len(t.align)] = a
        # align boundary -> display boundary (several align words can share a display word)
        bounds, acc = [0], 0
        for k in ks:
            acc += len(use.get(k, [said[k]]))
            bounds.append(acc)
        t.align_to_display = [next(j for j, b in enumerate(bounds) if b >= i) for i in range(len(t.align) + 1)]
        out[h] = t
    return out


# ---------------------------------------------------------------- which reading is recited

FPS = 50  # model frames per second
MARGIN = 0.005  # how much closer to the Warsh text what is heard must be (Hafs is the most recited)


def reading_heard(em, model, blocks: list) -> str:
    """Hafs or Warsh: the reading whose text what the model heard is closer to."""
    return "warsh" if warsh_score(em, model, blocks) > MARGIN else "hafs"


def warsh_score(em, model, blocks: list) -> float:
    """How much closer to the Warsh text than to the Hafs one what the model heard is, over the
    verses recited whole (blocks found with the Hafs text). Most of their words are said the
    same in both: the verses with others decide. (The model learned from Hafs recitations and
    leans to their spelling: a Hafs recitation is never closer to Warsh, a Warsh one only a little.)"""
    from . import identify

    gain = weight = 0.0
    i = 0
    while i < len(blocks):
        b, j = blocks[i], i
        if b.kind == "verse":
            while (j + 1 < len(blocks) and blocks[j + 1].kind == "verse" and blocks[j + 1].a0 == blocks[j].a1
                   and (blocks[j + 1].surah, blocks[j + 1].ayah) == (b.surah, b.ayah)):
                j += 1
            hafs, warsh = quran._verse(b.surah, b.ayah, "hafs"), quran._verse(b.surah, b.ayah, "warsh")
            h, w = same_key("".join(hafs.align)), same_key("".join(warsh.align))
            if b.a0 == 0 and blocks[j].a1 == len(hafs.align) and h != w:
                part = em[int(b.voice_start * FPS): int(blocks[j].voice_end * FPS) + 1]
                heard = same_key(identify.transcript(part, model).replace(" ", ""))
                ratio = lambda t: difflib.SequenceMatcher(None, heard, t, autojunk=False).ratio()
                gain += (ratio(w) - ratio(h)) * len(h)
                weight += len(h)
        i = j + 1
    return gain / weight if weight else 0.0
