"""Turn word timings into subtitle blocks.

Rules (learned from hand-made videos):
  * a new block at every verse boundary and whenever the reciter repeats;
  * inside a verse, a new block at every real breath (the audio drops well
    below the speech level for a moment). Elongated letters (madd, ghunna)
    leave long gaps in the character timings but no breath, so the decision
    is made on the audio, not on the gaps;
  * a part that is still too long is split again at the best place: pause
    marks (waqf), then the deepest dip in the audio, keeping parts balanced;
  * the translation is cut at the punctuation that best matches the Arabic
    cut (helped, in French and English, by the words that usually render the
    Arabic word opening the next part);
  * a block appears ~0.1 s before the reciter starts it and stays until the
    next block replaces it.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

import numpy as np

from . import quran, translit
from .i18n import UserError
from .align import WordTiming

ISTIADHA_TR = "AAoothu biAllahi mina alshshaytani alrrajeemi"  # in the Tanzil convention
ISTIADHA_UTHMANI = "أَعُوذُ بِٱللَّهِ مِنَ ٱلشَّيْطَـٰنِ ٱلرَّجِيمِ"
CUT_START_S = 1.5  # a recording whose first verse starts mid-verse this early was cut there
MISSED_WORDS = 2  # words at the start or end of a verse the aligner may miss (shown anyway)


@dataclass
class Options:
    breath_quiet_s: float = 0.15  # how long the audio must stay quiet to count as a breath
    breath_depth_db: float = 12.0  # how far below the speech level
    max_words: int = 11  # longer parts get split
    max_french_chars: int = 115  # ~2 lines of French
    max_part_s: float = 9.0
    min_part_words: int = 2
    lead_s: float = 0.10  # show a block this long before the voice starts
    max_hold_s: float = 1.5  # keep a block on screen at most this long after its last word
    show_istiadha: bool = True
    show_basmala: bool = True
    lang: str = "fr"  # translation language (quran.LANGS)
    translation: str = ""  # which translation of that language (quran.EDITIONS); "" = the default one
    translit: str = "simple"  # how the phonetic line is written: translit.STYLES, or "tanzil"


def translation(v: quran.Verse, lang: str, chosen: str | None = None) -> str:
    if lang == "fr" and quran.edition("fr", chosen) == "fr.hamidullah":
        return v.french
    return quran.translation(lang, v.surah, v.ayah, chosen)


def phonetic(kind: str, v: quran.Verse | None, a0: int, a1: int, style: str) -> list[str]:
    """Transliterated words of a block: verse words [a0, a1), or the isti'adha / basmala."""
    if kind == "istiadha":
        return ISTIADHA_TR.split() if style == "tanzil" else translit.transliterate(quran.ISTIADHA.split(), style, True)
    if kind == "basmala":
        v = quran.verse(1, 1)
        a0, a1 = 0, len(v.align)
    return v.phonetic(a0, a1, style)


@dataclass
class Block:
    kind: str  # "verse" | "istiadha" | "basmala"
    surah: int
    ayah: int  # 0 for istiadha/basmala
    a0: int  # align-word range inside the verse
    a1: int
    start: float  # on-screen start (s)
    end: float  # on-screen end (s)
    ar: str
    fr: str
    tr: str
    highlight: bool = False
    voice_start: float = 0.0  # when the reciter actually starts / stops this block
    voice_end: float = 0.0
    words: list[dict] = field(default_factory=list)  # per-word timings, for the editor
    edited: bool = False  # Arabic / phonetic corrected by hand in the editor

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Block":
        return Block(**{k: d[k] for k in Block.__dataclass_fields__ if k in d})


# ---------------------------------------------------------------- audio

class Loudness:
    """Short-term loudness relative to the surrounding speech level."""

    def __init__(self, audio: np.ndarray, sr: int = 16000):
        hop, win = sr // 100, sr // 50  # 10 ms hop, 20 ms window
        n = max(1, (len(audio) - win) // hop)
        frames = np.lib.stride_tricks.sliding_window_view(audio, win)[::hop][:n]
        db = 20 * np.log10(np.sqrt((frames.astype(np.float64) ** 2).mean(axis=1)) + 1e-9)
        # speech level: 80th percentile over a 3 s window
        k = 150
        padded = np.pad(db, k, mode="edge")
        win_view = np.lib.stride_tricks.sliding_window_view(padded, 2 * k + 1)[::5]
        ref = np.repeat(np.percentile(win_view, 80, axis=1), 5)[: len(db)]
        self.rel = db - ref

    def pause(self, t0: float, t1: float, depth_db: float) -> tuple[float, float]:
        """(quiet seconds, deepest dip in dB) between t0 and t1."""
        i0, i1 = int(t0 * 100), max(int(t1 * 100), int(t0 * 100) + 1)
        seg = self.rel[i0:i1]
        if len(seg) == 0:
            return 0.0, 0.0
        return float((seg < -depth_db).sum() * 0.01), float(seg.min())


# ---------------------------------------------------------------- french

_STRONG = re.compile(r"[.;!?»”\"۔؟](?=\s)")
_WEAK = re.compile(r"[,،](?=\s)")
_COLON = re.compile(r":(?=\s)")
_OPEN_PAREN = re.compile(r"\s(?=\()")
_OPEN_QUOTE = re.compile(r"\s(?=[«“])")  # also used around Arabic terms («Kursiy»), so weaker
# words that open a clause, per language
_CONJ_WORDS = {
    "fr": "et|mais|car|puis|sinon|ou|or|donc|alors|afin|lorsque|quand|tandis",
    "en": "and|but|for|then|so|or|when|while|that|which|who|lest|until|indeed",
    "es": "y|pero|pues|luego|entonces|o|cuando|mientras|que|para",
    "pt": "e|mas|pois|então|ou|quando|enquanto|que|para",
    "it": "e|ma|poi|allora|o|quando|mentre|che|perché",
    "de": "und|aber|denn|dann|oder|wenn|während|dass|damit",
    "nl": "en|maar|want|dan|of|wanneer|terwijl|dat",
    "sv": "och|men|för|sedan|eller|när|medan|att",
    "tr": "ve|ama|fakat|çünkü|sonra|veya",
    "id": "dan|tetapi|maka|lalu|atau|ketika|bahwa|agar",
    "ms": "dan|tetapi|maka|lalu|atau|ketika|bahawa|supaya",
    "bs": "i|ali|pa|ili|kad|da",
    "sq": "dhe|por|pastaj|ose|kur|që",
    "ru": "и|но|а|или|когда|чтобы",
}
_CONJ = {k: re.compile(r"\s(?=(" + v + r")\b)", re.I) for k, v in _CONJ_WORDS.items()}

# Arabic words that open a clause, and how Hamidullah usually renders them.
# When an Arabic part starts with one of these, a French cut followed by the
# matching words is very likely the right one.
_ANCHORS = [
    (("قل",), r"dis\b|dites\b"),
    (("سيقولون", "يقولون", "قالوا", "قال", "وقالوا", "وقال", "فقال", "فقالوا"), r"(ils )?(diront|disent|dirent|dit)\b|il dit\b"),
    (("سبحن", "سبحان", "فسبحن", "فسبحان"), r"gloire|pureté"),
    (("يايها", "ايها", "يا"), r"ô\b"),
    (("الذين", "والذين", "الذي", "والذي"), r"ceux qui|celui qui|qui\b"),
    (("اذا", "اذن"), r"sinon|alors|quand|lorsque|si\b"),
    (("ان",), r"si\b|certes"),
    (("بل",), r"plutôt|mais|non\b|bien au contraire"),
    (("ثم",), r"puis|ensuite"),
    (("كلا",), r"mais non|non\b|prenez garde"),
    (("لعلكم", "لعلهم"), r"afin|peut-être|pour que"),
    (("افلا", "افلم", "اولم", "الم"), r"ne\b|n'"),
    (("ولا",), r"et (ne|n')|ni\b|sans\b|et qui ne|et n'"),
    (("فمن", "من"), r"quiconque|celui qui|qui\b"),
    (("ربنا",), r"seigneur|ô notre seigneur"),
]


_ANCHORS_EN = [
    (("قل",), r"say\b"),
    (("سيقولون", "يقولون", "قالوا", "قال", "وقالوا", "وقال", "فقال", "فقالوا"), r"(they |he )?(will )?(say|said)\b"),
    (("سبحن", "سبحان", "فسبحن", "فسبحان"), r"exalted|glory|glorified"),
    (("يايها", "ايها", "يا"), r"o\b"),
    (("الذين", "والذين", "الذي", "والذي"), r"(those|he|the one) who|who\b|which\b"),
    (("اذا", "اذن"), r"then\b|when\b|if\b"),
    (("ان",), r"if\b|indeed"),
    (("بل",), r"but|rather|nay"),
    (("ثم",), r"then\b"),
    (("كلا",), r"no\b|nay"),
    (("لعلكم", "لعلهم"), r"that (you|they)|so that|perhaps"),
    (("ولا",), r"and (do |does )?not|nor\b"),
    (("فمن", "من"), r"whoever|who\b"),
    (("ربنا",), r"our lord"),
]
_AND = {"fr": ("et", "puis|alors|donc|et"), "en": ("and", "then|so|and")}


# "Say" (قل, 332 times in the Quran) in the other languages
_SAY = {"es": r"di\b|decid", "pt": r"diz|dize|diga", "it": r"di['’]?\b|dì|dite", "de": r"sag|sprich", "nl": r"zeg",
        "sv": r"säg", "tr": r"de ki|de\b", "id": r"katakanlah", "ms": r"katakanlah", "bs": r"reci|kaži", "sq": r"thuaj",
        "ru": r"скажи", "ur": r"کہو|کہہ"}


def _anchor_pattern(arabic_word: str | None, lang: str = "fr") -> tuple[re.Pattern | None, float]:
    if not arabic_word:
        return None, 0.0
    sk = quran.skeleton(arabic_word)
    if lang not in _AND:
        if sk == "قل" and lang in _SAY:
            return re.compile(r"[\s«“\"(\[]*(" + _SAY[lang] + ")", re.I), 4.0
        return None, 0.0
    for words, pat in (_ANCHORS if lang == "fr" else _ANCHORS_EN):
        if sk in words:
            return re.compile(r"[\s«“\"(\[]*(" + pat + ")", re.I), 4.0
    wa, fa = _AND[lang]
    if sk.startswith("و"):  # wa- usually becomes "et" / "and"
        return re.compile(r"[\s«“\"(\[]*(" + wa + r")\b", re.I), 1.5
    if sk.startswith("ف"):  # fa- : "puis", "alors", "donc"
        return re.compile(r"[\s«“\"(\[]*(" + fa + r")\b", re.I), 1.0
    return None, 0.0


def _french_cut_points(fr: str, lang: str = "fr") -> list[tuple[int, float]]:
    """(character position, strength) of the places a sentence can be cut.
    Never inside [...] or (...) asides."""
    pts = {}
    for m in _STRONG.finditer(fr):
        pts[m.end()] = 3.0
    for m in _OPEN_PAREN.finditer(fr):
        pts.setdefault(m.start(), 2.5)
    for m in _OPEN_QUOTE.finditer(fr):
        pts.setdefault(m.start(), 1.0)
    for m in _WEAK.finditer(fr):
        pts.setdefault(m.end(), 2.0)
    if lang in _CONJ:
        for m in _CONJ[lang].finditer(fr):
            pts.setdefault(m.start(), 1.0)
    for m in _COLON.finditer(fr):
        pts.setdefault(m.end(), 0.5)
    for m in re.finditer(r"\s", fr):  # any space, as a last resort
        pts.setdefault(m.start(), 0.0)
    depth, inside = 0, set()
    for i, ch in enumerate(fr):
        if ch in "[(":
            depth += 1
        elif ch in "])":
            depth = max(0, depth - 1)
        elif depth:
            inside.add(i)
    return sorted((p, s) for p, s in pts.items() if p not in inside and 0 < p < len(fr))


def _effective_positions(fr: str) -> list[float]:
    """Cumulative length that ignores [bracketed] translator additions,
    which have no Arabic counterpart."""
    out, acc, depth = [0.0], 0.0, 0
    for ch in fr:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth = max(0, depth - 1)
        elif not depth:
            acc += 1
        out.append(acc)
    return out


def french_cut_cost(fr: str, fraction: float, next_arabic: str | None, lang: str = "fr") -> float:
    """How well `fr` can be cut near `fraction` (lower is better)."""
    eff = _effective_positions(fr)
    pat, bonus = _anchor_pattern(next_arabic, lang)
    best = 1e9
    for pos, strength in _french_cut_points(fr, lang):
        c = 30 * abs(eff[pos] / max(eff[-1], 1) - fraction) - strength
        if pat and pat.match(fr, pos):
            c -= bonus
        best = min(best, c)
    return best


def split_french(fr: str, fractions: list[float], next_arabic: list[str | None] | None = None,
                 lang: str = "fr") -> list[str]:
    """Cut the translation `fr` at len(fractions) places close to the given
    fractions (0..1) of its length, preferring punctuation and the usual
    rendering of the Arabic word that starts each next part. Returns
    len(fractions)+1 parts."""
    if not fractions:
        return [fr.strip()]
    cands = _french_cut_points(fr, lang)
    if len(cands) < len(fractions):
        return [fr.strip()] + [""] * len(fractions)
    n = len(fractions)
    eff = _effective_positions(fr)
    total = max(eff[-1], 1)
    anchors = [_anchor_pattern(w, lang) for w in (next_arabic or [None] * n)]
    # dynamic programming over candidates (keeps cuts in order)
    INF = 1e9
    cost = [[INF] * len(cands) for _ in range(n)]
    back = [[-1] * len(cands) for _ in range(n)]

    def c(i, j):
        pos, strength = cands[j]
        v = abs(eff[pos] / total - fractions[i]) * 30 - strength
        pat, bonus = anchors[i]
        if pat and pat.match(fr, pos):
            v -= bonus
        return v

    for j in range(len(cands)):
        cost[0][j] = c(0, j)
    for i in range(1, n):
        best, arg = INF, -1
        for j in range(len(cands)):
            if j > 0 and cost[i - 1][j - 1] < best:
                best, arg = cost[i - 1][j - 1], j - 1
            if arg >= 0:
                cost[i][j], back[i][j] = best + c(i, j), arg
    j = int(np.argmin(cost[n - 1]))
    cuts = []
    for i in range(n - 1, -1, -1):
        cuts.append(cands[j][0])
        j = back[i][j]
    cuts = [0] + cuts[::-1] + [len(fr)]
    parts = [fr[a:b].strip() for a, b in zip(cuts, cuts[1:])]
    return [p[:1].upper() + p[1:] if i and p[:1].isalpha() and parts[i - 1][-1:] in ".!?" else p
            for i, p in enumerate(parts)]


# ---------------------------------------------------------------- blocks

@dataclass
class _Piece:
    kind: str
    verse_index: int
    occ: list[WordTiming]

    @property
    def a0(self):
        return self.occ[0].word.index

    @property
    def a1(self):
        return self.occ[-1].word.index + 1


def _pieces(occ: list[WordTiming]) -> list[_Piece]:
    """Contiguous runs of words inside one verse (or prefix)."""
    out: list[_Piece] = []
    for o in occ:
        w = o.word
        last = out[-1] if out else None
        if last and last.kind == w.unit and last.verse_index == w.verse_index and w.index == last.occ[-1].word.index + 1:
            last.occ.append(o)
        else:
            out.append(_Piece(w.unit, w.verse_index, [o]))
    return out


def _arabic_weight(v: quran.Verse, a0: int, a1: int) -> float:
    return sum(len(quran.skeleton(w)) for w in v.align[a0:a1])


def _split_piece(p: _Piece, v: quran.Verse | None, loud: Loudness, opt: Options) -> list[list[WordTiming]]:
    occ = p.occ
    n = len(occ)
    if n <= 1 or v is None:
        return [occ]
    # features of each inner boundary k (between occ[k-1] and occ[k])
    feats = {}
    for k in range(1, n):
        a, b = occ[k - 1], occ[k]
        quiet, dip = loud.pause(a.end - 0.06, b.start + 0.04, opt.breath_depth_db)
        d_idx = v.align_to_display[a.word.index + 1]
        waqf = v.display[d_idx - 1].waqf if d_idx > 0 else ""
        feats[k] = (quiet, dip, quran.WAQF_STRENGTH.get(waqf, -1) if waqf else -1)

    # 1) breaths
    cuts = [k for k in range(1, n) if feats[k][0] >= opt.breath_quiet_s]
    # don't leave tiny fragments around a breath
    cuts = [k for k in cuts if k >= opt.min_part_words and n - k >= opt.min_part_words] or []
    # and always where a verse ends inside this one (Warsh counts some Hafs verses as two)
    cuts += [k for k in range(1, n) if occ[k - 1].word.index + 1 in v.ends]
    parts = _cut(occ, cuts)

    # 2) length
    def too_long(ws):
        a0, a1 = ws[0].word.index, ws[-1].word.index + 1
        fr_len = len(translation(v, opt.lang, opt.translation)) * _arabic_weight(v, a0, a1) / max(1.0, _arabic_weight(v, 0, len(v.align)))
        return (len(ws) > opt.max_words or fr_len > opt.max_french_chars or ws[-1].end - ws[0].start > opt.max_part_s)

    changed = True
    while changed:
        changed = False
        out = []
        for ws in parts:
            if too_long(ws) and len(ws) >= 2 * opt.min_part_words:
                base = occ.index(ws[0])
                best, arg = -1e9, None
                for k in range(opt.min_part_words, len(ws) - opt.min_part_words + 1):
                    quiet, dip, waqf = feats[base + k]
                    balance = abs(k / len(ws) - 0.5)
                    # prefer cuts the French translation can follow too
                    frac = _arabic_weight(v, 0, ws[k].word.index) / max(1.0, _arabic_weight(v, 0, len(v.align)))
                    fr_fit = french_cut_cost(translation(v, opt.lang, opt.translation), frac, ws[k].word.text, opt.lang)
                    score = (2.0 * max(waqf, 0) + (1.5 if waqf >= 0 else 0) + 6 * quiet - dip / 8
                             - 6 * balance - 0.5 * fr_fit)
                    if score > best:
                        best, arg = score, k
                if arg is not None:
                    out += [ws[:arg], ws[arg:]]
                    changed = True
                    continue
            out.append(ws)
        parts = out
    return parts


def _cut(seq, cuts):
    out, prev = [], 0
    for k in sorted(set(cuts)):
        out.append(seq[prev:k])
        prev = k
    out.append(seq[prev:])
    return [p for p in out if p]


def _is_tasbih(v: quran.Verse, a0: int) -> bool:
    return quran.skeleton(v.align[a0]).startswith("سبحن") or quran.skeleton(v.align[a0]).startswith("سبحان")


def build_blocks(occ: list[WordTiming], verses: list[quran.Verse], audio: np.ndarray,
                 duration: float, opt: Options | None = None) -> list[Block]:
    opt = opt or Options()
    loud = Loudness(audio)
    raw: list[tuple[_Piece, list[WordTiming]]] = []
    for p in _pieces(occ):
        if p.kind == "istiadha" and not opt.show_istiadha:
            continue
        if p.kind == "basmala" and not opt.show_basmala:
            continue
        v = verses[p.verse_index] if p.kind == "verse" else None
        for ws in _split_piece(p, v, loud, opt):
            raw.append((p, ws))

    blocks: list[Block] = []
    # French text per verse occurrence, split across its parts together
    i = 0
    while i < len(raw):
        p = raw[i][0]
        group = [ws for (pp, ws) in raw[i:] if pp is p]
        if p.kind == "verse":
            v = verses[p.verse_index]
            total = _arabic_weight(v, 0, len(v.align))
            bounds = [ws[0].word.index for ws in group] + [group[-1][-1].word.index + 1]
            # the recording stops mid-verse: show the whole verse if little is missing
            missing = len(v.align) - bounds[-1]
            if (i + len(group) == len(raw) and missing > 0 and group[-1][-1].end >= duration - 0.6
                    and (missing <= 4 or len(v.align) - bounds[-2] <= opt.max_words + 3)):
                bounds[-1] = len(v.align)
            # and the same when it starts mid-verse (the clip was cut): the verse from its start
            if (i == 0 and 0 < bounds[0] and group[0][0].start <= CUT_START_S
                    and (bounds[0] <= 4 or bounds[1] <= opt.max_words + 3)):
                bounds[0] = 0
            # a word or two the model barely heard (a voice fading on the last madd, a soft
            # first word): a verse is recited whole unless the reciter goes back inside it
            # (said again from its start after a voice, not a pause: it was finished)
            prev = raw[i - 1][0] if i else None
            nxt = raw[i + len(group)][0] if i + len(group) < len(raw) else None
            same = lambda q: q is not None and q.kind == "verse" and q.verse_index == p.verse_index
            if same(nxt):
                end, again = group[-1][-1].end, raw[i + len(group)][1][0]
                finished = again.word.index == 0 and (again.start - end) - loud.pause(
                    end, again.start, opt.breath_depth_db)[0] >= 0.3 * missing
            if 0 < missing <= MISSED_WORDS and nxt is not None and (not same(nxt) or finished):
                bounds[-1] = len(v.align)
            if 0 < bounds[0] <= MISSED_WORDS and prev is not None and not same(prev):
                bounds[0] = 0
            fracs = [_arabic_weight(v, 0, b) / total for b in bounds]
            # cut the whole verse translation, then keep the slices this run covers
            # (a run may start or stop mid-verse, e.g. when the clip is cut)
            inner = [(f, v.align[b]) for f, b in zip(fracs, bounds) if 0 < f < 1]
            fr_parts = split_french(translation(v, opt.lang, opt.translation), [f for f, _ in inner], [w for _, w in inner], opt.lang)
            offset = 1 if fracs[0] > 0 else 0
            for gi, ws in enumerate(group):
                a0, a1 = bounds[gi], bounds[gi + 1]
                d0, d1 = v.align_to_display[a0], v.align_to_display[a1]
                fr = fr_parts[gi + offset] if gi + offset < len(fr_parts) else ""
                tr = phonetic("verse", v, a0, a1, opt.translit)
                blocks.append(Block(
                    "verse", v.surah, v.ayah, a0, a1, 0, 0,
                    v.display_text(d0, d1), fr, " ".join(tr),
                    highlight=_is_tasbih(v, a0),
                    voice_start=ws[0].start, voice_end=ws[-1].end,
                    words=[{"t0": round(o.start, 3), "t1": round(o.end, 3), "w": o.word.text,
                            "tr": tr[k] if k < len(tr) else ""} for k, o in enumerate(ws)],
                ))
        else:
            ws = group[0]
            tr = " ".join(phonetic(p.kind, None, 0, 0, opt.translit))
            if p.kind == "istiadha":
                ar, fr = ISTIADHA_UTHMANI, quran.ISTIADHA_TRANSLATION[opt.lang]
            else:
                ar, fr = quran.basmala_uthmani(), translation(quran.verse(1, 1), opt.lang, opt.translation)
            blocks.append(Block(p.kind, 0, 0, 0, len(ws), 0, 0, ar, fr, tr,
                                voice_start=ws[0].start, voice_end=ws[-1].end,
                                words=[{"t0": round(o.start, 3), "t1": round(o.end, 3), "w": o.word.text} for o in ws]))
        i += len(group)

    retime(blocks, duration, opt)
    return blocks


def retime(blocks: list[Block], duration: float, opt: Options | None = None) -> None:
    """Set on-screen start/end from the voice timings."""
    opt = opt or Options()
    for i, b in enumerate(blocks):
        if i == 0:  # the voice starts right away (a cut clip): the subtitle is there from the first frame
            b.start = 0.0 if b.voice_start <= CUT_START_S else max(0.0, b.voice_start - opt.lead_s)
        if i + 1 < len(blocks):
            nxt = blocks[i + 1]
            gap = nxt.voice_start - b.voice_end
            if gap > opt.max_hold_s + opt.lead_s:
                b.end = b.voice_end + opt.max_hold_s
                nxt.start = nxt.voice_start - opt.lead_s
            else:
                cut = max(b.voice_end, nxt.voice_start - opt.lead_s)
                b.end = nxt.start = cut
        else:
            b.end = min(duration, b.voice_end + opt.max_hold_s)
    for b in blocks:
        b.start, b.end = round(b.start, 3), round(b.end, 3)


# ---------------------------------------------------------------- editing

def verse_texts(b: Block, style: str = "simple") -> None:
    """Refresh the Arabic and phonetic text of a verse block from its word range."""
    v = quran.verse(b.surah, b.ayah)
    b.ar = v.display_text(v.align_to_display[b.a0], v.align_to_display[b.a1])
    set_phonetic(b, style)
    b.edited = False


def set_phonetic(b: Block, style: str) -> None:
    """The phonetic line of a block (and of each of its words), in a convention."""
    tr = phonetic(b.kind, quran.verse(b.surah, b.ayah) if b.kind == "verse" else None, b.a0, b.a1, style)
    b.tr = " ".join(tr)
    if b.kind == "verse":
        for k, w in enumerate(b.words):
            w["tr"] = tr[k] if k < len(tr) else ""


def rephonetize(blocks: list[Block], style: str) -> None:
    """Write the phonetic line of every block in another convention."""
    for b in blocks:
        set_phonetic(b, style)


def split_block(blocks: list[Block], i: int, k: int, lang: str = "fr", style: str = "simple") -> None:
    """Split block i before its k-th word (1 <= k < number of words)."""
    b = blocks[i]
    if b.kind != "verse" or not 0 < k < len(b.words):
        raise UserError("cannot_split")
    v = quran.verse(b.surah, b.ayah)
    first, second = Block.from_dict(b.to_dict()), Block.from_dict(b.to_dict())
    first.a1 = second.a0 = b.a0 + k
    first.words, second.words = b.words[:k], b.words[k:]
    first.voice_end, second.voice_start = first.words[-1]["t1"], second.words[0]["t0"]
    cut = max(first.voice_end, second.voice_start - Options().lead_s)
    first.end = second.start = round(cut, 3)
    total = _arabic_weight(v, 0, len(v.align))
    frac = _arabic_weight(v, 0, first.a1) / total
    # split this block's own French at the point matching the new Arabic boundary
    lo, hi = _arabic_weight(v, 0, b.a0) / total, _arabic_weight(v, 0, b.a1) / total
    local = (frac - lo) / max(hi - lo, 1e-6)
    first.fr, second.fr = split_french(b.fr, [local], [v.align[first.a1]], lang)
    for x in (first, second):
        verse_texts(x, style)
    second.highlight = _is_tasbih(v, second.a0)
    blocks[i: i + 1] = [first, second]


def merge_blocks(blocks: list[Block], i: int, style: str = "simple") -> None:
    """Merge block i with block i+1 (same verse, consecutive words)."""
    a, b = blocks[i], blocks[i + 1]
    if a.kind != b.kind or (a.surah, a.ayah) != (b.surah, b.ayah) or a.a1 != b.a0:
        raise UserError("cannot_merge")
    a.a1, a.end, a.voice_end = b.a1, b.end, b.voice_end
    a.words = a.words + b.words
    a.fr = (a.fr + " " + b.fr).strip()
    a.highlight = a.highlight and b.highlight
    if a.kind == "verse":
        verse_texts(a, style)
    del blocks[i + 1]


def retranslate(blocks: list[Block], lang: str, chosen: str | None = None) -> None:
    """Replace the translation line of every block with another language,
    cut at the same places as the Arabic."""
    i = 0
    while i < len(blocks):
        b = blocks[i]
        if b.kind != "verse":
            v = quran.verse(1, 1)
            b.fr = quran.ISTIADHA_TRANSLATION[lang] if b.kind == "istiadha" else translation(v, lang, chosen)
            i += 1
            continue
        # consecutive parts of the same recitation of a verse
        j = i + 1
        while j < len(blocks) and blocks[j].kind == "verse" and (blocks[j].surah, blocks[j].ayah) == (b.surah, b.ayah) \
                and blocks[j].a0 == blocks[j - 1].a1:
            j += 1
        group = blocks[i:j]
        v = quran.verse(b.surah, b.ayah)
        total = _arabic_weight(v, 0, len(v.align))
        bounds = [g.a0 for g in group] + [group[-1].a1]
        fracs = [_arabic_weight(v, 0, x) / total for x in bounds]
        inner = [(f, v.align[x]) for f, x in zip(fracs, bounds) if 0 < f < 1]
        parts = split_french(translation(v, lang, chosen), [f for f, _ in inner], [w for _, w in inner], lang)
        offset = 1 if fracs[0] > 0 else 0
        for k, g in enumerate(group):
            g.fr = parts[k + offset] if k + offset < len(parts) else ""
        i = j
