"""Colour correction curves and back-and-forth loops."""

import subprocess

import numpy as np

from tilawa import media, render


def test_neutral_correction_changes_nothing():
    assert render.is_neutral({}) and render.is_neutral({"exposure": 0, "contrast": 0})
    for ch in range(3):
        assert render.tone_table({}, ch) == [round(i / 255, 5) for i in range(256)]


def test_corrections_go_the_right_way():
    mid = 128
    assert render.tone_table({"exposure": 1}, 0)[mid] > mid / 255
    assert render.tone_table({"contrast": 50}, 0)[200] > 200 / 255 > render.tone_table({"contrast": -50}, 0)[200]
    warm = {"temperature": 50}
    assert render.tone_table(warm, 0)[mid] > render.tone_table(warm, 2)[mid]  # more red than blue
    # highlights and shadows keep black and white in place
    for k in ("highlights", "shadows"):
        t = render.tone_table({k: 100}, 1)
        assert t[0] == 0 and t[255] == 1


def test_pingpong_plays_forward_then_backward_without_repeating_the_turns(tmp_path):
    ff = media.tools()[0]
    src = tmp_path / "src.mp4"
    subprocess.run([ff, "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=1.5",
                    "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(src)], check=True)
    media.pingpong(src, tmp_path / "cycle.mkv")

    def frames(p):
        raw = subprocess.run([ff, "-v", "error", "-i", str(p), "-vf", "scale=32:18,format=gray", "-f", "rawvideo", "-"],
                             capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.uint8).reshape(-1, 32 * 18).astype(float)

    s, c = frames(src), frames(tmp_path / "cycle.mkv")
    order = [int(np.argmin(((s - f) ** 2).mean(1))) for f in c]
    n = len(s)
    assert order == list(range(n)) + list(range(n - 2, 0, -1))
