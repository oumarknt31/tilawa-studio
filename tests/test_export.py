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
