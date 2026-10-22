"""Formats, languages and finding the recited passage (no model, no video)."""

import numpy as np

from tilawa import identify, media, quran, render, segment


def test_output_sizes_per_format():
    info = media.VideoInfo(path=None, width=1080, height=1920, fps=30, fps_str="30/1", duration=10, vcodec="h264",
                           pix_fmt="yuv420p", bit_depth=8, color_primaries=None, color_transfer=None, color_space=None,
                           color_range=None, acodec="aac", asample_rate=48000, achannels=2)
    opt = render.RenderOptions
    assert render.output_size(info, opt(size="auto"), "9:16") == (1080, 1920)  # native
    assert render.output_size(info, opt(size="auto"), "16:9") == (1920, 1080)
    assert render.output_size(info, opt(size="4k"), "16:9") == (3840, 2160)
    assert render.output_size(info, opt(size="4k"), "4:5") == (2160, 2700)
    assert render.output_size(info, opt(size="2160x3840"), "9:16") == (2160, 3840)  # old projects


def test_titles_follow_the_language():
    assert render.surah_title(1, "fr") == "SOURATE AL FATIHAH"
    assert render.surah_title(1, "en") == "SURAH AL FATIHAH"
    assert render.surah_title(1, "ur").startswith("سورة")


def test_every_language_has_every_verse():
    for code, (_, file, _, _) in quran.LANGS.items():
        if file:
            assert len(quran.translation_table(code)) == 6236, code


def test_retranslate_keeps_the_cuts():
    v = quran.verse(23, 89)
    blocks = [segment.Block("verse", 23, 89, 0, 2, 0, 1, "", "", ""), segment.Block("verse", 23, 89, 2, 5, 1, 2, "", "", "")]
    segment.retranslate(blocks, "en")
    assert blocks[0].fr == 'They will say, "[All belongs] to Allah."'
    assert blocks[1].fr.startswith("Say,")
    assert len(v.align) == 5


class _FakeModel:
    """Just the vocabulary of the recitation model."""
    def __init__(self, letters):
        self.vocab = {"<pad>": 0, "|": 1, **{c: i + 2 for i, c in enumerate(sorted(letters))}}
        self.blank = 0


def _emissions_of(text, model):
    """What the model would output for a perfect recitation of `text`."""
    frames = []
    for ch in text.replace(" ", "|"):
        if ch in model.vocab:
            frames += [model.vocab[ch], model.blank]
    em = np.full((len(frames), len(model.vocab)), -10.0)
    em[np.arange(len(frames)), frames] = 0
    return em


def test_identify_finds_surah_and_verses():
    align = quran._sources()[1]
    model = _FakeModel({c for t in align.values() for c in t if c != " "})
    heard = " ".join(align[(67, a)] for a in range(3, 7))  # Al-Mulk 3-6
    best = identify.identify(_emissions_of(heard, model), model)[0]
    assert (best.surah, best.first, best.last) == (67, 3, 6)
    # starting in the middle of a verse still points to it
    heard = " ".join(align[(18, 10)].split()[3:] + [align[(18, 11)], align[(18, 12)]])
    best = identify.identify(_emissions_of(heard, model), model)[0]
    assert (best.surah, best.first, best.last) == (18, 10, 12)


def test_imported_font_names_cannot_inject_css(tmp_path):
    import json
    from tilawa.library import Library

    lib = Library(tmp_path)
    lib.fonts_dir.mkdir()
    (lib.fonts_dir / "fonts.json").write_text(json.dumps([
        {"family": 'Evil"; } body { background: url(x)', "files": [["a.ttf", "400"]], "script": "latin"},
        {"family": "Good Font", "files": [["good.ttf", "400"]], "script": "latin"},
        {"family": "Bad File", "files": [['x"); }', "400"]], "script": "latin"}]))
    assert [f["family"] for f in lib.user_fonts()] == ["Good Font"]
