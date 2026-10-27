"""Fast checks of the text logic (no model, no video needed).

Run: uv run python -m pytest -q
"""

from tilawa import quran, segment


def test_every_verse_maps_alignment_words_to_display_words():
    for s in range(1, 115):
        for a in range(1, quran.surah(s)["verses"] + 1):
            v = quran.verse(s, a)
            m = v.align_to_display
            assert m[0] == 0 and m[-1] == len(v.display)
            assert all(m[i] <= m[i + 1] for i in range(len(m) - 1))


def test_basmala_is_not_part_of_first_verses():
    assert quran.verse(2, 1).display_text() == "الٓمٓ"
    assert quran.verse(1, 1).display_text().startswith("بِسْمِ")


def test_split_words_differ_between_texts():
    v = quran.verse(2, 21)  # "يَا أَيُّهَا" (2 words) vs "يَـٰٓأَيُّهَا" (1 word)
    assert v.align_to_display[:3] == [0, 0, 1]
    assert v.display_text(v.align_to_display[0], v.align_to_display[2]) == v.display[0].text


def test_pause_marks_kept_inside_and_dropped_at_cut():
    v = quran.verse(23, 91)
    assert "ۚ" in v.display_text()
    assert not v.display_text(0, 10).endswith("ۚ")


def test_translit_clean():
    assert quran.verse(23, 84).translit_text(0, 8) == "Qul limani alardu waman feeha in kuntum taAAlamoona"


def _split(s, a, bounds):
    v = quran.verse(s, a)
    total = segment._arabic_weight(v, 0, len(v.align))
    return segment.split_french(v.french, [segment._arabic_weight(v, 0, b) / total for b in bounds],
                                [v.align[b] for b in bounds])


def test_french_split_matches_hand_made_video():
    # the cuts made by hand in the reference video (Al-Mu'minun 88, 89, 91)
    assert _split(23, 88, [8]) == [
        "Dis: «Qui détient dans sa main la royauté absolue de toute chose, et qui protège",
        "et n'a pas besoin d'être protégé? [Dites], si vous le savez!»"]
    assert _split(23, 89, [2]) == [
        "Ils diront: «Allah».",
        "Dis: «Comment donc se fait-il que vous soyez ensorcelés?» [au point de ne pas croire en Lui]."]
    assert _split(23, 91, [10, 16, 20]) == [
        "Allah ne S'est point attribué d'enfant et il n'existe point de divinité avec Lui;",
        "sinon, chaque divinité s'en irait avec ce qu'elle a créé,",
        "et certaines seraient supérieures aux autres.",
        "(Gloire et pureté) à Allah! Il est Supérieur à tout ce qu'ils décrivent."]


def _verse_block(surah, ayah, a0, a1, **kw):
    return segment.Block("verse", surah, ayah, a0, a1, 0.0, 1.0, "", "", "", **kw)


def test_verses_said_counts_a_verse_said_again():
    from tilawa import detect
    n = len(quran.verse(97, 3).align)
    blocks = [_verse_block(97, 2, 0, 5), _verse_block(97, 3, 0, 3), _verse_block(97, 3, 3, n), _verse_block(97, 3, 0, n)]
    assert detect._said(blocks) == [((97, 2), [0]), ((97, 3), [1, 2]), ((97, 3), [3])]


def test_second_listen_kept_only_for_a_repeat():
    from tilawa import detect
    said = [(97, 1), (97, 2), (97, 3)]
    assert detect._adds_repeat(said, [(97, 1), (97, 2), (97, 3), (97, 3)])
    assert not detect._adds_repeat(said, said)
    assert not detect._adds_repeat(said, [(97, 1), (97, 2), (97, 4)])  # other verses: not a repeat
    assert not detect._adds_repeat(said, [(97, 1), (97, 3), (97, 3)])
    # spelled letters: "Alif Laaam Miiim" heard twice is a long "amin" before it
    assert not detect._adds_repeat([(1, 7), (2, 1), (2, 2)], [(1, 7), (2, 1), (2, 1), (2, 2)])


def test_doubts_mark_faint_words_and_the_reason_given():
    from tilawa import detect
    heard = [{"t0": 0.0, "t1": 0.5, "s": -0.1}, {"t0": 0.5, "t1": 6.0, "s": -0.1}]
    faint = [{"t0": 0.0, "t1": 0.5, "s": -2.5}, {"t0": 0.5, "t1": 1.0, "s": -1.0}]
    blocks = [_verse_block(97, 1, 0, 2, words=heard), _verse_block(97, 2, 0, 2, words=faint), _verse_block(97, 3, 0, 1)]
    detect._doubts(blocks, {2: "differ"})
    assert [b.doubt for b in blocks] == ["", "faint", "differ"]
