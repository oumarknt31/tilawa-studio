"""Framing of background clips (no video needed)."""

from tilawa import render


def test_vertical_source_at_native_size_is_untouched():
    assert render.frame_filter(1080, 1920, 1080, 1920, 1.0, 0, 0, "blur") == "null"


def test_cover_zoom_fills_the_frame_without_borders():
    z = render.cover_zoom(1920, 1080)
    f = render.frame_filter(1920, 1080, 1080, 1920, z, 0, 0, "blur")
    assert "pad" not in f and "overlay" not in f
    assert "crop=1080:1920" in f or "scale=1080:1920" in f  # exactly the frame size


def test_whole_picture_gets_a_fill_behind():
    assert "pad=1080:1920" in render.frame_filter(1920, 1080, 1080, 1920, 1.0, 0, 0, "black")
    assert "boxblur" in render.frame_filter(1920, 1080, 1080, 1920, 1.0, 0, 0, "blur", "t")


def test_only_the_visible_part_is_scaled_when_zoomed_in():
    # 4x zoom on a 4000 px photo: the crop keeps a small part of the source
    f = render.frame_filter(4000, 3000, 1080, 1920, 4.0, 0.2, 0, "blur")
    crop = f.split("crop=")[1].split(":")
    assert int(crop[0]) < 2000


def test_picture_moved_off_screen_gives_black():
    assert "drawbox" in render.frame_filter(1080, 1920, 1080, 1920, 1.0, 2.0, 0, "blur")


def test_clip_spans_last_clip_runs_to_the_end():
    clips = [{"dur": 10}, {"dur": 5}, {"dur": 1}]
    assert [(s, e) for _, s, e in render.clip_spans(clips, 30)] == [(0, 10), (10, 15), (15, 30)]
    # clips past the end are dropped
    assert len(render.clip_spans([{"dur": 40}, {"dur": 5}], 30)) == 1


def test_default_background_matches_old_fit_modes():
    assert render.default_background(1080, 1920)["clips"][0]["zoom"] == 1.0
    landscape = render.default_background(1920, 1080)
    assert landscape["clips"][0]["zoom"] == 1.0 and landscape["fill"] == "blur"
    assert render.default_background(1920, 1080, "crop")["clips"][0]["zoom"] > 3
    assert render.default_background(1920, 1080, "pad")["fill"] == "black"
