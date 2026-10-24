"""Find when every word of the expected verses is recited.

A wav2vec2 CTC model fine-tuned on Quran recitation gives, for every 20 ms
frame, the probability of each Arabic character. Because we already know the
text (surah + starting verse), we don't need speech recognition: we only need
to find the best path of the known text through those probabilities (forced
alignment). That is far more precise than any auto-captioner.

Real recordings are messier than a clean verse list, so the path runs through
a graph rather than a straight line:
  * optional Isti'adha / Basmala before the first verse
  * free start/end: audio before or after the recitation is absorbed by a
    "filler" state, and the recording may stop mid-verse
  * repeats: the reciter may go back to an earlier word and recite again
  * several passages one after the other (a prayer: Al-Fatiha, then another
    surah), each with its own optional Isti'adha / Basmala, with silence or
    anything else between them; each passage's words may be placed only around
    when the tracker (identify.track) heard it
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

import numba
import numpy as np

from . import quran

MODEL_ID = "rabah2026/wav2vec2-large-xlsr-53-arabic-quran-v_final"
SR = 16000

# Log-domain penalties (natural log). Tuned on real recitations.
FILLER_PENALTY = 1.2  # per frame, below the model's best guess: audio that is not the expected text
START_OTHER_VERSE = 3.0  # start at another verse than the one given (plus 0.5 per verse away)
START_MID_VERSE = 8.0  # start somewhere inside a verse (clip cut mid-verse)
LOOKBACK_VERSES = 3  # verses before the given start that are also considered
SKIP_PREFIX = 0.0  # Isti'adha / Basmala are optional
JUMP_TO_VERSE_START = 6.0  # reciter repeats from the start of a verse
JUMP_TO_WORD = 14.0  # reciter repeats from some earlier word
JUMP_WINDOW_VERSES = 1  # how far back a repeat may go (in verses)
SKIP_SEGMENT = 30.0  # a passage the tracker found is not aligned at all
GAP_BLANK = 0.2  # between passages, a frame the model hears as blank counts as garbage this much below it


@dataclass
class Word:
    unit: str  # "istiadha", "basmala" or "verse"
    verse_index: int  # index into the verse list (-1 for prefixes)
    index: int  # word index inside its unit
    text: str
    tokens: list[int] = field(default_factory=list)
    seg: int = 0  # passage (Segment) it belongs to


@dataclass
class Segment:
    """One passage to align: the verses it may hold, the one expected first (index in
    verses), and the time (s) where its words may be placed (None: anywhere)."""
    verses: list[quran.Verse]
    hint: int = 0
    prefixes: bool = True
    band: tuple[float, float] | None = None
    prefix_band: tuple[float, float] | None = None


@dataclass
class WordTiming:
    word: Word
    start: float  # first character onset (s)
    end: float  # last character (s)
    score: float  # mean log-prob of its characters (confidence)


class Model:
    def __init__(self, device: str | None = None):
        import certifi
        import torch
        from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

        os.environ.setdefault("SSL_CERT_FILE", certifi.where())
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        self.device = device
        self.processor = Wav2Vec2Processor.from_pretrained(MODEL_ID)
        self.model = Wav2Vec2ForCTC.from_pretrained(MODEL_ID).eval().to(device)
        vocab = self.processor.tokenizer.get_vocab()
        self.vocab = vocab
        self.blank = vocab["<pad>"]
        self.sep = vocab["|"]

    def tokens(self, word: str) -> list[int]:
        return [self.vocab[c] for c in word if c in self.vocab and c != "|"]

    def _pass(self, audio: np.ndarray, starts: list[int], chunk: int, ctx: int, n_frames: int) -> np.ndarray:
        import torch

        hop = 320  # samples per output frame
        out = np.full((n_frames, len(self.vocab)), -1e4, dtype=np.float32)
        out[:, self.blank] = 0.0
        for i, pos in enumerate(starts):
            stop = starts[i + 1] if i + 1 < len(starts) else len(audio)
            a0, a1 = max(0, pos - ctx), min(len(audio), stop + ctx)
            x = audio[a0:a1]
            if len(x) < hop * 2:
                continue
            with torch.inference_mode():
                iv = self.processor(x, sampling_rate=SR, return_tensors="pt").input_values.to(self.device)
                lp = torch.log_softmax(self.model(iv).logits[0].float(), dim=-1).cpu().numpy()
            f0 = (pos - a0) // hop
            keep_from, keep_to = pos // hop, min(n_frames, stop // hop)
            take = lp[f0: f0 + keep_to - keep_from]
            out[keep_from: keep_from + len(take)] = take
        return out

    def emissions(self, audio: np.ndarray, chunk_s: float = 4.0, context_s: float = 1.0,
                  progress=None) -> np.ndarray:
        """Per-frame log-probabilities, shape (frames, vocab).

        The model was fine-tuned on the Quran in order and, given a long
        window, it "expects" the next verse: when a reciter repeats a verse it
        can go deaf to the repeat. Short windows (4 s + 1 s of context on each
        side) keep it listening to what is actually recited. The audio is cut
        twice, the second time shifted by half a window, and the two passes
        are averaged so every moment is heard well inside a window."""
        hop = 320
        n_frames = len(audio) // hop
        chunk, ctx = int(chunk_s * SR), int(context_s * SR)
        a = list(range(0, len(audio), chunk))
        b = [0] + list(range(chunk // 2, len(audio), chunk))
        p1 = self._pass(audio, a, chunk, ctx, n_frames)
        if progress:
            progress(0.5)
        p2 = self._pass(audio, b, chunk, ctx, n_frames)
        return (np.logaddexp(p1, p2) - np.log(2.0)).astype(np.float32)


@lru_cache(maxsize=1)
def get_model() -> Model:
    return Model()


# ---------------------------------------------------------------- graph

def build_words(model: Model, verses: list[quran.Verse], prefixes: bool = True, seg: int = 0,
                offset: int = 0) -> list[Word]:
    words: list[Word] = []
    if prefixes:
        for unit, text in (("istiadha", quran.ISTIADHA), ("basmala", quran.BASMALA)):
            for i, w in enumerate(text.split()):
                words.append(Word(unit, -1, i, w, model.tokens(w), seg))
    for vi, v in enumerate(verses):
        for i, w in enumerate(v.align):
            words.append(Word("verse", offset + vi, i, w, model.tokens(w) or [model.sep], seg))
    return words


def _build_graph(words: list[Word], blank: int, hints: list[int]):
    """States: 0 = filler-start, 1 = filler-end, 2 = end-blank, then a filler and a
    blank between each passage and the next, then for each word [blank, c1, blank, c2,
    ..., blank, cn]. hints: per passage, the verse index expected first.

    Returns token-per-state (-1 blank, -2 filler, -3 filler between passages), the CSR predecessor lists
    with penalties, the word owning every state, whether a state is a char,
    and the allowed final states."""
    n_seg = len(hints)
    tok, owner, is_char = [-2, -2, -1], [-1, -1, -1], [False, False, False]
    gaps, rests = [], []  # before passage k (k >= 1): a filler, and a blank (the silence after a passage:
    for _ in range(n_seg - 1):  # without it the last letter would stretch over it)
        gaps.append(len(tok))
        rests.append(len(tok) + 1)
        tok += [-3, -1]
        owner += [-1, -1]
        is_char += [False, False]
    sources = [[0]] + [[g, r] for g, r in zip(gaps, rests)]  # where each passage is entered from
    first, last = [], []
    for wi, w in enumerate(words):
        first.append(len(tok))
        for k, t in enumerate(w.tokens):
            tok += [-1, t]
            owner += [wi, wi]
            is_char += [False, True]
        last.append(len(tok) - 1)
    S = len(tok)
    preds: list[list[tuple[int, float]]] = [[] for _ in range(S)]
    preds[0].append((0, 0.0))
    preds[1] += [(1, 0.0), (2, 0.0)]
    preds[2].append((2, 0.0))
    for k, (g, r) in enumerate(zip(gaps, rests)):
        preds[g] += [(g, 0.0), (r, 0.0), (sources[k][0], SKIP_SEGMENT)]  # (passage k not there at all)
        preds[r].append((r, 0.0))
    preds[1].append((sources[-1][0], SKIP_SEGMENT))

    def enter(wi: int, src: int, pen: float):
        b, c = first[wi], first[wi] + 1
        preds[b].append((src, pen))
        src_tok = tok[src]
        if src_tok < 0 or src_tok != tok[c]:  # need a blank between repeated letters
            preds[c].append((src, pen))

    for wi, w in enumerate(words):
        b0 = first[wi]
        # inside the word: standard CTC topology
        for s in range(b0, last[wi] + 1):
            preds[s].append((s, 0.0))
            if s > b0:
                preds[s].append((s - 1, 0.0))
            if is_char[s] and s - 2 > b0 and tok[s - 2] != tok[s]:
                preds[s].append((s - 2, 0.0))
        # the end states can be reached from every word end (recording may stop mid-verse),
        # and the next passage from every word end of this one
        preds[1].append((last[wi], 0.0))
        preds[2].append((last[wi], 0.0))
        if w.seg + 1 < n_seg:
            preds[gaps[w.seg]].append((last[wi], 0.0))
            preds[rests[w.seg]].append((last[wi], 0.0))

    for seg in range(n_seg):
        hint = hints[seg]
        unit_words: dict[str, list[int]] = {}
        for wi, w in enumerate(words):
            if w.seg == seg:
                unit_words.setdefault(w.unit, []).append(wi)
        verse_words = unit_words.get("verse", [])
        ist, bas = unit_words.get("istiadha", []), unit_words.get("basmala", [])
        v0 = words[verse_words[0]].verse_index if verse_words else 0  # verse indexes are global

        # sequential flow inside each unit / between verses
        for a, b in zip(verse_words, verse_words[1:]):
            enter(b, last[a], 0.0)
        for unit in (ist, bas):
            for a, b in zip(unit, unit[1:]):
                enter(b, last[a], 0.0)
        # prefixes: [istiadha] -> [basmala] -> verses
        if ist:
            for src0 in sources[seg]:
                enter(ist[0], src0, SKIP_PREFIX)
            if bas:
                enter(bas[0], last[ist[-1]], 0.0)
        if bas:
            for src0 in sources[seg]:
                enter(bas[0], src0, SKIP_PREFIX)
        # start: the given verse (free), the start of another verse (small
        # penalty, the user may be off by a few verses), or mid-verse (clip cut)
        for wi in verse_words:
            w = words[wi]
            if w.index == 0:
                d = w.verse_index - v0 - hint
                pen = 0.0 if d == 0 else START_OTHER_VERSE + 0.5 * abs(d)
                for src0 in sources[seg]:
                    enter(wi, src0, pen)
                for unit in (ist, bas):  # after Isti'adha / Basmala
                    if unit:
                        enter(wi, last[unit[-1]], pen)
            else:
                for src0 in sources[seg]:
                    enter(wi, src0, START_MID_VERSE)
        # repeats: from any word end back to an earlier word of this or the previous verse
        for ai in verse_words:
            va = words[ai].verse_index
            for bi in verse_words:
                if bi > ai:
                    break
                vb = words[bi].verse_index
                if va - vb > JUMP_WINDOW_VERSES:
                    continue
                pen = JUMP_TO_VERSE_START if words[bi].index == 0 else JUMP_TO_WORD
                enter(bi, last[ai], pen)

    # CSR
    ptr = np.zeros(S + 1, dtype=np.int64)
    for s in range(S):
        ptr[s + 1] = ptr[s] + len(preds[s])
    src = np.empty(ptr[-1], dtype=np.int64)
    pen = np.empty(ptr[-1], dtype=np.float32)
    for s in range(S):
        for k, (p, q) in enumerate(preds[s]):
            src[ptr[s] + k], pen[ptr[s] + k] = p, q
    finals = np.array([1, 2] + last, dtype=np.int64)
    return (np.array(tok, dtype=np.int64), ptr, src, pen, np.array(owner), np.array(is_char), finals)


@numba.njit(cache=True)
def _emit(em, t, k, blank, sep, filler):
    if k == -2:  # garbage: whatever the audio is, a fixed amount below the best guess
        return filler[t]
    if k == -3:  # between passages: garbage, or a blank a little below it (speech that is not a
        # passage is mostly blank for the model too: a free blank would swallow a basmala)
        return max(filler[t], max(em[t, blank], em[t, sep]) - GAP_BLANK)
    if k == -1:  # blank also absorbs the word separator
        a, b = em[t, blank], em[t, sep]
        m = max(a, b)
        return m + np.log(np.exp(a - m) + np.exp(b - m))
    return em[t, k]


@numba.njit(cache=True)
def _viterbi(em, tok, ptr, src, pen, blank, sep, filler, finals, lo, hi):
    # lo/hi: the frames where each state may be (its passage's time)
    T, S = em.shape[0], tok.shape[0]
    NEG = -1e30
    score = np.full(S, NEG, dtype=np.float64)
    new = np.empty(S, dtype=np.float64)
    back = np.zeros((T, S), dtype=np.uint16)  # index into this state's predecessor list

    # t = 0: the filler, or any state the filler leads to
    score[0] = _emit(em, 0, tok[0], blank, sep, filler)
    for s in range(1, S):
        if lo[s] > 0:
            continue
        for k in range(ptr[s], ptr[s + 1]):
            if src[k] == 0:
                v = _emit(em, 0, tok[s], blank, sep, filler) - pen[k]
                if v > score[s]:
                    score[s] = v
                    back[0, s] = k - ptr[s]
    for t in range(1, T):
        for s in range(S):
            if t < lo[s] or t > hi[s]:
                new[s] = NEG
                back[t, s] = 0
                continue
            best, arg = NEG, 0
            for k in range(ptr[s], ptr[s + 1]):
                v = score[src[k]] - pen[k]
                if v > best:
                    best, arg = v, k - ptr[s]
            new[s] = best + _emit(em, t, tok[s], blank, sep, filler)
            back[t, s] = arg
        for s in range(S):
            score[s] = new[s]
    best, end = NEG, 0
    for s in finals:
        if score[s] > best:
            best, end = score[s], s
    path = np.empty(T, dtype=np.int64)
    s = end
    for t in range(T - 1, -1, -1):
        path[t] = s
        if t > 0:
            s = src[ptr[s] + back[t, s]]
    return path, best


FRAME_S = 0.02


def align(em: np.ndarray, model: Model, verses: list[quran.Verse], prefixes: bool = True,
          hint: int = 0) -> list[WordTiming]:
    """Word occurrences in the order they are recited (repeats included).
    `hint` is the index in `verses` of the verse the user said comes first."""
    return align_segments(em, model, [Segment(verses, hint, prefixes)])


def align_segments(em: np.ndarray, model: Model, segments: list[Segment]) -> list[WordTiming]:
    """Several passages one after the other. Word.verse_index counts in all the
    passages' verses put end to end; Word.seg tells the passage."""
    words: list[Word] = []
    offset = 0
    for k, seg in enumerate(segments):
        words += build_words(model, seg.verses, seg.prefixes, k, offset)
        offset += len(seg.verses)
    tok, ptr, src, pen, owner, is_char, finals = _build_graph(words, model.blank, [seg.hint for seg in segments])
    T = len(em)
    lo, hi = np.zeros(len(tok), dtype=np.int64), np.full(len(tok), T, dtype=np.int64)
    for s, wi in enumerate(owner):
        if wi < 0:
            continue
        seg = segments[words[wi].seg]
        band = seg.band if words[wi].unit == "verse" else (seg.prefix_band or seg.band)
        if band:
            lo[s], hi[s] = max(0, int(band[0] / FRAME_S)), min(T, int(np.ceil(band[1] / FRAME_S)))
    filler = em.max(axis=1).astype(np.float64) - FILLER_PENALTY
    if np.diff(ptr).max() >= 65535:
        raise ValueError("Too many verses for one alignment; choose a shorter verse range")
    path, _ = _viterbi(em.astype(np.float64), tok, ptr, src, pen, model.blank, model.sep, filler, finals, lo, hi)

    out: list[WordTiming] = []
    cur, chars, prev_state = -1, [], -1
    for t, s in enumerate(path):
        w = owner[s]
        # states inside a word only move forward, so going back to a lower
        # state of the same word means the reciter repeated it
        if w != cur or s < prev_state:
            if cur >= 0 and chars:
                out.append(_timing(words[cur], chars, em, tok))
            cur, chars = w, []
        if w >= 0 and is_char[s]:
            chars.append((t, s))
        prev_state = s
    if cur >= 0 and chars:
        out.append(_timing(words[cur], chars, em, tok))
    return out


def _timing(word: Word, chars: list[tuple[int, int]], em: np.ndarray, tok: np.ndarray) -> WordTiming:
    frames = [t for t, _ in chars]
    score = float(np.mean([em[t, tok[s]] for t, s in chars]))
    return WordTiming(word, frames[0] * FRAME_S, (frames[-1] + 1) * FRAME_S, score)


def max_verses_for(duration_s: float, verses_available: int) -> int:
    """How many verses to offer the aligner when the end verse is unknown.
    Generous on purpose: unused verses cost nothing but a little time."""
    return max(3, min(verses_available, int(duration_s * 0.6) + 5))
