"""Transliteration made from the Arabic (translit.py), translations, verse grouping."""

from tilawa import project, quran, segment, translit


def tr(s, a, style="academic", a0=0, a1=None):
    v = quran.verse(s, a)
    return " ".join(v.phonetic(a0, len(v.align) if a1 is None else a1, style))


def test_rules_on_known_verses():
    assert tr(1, 1) == "Bismi llāhi r-raḥmāni r-raḥīm"
    assert tr(1, 2) == "Al-ḥamdu li-llāhi rabbi l-ʿālamīn"
    assert tr(1, 6) == "Ihdinā ṣ-ṣirāṭa l-mustaqīm"
    assert tr(2, 1) == "Alif lām mīm"
    assert tr(112, 1) == "Qul huwa llāhu aḥad"
    assert tr(114, 6) == "Mina l-jinnati wa-n-nās"  # Tanzil's own line has a typo there
    assert tr(85, 2, "simple") == "Wal yawmil maw'ood"
    assert tr(109, 2, "simple") == "Laa a'budu maa ta'budoon"
    assert tr(1, 2, "fr") == "Alhamdou lillâhi rabbil 'âlamîn"
    assert "l-ūlā" in tr(20, 51) and tr(2, 5).startswith("Ulāʾika")  # the waw of ulāʾika only is silent
    assert "miṣbāḥuni l-miṣbāḥu" in tr(24, 35)  # helping vowel after -un


def test_every_word_has_its_transliteration():
    for s in range(1, 115):
        for a in range(1, quran.surah(s)["verses"] + 1):
            v = quran.verse(s, a)
            words = v.phonetic(0, len(v.align), "simple")
            assert len(words) == len(v.align) and all(words), (s, a)


def test_a_part_of_a_verse_is_said_after_a_pause():
    # starting mid-verse with a connecting hamza: its vowel is said; the end is in pausal form
    assert tr(1, 7, "academic", 0, 4) == "Ṣirāṭa l-ladhīna anʿamta ʿalayhim"
    assert quran.verse(3, 103).phonetic(4, 6, "academic")[0].startswith(("wa", "l"))


def test_conventions_and_blocks():
    b = segment.Block("verse", 85, 2, 0, 2, 0, 1, "", "", "", words=[{"w": "x"}, {"w": "y"}])
    segment.set_phonetic(b, "simple")
    assert b.tr == "Wal yawmil maw'ood" and [w["tr"] for w in b.words] == ["Wal yawmil", "maw'ood"]
    segment.set_phonetic(b, "tanzil")
    assert b.tr == "Waalyawmi almawAAoodi"
    assert segment.phonetic("istiadha", None, 0, 0, "simple") == ["A'oodhu", "billaahi", "minash", "shaytaanir", "rajeem"]


def test_translations():
    assert [f for f, _ in quran.editions("fr")] == ["fr.hamidullah", "fr.maach", "fr.noor"]
    assert [f for f, _ in quran.editions("en")] == ["en.sahih", "en.yusufali", "en.pickthall"]
    assert quran.edition("fr", "en.sahih") == "fr.hamidullah"  # another language's: the default
    for f, _ in quran.editions("fr") + quran.editions("en"):
        lang = f[:2]
        t = quran.translation_table(lang, f)
        assert len(t) == 6236 and all(t.values()) and "[1]" not in t[(1, 1)], f
    v = quran.verse(1, 2)
    assert segment.translation(v, "fr") == v.french
    assert segment.translation(v, "fr", "fr.maach") != v.french


def test_a_verse_recitation_is_grouped(tmp_path):
    p = project.Project(tmp_path, "v.mp4", 2, 153)
    v = lambda ayah, a0, a1: {"kind": "verse", "surah": 2, "ayah": ayah, "a0": a0, "a1": a1}
    n = len(quran.verse(2, 153).align)
    # 153 recited whole, then a recitation heard as 153 too, then 155
    p.blocks = [v(153, 0, 5), v(153, 5, n), v(153, 0, 4), v(153, 4, 7), v(155, 0, 3)]
    assert project.occurrence(p, 1) == (0, 2)
    assert project.occurrence(p, 3) == (2, 4)


def test_basmala_before_the_recitation(tmp_path):
    from tilawa import basmala

    p = project.Project(tmp_path, "v.mp4", 85, 1, format="16:9", style={"--layout": "band", "--header-mode": "intro"})
    verse = lambda ayah: {"kind": "verse", "surah": p.surah, "ayah": ayah, "a0": 0, "a1": 2}
    p.blocks = [verse(1), verse(2)]
    assert project.basmala_state(p) == {"available": True, "reason": "start", "possible": True}  # recommended
    p.blocks = [{"kind": "basmala", "surah": 0, "ayah": 0, "a0": 0, "a1": 4}, verse(1)]
    assert project.basmala_state(p)["reason"] == "said"  # the reciter's own is used
    p.blocks = [verse(5)]
    assert project.basmala_state(p)["reason"] == "middle"
    p.surah = 9
    assert not project.basmala_state(p)["possible"]  # At-Tawbah
    p.surah, p.format = 85, "9:16"
    assert not project.basmala_state(p)["available"]  # Shorts and Reels: not offered
    pay = project.basmala_payload(p)
    assert pay["num"] == "" and pay["ar"].startswith("بِسْمِ") and pay["tr"]
    assert len(basmala.RECITERS) == 10
