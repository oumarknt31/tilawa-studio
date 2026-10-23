"""Draw the overlays and produce the final video.

Text is drawn by headless Chromium (perfect Arabic shaping, real outlines,
gradients, colour emoji) straight at the output resolution, one transparent
PNG per subtitle block plus one for the header. ffmpeg then lays those PNGs
over the untouched source frames with fades and encodes once, so the video
goes through exactly one high-quality encode.
"""

from __future__ import annotations

import math
import mimetypes
import re
from fractions import Fraction
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import media, quran
from .segment import Block

PKG = Path(__file__).parent
ORIGIN = "http://tilawa.local"
USER_FONTS: Path | None = None  # fonts imported by the user (set by the app)
USER_LOGO: Path | None = None  # the user's logo, a PNG (set by the app)
LOGO_AUTO = True  # the logo goes on every video (where its style doesn't place or remove it)
RUNNING: set = set()  # ffmpeg encodes in progress (stopped if the app quits)

# aspect -> overlay canvas: texts are laid out on this canvas (in CSS pixels)
# and drawn at the output resolution
FORMATS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350)}
# output sizes, by the short side of the picture
SIZES = {"hd": 1080, "2k": 1440, "4k": 2160}
_OLD_SIZES = {"1080x1920": "hd", "1440x2560": "2k", "2160x3840": "4k"}


@dataclass
class RenderOptions:
    size: str = "auto"  # "auto" (native when the source has the right shape) | "hd" | "2k" | "4k"
    fit: str = "auto"  # framing when the project has no background clips: "auto" | "crop" | "blur" | "pad"
    quality: str = "max"  # "max" | "high" (lighter file) | "hevc" (10-bit H.265) | "prores" (editing master)
    #                       | "studio" (x264 slower, very slow) | "png" (still); see _encode_args
    fade_in: float = 0.25
    fade_out: float = 0.25
    show_header: bool = True
    trim_start: float = 0.0
    trim_end: float | None = None
    audio_fade_in: float = 0.0
    audio_fade_out: float = 0.0
    loudnorm: bool = True  # -14 LUFS, the level YouTube, TikTok and Instagram play at


# "Surah X" in each translation language ({} = the surah's name)
TITLE = {"fr": "SOURATE {}", "en": "SURAH {}", "es": "SURA {}", "de": "SURE {}", "it": "SURA {}", "pt": "SURATA {}",
         "nl": "SOERA {}", "sv": "SURA {}", "tr": "{} SURESİ", "id": "SURAH {}", "ms": "SURAH {}", "bs": "SURA {}",
         "sq": "SURJA {}", "ru": "СУРА {}", "ur": "سورة {}"}


def surah_title(n: int, lang: str = "fr") -> str:
    info = quran.surah(n)
    if lang in ("ur", "none"):
        return f"سورة {info['ar']}"
    return TITLE.get(lang, TITLE["fr"]).format(info["name"].upper().replace("-", " "))


def ends_verse(b: Block) -> bool:
    return b.kind == "verse" and b.a1 >= len(quran.verse(b.surah, b.ayah).align)


def block_payload(b: Block, lang: str = "fr") -> dict:
    """What the overlay page draws for a block (same as payload() in index.html)."""
    return {"num": f"{b.ayah}." if b.kind == "verse" else "", "fr": b.fr, "ar": b.ar, "tr": b.tr,
            "highlight": b.highlight, "ayah": b.ayah if ends_verse(b) else 0,
            "rtl": quran.LANGS.get(lang, ("", "", "", False))[3], "lang": lang}


def _serve(route):
    """Serve the package's web/ and fonts/ folders to the headless page."""
    path = route.request.url.removeprefix(ORIGIN).split("?")[0]
    if path.startswith("/fonts/"):
        f = PKG / "fonts" / path.removeprefix("/fonts/")
    elif path.startswith("/userfonts/") and USER_FONTS:
        f = USER_FONTS / Path(path.removeprefix("/userfonts/")).name
    elif path.startswith("/userlogo/") and USER_LOGO:
        f = USER_LOGO
    else:
        f = PKG / "web" / path.lstrip("/")
    if not f.is_file():
        return route.fulfill(status=404, body="")
    route.fulfill(status=200, body=f.read_bytes(), content_type=mimetypes.guess_type(f.name)[0] or "application/octet-stream")


class OverlayRenderer:
    def __init__(self, width: int, height: int, fmt: str = "9:16"):
        from playwright.sync_api import sync_playwright

        self.width, self.height = width, height
        self.canvas_w = FORMATS[fmt][0]
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(args=["--font-render-hinting=none", "--disable-lcd-text"])
        scale = width / self.canvas_w
        self.scale = scale
        # CSS pixel step that lands on whole output pixels (1 at 1080p and 4K, 3 at 1440p)
        self.grid = Fraction(width, self.canvas_w).denominator
        self.page = self._browser.new_page(
            viewport={"width": self.canvas_w, "height": round(height / scale)},
            device_scale_factor=scale,
        )
        self.page.route(f"{ORIGIN}/**", _serve)
        self.page.goto(f"{ORIGIN}/overlay.html")
        self.page.evaluate("window.ready")
        self.page.evaluate("(f) => setCanvas(f, window.innerHeight)", fmt)
        if USER_LOGO and USER_LOGO.is_file():
            self.page.evaluate("([u, a]) => setLogo(u, a)", [f"{ORIGIN}/userlogo/logo.png?v={USER_LOGO.stat().st_mtime_ns}", LOGO_AUTO])

    def cards(self, title: str, reciter: str, surah: int, lang: str) -> list[dict]:
        """The title cards shown before the recitation (made by the page)."""
        info = quran.surah(surah) if surah else None
        return self.page.evaluate("([t, r, s, l]) => introCards(t, r, s, l)", [title, reciter, info, lang])

    def png(self, out: Path, style: dict | None, header: dict | None = None, block: dict | None = None,
            frame: bool = False, intro: dict | None = None) -> tuple[Path, int]:
        """Draw one layer of the overlay; returns the PNG (cropped to the band
        that holds something, full width) and its vertical position in output pixels."""
        set_all = "([h, b, s, f, c]) => { setStyle(s); setHeader(h); setBlock(b); setFrame(f); setIntro(c); }"
        args = [header, block, style or {}, frame, intro]
        self.page.evaluate(set_all, args)
        self.page.evaluate("settle()")
        # again, now that the fonts are loaded (line breaks depend on them)
        self.page.evaluate(set_all, args)
        self.page.evaluate("settle()")
        top, bottom = self.page.evaluate("""() => {
            let t = Infinity, b = -Infinity;
            for (const el of document.querySelectorAll('.o, #mic, .ink')) {
                const r = el.getBoundingClientRect();
                if (!r.height || el.closest('[hidden]') || getComputedStyle(el).display === 'none') continue;
                t = Math.min(t, r.top); b = Math.max(b, r.bottom);
            }
            return [t, b];
        }""")
        css_h = self.height / self.scale
        if top == float("inf"):  # nothing visible
            top, bottom = 0, 2
        # margin for outline + shadow, snapped so the crop starts on a whole output pixel
        q = self.grid
        y0 = max(0, int(top - 24) // q * q)
        y1 = min(int(css_h) // q * q, -(-int(bottom + 24) // q) * q)
        self.page.screenshot(path=str(out), omit_background=True, type="png",
                             clip={"x": 0, "y": y0, "width": self.canvas_w, "height": max(q, y1 - y0)})
        return out, round(y0 * self.scale)

    def close(self):
        self._browser.close()
        self._pw.stop()


# ---------------------------------------------------------------- geometry

def output_size(info: media.VideoInfo, opt: RenderOptions, fmt: str = "9:16") -> tuple[int, int]:
    cw, ch = FORMATS[fmt]
    size = _OLD_SIZES.get(opt.size, opt.size)
    if size == "auto":
        # native resolution of a source that already has the right shape, never below Full HD
        if info.width * ch == info.height * cw and min(info.width, info.height) >= 1080:
            return info.width - info.width % 2, info.height - info.height % 2
        size = "hd"
    k = SIZES.get(size, 1080) / min(cw, ch)
    return round(cw * k / 2) * 2, round(ch * k / 2) * 2


# HDR (iPhone HLG, PQ) -> SDR BT.709 before the text goes on, otherwise white
# subtitles would be drawn at full HDR brightness.
TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
           "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p10le")
SCALE = "flags=lanczos+accurate_rnd+full_chroma_int"
MOTION_ZOOM = 1.12  # slow zoom on a background clip: from 1 to this factor (or back)
# title cards before the recitation (style "--header-mode": "intro"): each card's
# time on screen and fades, and the pause before the recitation starts
INTRO_CARD, INTRO_FADE, INTRO_GAP = 2.6, 0.45, 0.3


def header_mode(style: dict | None) -> str:
    return str((style or {}).get("--header-mode") or "top").strip('"')


# ---------------------------------------------------------------- background
#
# The background is a sequence of clips on the source timeline, each either
# the original video (in sync with the recitation) or an imported photo or
# video, with its own framing:
#   zoom  1 = whole picture visible; larger = closer (see cover_zoom)
#   x, y  offset of the picture centre, in fractions of the frame width/height
#   motion "none" | "in" | "out"  slow zoom over the clip

def aspect(fmt: str) -> float:
    cw, ch = FORMATS[fmt]
    return cw / ch


def cover_zoom(sw: int, sh: int, fmt: str = "9:16") -> float:
    """Zoom at which a sw x sh picture exactly fills the frame."""
    r = aspect(fmt) * sh / sw
    return max(r, 1 / r)


def default_background(sw: int, sh: int, fit: str = "auto", fmt: str = "9:16") -> dict:
    """The original video alone: filling the frame if its shape is close,
    else whole over a blurred copy."""
    if fit == "auto":
        ratio = (sw / sh) / aspect(fmt)
        fit = "crop" if 1 / 1.45 < ratio < 1.45 else "blur"
    return {"clips": [new_clip("original", sw, sh, fill=fit == "crop", fmt=fmt)], "transition": 0.5,
            "fill": "black" if fit == "pad" else "blur", "dim": 0.0}


def new_clip(src: str, sw: int, sh: int, dur: float = 5.0, fill: bool = True, fmt: str = "9:16") -> dict:
    return {"src": src, "dur": dur, "zoom": round(cover_zoom(sw, sh, fmt), 4) if fill else 1.0,
            "x": 0.0, "y": 0.0, "motion": "none", "offset": 0.0}


def clip_spans(clips: list[dict], duration: float) -> list[tuple[dict, float, float]]:
    """(clip, start, end) on the source timeline; the last clip runs to the end."""
    spans, t = [], 0.0
    for i, c in enumerate(clips):
        end = duration if i == len(clips) - 1 else min(duration, t + max(0.1, float(c.get("dur") or 0)))
        if end > t:
            spans.append((c, t, end))
        t = end
        if t >= duration:
            break
    return spans


def frame_filter(sw: int, sh: int, w: int, h: int, zoom: float, x: float, y: float, fill: str, tag: str = "") -> str:
    """Filter that places a sw x sh yuv444p picture in a w x h frame.

    Only the visible part of the picture is cropped and scaled (one
    resampling, and no huge intermediate frames when zoomed in). What the
    picture does not cover shows a blurred copy of it, or black."""
    s = min(w / sw, h / sh) * max(0.05, zoom)
    if abs(s - 1) * max(w, h) < 2:  # within a pixel of 1:1: copy the pixels, a resampling would only soften them
        s = 1.0
    X = w / 2 + x * w - sw * s / 2
    Y = h / 2 + y * h - sh * s / 2
    cx0, cy0 = max(0, math.floor(-X / s)), max(0, math.floor(-Y / s))
    cx1, cy1 = min(sw, math.ceil((w - X) / s)), min(sh, math.ceil((h - Y) / s))
    if cx1 - cx0 < 2 or cy1 - cy0 < 2:  # moved off screen
        return f"scale={w}:{h},drawbox=t=fill:c=black"
    ox, oy = round(X + cx0 * s), round(Y + cy0 * s)
    tw, th = max(1, round((cx1 - cx0) * s)), max(1, round((cy1 - cy0) * s))
    covers = ox <= 0 and oy <= 0 and ox + tw >= w - 1 and oy + th >= h - 1
    if covers:
        tw, th = max(tw, w - ox), max(th, h - oy)
    crop = "" if (cx0, cy0, cx1, cy1) == (0, 0, sw, sh) else f"crop={cx1 - cx0}:{cy1 - cy0}:{cx0}:{cy0}:exact=1,"
    size = "" if (tw, th) == (cx1 - cx0, cy1 - cy0) else f"scale={tw}:{th}:{SCALE},"
    pic = (crop + size).rstrip(",") or "null"
    if covers:
        return pic if (ox, oy, tw, th) == (0, 0, w, h) else f"{pic},crop={w}:{h}:{-ox}:{-oy}"
    ox, oy = min(max(0, ox), w - tw), min(max(0, oy), h - th)
    if fill == "black":
        return f"{pic},pad={w}:{h}:{ox}:{oy}:black"
    bw, bh = max(2, w // 4 // 2 * 2), max(2, h // 4 // 2 * 2)
    radius = max(1, round(min(bw, bh) * 20 / 270))  # the same blur whatever the working size
    return (f"split=2[{tag}bg][{tag}fg];[{tag}bg]scale={bw}:{bh}:force_original_aspect_ratio=increase,crop={bw}:{bh},"
            f"boxblur={radius}:2,scale={w}:{h}:{SCALE},eq=brightness=-0.08[{tag}bgb];[{tag}fg]{pic}[{tag}fgs];"
            f"[{tag}bgb][{tag}fgs]overlay={ox}:{oy}")


def motion_filter(w: int, h: int, motion: str, frames: int) -> str:
    """Slow zoom of a frame drawn MOTION_ZOOM times larger than the output:
    a shrinking (or growing) window of it is resampled to w x h with
    sub-pixel precision, so the movement is perfectly smooth."""
    k = MOTION_ZOOM
    p = f"(in/{max(1, frames - 1)})"
    m = f"(1+{k - 1:.4f}*{p})" if motion == "in" else f"({k:.4f}-{k - 1:.4f}*{p})"
    hw, hh = f"(W/2/{m})", f"(H/2/{m})"
    return (f"perspective=x0='W/2-{hw}':y0='H/2-{hh}':x1='W/2+{hw}':y1='H/2-{hh}':"
            f"x2='W/2-{hw}':y2='H/2+{hh}':x3='W/2+{hw}':y3='H/2+{hh}':eval=frame:interpolation=cubic,"
            f"scale={w}:{h}:{SCALE}")


# ---------------------------------------------------------------- colour
#
# Colour correction of a background clip, done exactly like the editor's
# preview (an SVG filter in sRGB): a per-channel tone curve (exposure, white
# balance, contrast, highlights, shadows) sampled at 256 points, then the CSS
# saturation matrix. Keep in sync with toneTable() in web/index.html.

ADJUST_KEYS = ("exposure", "contrast", "highlights", "shadows", "saturation", "temperature", "tint")


def tone_table(adj: dict, ch: int) -> list[float]:
    """Output level (0..1) for each of 256 input levels of channel ch (0 R, 1 G, 2 B)."""
    ev = float(adj.get("exposure") or 0)
    con = float(adj.get("contrast") or 0) / 100
    hi = float(adj.get("highlights") or 0) / 100
    sh = float(adj.get("shadows") or 0) / 100
    temp = float(adj.get("temperature") or 0) / 100
    tint = float(adj.get("tint") or 0) / 100
    wb = (1 + 0.12 * temp + 0.04 * tint, 1 - 0.08 * tint, 1 - 0.12 * temp + 0.04 * tint)[ch]
    gain = 2 ** (ev / 2.2) * wb
    c = 2 ** con
    out = []
    for i in range(256):
        x = (i / 255 * gain - 0.5) * c + 0.5
        x = min(1.0, max(0.0, x))
        x += 0.3 * hi * 6.75 * x * x * (1 - x) + 0.3 * sh * 6.75 * x * (1 - x) * (1 - x)
        out.append(round(min(1.0, max(0.0, x)), 5))
    return out


def is_neutral(adj: dict | None) -> bool:
    return not adj or all(not float(adj.get(k) or 0) for k in ADJUST_KEYS)


def adjust_filter(adj: dict, cube: Path) -> str:
    """Filter applying the colour correction; writes the curves to `cube`
    (referenced by its bare name: ffmpeg runs inside that folder)."""
    tables = [tone_table(adj, ch) for ch in range(3)]
    cube.write_text("LUT_1D_SIZE 256\n" + "".join(f"{r} {g} {b}\n" for r, g, b in zip(*tables)))
    s = 1 + float(adj.get("saturation") or 0) / 100
    mix = (f"colorchannelmixer=rr={0.213 + 0.787 * s:.5f}:rg={0.715 - 0.715 * s:.5f}:rb={0.072 - 0.072 * s:.5f}:"
           f"gr={0.213 - 0.213 * s:.5f}:gg={0.715 + 0.285 * s:.5f}:gb={0.072 - 0.072 * s:.5f}:"
           f"br={0.213 - 0.213 * s:.5f}:bg={0.715 - 0.715 * s:.5f}:bb={0.072 + 0.928 * s:.5f}")
    return (f"scale=in_color_matrix=bt709:in_range=tv:out_range=pc,format=gbrp16le,"
            f"lut1d=file={cube.name}:interp=linear,{mix},"
            f"scale=out_color_matrix=bt709:out_range=tv,format=yuv444p")


def _prep(info: media.VideoInfo | None) -> str:
    """Bring any source to BT.709 limited-range yuv444p."""
    pre = f"{TONEMAP}," if info is not None and info.is_hdr and "zscale" in media.encoders() else ""
    if info is not None and not pre and info.bit_depth <= 8 and info.color_range in (None, "tv", "unknown"):
        # swscale's accurate path converts colour matrices at ~15 fps in 1080p:
        # BT.601 goes through the colormatrix filter instead (same picture, ~20x
        # faster), and BT.709 (or untagged HD, which is BT.709) needs no conversion
        space = info.color_space or "unknown"
        if space in ("smpte170m", "bt470bg"):
            pre = "colormatrix=src=bt601:dst=bt709,"
        if pre or space == "bt709" or (space == "unknown" and min(info.width, info.height) >= 720):
            return f"{pre}scale=in_color_matrix=bt709:out_color_matrix=bt709:out_range=tv:{SCALE},format=yuv444p"
    return f"{pre}scale=out_color_matrix=bt709:out_range=tv:{SCALE},format=yuv444p"


class _Inputs:
    def __init__(self):
        self.args: list[str] = []
        self.n = 0

    def add(self, *args: str) -> int:
        self.args += list(args)
        self.n += 1
        return self.n - 1


def pingpong_file(f: Path) -> Path:
    """Forward + backward cycle of an imported video, made once and kept."""
    pp = f.with_name(f"{f.stem}.pp.mkv")
    if not pp.exists():
        media.pingpong(f, pp)
    return pp


def _source_size(c: dict, info: media.VideoInfo, media_dir: Path | None) -> tuple[int, int]:
    if c["src"] == "original":
        return info.width, info.height
    f = (media_dir / Path(c["src"]).name) if media_dir else Path(c["src"])
    if f.suffix.lower() == ".png":
        from PIL import Image

        with Image.open(f) as im:
            return im.size
    i = media.probe(f)
    return i.width, i.height


def work_size(clips: list[dict], sizes: list[tuple[int, int]], w: int, h: int) -> tuple[int, int]:
    """Size at which the background is built before one final upscale to w x h.

    A 1080p clip shown in a 4K frame has no more detail than at 1080p: zooming,
    blurring, colouring and fading it at its own resolution gives the same
    picture for a fraction of the work. Sharp sources (a 4K video, a photo)
    keep the full size."""
    k = min((min(w / sw, h / sh) * max(0.05, float(c.get("zoom") or 1))
             # a slow zoom interpolates between pixels: twice the density keeps it as sharp
             / (2 if c.get("motion", "none") != "none" else 1) for c, (sw, sh) in zip(clips, sizes)), default=1)
    if k < 1.5:  # too little to gain for an extra resampling
        return w, h
    return max(2, round(w / k / 2) * 2), max(2, round(h / k / 2) * 2)


def _background_graph(bg: dict, info: media.VideoInfo, video: Path, media_dir: Path | None,
                      t0: float, t1: float, w: int, h: int, inputs: _Inputs, graph: list[str],
                      work: Path, progress: Callable[[str, float], None], fmt: str = "9:16",
                      out_pix: str = "yuv420p", lead: float = 0.0) -> str:
    """Adds the background (w x h in out_pix, lead + t1 - t0 long) to the graph; returns its label.
    lead: seconds before the recitation (title cards), where the first clip starts earlier."""
    fps, rate = info.fps_str, info.fps
    W, H = w, h
    spans = []
    for c, s, e in clip_spans(bg["clips"], info.duration):
        s, e = max(s, t0) - t0, min(e, t1) - t0
        if e - s >= 1 / rate:
            spans.append((c, s, e))
    if not spans:
        spans = [(default_background(info.width, info.height, "auto", fmt)["clips"][0], 0.0, t1 - t0)]
    if lead:
        spans = [(c, s + lead if i else 0.0, e + lead) for i, (c, s, e) in enumerate(spans)]
    w, h = work_size([c for c, _, _ in spans], [_source_size(c, info, media_dir) for c, _, _ in spans], W, H)
    # crossfades: centred on each cut, at most half of either neighbour
    d = [0.0] + [min(float(bg.get("transition") or 0), (spans[i - 1][2] - spans[i - 1][1]) / 2,
                     (spans[i][2] - spans[i][1]) / 2) for i in range(1, len(spans))] + [0.0]
    labels = []
    for i, (c, s, e) in enumerate(spans):
        a, b = s - d[i] / 2, e + d[i + 1] / 2
        length, frames = b - a, max(1, round((b - a) * rate))
        motion = c.get("motion", "none")
        fw, fh = (round(w * MOTION_ZOOM / 2) * 2, round(h * MOTION_ZOOM / 2) * 2) if motion != "none" else (w, h)
        src = c["src"]
        if src == "original":
            sinfo = info
            # in sync with the recitation; before the video's start, its first picture
            src0 = t0 + a - lead
            k = inputs.add("-ss", f"{max(0.0, src0):.3f}", "-to", f"{t0 + b - lead:.3f}", "-i", str(video))
            head = f"[{k}:v]setpts=PTS-STARTPTS,{_prep(sinfo)}"
            if src0 < -0.001:
                head += f",tpad=start_duration={-src0:.3f}:start_mode=clone"
        else:
            f = (media_dir / Path(src).name) if media_dir else Path(src)
            if f.suffix.lower() == ".png":  # imported photo
                from PIL import Image

                with Image.open(f) as im:
                    sw, sh = im.size
                k = inputs.add("-i", str(f))
                sinfo = None
                head = f"[{k}:v]{_prep(None)}"
            else:
                sinfo = media.probe(f)
                offset = float(c.get("offset") or 0)
                if c.get("loop", "pingpong") == "pingpong" and length > sinfo.duration - offset + 0.05:
                    # longer than the video: play it forward, then backward, and so on
                    progress("prepare", 0.0)
                    f = pingpong_file(f)
                k = inputs.add("-stream_loop", "-1", "-ss", f"{offset:.3f}", "-i", str(f))
                head = f"[{k}:v]trim=duration={length:.3f},setpts=PTS-STARTPTS,{_prep(sinfo)}"
        sw, sh = (sinfo.width, sinfo.height) if sinfo else (sw, sh)
        chain = head + "," + frame_filter(sw, sh, fw, fh, float(c.get("zoom") or 1), float(c.get("x") or 0),
                                          float(c.get("y") or 0), bg.get("fill", "blur"), f"f{i}")
        if sinfo is None:  # a photo: framed once, then repeated
            chain += f",loop=loop={frames - 1}:size=1:start=0,setpts=N/({fps})/TB"
        if motion != "none":
            chain += "," + motion_filter(w, h, motion, frames)
        if not is_neutral(c.get("adjust")):
            chain += "," + adjust_filter(c["adjust"], work / f"adjust{i}.cube")
        # constant rate and a common time base, as the crossfades require
        chain += f",trim=duration={length:.3f},setpts=PTS-STARTPTS,settb=AVTB,fps={fps},format=yuv444p"
        graph.append(f"{chain}[c{i}]")
        labels.append(f"c{i}")
    last = labels[0]
    for i in range(1, len(labels)):
        a = spans[i][1] - d[i] / 2
        if d[i] >= 1 / rate:
            graph.append(f"[{last}][{labels[i]}]xfade=transition=fade:duration={d[i]:.3f}:offset={a:.3f}[x{i}]")
        else:
            graph.append(f"[{last}][{labels[i]}]concat=n=2:v=1:a=0[x{i}]")
        last = f"x{i}"
    # darkening = blending with black (Y 16, U/V 128), done before the upscale
    dim = min(float(bg.get("dim") or 0), 0.9)
    k = 1 - dim
    darken = f"lutyuv=y='16+(val-16)*{k:.4f}':u='128+(val-128)*{k:.4f}':v='128+(val-128)*{k:.4f}'," if dim > 0 else ""
    size = f"scale={W}:{H}:{SCALE}," if (w, h) != (W, H) else ""
    graph.append(f"[{last}]{darken}{size}format={out_pix}[bgout]")
    return "bgout"


def _hardware() -> bool:
    """Apple's media engine (VideoToolbox) is there: every Apple Silicon Mac."""
    return sys.platform == "darwin" and "h264_videotoolbox" in media.encoders()


def _encode_args(info: media.VideoInfo, opt: RenderOptions, hardware: bool | None = None) -> tuple[list[str], str, str]:
    """Encoder arguments, file extension, and the pixel format the encoder takes.

    Quality levels were chosen by VMAF against a lossless render of a real
    project (20 s, 1080p; x264 near-lossless = 95.7): "max" hardware H.264 q88
    = 95.55 at ~8x the speed of x264 slower CRF 12 (95.48); without hardware,
    x264 faster CRF 12 = 95.35 at ~3.4x."""
    enc = media.encoders()
    hw = _hardware() if hardware is None else hardware
    tags = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]
    if opt.quality == "prores":
        if hw and "prores_videotoolbox" in enc:
            return ["-c:v", "prores_videotoolbox", "-profile:v", "hq", *tags], ".mov", "p210le"
        return ["-c:v", "prores_ks", "-profile:v", "3", "-vendor", "apl0", *tags], ".mov", "yuv422p10le"
    if opt.quality == "hevc":
        if hw and "hevc_videotoolbox" in enc:
            return ["-c:v", "hevc_videotoolbox", "-profile:v", "main10", "-q:v", "80", "-tag:v", "hvc1", *tags], ".mp4", "p010le"
        if "libx265" in enc:
            return ["-c:v", "libx265", "-preset", "medium", "-crf", "14", "-tag:v", "hvc1",
                    "-x265-params", "aq-mode=3:no-sao=1:log-level=error", *tags], ".mp4", "yuv420p10le"
    if opt.quality == "studio":  # the slowest, for whoever wants it
        return ["-c:v", "libx264", "-preset", "slower", "-crf", "12", "-profile:v", "high",
                "-x264-params", "aq-mode=3:deblock=-1,-1", *tags], ".mp4", "yuv420p"
    q = "88" if opt.quality == "max" else "80"
    if hw:
        return ["-c:v", "h264_videotoolbox", "-q:v", q, "-profile:v", "high", *tags], ".mp4", "nv12"
    crf = "12" if opt.quality == "max" else "16"
    return ["-c:v", "libx264", "-preset", "faster", "-crf", crf, "-profile:v", "high",
            "-x264-params", "aq-mode=3", *tags], ".mp4", "yuv420p"


def _audio_args(info: media.VideoInfo, trimmed: bool) -> list[str]:
    if info.acodec is None:
        return ["-an"]
    if info.acodec == "aac" and not trimmed:
        return ["-c:a", "copy"]  # no generational loss
    enc = "aac_at" if "aac_at" in media.encoders() else "aac"
    rate = "48000" if (info.asample_rate or 48000) >= 44100 else str(info.asample_rate)
    return ["-c:a", enc, "-b:a", "320k", "-ar", rate]


def _graph_arg(script: Path) -> list[str]:
    """Read the filter graph from a file (the command line gets too long otherwise)."""
    out = subprocess.run([media.tools()[0], "-version"], capture_output=True, text=True).stdout
    m = re.search(r"ffmpeg version n?(\d+)", out)
    if m and int(m.group(1)) >= 7:
        return ["-/filter_complex", str(script)]
    return ["-filter_complex_script", str(script)]


# ---------------------------------------------------------------- render

def render(video: Path, blocks: list[Block], title: str, reciter: str, out: Path,
           opt: RenderOptions | None = None, style: dict | None = None,
           progress: Callable[[str, float], None] | None = None,
           background: dict | None = None, media_dir: Path | None = None,
           fmt: str = "9:16", lang: str = "fr", surah: int = 0) -> Path:
    """Make the video (or, with quality "png", a still image of its first frame)."""
    opt = opt or RenderOptions()
    progress = progress or (lambda stage, f: None)
    # absolute paths: ffmpeg runs inside the work folder
    video, out = Path(video).resolve(), Path(out).resolve()
    media_dir = Path(media_dir).resolve() if media_dir else None
    info = media.probe(video)
    w, h = output_size(info, opt, fmt)
    t0 = max(0.0, opt.trim_start)
    t1 = min(info.duration, opt.trim_end) if opt.trim_end else info.duration
    still_image = opt.quality == "png"
    if still_image:
        t1 = min(info.duration, t0 + 2 / info.fps)
    work = out.parent / f".{out.stem}-overlays"
    work.mkdir(parents=True, exist_ok=True)

    # 1) overlays
    shown = [b for b in blocks if b.end > t0 and b.start < t1]
    renderer = OverlayRenderer(w, h, fmt)
    try:
        intro = header_mode(style) == "intro" and opt.show_header and not still_image
        cards = renderer.cards(title, reciter, surah, lang) if intro else []
        # what stays all along: the header (unless shown as cards), the logo, the band
        header = renderer.png(work / "header.png", style, {"title": title, "reciter": reciter, "visible": opt.show_header},
                              frame=True)
        card_pngs = [renderer.png(work / f"intro{k}.png", style, intro=c) for k, c in enumerate(cards)]
        pngs = []
        for i, b in enumerate(shown):
            pngs.append(renderer.png(work / f"block{i:03d}.png", style, block=block_payload(b, lang)))
            progress("overlays", (i + 1) / max(1, len(shown)))
    finally:
        renderer.close()
    lead = len(cards) * INTRO_CARD + INTRO_GAP if cards else 0.0

    # 2) compose + encode
    # Each overlay PNG is decoded and colour-converted once, then repeated with
    # the loop filter (cheap), faded, and placed at its time and height.
    fps = info.fps_str
    total = lead + t1 - t0
    if still_image:
        vargs, ext, enc_pix = [], ".png", "yuv444p"
    else:
        vargs, ext, enc_pix = _encode_args(info, opt)
    # compose in the encoder's chroma layout: 4:2:0 for H.264/HEVC (as the
    # file will be anyway, and ~4x cheaper per 4K frame), 4:4:4 for ProRes / stills
    full = enc_pix in ("yuv444p", "yuv422p10le", "p210le")
    pix, ov = ("yuv444p", "yuv444") if full else ("yuv420p", "yuv420")
    to_yuv = f"format=rgba,scale=out_color_matrix=bt709:out_range=tv,format=yuva{pix[3:]}"

    def still(k: int, dur: float) -> str:
        n = math.ceil(dur * info.fps) + 1
        return f"[{k}:v]{to_yuv},loop=loop={n - 1}:size=1:start=0,setpts=N/({fps})/TB"

    inputs = _Inputs()
    audio = inputs.add("-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", str(video))
    graph: list[str] = []
    base = _background_graph(background or default_background(info.width, info.height, opt.fit, fmt),
                             info, video, media_dir, t0, t1, w, h, inputs, graph, work, progress, fmt, pix, lead)
    hdr = inputs.add("-i", str(header[0]))
    if lead:  # after the cards
        graph.append(f"{still(hdr, total - lead)},fade=t=in:st=0:d={INTRO_FADE}:alpha=1,setpts=PTS+{lead:.3f}/TB[hdr]")
    else:
        graph.append(f"{still(hdr, total)}[hdr]")
    graph.append(f"[{base}][hdr]overlay=x=0:y={header[1]}:format={ov}:eof_action=pass[v0]")
    last = "v0"
    for k, (png, y) in enumerate(card_pngs):
        c = inputs.add("-i", str(png))
        graph.append(f"{still(c, INTRO_CARD)},fade=t=in:st=0:d={INTRO_FADE}:alpha=1,"
                     f"fade=t=out:st={INTRO_CARD - INTRO_FADE:.3f}:d={INTRO_FADE}:alpha=1,trim=duration={INTRO_CARD},"
                     f"setpts=PTS+{k * INTRO_CARD:.3f}/TB[in{k}]")
        graph.append(f"[{last}][in{k}]overlay=x=0:y={y}:format={ov}:eof_action=pass[vi{k}]")
        last = f"vi{k}"
    for i, (b, (png, y)) in enumerate(zip(shown, pngs)):
        s, e = max(b.start, t0) - t0 + lead, min(b.end, t1) - t0 + lead
        dur = max(e - s, 1 / info.fps)
        fi, fo = min(opt.fade_in, dur / 3), min(opt.fade_out, dur / 3)
        if still_image:
            fi = fo = 0  # a still shows the subtitle fully
        k = inputs.add("-i", str(png))
        fade_in = f"fade=t=in:st=0:d={fi:.3f}:alpha=1," if (b.start > t0 + 0.01 or lead) and fi > 0 else ""
        fade_out = f"fade=t=out:st={dur - fo:.3f}:d={fo:.3f}:alpha=1," if fo > 0 else ""
        graph.append(f"{still(k, dur)},{fade_in}{fade_out}trim=duration={dur:.3f},setpts=PTS+{s:.3f}/TB[o{i}]")
        graph.append(f"[{last}][o{i}]overlay=x=0:y={y}:format={ov}:eof_action=pass[v{i + 1}]")
        last = f"v{i + 1}"
    script = work / "graph.txt"
    common = [media.tools()[0], "-y", "-hide_banner", "-loglevel", "error", "-stats_period", "0.5", "-progress", "pipe:1"]

    if still_image:
        out = out.with_suffix(".png")
        graph.append(f"[{last}]scale=in_color_matrix=bt709:in_range=tv:out_range=pc,format=rgb24[vout]")
        script.write_text(";\n".join(graph))
        cmd = [*common, *inputs.args, *_graph_arg(script), "-map", "[vout]", "-frames:v", "1", "-c:v", "png", str(out)]
        total = 1 / info.fps
    else:
        out = out.with_suffix(ext)
        graph.append(f"[{last}]format={enc_pix}[vout]")
        afi, afo = min(opt.audio_fade_in, total / 2), min(opt.audio_fade_out, total / 2)
        afilters = []
        if info.acodec is not None and opt.loudnorm:
            progress("loudness", 0.0)
            afilters += [media.loudnorm_filter(video, t0, t1), "aresample=48000"]
        if lead:  # silence under the title cards
            afilters.append(f"adelay=delays={round(lead * 1000)}:all=1")
        if afi > 0:
            afilters.append(f"afade=t=in:st={lead:.3f}:d={afi:.3f}")
        if afo > 0:
            afilters.append(f"afade=t=out:st={total - afo:.3f}:d={afo:.3f}")
        if info.acodec is not None and afilters:
            graph.append(f"[{audio}:a]{','.join(afilters)}[aout]")
            amap = ["-map", "[aout]"]
        else:
            amap = ["-map", f"{audio}:a?"]
        script.write_text(";\n".join(graph))
        head = [*common, *inputs.args, *_graph_arg(script), "-map", "[vout]", *amap, "-fps_mode", "cfr", "-r", fps]
        tail = [*_audio_args(info, t0 > 0 or t1 < info.duration or bool(afilters)),
                "-movflags", "+faststart", "-t", f"{total:.3f}", str(out)]
        cmd = [*head, *vargs, *tail]
    code, err = _run(cmd, work, total, progress)
    if code > 0 and any("videotoolbox" in a for a in vargs):
        # the media engine refused the job: same video with the software encoder
        progress("encoding", 0.0)
        code, err = _run([*head, *_encode_args(info, opt, hardware=False)[0], *tail], work, total, progress)
    if code != 0:
        raise RuntimeError(f"ffmpeg failed:\n{err[-3000:]}")
    progress("encoding", 1.0)
    return out


def _run(cmd: list[str], work: Path, total: float, progress: Callable[[str, float], None]) -> tuple[int, str]:
    """Runs ffmpeg, reporting its progress; returns its exit code (negative
    when it was stopped) and the end of its error output."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=work)
    RUNNING.add(proc)
    try:
        for line in proc.stdout:
            m = re.match(r"out_time_us=(\d+)", line)
            if m:
                progress("encoding", min(1.0, int(m.group(1)) / 1e6 / total))
        err = proc.stderr.read()
        return proc.wait(), err
    finally:
        RUNNING.discard(proc)
