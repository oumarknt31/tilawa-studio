"""From the model's letters to subtitle blocks: which verses are recited, and when.

1. identify.track follows the recording through the Quran and finds the passages
   recited (one per surah: a prayer may hold Al-Fatiha and another surah), with
   roughly when each is heard.
2. align.align_segments places every word of those passages in one search, each
   passage only around the time it was heard, so a passage never borrows audio
   that is something else (another surah, speech, music).
3. segment.build_blocks makes the subtitles.
"""

from __future__ import annotations

from dataclasses import replace
from difflib import SequenceMatcher

import numpy as np

from . import align, identify, quran, segment

PRE = 4.0  # s before the first letter heard where a passage's words may start (missed letters)
POST = 3.0  # and after the last one
PREFIX = 14.0  # isti'adha and basmala before a passage
AMIN = 6.0  # more after Al-Fatiha: "ad-daaaallin" (heard as blank), then "amin" in prayer
TAIL_LETTERS = 24  # letters heard after the last passage: it may go on...
TAIL_VERSES = 12  # ...for this many verses more
MUQATTAAT = 8.0  # more before spelled letters ("Alif Laaam Miiim": the tracker hears the last one)
MAX_CELLS = 120_000_000  # frames x states of one alignment (2 bytes each): longer recordings go in pieces
PIECE_S = 150.0  # length of those pieces (cut at a quiet moment between two verses)...
OVERLAP_S = 8.0  # ...aligned with this much more on each side, and joined where both agree


def detect(em: np.ndarray, audio: np.ndarray, model, opt: segment.Options, surah: int = 0, first: int = 1,
           last: int | None = None, short: np.ndarray | None = None) -> tuple[list[segment.Block], list[dict]]:
    """Blocks of the recitation, and the passages heard: [{surah, first, last, t0, t1, coverage}].
    surah 0: found in the audio; otherwise the user's choice, used when the audio agrees or
    says nothing. short: the model's letters with short windows (Model.emissions(audio,
    SHORT_CHUNK_S, SHORT_CONTEXT_S)). With its usual windows the model, which knows the Quran's
    order, may not hear a verse said again; the words are placed again with the short ones
    (in the same passages), and that is kept when it hears the same verses and a repeat."""
    passages = identify.track(em, model)
    blocks = _detect(em, audio, model, opt, surah, first, last, passages)
    doubt = {}
    if short is not None and blocks:
        again = _detect(short, audio, model, opt, surah, first, last, passages)
        said, said2 = _said(blocks), _said(again)
        if _adds_repeat([v for v, _ in said], [v for v, _ in said2]):
            blocks = again
        else:  # heard otherwise this time: to check
            ops = SequenceMatcher(None, [v for v, _ in said], [v for v, _ in said2], autojunk=False).get_opcodes()
            for op, i1, i2, _, _ in ops:
                if op != "equal":
                    doubt.update({k: "differ" for _, ks in said[max(0, min(i1, i2 - 1)):max(i2, i1 + 1)] for k in ks})
    _doubts(blocks, doubt)
    return blocks, [p.to_dict() for p in passages]


def _said(blocks: list[segment.Block]) -> list[tuple[tuple[int, int], list[int]]]:
    """The verses recited, in order (a verse said twice is there twice), with their blocks."""
    out, prev = [], None
    for k, b in enumerate(blocks):
        if b.kind != "verse":
            continue
        if not out or out[-1][0] != (b.surah, b.ayah) or (b.a0 == 0 and prev.a1 == len(quran.verse(b.surah, b.ayah).align)):
            out.append(((b.surah, b.ayah), []))
        out[-1][1].append(k)
        prev = b
    return out


def _adds_repeat(said: list[tuple[int, int]], again: list[tuple[int, int]]) -> bool:
    """again is said with one verse or more said twice in a row more (not spelled letters:
    "Alif Laaam Miiim" can be heard in a long "amin" before it)."""
    once = lambda s: [v for k, v in enumerate(s) if not k or s[k - 1] != v]
    added = [v for k, v in enumerate(again) if k and again[k - 1] == v]
    return len(again) > len(said) and once(again) == once(said) and not set(added) & quran.MUQATTAAT


def _detect(em: np.ndarray, audio: np.ndarray, model, opt: segment.Options, surah: int, first: int,
            last: int | None, passages: list[identify.Passage]) -> list[segment.Block]:
    """The blocks of those passages, with these letters of the model."""
    duration = len(audio) / align.SR
    if surah and not any(p.surah == surah for p in passages):
        # the user's choice, over the whole recording (the audio was not clear enough)
        total = quran.surah(surah)["verses"]
        hi = last or min(total, first - 1 + align.max_verses_for(duration, total))
        lo = max(1, first - align.LOOKBACK_VERSES)
        jobs = [(0.0, duration, 0.0, duration, [0], [align.Segment(quran.verses(surah, lo, hi), first - lo)])]
    else:
        if not passages:
            return []
        if surah:  # the verses the user gave, if the audio is near them
            for p in passages:
                if p.surah == surah and 0 < p.first - first <= 10:
                    p.first = first
        # letters heard after the last passage: the reciter may read on, heard too badly for the
        # tracker (the aligner tries the next verses there)
        codes, frames = identify.heard(em, model)
        end = max(passages, key=lambda p: p.t1)
        tail = end if np.count_nonzero(frames * align.FRAME_S > end.t1) >= TAIL_LETTERS else None
        jobs = []
        for a, b, parts in _pieces(passages, audio, duration):
            lo, hi = max(0.0, a - OVERLAP_S) if a else 0.0, min(duration, b + OVERLAP_S)
            jobs.append((a, b, lo, hi, [k for k, _ in parts], _segments([q for _, q in parts], lo, hi, tail)))
    occ, verses, index = [], [], {}
    for a, b, lo, hi, which, segments in jobs:
        o, vs = _align(em, audio, model, lo, hi, segments)
        mapped = []
        for x in o:  # verse and passage numbers over the whole recording (a verse is one, in every piece)
            w, k = x.word, which[x.word.seg]
            vi = -1
            if w.verse_index >= 0:
                v = vs[w.verse_index]
                vi = index.setdefault((k, v.surah, v.ayah), len(verses))
                if vi == len(verses):
                    verses.append(v)
            mapped.append(align.WordTiming(replace(w, verse_index=vi, seg=k), x.start, x.end, x.score))
        occ = _stitch(occ, mapped, a) if occ else mapped
    occ = _drop_strays(occ, verses, em, model)
    occ = _fatiha_basmala(occ, verses)  # (may add 1:1 to verses)
    occ = _trim_ends(occ, audio, opt)
    if passages and not surah:
        occ = _finish_verses(occ, verses, passages, audio, opt)
        occ = _cut_verse(occ, verses, passages[0], em, model)  # (may add that verse to verses)
        occ = _cut_word(occ, em, audio, model, opt)
        occ = _missed_start(occ, verses, em, audio, model, opt)
    return segment.build_blocks(occ, verses, audio, duration, opt)


# why a subtitle may be wrong, most telling first: the editor asks to check those by ear
DOUBTS = ("differ", "faint")
DOUBT_SCORE = -1.5  # words heard this badly on average (mean log-prob): "faint"


def _doubts(blocks: list[segment.Block], why: dict[int, str]) -> None:
    """Mark the subtitles to check: heard otherwise with short windows (differ), words barely
    heard (faint). Only these: a flag must be rare on the subtitles that are right, or it is soon
    ignored (on the benchmark, a long word or a repeat heard with short windows are as often
    right as wrong)."""
    for k, b in enumerate(blocks):
        reasons = [why[k]] if k in why else []
        if b.kind == "verse" and b.words and float(np.mean([w.get("s", 0.0) for w in b.words])) < DOUBT_SCORE:
            reasons.append("faint")
        b.doubt = min(reasons, key=DOUBTS.index) if reasons else ""


def _segments(passages: list[identify.Passage], a: float, b: float,
              tail: identify.Passage | None = None) -> list[align.Segment]:
    """What the aligner searches for between a and b (s): each passage, around when it was heard.
    Where one passage ends and the next starts is left to the aligner (the tracker may match a
    few letters of the silence between them). tail: the last passage, which may go on further
    than the tracker heard, until the end."""
    out = []
    for k, p in enumerate(passages):
        prev_start = passages[k - 1].t0 if k else a
        next_end = passages[k + 1].t1 if k + 1 < len(passages) else b
        total = quran.surah(p.surah)["verses"]
        lo, hi = max(1, p.first - 1), min(total, p.last + (TAIL_VERSES if p is tail else 1))
        post = (b - p.t1) if p is tail else POST + (AMIN if (p.surah, hi) == (1, 7) else 0.0)
        pre = PRE + (MUQATTAAT if {(p.surah, lo), (p.surah, p.first)} & quran.MUQATTAAT else 0.0)
        band = (max(prev_start, p.t0 - pre, a), min(next_end, p.t1 + post, b))
        out.append(align.Segment(quran.verses(p.surah, lo, hi), p.first - lo, True, band,
                                 (max(prev_start, p.t0 - PREFIX, a), band[1])))
    return out


def _align(em: np.ndarray, audio: np.ndarray, model, a: float, b: float, segments: list[align.Segment]):
    """Word timings of the passages between a and b (s), and their verses."""
    f0, f1 = int(a / align.FRAME_S), min(len(em), int(round(b / align.FRAME_S)))
    shift = lambda band: (band[0] - a, band[1] - a) if band else None
    segs = [replace(s, band=shift(s.band), prefix_band=shift(s.prefix_band)) for s in segments]
    verses = [v for seg in segs for v in seg.verses]
    part, sound = em[f0:f1], audio[f0 * 320:f1 * 320]
    occ = align.align_segments(part, model, segs)
    spans = _long_words(occ, verses, (f1 - f0) * align.FRAME_S)
    if spans:  # listened to again closely, and aligned again
        occ = align.align_segments(_relisten(part, sound, model, spans), model, segs)
    t = f0 * align.FRAME_S
    return [align.WordTiming(o.word, o.start + t, o.end + t, o.score) for o in occ if o.word.unit != "amin"], verses


def _pieces(passages: list[identify.Passage], audio: np.ndarray, duration: float):
    """[(start, end, [(passage number, the part of it heard there)])]: the whole recording, or,
    when it is too long to align at once, pieces of about PIECE_S cut at a quiet moment before a verse."""
    frames = duration / align.FRAME_S
    states = sum(2 * len(identify._letters(" ".join(v.align))) + 8 * len(v.align)
                 for p in passages for v in quran.verses(p.surah, max(1, p.first - 1),
                                                         min(quran.surah(p.surah)["verses"], p.last + 1)))
    if frames * states <= MAX_CELLS:
        return [(0.0, duration, list(enumerate(passages)))]
    # where a verse starts (heard by the tracker), and between passages
    starts = []
    for k, p in enumerate(passages):
        seen = set()
        for t, v in p.marks:
            if v > p.first and v not in seen:
                starts.append(t)
            seen.add(v)
        if k + 1 < len(passages):
            starts.append((p.t1 + passages[k + 1].t0) / 2)
    starts.sort()
    loud = segment.Loudness(audio)
    cuts, at = [0.0], 0.0
    while duration - at > 1.5 * PIECE_S:
        near = [t for t in starts if t > at + PIECE_S / 2]
        if not near:
            break
        t = min(near, key=lambda x: abs(x - at - PIECE_S))
        # the quietest moment just before it (the pause between two verses)
        i0, i1 = int(max(at, t - 2.5) * 100), int(t * 100) + 20
        i = i0 + int(np.argmin(np.convolve(loud.rel[i0:i1], np.ones(20) / 20, mode="same")))
        at = max(at + 1.0, i / 100)
        cuts.append(at)
    cuts.append(duration)
    out = []
    for a, b in zip(cuts, cuts[1:]):
        lo, hi = a - OVERLAP_S, b + OVERLAP_S
        parts = []
        for k, p in enumerate(passages):
            if p.t1 <= lo or p.t0 >= hi:
                continue
            heard = [v for t, v in p.marks if lo <= t < hi and v > 0]
            first = p.first if p.t0 >= lo or not heard else min(heard)
            last = p.last if p.t1 <= hi or not heard else max(heard)
            parts.append((k, replace(p, first=first, last=max(first, last), t0=max(p.t0, lo), t1=min(p.t1, hi))))
        out.append((a, b, parts))
    return out


def _stitch(left: list[align.WordTiming], right: list[align.WordTiming], cut: float) -> list[align.WordTiming]:
    """Two overlapping pieces, joined at a word both placed at the same moment (nearest the cut),
    else at the cut."""
    key = lambda o: (o.word.unit, o.word.verse_index, o.word.index, o.word.seg)
    at = {key(o): i for i, o in enumerate(left) if abs(o.start - cut) <= OVERLAP_S}
    best = None
    for j, r in enumerate(right):
        i = at.get(key(r))
        if i is not None and abs(left[i].start - r.start) < 0.15 and abs(left[i].end - r.end) < 0.3:
            if best is None or abs(r.start - cut) < abs(right[best[1]].start - cut):
                best = (i, j)
    if best:
        return left[:best[0]] + right[best[1]:]
    return [o for o in left if o.start < cut] + [o for o in right if o.start >= cut]


LONG_WORD_S = 3.0  # a word this long may hide a repeat the model did not hear...
LONG_LAST_WORD_S = 6.0  # ...or this long at the end of a verse (where the voice is held anyway)
SHORT_CHUNK_S, SHORT_CONTEXT_S = 2.0, 0.5  # short windows hear repeats better (but the rest less well)
SHORT_WEIGHT = 0.3  # share of the short windows in the mix


def _long_words(occ: list[align.WordTiming], verses: list[quran.Verse], duration: float) -> list[tuple[float, float]]:
    """Where a word lasts suspiciously long (with some audio around), merged."""
    spans = []
    for o in occ:
        w = o.word
        last = w.unit != "verse" or w.index + 1 == len(verses[w.verse_index].align)
        if o.end - o.start > (LONG_LAST_WORD_S if last else LONG_WORD_S):
            a, b = max(0.0, o.start - 2.0), min(duration, o.end + 2.0)
            if spans and a <= spans[-1][1]:
                spans[-1] = (spans[-1][0], max(spans[-1][1], b))
            else:
                spans.append((a, b))
    return spans


def _relisten(em: np.ndarray, audio: np.ndarray, model, spans: list[tuple[float, float]]) -> np.ndarray:
    """The model's letters on these spans, listening in short windows too: when a reciter
    says a verse twice in a row, the model, which knows the Quran's order, may not write
    the second time down with its usual windows, and that word then seems to last long."""
    em = em.copy()
    for a, b in spans:
        f0, f1 = int(a / align.FRAME_S), min(len(em), int(b / align.FRAME_S))
        short = model.emissions(audio[f0 * 320:f1 * 320], SHORT_CHUNK_S, SHORT_CONTEXT_S)
        n = min(len(short), f1 - f0)
        em[f0:f0 + n] = np.logaddexp(np.log(1 - SHORT_WEIGHT) + em[f0:f0 + n], np.log(SHORT_WEIGHT) + short[:n])
    return em


CUT_VERSE_WORDS = 4  # a verse this short, matched by the tracker at the start of a clip, is shown whole
CUT_VERSE_S = 8.0  # ...or, when its last word is heard, if the next verse starts this soon
CUT_HEARD_WORDS = 8  # ...and it is this short (one subtitle)


def _cut_verse(occ: list[align.WordTiming], verses: list[quran.Verse], first: identify.Passage,
               em: np.ndarray, model) -> list[align.WordTiming]:
    """A clip cut in the last words of a short verse: the model often hears too little of it
    to place its words, but the tracker matched it right at the start, or the letters heard
    before the next verse are its last word's. That verse is shown from the first frame until
    the next one starts (as a recording that stops mid-verse shows the whole verse). (Without
    letters, a held word cannot be told from a breath, noise or music.)"""
    w = occ[0].word if occ else None
    if not w or w.unit != "verse" or w.index != 0 or occ[0].start < 0.6:
        return occ
    after = verses[w.verse_index]
    if (after.surah, after.ayah) == (first.surah, first.first + 1) and first.t0 <= segment.CUT_START_S + 0.5:
        v = quran.verse(first.surah, first.first)
        if len(v.align) > CUT_VERSE_WORDS:
            return occ
    elif (after.surah, after.ayah) == (first.surah, first.first) and after.ayah > 1 and occ[0].start <= CUT_VERSE_S:
        v = quran.verse(after.surah, after.ayah - 1)
        codes, frames = identify.heard(em, model)
        end = occ[0].start - 0.3
        if not _fits(codes, frames, v.align[-1:], 0.0, end):
            return occ
        if len(v.align) > CUT_HEARD_WORDS:
            return occ
    else:
        return occ
    vi = next((i for i, x in enumerate(verses) if (x.surah, x.ayah) == (v.surah, v.ayah)), len(verses))
    if vi == len(verses):
        verses.append(v)
    t0, t1 = 0.0, max(0.1, occ[0].start - 0.3)
    step = (t1 - t0) / len(v.align)
    return [align.WordTiming(align.Word("verse", vi, i, text, [], w.seg), t0 + i * step, t0 + (i + 1) * step, 0.0)
            for i, text in enumerate(v.align)] + occ


CUT_WORD_S = 4.0  # a clip may start with this much of a word the aligner did not place


def _cut_word(occ: list[align.WordTiming], em: np.ndarray, audio: np.ndarray, model,
              opt: segment.Options) -> list[align.WordTiming]:
    """A clip cut inside a word: the model hears its end from the first frame, but too little
    of it for the aligner. The voice runs, without a pause, from the start into the first word
    placed (mid-verse): that word starts there, so the clip is seen as cut."""
    o = occ[0] if occ else None
    if not o or o.word.unit != "verse" or o.word.index == 0 or not segment.CUT_START_S < o.start <= CUT_WORD_S:
        return occ
    loud = segment.Loudness(audio)
    rel = loud.rel[:int(o.start * 100)]
    start = int(np.argmax(rel >= -opt.breath_depth_db))
    if rel[start] < -opt.breath_depth_db or start > 30:  # (voice within 0.3 s)
        return occ
    if loud.pause(start / 100, o.start, opt.breath_depth_db)[0] >= 0.3:
        return occ
    heard = em[start // 2:int(o.start / align.FRAME_S)].argmax(axis=1)
    if not np.any((heard != model.blank) & (heard != model.sep)):
        return occ
    return [replace(o, start=start / 100)] + occ[1:]


MISSED_START_S = 4.0  # the first word(s) of a passage the aligner missed may last this long
MISSED_START_FIT = -1.0  # from a word heard this well (not a stray one over something else)


def _missed_start(occ: list[align.WordTiming], verses: list[quran.Verse], em: np.ndarray, audio: np.ndarray,
                  model, opt: segment.Options) -> list[align.WordTiming]:
    """A passage placed from its second or third word: the first was held long ("yaaaa", the
    ghunna of "innaaa"), the model heard it as blank and the tracker found the passage only
    after it, too late for the aligner. The voice runs, without a pause, from a pause before
    into that word, and the letters heard there (if any) are those words: the passage starts
    there (segment shows the words missed). (Speech running into the verse has other letters.)"""
    loud = segment.Loudness(audio)
    codes, frames = identify.heard(em, model)
    quiet = loud.rel < -opt.breath_depth_db
    need = int(0.3 * 100)
    out = list(occ)
    for i, o in enumerate(out):
        if o.word.unit != "verse" or not 0 < o.word.index <= segment.MISSED_WORDS or o.score < MISSED_START_FIT:
            continue
        if i and out[i - 1].word.seg == o.word.seg:
            continue
        floor = int(max(out[i - 1].end if i else 0.0, o.start - MISSED_START_S) * 100)
        j, run = int(o.start * 100), 0
        while j > floor and run < need:
            j -= 1
            run = run + 1 if quiet[j] else 0
        if run < need:  # (no pause: the voice before is something else)
            continue
        onset = (j + run) / 100
        missed = verses[o.word.verse_index].align[:o.word.index]
        heard = np.count_nonzero((frames >= onset / align.FRAME_S) & (frames < o.start / align.FRAME_S))
        if o.start - onset >= 0.3 * o.word.index and (not heard or _fits(codes, frames, missed, onset, o.start)):
            out[i] = replace(o, start=onset)
    return out


TRAIL_S = 1.0  # quiet this long inside a word is a silence between passages (a stop on a doubled
# letter, or between the letters of "Alif Lam Ra", lasts up to 0.8 s)
SILENCE_DB = 30.0  # below the recording's speech level: quiet even in a long silence


def _trim_ends(occ: list[align.WordTiming], audio: np.ndarray, opt: segment.Options) -> list[align.WordTiming]:
    """A passage's last word ends where its voice stops, its first word starts where the voice
    starts: the aligner may stretch them over the silence between two passages (blank inside a
    word costs nothing, like silence), or over the other passage's sound. Such a word, with a
    long pause inside, keeps the first (last) stretch of voice it covers."""
    loud = segment.Loudness(audio)
    quiet = (loud.rel < -opt.breath_depth_db) | (loud.level < -SILENCE_DB)
    need = int(TRAIL_S * 100)
    out = list(occ)
    for i, o in enumerate(out):
        last = i + 1 == len(out) or out[i + 1].word.seg != o.word.seg
        first = i == 0 or out[i - 1].word.seg != o.word.seg
        if o.word.unit != "verse" or not (first or last):
            continue
        i0 = int(o.start * 100)
        q = quiet[i0:min(len(quiet), int(o.end * 100))]
        edges, j = [0], 0  # pieces of the word between pauses of `need` or more (in 10 ms)
        while j < len(q):
            k = j
            while k < len(q) and q[k]:
                k += 1
            if k - j >= need:
                edges += [j, k]
            j = max(k, j + 1)
        if len(edges) == 1:
            continue
        edges.append(len(q))
        ps = [(x, y) for x, y in zip(edges[::2], edges[1::2]) if np.count_nonzero(~q[x:y]) >= 10]  # (0.1 s of voice)
        if not ps:
            continue
        x, y = ps[-1] if first and not last else ps[0] if last and not first else max(ps, key=lambda p: p[1] - p[0])
        out[i] = replace(o, start=(i0 + x) / 100, end=(i0 + y) / 100 + align.FRAME_S)
    return out


FINISH_AFTER_S = 0.5  # the tracker heard the passage this long after its last word placed (or nothing follows)...
FINISH_TAIL_S = 0.4  # ...and the voice goes on this long after the last letter it heard
FINISH_STOP_S = 0.8  # a stop this long may come before the missing word (the doubled ḍ of "ad-daallin")


def _finish_verses(occ: list[align.WordTiming], verses: list[quran.Verse], passages: list[identify.Passage],
                   audio: np.ndarray, opt: segment.Options) -> list[align.WordTiming]:
    """The last word or two of a passage, held on a long madd (Al-Fatiha's "ad-daallin"): the
    model hears the madd as blank and its letters badly, so the aligner ends the passage before
    them (the silence after a passage is free). The tracker still heard that passage later on, or
    nothing follows it: those words are placed there, until the voice stops (the tracker's last
    letter may already be the next passage's), past a short stop before them."""
    duration = len(audio) / align.SR
    loud = segment.Loudness(audio)
    need = max(1, int(opt.breath_quiet_s * 100))

    def voice_start(t: float, limit: float) -> float | None:
        for i in range(int(t * 100), min(len(loud.rel), int(limit * 100))):
            if loud.rel[i] >= -opt.breath_depth_db:
                return i / 100
        return None

    def voice_end(t: float, limit: float) -> float:
        run = 0
        for i in range(int(t * 100), min(len(loud.rel), int(limit * 100))):
            run = run + 1 if loud.rel[i] < -opt.breath_depth_db else 0
            if run >= need:
                return (i - run + 1) / 100
        return limit

    out = list(occ)
    for k, p in enumerate(passages):
        i = max((j for j, o in enumerate(out) if o.word.seg == k and o.word.unit == "verse"), default=None)
        if i is None:
            continue
        o = out[i]
        v = verses[o.word.verse_index]
        missing = len(v.align) - o.word.index - 1
        if not 0 < missing <= segment.MISSED_WORDS or (v.surah, v.ayah) != (p.surah, p.last):
            continue
        later = [x.start for x in out[i + 1:] if x.start > o.end]
        if p.t1 < o.end + FINISH_AFTER_S and later:
            continue
        limit = min(duration, p.t1 + FINISH_TAIL_S if later else duration, *later)
        t0 = o.end + align.FRAME_S
        t1 = voice_end(t0, limit)
        if t1 - t0 < 0.2 * missing:  # a stop before the word: it starts when the voice is back
            t0 = voice_start(t1, min(limit, t1 + FINISH_STOP_S))
            if t0 is None:
                continue
            t1 = voice_end(t0, limit)
        if t1 - t0 < 0.2 * missing:
            continue
        rest = v.align[o.word.index + 1:]
        sizes = [max(1, len(quran.skeleton(w))) for w in rest]
        at, added = t0, []
        for n, (text, size) in enumerate(zip(rest, sizes)):
            end = t1 if n + 1 == len(rest) else at + (t1 - t0) * size / sum(sizes)
            added.append(align.WordTiming(align.Word("verse", o.word.verse_index, o.word.index + 1 + n, text, [],
                                                     o.word.seg), at, end, 0.0))
            at = end
        out[i + 1:i + 1] = added
    return out


STRAY_FIT = 0.45  # an isolated stretch of words must match this share of the letters heard there
STRAY_SCORE = -1.5  # a word or two heard this badly (mean log-prob) are checked so too
STRAY_FIT_WEAK = 0.7  # (isolated as well: most of their letters)
STRAY_GAP_S = 0.5  # a passage's weak first words this far from the next are checked so too


def _fatiha_basmala(occ: list[align.WordTiming], verses: list[quran.Verse]) -> list[align.WordTiming]:
    """The basmala before Al-Fatiha is its first verse: placed as the basmala said before a
    surah (the same words), followed by 1:2, it is shown as 1:1."""
    out = list(occ)
    for i, o in enumerate(out):
        nxt = out[i + 1] if i + 1 < len(out) else None
        if o.word.unit != "basmala" or not nxt or nxt.word.unit != "verse" or nxt.word.index != 0 or nxt.word.seg != o.word.seg:
            continue
        if (verses[nxt.word.verse_index].surah, verses[nxt.word.verse_index].ayah) != (1, 2):
            continue
        v = quran.verse(1, 1)
        vi = next((k for k, x in enumerate(verses) if (x.surah, x.ayah) == (1, 1)), len(verses))
        if vi == len(verses):
            verses.append(v)
        j = i
        while j >= 0 and out[j].word.unit == "basmala" and out[j].word.seg == o.word.seg:
            w = out[j].word
            out[j] = replace(out[j], word=replace(w, unit="verse", verse_index=vi, text=v.align[w.index]))
            j -= 1
    return out


def _fits(codes: np.ndarray, frames: np.ndarray, texts: list[str], t0: float, t1: float, share: float = 0.0) -> bool:
    """The letters heard between t0 and t1 (s; identify.heard) match these words (this share of
    them, STRAY_FIT by default)."""
    _, table = identify._codes()
    text = np.array([table[c] for w in texts for c in quran.skeleton(w) if c in table], dtype=np.int16)
    heard = codes[(frames >= t0 / align.FRAME_S - 3) & (frames <= t1 / align.FRAME_S + 3)]
    matched = identify._fit(heard, text)[0] if len(heard) and len(text) else 0
    return matched >= (share or STRAY_FIT) * max(len(text), len(heard))


def _drop_strays(occ: list[align.WordTiming], verses: list[quran.Verse], em: np.ndarray, model) -> list[align.WordTiming]:
    """The aligner may put a few words of a verse on speech or noise next to a passage (cheaper
    for it than saying "not the Quran"). Such a stretch is isolated: it neither follows the
    recitation before it nor leads into the one after it. It is kept only if the letters
    heard there match it."""
    runs: list[list[align.WordTiming]] = []
    for o in occ:  # stretches of words read in a row
        w, last = o.word, runs[-1][-1].word if runs else None
        if last and (w.unit, w.verse_index, w.seg) == (last.unit, last.verse_index, last.seg) and w.index == last.index + 1:
            runs[-1].append(o)
        else:
            runs.append([o])

    def ends_verse(r):
        w = r[-1].word
        return w.unit != "verse" or w.index + 1 == len(verses[w.verse_index].align)

    def follows(a, b):  # b reads on from a
        x, y = a[-1].word, b[0].word
        if x.seg != y.seg:
            return False
        if y.unit != "verse":
            return False
        if x.unit != "verse":  # after the basmala: a verse start
            return y.index == 0
        vx, vy = verses[x.verse_index], verses[y.verse_index]
        return (y.verse_index == x.verse_index and y.index == x.index + 1) or \
            ((vy.surah, vy.ayah) == (vx.surah, vx.ayah + 1) and y.index == 0 and ends_verse(a))

    codes, frames = identify.heard(em, model)
    fits = lambda r, share=0.0: _fits(codes, frames, [o.word.text for o in r], r[0].start, r[-1].end, share)

    weak = lambda r: len(r) <= segment.MISSED_WORDS and np.mean([o.score for o in r]) < STRAY_SCORE  # (a few words)
    out = []
    for k, r in enumerate(runs):
        prev, nxt = (runs[k - 1] if k else None), (runs[k + 1] if k + 1 < len(runs) else None)
        linked = (follows(prev, r) if prev and prev[-1].word.seg == r[0].word.seg else r[0].word.index == 0) or \
            (follows(r, nxt) if nxt and nxt[0].word.seg == r[-1].word.seg else ends_verse(r))
        if (not linked or weak(r)) and not fits(r, STRAY_FIT_WEAK if not linked and weak(r) else 0.0):
            continue
        out += r
    # a passage's first word or two put, barely heard, on what comes before it (speech), apart
    # from the rest: left out (segment shows a verse's first words the aligner missed). (Next to
    # the rest, a weak first word is more often the verse, half on what comes before it.)
    for i in range(len(out) - 1, -1, -1):
        first = i == 0 or out[i - 1].word.seg != out[i].word.seg
        if not first or out[i].word.unit != "verse":
            continue
        n = 0
        while (i + n + 1 < len(out) and n < segment.MISSED_WORDS and out[i + n + 1].word.seg == out[i].word.seg
               and out[i + n + 1].word.verse_index == out[i].word.verse_index and weak([out[i + n]])):
            n += 1
        if n and out[i + n].start - out[i + n - 1].end >= STRAY_GAP_S and not fits(out[i:i + n]):
            del out[i:i + n]
    return out
