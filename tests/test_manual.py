"""Subtitles written by hand in the timeline: kept as typed, filled with a verse."""

from pathlib import Path

from tilawa import project, quran, segment


def _text(start, end, fr="", ar="", tr=""):
    return segment.Block("text", 0, 0, 0, 0, start, end, ar, fr, tr, voice_start=start, voice_end=end)


def test_hand_written_text_stays_through_language_and_translit_changes():
    b = _text(1, 3, "Ma phrase", "كلام", "kalam")
    v = segment.Block("verse", 103, 1, 0, 1, 3, 5, "", "", "")
    segment.retranslate([b, v], "en")
    segment.rephonetize([b, v], "academic")
    assert (b.fr, b.ar, b.tr) == ("Ma phrase", "كلام", "kalam")
    assert v.fr and v.tr  # the verse after it is still translated


def test_two_hand_written_subtitles_merge_their_texts():
    blocks = [_text(0, 2, "un", "أ", "a"), _text(2, 4, "deux", "ب", "b")]
    segment.merge_blocks(blocks, 0)
    assert len(blocks) == 1 and (blocks[0].fr, blocks[0].ar, blocks[0].tr, blocks[0].end) == ("un deux", "أ ب", "a b", 4)


def _project(reading="hafs"):
    quran.use_reading(reading)
    return project.Project(folder=Path("."), video="", surah=1, first_verse=1, lang="fr", reading=reading)


def test_filled_with_a_verse_as_the_reading_numbers_it():
    d = project.filled(_project(), "verse", 103, 2)
    assert (d["kind"], d["surah"], d["ayah"], d["a0"], d["a1"], d["num"], d["ends_verse"]) == ("verse", 103, 2, 0, 4, 2, 2)
    assert d["ar"] and d["fr"] and d["tr"]
    # Warsh: verse 7 of Al-Fatiha is the end of Hafs 1:7, with its half of the translation
    d = project.filled(_project("warsh"), "verse", 1, 7)
    assert (d["ayah"], d["num"], d["a0"] > 0, d["a1"]) == (7, 7, True, len(quran.verse(1, 7).align))
    assert d["fr"].startswith("non pas")
    quran.use_reading("hafs")


def test_filled_with_the_basmala_or_the_istiadha():
    p = _project()
    assert project.filled(p, "basmala")["fr"].startswith("Au nom d'Allah")
    assert project.filled(p, "istiadha")["tr"]
