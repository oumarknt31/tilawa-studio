"""Recitations and streaks (no model needed): the days counted, the label, the recorder."""

import datetime as dt
import os
import time
import wave

from tilawa import recite


def test_streak_counts_days_in_a_row_and_keeps_it_until_tonight():
    days = {"2026-11-01", "2026-11-02", "2026-11-03", "2026-11-04", "2026-11-08", "2026-11-09", "2026-11-10"}
    s = recite.streak(days, dt.date(2026, 11, 11))  # not done yet today: still alive
    assert (s["current"], s["best"], s["today"]) == (3, 4, False)
    assert [d["done"] for d in s["week"]] == [False, False, False, True, True, True, False]
    assert recite.streak(days | {"2026-11-11"}, dt.date(2026, 11, 11))["current"] == 4
    assert recite.streak(days, dt.date(2026, 11, 12))["current"] == 0  # a day missed


def test_label_of_the_passages():
    assert recite.label([[67, 1, 10], [112, 1, 4]]) == "Al-Mulk 1–10 · Al-Ikhlas 1–4"
    assert recite.label([[103, 2, 2]]) == "Al-'Asr 2"


def test_exports_count_for_the_creation_streak(tmp_path):
    videos = tmp_path / "Videos"
    videos.mkdir()
    (videos / "old.mp4").write_bytes(b"x")
    old = time.mktime(dt.date(2026, 11, 1).timetuple()) + 3600
    os.utime(videos / "old.mp4", (old, old))
    recite.log_export(tmp_path, "p1", "new.mp4")
    assert recite.export_days(tmp_path, videos) == {"2026-11-01", dt.date.today().isoformat()}


def test_the_recorder_writes_what_it_hears(tmp_path, monkeypatch):
    monkeypatch.setenv("TILAWA_MIC", "sine=frequency=440:sample_rate=48000")
    r = recite.Recorder(tmp_path / "r.wav")
    time.sleep(1.2)
    assert r.level > 0.3 and 0.5 < r.seconds < 2
    w = wave.open(str(r.stop()))
    assert (w.getframerate(), w.getnchannels()) == (16000, 1) and w.getnframes() > 16000
