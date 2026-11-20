"""Word tracking: the displayed word of each recited word, the translation's links, and an export
whose subtitle follows the words (the same page and times as the preview)."""

import subprocess

import numpy as np
from PIL import Image

from tilawa import media, render, segment


def test_each_recited_word_knows_its_displayed_word():
    # يَـٰبَنِىٓ is displayed as one word: يَا and بَنِي both take its colour, in turn
    b = {"kind": "verse", "surah": 36, "ayah": 60, "a0": 0, "a1": 6,
         "words": [{"w": w, "t0": k, "t1": k + 1} for k, w in enumerate("أَلَمْ أَعْهَدْ إِلَيْكُمْ يَا بَنِي آدَمَ".split())]}
    segment.add_display_indexes(b)
    assert [w["di"] for w in b["words"]] == [0, 1, 2, 3, 3, 4]


def test_the_translation_groups_start_with_the_word_that_opens_them():
    blocks = [{"words": [{"w": "وَهُوَ"}, {"w": "قُلْ"}, {"w": "بِيَدِهِ"}]}]
    segment.add_anchors(blocks, "fr")
    ws = blocks[0]["words"]
    assert ws[0]["an"][0].startswith("et") and ws[1]["an"][0].startswith("dis") and "an" not in ws[2]


def test_a_tracked_subtitle_is_drawn_frame_by_frame(tmp_path):
    ff, _ = media.tools()
    video = tmp_path / "v.mp4"
    subprocess.run([ff, "-v", "error", "-f", "lavfi", "-i", "color=c=0xf3e2c0:size=640x360:rate=10:duration=3",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)], check=True)
    words = [{"w": w, "t0": 0.2 + 0.6 * k, "t1": 0.8 + 0.6 * k, "di": k} for k, w in enumerate("أَلَمْ أَعْهَدْ إِلَيْكُمْ".split())]
    b = segment.Block("verse", 36, 60, 0, 3, 0.0, 3.0, "أَلَمْ أَعْهَدْ إِلَيْكُمْ", "Ne vous ai-Je pas engagés,",
                      "Alam a'had ilaykoum", words=words)
    style = {"--track-ar": "marker", "--track-tr": "capsule", "--track-accent": "#bf4527", "--ar-color": "#1c5961"}
    out = render.render(video, [b], "", "", tmp_path / "out", render.RenderOptions(fade_in=0, fade_out=0, loudnorm=False),
                        style, fmt="16:9")
    assert out.exists() and not (tmp_path / ".out-overlays").exists()  # the pictures drawn are gone
    frames = []
    for t in (0.5, 1.1, 1.7):
        f = tmp_path / f"f{t}.png"
        subprocess.run([ff, "-v", "error", "-y", "-ss", str(t), "-i", str(out), "-frames:v", "1", str(f)], check=True)
        frames.append(np.asarray(Image.open(f).convert("RGB"), float))
    # the marker and the capsule move from word to word: the moments look different
    changed = lambda a, b: int((np.abs(a - b).max(axis=2) > 30).sum())
    assert changed(frames[0], frames[1]) > 100 and changed(frames[1], frames[2]) > 100
