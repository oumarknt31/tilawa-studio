"""Export speed choices: working size and encoders (no video needed)."""

from tilawa import media, render


def test_hd_source_in_4k_is_built_at_its_own_size():
    # a 1080p landscape video filling a vertical 4K frame: ~3.6x upscale, done once at the end
    clip = {"zoom": render.cover_zoom(1920, 1080)}
    w, h = render.work_size([clip], [(1920, 1080)], 2160, 3840)
    assert (w, h) == (608, 1080)
    # its crop is then copied as is, not resampled
    assert "scale" not in render.frame_filter(1920, 1080, w, h, clip["zoom"], 0, 0, "blur").split("crop=", 2)[1]


def test_sharp_sources_and_small_gains_keep_the_full_size():
    assert render.work_size([{"zoom": 1.0}], [(2160, 3840)], 2160, 3840) == (2160, 3840)
    assert render.work_size([{"zoom": 1.0}], [(1920, 1080)], 2160, 3840) == (2160, 3840)  # 1.125x only
    # the sharpest clip decides
    clips = [{"zoom": 3.16}, {"zoom": 1.0}]
    assert render.work_size(clips, [(1920, 1080), (4032, 3024)], 2160, 3840) == (2160, 3840)


def test_slow_zoom_keeps_twice_the_density():
    still = render.work_size([{"zoom": 3.16}], [(1920, 1080)], 2160, 3840)
    moving = render.work_size([{"zoom": 3.16, "motion": "in"}], [(1920, 1080)], 2160, 3840)
    assert moving[0] == 2 * still[0]


def test_encoders(monkeypatch):
    info = media.VideoInfo.__new__(media.VideoInfo)
    opt = render.RenderOptions()
    monkeypatch.setattr(media, "encoders", lambda: {"libx264", "libx265", "prores_ks", "h264_videotoolbox",
                                                     "hevc_videotoolbox", "prores_videotoolbox"})
    monkeypatch.setattr(render.sys, "platform", "darwin")
    args, ext, pix = render._encode_args(info, opt)
    assert args[1] == "h264_videotoolbox" and pix == "nv12" and ext == ".mp4"
    opt.quality = "hevc"
    args, _, pix = render._encode_args(info, opt)
    assert args[1] == "hevc_videotoolbox" and pix == "p010le" and "hvc1" in args
    # without the media engine (Windows, Linux) or when it fails: software encoders
    opt.quality = "max"
    args, _, pix = render._encode_args(info, opt, hardware=False)
    assert args[1] == "libx264" and "faster" in args and pix == "yuv420p"
    opt.quality = "prores"
    assert render._encode_args(info, opt, hardware=False)[0][1] == "prores_ks"
    opt.quality = "studio"
    assert "slower" in render._encode_args(info, opt)[0]
    monkeypatch.setattr(render.sys, "platform", "win32")
    opt.quality = "max"
    assert render._encode_args(info, opt)[0][1] == "libx264"


def _info(**kw):
    base = dict(path=None, width=1920, height=1080, fps=30.0, fps_str="30/1", duration=60.0, vcodec="h264",
                pix_fmt="yuv420p", bit_depth=8, color_primaries="bt709", color_transfer="bt709", color_space="bt709",
                color_range="tv", acodec="aac", asample_rate=48000, achannels=2)
    return media.VideoInfo(**(base | kw))


def test_bt601_sources_skip_the_slow_matrix_conversion():
    assert "colormatrix=src=bt601:dst=bt709" in render._prep(_info(color_space="smpte170m"))
    assert "colormatrix" not in render._prep(_info())
    assert "in_color_matrix=bt709" in render._prep(_info(color_space=None))  # untagged HD is BT.709
    assert "in_color_matrix" not in render._prep(_info(color_space=None, width=640, height=360))  # untagged SD: BT.601


def test_title_cards_start_the_background_earlier(tmp_path):
    bg = {"clips": [{"src": "original", "dur": 5, "zoom": 1.0}], "transition": 0.5, "fill": "blur", "dim": 0}
    graph = []
    render._background_graph(bg, _info(), tmp_path / "v.mp4", None, 2.0, 10.0, 1920, 1080, render._Inputs(), graph,
                             tmp_path, lambda s, f: None, "16:9", lead=8.0)
    # the video starts at 0 (2 s before the recitation), its first picture fills the 6 s before
    assert "tpad=start_duration=6.000:start_mode=clone" in graph[0]
    assert "trim=duration=16.000" in graph[0]


def test_youtube_styles():
    from tilawa import library

    yt = [s for s in library.BUILTIN_STYLES if s.get("formats")]
    assert len(yt) >= 4 and all(s["formats"] == ["16:9"] for s in yt)
    for s in library.BUILTIN_STYLES:  # a style never moves the texts
        assert not set(s["style"]) & set(library.POSITION_KEYS)
    assert render.header_mode({"--header-mode": "intro"}) == "intro" and render.header_mode(None) == "top"


def test_a_dragged_logo_place_stays_with_its_video(tmp_path):
    from tilawa import library

    lib = library.Library(tmp_path)
    saved = lib.save_style("Mine", {"--logo-pos": "custom", "--logo-x": "250px", "--logo-y": "690px", "--logo-size": "150px"})
    assert saved["style"] == {"--logo-size": "150px"}  # other videos get the best corner of their format
    assert lib.save_style("Corner", {"--logo-pos": "tl"})["style"] == {"--logo-pos": "tl"}
