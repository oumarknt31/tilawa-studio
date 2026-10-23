"""Transliteration of the Quran, made from the vowelled Arabic text.

Every word is read as a list of sounds (consonants, short and long vowels,
doubled letters) from its letters and diacritics, with what happens when
words are recited one after the other: the article melting into sun letters
(ar-raḥmān), the connecting hamza falling after a vowel (bismi llāh), and the
pause at the end of a subtitle (al-ʿālamīn, not al-ʿālamīna). The sounds are
then written in one convention, so a subtitle cut anywhere, or a word
corrected, always follows the same rules.

Input: the Tanzil "simple" text with full diacritics (quran-align.txt), which
spells words as they are pronounced, marks every sukun, and leaves the lam of
the article bare before the sun letters.
"""

from __future__ import annotations

from dataclasses import dataclass, field

FATHA, DAMMA, KASRA = "َ", "ُ", "ِ"
FATHATAN, DAMMATAN, KASRATAN = "ً", "ٌ", "ٍ"
SUKUN, SHADDA, DAGGER, MADDA = "ْ", "ّ", "ٰ", "ٓ"
TATWEEL = "ـ"
MARKS = {FATHA, DAMMA, KASRA, FATHATAN, DAMMATAN, KASRATAN, SUKUN, SHADDA, DAGGER, MADDA}
VOWEL_OF = {FATHA: "a", DAMMA: "u", KASRA: "i", FATHATAN: "a", DAMMATAN: "u", KASRATAN: "i"}
TANWIN = {FATHATAN, DAMMATAN, KASRATAN}
HAMZA = set("ءأإؤئ")

# letter -> sound key (written by the conventions below)
CONSONANT = {
    "ب": "b", "ت": "t", "ث": "th", "ج": "j", "ح": "H", "خ": "kh", "د": "d", "ذ": "dh", "ر": "r", "ز": "z",
    "س": "s", "ش": "sh", "ص": "S", "ض": "D", "ط": "T", "ظ": "Z", "ع": "3", "غ": "gh", "ف": "f", "ق": "q",
    "ك": "k", "ل": "l", "م": "m", "ن": "n", "ه": "h", "و": "w", "ي": "y", "ة": "t",
    "ء": "'", "أ": "'", "إ": "'", "ؤ": "'", "ئ": "'",
}
# the letters read by their names at the start of some surahs (Alif Lām Mīm)
LETTER_NAMES = {"ا": "alif", "ل": "lām", "م": "mīm", "ص": "ṣād", "ر": "rā", "ك": "kāf", "ه": "hā", "ي": "yā",
                "ع": "ʿayn", "ط": "ṭā", "س": "sīn", "ح": "ḥā", "ق": "qāf", "ن": "nūn"}

# How each sound is written.
STYLES = {
    # easy to read, the spelling of most recitation videos (Wal yawmil maw'ood)
    "simple": {"H": "h", "S": "s", "D": "d", "T": "t", "Z": "z", "3": "'", "'": "'",
               "aa": "aa", "ii": "ee", "uu": "oo", "join": True},
    # the same for French readers (Wal yawmil maw'oud)
    "fr": {"H": "h", "S": "s", "D": "d", "T": "t", "Z": "z", "3": "'", "'": "'", "sh": "ch", "j": "dj", "u": "ou",
           "aa": "â", "ii": "î", "uu": "oû", "join": True},
    # scholarly, every letter told apart (wa-l-yawmi l-mawʿūd)
    "academic": {"H": "ḥ", "S": "ṣ", "D": "ḍ", "T": "ṭ", "Z": "ẓ", "3": "ʿ", "'": "ʾ",
                 "aa": "ā", "ii": "ī", "uu": "ū", "join": False},
}


@dataclass
class Sound:
    kind: str  # "c" consonant, "v" vowel
    value: str  # consonant key, or the vowel a / i / u
    long: bool = False
    double: bool = False
    nunation: bool = False  # tanwin: -an, -in, -un
    marbuta: bool = False  # ة: t when the word goes on, h at a pause


@dataclass
class Word:
    prefix: list[Sound] = field(default_factory=list)  # wa-, fa-, bi-, li-, ka-, ta- before the article / hamza
    wasl: bool = False  # connecting hamza: its vowel is only said at the start of a phrase
    article: str = ""  # "" | "moon" (al- said) | the sun letter it melts into (ar-, an-, al- of al-layl...)
    allah: bool = False  # the name Allah (its lam is doubled, its a long)
    sounds: list[Sound] = field(default_factory=list)  # the rest of the word
    names: str = ""  # letters read by name


def _letters(word: str) -> list[tuple[str, set[str]]]:
    out: list[tuple[str, set[str]]] = []
    for ch in word:
        if ch == TATWEEL:
            continue
        if ch in MARKS:
            if out:
                out[-1][1].add(ch)
        else:
            out.append((ch, set()))
    return out


def _vowel(m: set[str]) -> str | None:
    return next((VOWEL_OF[x] for x in (FATHA, DAMMA, KASRA, FATHATAN, DAMMATAN, KASRATAN) if x in m), None)


def parse(word: str, first_of_verse: bool = False) -> Word:
    lets = _letters(word)
    w = Word()
    if not lets:
        return w
    if first_of_verse and not any(m for _, m in lets) and all(c in LETTER_NAMES for c, _ in lets) and len(lets) <= 5:
        w.names = " ".join(LETTER_NAMES[c] for c, _ in lets)
        return w
    i = 0

    def plain(k):  # a prefix letter: one short vowel, nothing else
        return lets[k][0] in "وفبكلت" and _vowel(lets[k][1]) and not lets[k][1] & ({SHADDA, SUKUN} | TANWIN)

    def wasl_at(k):  # a bare alif opening a connecting hamza: a consonant without vowel follows, or the article
        if k + 1 >= len(lets) or lets[k][0] != "ا" or lets[k][1]:
            return False
        nx = lets[k + 1][1]
        return SUKUN in nx or SHADDA in nx or (lets[k + 1][0] == "ل" and not nx and k + 2 < len(lets) and SHADDA in lets[k + 2][1])

    # up to two prefixes before the connecting hamza (wa-l-yawmi, bi-llāhi, wa-bi-l-ākhirati, fa-staqim)
    for p in (0, 1, 2):
        if all(plain(q) for q in range(p)) and p + 2 < len(lets) and wasl_at(p):
            w.prefix = [x for q in range(p) for x in (Sound("c", CONSONANT[lets[q][0]]), Sound("v", _vowel(lets[q][1])))]
            w.wasl, i = True, p + 1
            break
        # li- + article, whose alif is not written (li-l-muttaqīn, li-n-nās, lillāh, wa-li-llāhi)
        if (all(plain(q) for q in range(p)) and p + 2 < len(lets) and lets[p][0] == "ل" and KASRA in lets[p][1]
                and plain(p) and lets[p + 1][0] == "ل" and (lets[p + 1][1] & {SUKUN, SHADDA} or SHADDA in lets[p + 2][1])):
            w.prefix = [x for q in range(p + 1) for x in (Sound("c", CONSONANT[lets[q][0]]), Sound("v", _vowel(lets[q][1])))]
            w.wasl, i = True, p + 1
            if SHADDA in lets[p + 1][1]:  # lillāh, lil-layl: the lam of the article melts into a doubled lam
                w.article = "l"
            break
    # the article
    if w.wasl and not w.article and i + 1 < len(lets) and lets[i][0] == "ل":
        m = lets[i][1]
        if SUKUN in m:
            w.article = "moon"
            i += 1
        elif not m and SHADDA in lets[i + 1][1] and lets[i + 1][0] in CONSONANT:
            w.article = CONSONANT[lets[i + 1][0]]
            i += 1  # the lam is not said: the next letter is doubled
        elif SHADDA in m:
            w.article = "l"  # alladhī, allatī: the article's lam is written once, doubled
    rest = lets[i:]
    # the name Allah (allāhu, bi-llāhi, lillāhi, allāhumma): article + doubled lam + h
    w.allah = w.article == "l" and len(rest) > 1 and rest[0][0] == "ل" and SHADDA in rest[0][1] and rest[1][0] == "ه"
    # a hamza starting the word, or the noun after the article, is not written (aʿūdhu, al-arḍ)
    w.sounds = _body(rest, allah=w.allah, start=not w.prefix and not w.wasl or bool(w.article))
    return w


def _body(lets: list[tuple[str, set[str]]], allah: bool = False, start: bool = True) -> list[Sound]:
    sounds: list[Sound] = []
    n = len(lets)

    def last_vowel():
        return sounds[-1] if sounds and sounds[-1].kind == "v" else None

    for k, (c, m) in enumerate(lets):
        v, nxt = last_vowel(), lets[k + 1] if k + 1 < n else None
        if c == "ا":  # alif: lengthens a fatha, else silent (after -an, the plural waw, ...)
            if v and v.value == "a" and not v.nunation:
                v.long = True
            continue
        if c == "ى":  # alif maqsura
            if v and not v.nunation:
                v.long = True
            continue
        if c == "آ":  # hamza + ā
            sounds += [Sound("c", "'"), Sound("v", "a", long=True)]
            continue
        if c in "وي" and not m & (set(VOWEL_OF) | {SHADDA}):
            if v and not v.nunation and ((c == "و" and v.value == "u") or (c == "ي" and v.value == "i")):
                # a long vowel; but the waw of ulāʾika, ulū, ulī, ulāt is not said (al-ūlā keeps it)
                after = lets[k + 2] if k + 2 < n else None
                silent = (c == "و" and k >= 1 and lets[k - 1][0] == "أ" and nxt and nxt[0] == "ل" and after is not None
                          and (after[0] in "وي" or after[0] in "ائ" or (DAGGER in nxt[1] and after[0] == "ئ")))
                if not silent:
                    v.long = True
                continue
            sounds.append(Sound("c", "w" if c == "و" else "y"))  # aw, ay
            continue
        key = CONSONANT.get(c)
        if key is None:
            continue
        if not m and c in "نل" and nxt and SHADDA in nxt[1]:
            continue  # merged into the doubled letter after it
        if c == "إ" and not _vowel(m):
            m = m | {KASRA}
        sounds.append(Sound("c", key, double=SHADDA in m, marbuta=c == "ة"))
        vowel = _vowel(m)
        if vowel:
            long = DAGGER in m or (allah and k == 0 and vowel == "a")
            sounds.append(Sound("v", vowel, long=long, nunation=bool(m & TANWIN)))
        elif DAGGER in m:
            sounds.append(Sound("v", "a", long=True))
    if start and sounds and sounds[0].kind == "c" and sounds[0].value == "'":
        sounds.pop(0)  # a hamza starting the word is not written (aʿūdhu)
    return sounds


def _write(sounds: list[Sound], st: dict, pause: bool) -> str:
    out = []
    for k, s in enumerate(sounds):
        end = k == len(sounds) - 1
        if s.kind == "c":
            if s.marbuta and pause and k >= len(sounds) - 2:
                out.append("h")  # raḥmah
                break
            txt = st.get(s.value, s.value)
            out.append(txt * 2 if s.double else txt)
        elif pause and end and not s.long:
            if s.nunation and s.value == "a":
                out.append(st["aa"])  # -an is said -ā at a pause
        else:
            out.append((st[s.value * 2] if s.long else st.get(s.value, s.value)) + ("n" if s.nunation else ""))
    return "".join(out)


def _ends_with_vowel(w: Word) -> bool:
    return bool(w.names) or bool(w.sounds and w.sounds[-1].kind == "v") or (not w.sounds and bool(w.prefix))


def transliterate(words: list[str], style: str = "simple", start_of_verse: bool = False, pause: bool = True) -> list[str]:
    """One transliterated word per Arabic word, as recited in a row (a subtitle)."""
    st = STYLES.get(style, STYLES["simple"])
    parsed = [parse(w, start_of_verse and k == 0) for k, w in enumerate(words)]
    if st["join"]:
        # a long vowel joined to the next word's article is said short (ihdinas siraata, fis samaawaati)
        for k in range(1, len(parsed)):
            prev = parsed[k - 1].sounds
            if (parsed[k].article or parsed[k].wasl) and not parsed[k].prefix and prev and prev[-1].kind == "v":
                prev[-1].long = False
    out: list[str] = []
    for k, w in enumerate(parsed):
        if w.names:
            out.append(_names(w.names, st, style))
            continue
        body = _write(w.sounds, st, pause and k == len(parsed) - 1)
        joined = k > 0 and _ends_with_vowel(parsed[k - 1])  # the hamza of al- / ihdi- falls
        if joined and (w.wasl or w.article) and not w.prefix and parsed[k - 1].sounds and parsed[k - 1].sounds[-1].nunation:
            out[-1] += "i"  # -un + al- -> -uni l-
        pre = _write(w.prefix, st, False)
        art = "" if not w.article else "l" if w.article == "moon" else st.get(w.article, w.article)
        if w.article and w.article != "moon" and not w.allah:
            body = body[len(art):] if body.startswith(art * 2) else body  # the sun letter is shared: ar-raḥmān
        if w.allah:  # the doubled lam of the name: (A)llāh, bi-llāh, lillāh
            word = ((pre + ("-" if style == "academic" else "")) if pre else ("" if joined else "A")) + body
            if joined and not pre and st["join"]:
                out[-1] += "l"  # Bismil laahi
                word = body[1:]
        elif w.article:
            if pre:  # wa-l-yawmi / wal yawmi
                word = pre + ("-" + art + "-" if style == "academic" else art + " ") + body
            elif joined:
                if st["join"]:
                    out[-1] += art  # rabbil 'aalameen, rahmaanir raheem
                    word = body
                else:
                    word = art + "-" + body
            else:
                if w.article == "moon":
                    word = "al" + ("-" if style == "academic" else "") + body
                else:  # an-nās, but alladhī
                    word = "a" + art + ("" if w.article == "l" else "-") + body
        elif w.wasl:
            if pre:
                word = pre + ("-" if style == "academic" else "") + body  # fa-staqim
            else:
                lead = "u" if next((s.value for s in w.sounds[1:] if s.kind == "v"), "") == "u" else "i"
                word = body if joined else st.get(lead, lead) + body
        else:
            word = body
        out.append(word)
    if start_of_verse and out:
        out[0] = out[0][:1].upper() + out[0][1:]
    return out


def _names(names: str, st: dict, style: str) -> str:
    if style != "academic":
        for a, b in (("ā", st["aa"]), ("ī", st["ii"]), ("ū", st["uu"]), ("ṣ", "s"), ("ṭ", "t"), ("ḥ", "h"), ("ʿ", "'")):
            names = names.replace(a, b)
    return names
