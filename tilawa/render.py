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
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import media, quran
from .segment import Block

PKG = Path(__file__).parent
CANVAS_W, CANVAS_H = 1080, 1920
ORIGIN = "http://tilawa.local"


@dataclass
class RenderOptions:
    size: str = "auto"  # "auto" | "1080x1920" | "1440x2560" | "2160x3840"
    fit: str = "auto"  # framing when the project has no background clips: "auto" | "crop" | "blur" | "pad"
    quality: str = "max"  # "max" (H.264 CRF 12) | "high" (CRF 16) | "hevc" (10-bit H.265) | "prores" (editing master)
    fade_in: float = 0.25
    fade_out: float = 0.25
    show_header: bool = True
    trim_start: float = 0.0
    trim_end: float | None = None
    audio_fade_in: float = 0.0
    audio_fade_out: float = 0.0


def surah_title(n: int) -> str:
    name = quran.surah(n)["name"].upper()
    return f"SOURATE {name.replace('-', ' ')}"


def block_payload(b: Block) -> dict:
    return {"num": f"{b.ayah}." if b.kind == "verse" else "", "fr": b.fr, "ar": b.ar, "tr": b.tr, "highlight": b.highlight}


def _serve(route):
    """Serve the package's web/ and fonts/ folders to the headless page."""
    path = route.request.url.removeprefix(ORIGIN).split("?")[0]
    if path.startswith("/fonts/"):
        f = PKG / "fonts" / path.removeprefix("/fonts/")
    else:
        f = PKG / "web" / path.lstrip("/")
    if not f.is_file():
        return route.fulfill(status=404, body="")
    route.fulfill(status=200, body=f.read_bytes(), content_type=mimetypes.guess_type(f.name)[0] or "application/octet-stream")


class OverlayRenderer:
    def __init__(self, width: int, height: int):
        from playwright.sync_api import sync_playwright

        self.width, self.height = width, height
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(args=["--font-render-hinting=none", "--disable-lcd-text"])
        scale = width / CANVAS_W
        self.scale = scale
        # CSS pixel step that lands on whole output pixels (1 at 1080p and 4K, 3 at 1440p)
        self.grid = Fraction(width, CANVAS_W).denominator
        self.page = self._browser.new_page(
            viewport={"width": CANVAS_W, "height": round(height / scale)},
            device_scale_factor=scale,
        )
        self.page.route(f"{ORIGIN}/**", _serve)
        self.page.goto(f"{ORIGIN}/overlay.html")
        # vertical position scales with the frame if its aspect is not exactly 9:16
        self.page.evaluate("document.body.style.height = window.innerHeight + 'px'")
        self.page.evaluate("window.ready")

    def png(self, header: dict | None, block: dict | None, style: dict | None, out: Path) -> tuple[Path, int]:
        """Draw one overlay; returns the PNG (cropped to the band that holds
        text, full width) and its vertical position in output pixels."""
        self.page.evaluate("([h, b, s]) => { setStyle(s); setHeader(h); setBlock(b); }", [header, block, style or {}])
        self.page.evaluate("document.fonts.ready")
        top, bottom = self.page.evaluate("""() => {
            let t = Infinity, b = -Infinity;
            for (const el of document.querySelectorAll('#header .o, #block .o, #mic')) {
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
                             clip={"x": 0, "y": y0, "width": CANVAS_W, "height": max(q, y1 - y0)})
        return out, round(y0 * self.scale)

    def close(self):
        self._browser.close()
        self._pw.stop()


# ---------------------------------------------------------------- geometry

def output_size(info: media.VideoInfo, opt: RenderOptions) -> tuple[int, int]:
    if opt.size != "auto":
        w, h = (int(x) for x in opt.size.split("x"))
        return w, h
    # native resolution of a vertical source, never below 1080x1920
    if info.width * 16 == info.height * 9 and info.width >= CANVAS_W:
        return info.width - info.width % 2, info.height - info.height % 2
    return CANVAS_W, CANVAS_H


# HDR (iPhone HLG, PQ) -> SDR BT.709 before the text goes on, otherwise white
# subtitles would be drawn at full HDR brightness.
TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
           "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p10le")
SCALE = "flags=lanczos+accurate_rnd+full_chroma_int"
MOTION_ZOOM = 1.12  # slow zoom on a background clip: from 1 to this factor (or back)


# ---------------------------------------------------------------- background
#
# The background is a sequence of clips on the source timeline, each either
# the original video (in sync with the recitation) or an imported photo or
# video, with its own framing:
#   zoom  1 = whole picture visible; larger = closer (see cover_zoom)
#   x, y  offset of the picture centre, in fractions of the frame width/height
#   motion "none" | "in" | "out"  slow zoom over the clip

def cover_zoom(sw: int, sh: int) -> float:
    """Zoom at which a sw x sh picture exactly fills the 9:16 frame."""
    r = (CANVAS_W / CANVAS_H) * sh / sw
    return max(r, 1 / r)


def default_background(sw: int, sh: int, fit: str = "auto") -> dict:
    """The original video alone, framed as the old `fit` setting did."""
    if fit == "auto":
        fit = "crop" if sw / sh < 0.8 else "blur"
    return {"clips": [new_clip("original", sw, sh, fill=fit == "crop")], "transition": 0.5,
            "fill": "black" if fit == "pad" else "blur", "dim": 0.0}


def new_clip(src: str, sw: int, sh: int, dur: float = 5.0, fill: bool = True) -> dict:
    return {"src": src, "dur": dur, "zoom": round(cover_zoom(sw, sh), 4) if fill else 1.0,
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
    bw, bh = w // 4 // 2 * 2, h // 4 // 2 * 2
    return (f"split=2[{tag}bg][{tag}fg];[{tag}bg]scale={bw}:{bh}:force_original_aspect_ratio=increase,crop={bw}:{bh},"
            f"boxblur=20:2,scale={w}:{h}:{SCALE},eq=brightness=-0.08[{tag}bgb];[{tag}fg]{pic}[{tag}fgs];"
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


def _prep(info: media.VideoInfo | None) -> str:
    """Bring any source to BT.709 limited-range yuv444p."""
    pre = f"{TONEMAP}," if info is not None and info.is_hdr and "zscale" in media.encoders() else ""
    return f"{pre}scale=out_color_matrix=bt709:out_range=tv:{SCALE},format=yuv444p"


class _Inputs:
    def __init__(self):
        self.args: list[str] = []
        self.n = 0

    def add(self, *args: str) -> int:
        self.args += list(args)
        self.n += 1
        return self.n - 1


def _background_graph(bg: dict, info: media.VideoInfo, video: Path, media_dir: Path | None,
                      t0: float, t1: float, w: int, h: int, inputs: _Inputs, graph: list[str]) -> str:
    """Adds the background (w x h, yuv444p, t1 - t0 long) to the graph; returns its label."""
    fps, rate = info.fps_str, info.fps
    spans = []
    for c, s, e in clip_spans(bg["clips"], info.duration):
        s, e = max(s, t0) - t0, min(e, t1) - t0
        if e - s >= 1 / rate:
            spans.append((c, s, e))
    if not spans:
        spans = [(new_clip("original", info.width, info.height), 0.0, t1 - t0)]
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
            k = inputs.add("-ss", f"{t0 + a:.3f}", "-to", f"{t0 + b:.3f}", "-i", str(video))
            head = f"[{k}:v]setpts=PTS-STARTPTS,{_prep(sinfo)}"
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
                k = inputs.add("-stream_loop", "-1", "-ss", f"{float(c.get('offset') or 0):.3f}", "-i", str(f))
                head = f"[{k}:v]trim=duration={length:.3f},setpts=PTS-STARTPTS,{_prep(sinfo)}"
        sw, sh = (sinfo.width, sinfo.height) if sinfo else (sw, sh)
        chain = head + "," + frame_filter(sw, sh, fw, fh, float(c.get("zoom") or 1), float(c.get("x") or 0),
                                          float(c.get("y") or 0), bg.get("fill", "blur"), f"f{i}")
        if sinfo is None:  # a photo: framed once, then repeated
            chain += f",loop=loop={frames - 1}:size=1:start=0,setpts=N/({fps})/TB"
        if motion != "none":
            chain += "," + motion_filter(w, h, motion, frames)
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
    dim = float(bg.get("dim") or 0)
    if dim > 0:
        graph.append(f"[{last}]drawbox=t=fill:c=black@{min(dim, 0.9):.2f}[bgdim]")
        last = "bgdim"
    return last


def _encode_args(info: media.VideoInfo, opt: RenderOptions) -> tuple[list[str], str]:
    enc = media.encoders()
    tags = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]
    if opt.quality == "prores":
        return ["-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "apl0", *tags], ".mov"
    if opt.quality == "hevc" and "libx265" in enc:
        return ["-c:v", "libx265", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p10le", "-tag:v", "hvc1",
                "-x265-params", "aq-mode=3:no-sao=1:deblock=-1,-1:log-level=error", *tags], ".mp4"
    crf = "12" if opt.quality == "max" else "16"
    return ["-c:v", "libx264", "-preset", "slower", "-crf", crf, "-pix_fmt", "yuv420p", "-profile:v", "high",
            "-x264-params", "aq-mode=3:deblock=-1,-1", *tags], ".mp4"


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
           background: dict | None = None, media_dir: Path | None = None) -> Path:
    opt = opt or RenderOptions()
    progress = progress or (lambda stage, f: None)
    info = media.probe(video)
    w, h = output_size(info, opt)
    t0 = max(0.0, opt.trim_start)
    t1 = min(info.duration, opt.trim_end) if opt.trim_end else info.duration
    work = out.parent / f".{out.stem}-overlays"
    work.mkdir(parents=True, exist_ok=True)

    # 1) overlays
    shown = [b for b in blocks if b.end > t0 and b.start < t1]
    renderer = OverlayRenderer(w, h)
    try:
        header = renderer.png({"title": title, "reciter": reciter, "visible": opt.show_header}, None, style, work / "header.png")
        pngs = []
        for i, b in enumerate(shown):
            pngs.append(renderer.png(None, block_payload(b), style, work / f"block{i:03d}.png"))
            progress("overlays", (i + 1) / max(1, len(shown)))
    finally:
        renderer.close()

    # 2) compose + encode
    # Each overlay PNG is decoded and colour-converted once, then repeated with
    # the loop filter (cheap), faded, and placed at its time and height.
    fps = info.fps_str
    total = t1 - t0
    to_yuv = "format=rgba,scale=out_color_matrix=bt709:out_range=tv,format=yuva444p"

    def still(k: int, dur: float) -> str:
        n = math.ceil(dur * info.fps) + 1
        return f"[{k}:v]{to_yuv},loop=loop={n - 1}:size=1:start=0,setpts=N/({fps})/TB"

    inputs = _Inputs()
    audio = inputs.add("-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", str(video))
    graph: list[str] = []
    base = _background_graph(background or default_background(info.width, info.height, opt.fit),
                             info, video, media_dir, t0, t1, w, h, inputs, graph)
    hdr = inputs.add("-i", str(header[0]))
    graph.append(f"{still(hdr, total)}[hdr]")
    graph.append(f"[{base}][hdr]overlay=x=0:y={header[1]}:format=yuv444:eof_action=pass[v0]")
    last = "v0"
    for i, (b, (png, y)) in enumerate(zip(shown, pngs)):
        s, e = max(b.start, t0) - t0, min(b.end, t1) - t0
        dur = max(e - s, 1 / info.fps)
        fi, fo = min(opt.fade_in, dur / 3), min(opt.fade_out, dur / 3)
        k = inputs.add("-i", str(png))
        fade_in = f"fade=t=in:st=0:d={fi:.3f}:alpha=1," if b.start > t0 + 0.01 and fi > 0 else ""
        fade_out = f"fade=t=out:st={dur - fo:.3f}:d={fo:.3f}:alpha=1," if fo > 0 else ""
        graph.append(f"{still(k, dur)},{fade_in}{fade_out}trim=duration={dur:.3f},setpts=PTS+{s:.3f}/TB[o{i}]")
        graph.append(f"[{last}][o{i}]overlay=x=0:y={y}:format=yuv444:eof_action=pass[v{i + 1}]")
        last = f"v{i + 1}"
    vargs, ext = _encode_args(info, opt)
    out = out.with_suffix(ext)
    graph.append(f"[{last}]format={'yuv422p10le' if opt.quality == 'prores' else 'yuv420p10le' if opt.quality == 'hevc' else 'yuv420p'}[vout]")
    afi, afo = min(opt.audio_fade_in, total / 2), min(opt.audio_fade_out, total / 2)
    if info.acodec is not None and (afi > 0 or afo > 0):
        fades = ([f"afade=t=in:st=0:d={afi:.3f}"] if afi > 0 else []) + \
                ([f"afade=t=out:st={total - afo:.3f}:d={afo:.3f}"] if afo > 0 else [])
        graph.append(f"[{audio}:a]{','.join(fades)}[aout]")
        amap = ["-map", "[aout]"]
    else:
        amap = ["-map", f"{audio}:a?"]
    script = work / "graph.txt"
    script.write_text(";\n".join(graph))
    cmd = [media.tools()[0], "-y", "-hide_banner", "-loglevel", "error", "-stats_period", "0.5", "-progress", "pipe:1",
           *inputs.args, *_graph_arg(script), "-map", "[vout]", *amap,
           "-fps_mode", "cfr", "-r", fps, *vargs,
           *_audio_args(info, t0 > 0 or t1 < info.duration or afi > 0 or afo > 0),
           "-movflags", "+faststart", "-t", f"{total:.3f}", str(out)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for line in proc.stdout:
        m = re.match(r"out_time_us=(\d+)", line)
        if m:
            progress("encoding", min(1.0, int(m.group(1)) / 1e6 / total))
    err = proc.stderr.read()
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg failed:\n{err[-3000:]}")
    progress("encoding", 1.0)
    return out
