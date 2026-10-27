"""The Warsh reading: its text laid out on the Hafs verses, and its numbers.

Run: uv run python -m pytest -q
"""

import pytest

from tilawa import quran, segment, warsh


@pytest.fixture
def in_warsh():
    quran.use_reading("warsh")
    yield
    quran.use_reading("hafs")


def test_every_hafs_verse_has_its_warsh_text(in_warsh):
    ends = 0
    for s in range(1, 115):
        for a in range(1, quran.surah(s)["verses"] + 1):
            v = quran.verse(s, a)
            m = v.align_to_display
            assert v.display and v.align and len(v.numbers) == len(v.align)
            assert m[0] == 0 and m[-1] == len(v.display) and all(m[i] <= m[i + 1] for i in range(len(m) - 1))
            ends += len(v.ends)
        assert quran.verse_count(s) == warsh.verse_count(s)
    assert ends == 6214  # every Warsh verse ends once


def test_warsh_numbers_its_verses_its_own_way(in_warsh):
    assert quran.verse(1, 1).number() == 0 and quran.verse(1, 1).ends == {}  # Al-Fatiha's basmala: not a verse
    assert quran.verse(1, 2).ends == {4: 1}
    v = quran.verse(1, 7)  # two Warsh verses
    assert v.ends == {4: 6, 9: 7} and v.label() == "6–7"
    assert quran.verse(2, 1).ends == {} and quran.verse(2, 2).number() == 1  # Alif Lam Mim with the next
    assert quran.key_of(2, 1) == (2, 1) and quran.key_of(2, 1, end=True) == (2, 2) and quran.key_of(1, 1) == (1, 2)
    assert quran.verse_count(2) == 285


def test_warsh_text_and_what_the_model_reads(in_warsh):
    assert quran.verse(1, 4).display_text().split()[0] == "مَلِكِ" and len(quran.verse(1, 4).display) == 3
    assert quran.verse(1, 4).align[0] == "مَلِكِ"  # not maaliki
    assert "يُومِنُونَ" in quran.verse(2, 4).align  # the hamza eased
    assert quran.verse(23, 1).align[:2] == ["قَدَ", "افْلَحَ"]  # its vowel moved onto the word before
    assert quran.verse(2, 1).align == ["الم"]  # spelled letters, as the model knows them
    assert "هُوَ" not in quran.verse(57, 24).align  # Warsh reads it without
    quran.use_reading("hafs")
    assert "هُوَ" in quran.verse(57, 24).align and quran.verse(1, 7).ends == {9: 7}


def test_warsh_display_uses_the_usual_codepoints(in_warsh):
    text = quran.verse(2, 7).display_text() + quran.verse(2, 26).display_text()
    assert not set("ےٖٗٞ‏") & set(text)
    assert quran.basmala_uthmani().startswith("بِسْمِ")


def test_warsh_phonetic():
    assert warsh.spoken("مَلِكِ") == "مَلِكِ"
    assert warsh.spoken("اِ۬لدِّينِۖ") == "الدِّينِ"
    assert warsh.spoken("اِنَّ", starts_verse=True) == "إِنَّ" and warsh.spoken("اِنَّ") == "انَّ"
    assert warsh.spoken("اَ۬لصَّلَوٰةَ") == "الصَّلَاةَ"


def test_subtitles_cut_where_a_warsh_verse_ends(in_warsh):
    import numpy as np

    from tilawa import align

    v = quran.verse(1, 7)
    occ = [align.WordTiming(align.Word("verse", 0, k, w), 0.5 * k, 0.5 * k + 0.4, 0.0) for k, w in enumerate(v.align)]
    blocks = segment.build_blocks(occ, [v], np.zeros(16000 * 6, np.float32), 6.0)
    assert [(b.a0, b.a1) for b in blocks] == [(0, 4), (4, 9)]
