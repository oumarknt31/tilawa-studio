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
    fit: str = "auto"  # how a non-vertical source fills the 9:16 frame: "auto" | "crop" | "blur" | "pad"
    quality: str = "max"  # "max" (H.264 CRF 12) | "high" (CRF 16) | "hevc" (10-bit H.265) | "prores" (editing master)
    fade_in: float = 0.25
    fade_out: float = 0.25
    show_header: bool = True
    trim_start: float = 0.0
    trim_end: float | None = None


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


def _base_filter(info: media.VideoInfo, w: int, h: int, fit: str) -> str:
    """Filter chain that turns the source into a w x h 9:16 frame."""
    chain = _fit_filter(info, w, h, fit)
    if info.is_hdr and "zscale" in media.encoders():
        return f"{TONEMAP},{chain}" if chain != "null" else TONEMAP
    return chain


def _fit_filter(info: media.VideoInfo, w: int, h: int, fit: str) -> str:
    sc = "flags=lanczos+accurate_rnd+full_chroma_int"
    src_ar, dst_ar = info.width / info.height, w / h
    if abs(src_ar - dst_ar) < 0.01:
        if (info.width, info.height) == (w, h):
            return "null"
        return f"scale={w}:{h}:{sc}"
    if fit == "auto":
        # a slightly off vertical video is cropped; a landscape one keeps its full picture
        fit = "crop" if src_ar < 0.8 else "blur"
    if fit == "crop":
        return f"scale={w}:{h}:force_original_aspect_ratio=increase:{sc},crop={w}:{h}"
    if fit == "pad":
        return f"scale={w}:{h}:force_original_aspect_ratio=decrease:{sc},pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black"
    # blur: the picture fitted in the middle over a blurred, enlarged copy of itself
    return (
        f"split=2[bg][fg];"
        f"[bg]scale={w // 4}:{h // 4}:force_original_aspect_ratio=increase,crop={w // 4}:{h // 4},"
        f"boxblur=20:2,scale={w}:{h}:{sc},eq=brightness=-0.08[bgb];"
        f"[fg]scale={w}:{h}:force_original_aspect_ratio=decrease:{sc}[fgs];"
        f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2"
    )


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
           progress: Callable[[str, float], None] | None = None) -> Path:
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

    inputs = ["-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", str(video), "-i", str(header[0])]
    graph = [f"[0:v]setpts=PTS-STARTPTS,{_base_filter(info, w, h, opt.fit)},format=yuv444p[base0]"]
    graph.append(f"{still(1, total)}[hdr]")
    graph.append(f"[base0][hdr]overlay=x=0:y={header[1]}:format=yuv444:eof_action=pass[v0]")
    last = "v0"
    for i, (b, (png, y)) in enumerate(zip(shown, pngs)):
        s, e = max(b.start, t0) - t0, min(b.end, t1) - t0
        dur = max(e - s, 1 / info.fps)
        fi, fo = min(opt.fade_in, dur / 3), min(opt.fade_out, dur / 3)
        inputs += ["-i", str(png)]
        fade_in = f"fade=t=in:st=0:d={fi:.3f}:alpha=1," if b.start > t0 + 0.01 and fi > 0 else ""
        fade_out = f"fade=t=out:st={dur - fo:.3f}:d={fo:.3f}:alpha=1," if fo > 0 else ""
        graph.append(f"{still(i + 2, dur)},{fade_in}{fade_out}trim=duration={dur:.3f},setpts=PTS+{s:.3f}/TB[o{i}]")
        graph.append(f"[{last}][o{i}]overlay=x=0:y={y}:format=yuv444:eof_action=pass[v{i + 1}]")
        last = f"v{i + 1}"
    vargs, ext = _encode_args(info, opt)
    out = out.with_suffix(ext)
    graph.append(f"[{last}]format={'yuv422p10le' if opt.quality == 'prores' else 'yuv420p10le' if opt.quality == 'hevc' else 'yuv420p'}[vout]")
    script = work / "graph.txt"
    script.write_text(";\n".join(graph))
    cmd = [media.tools()[0], "-y", "-hide_banner", "-loglevel", "error", "-stats_period", "0.5", "-progress", "pipe:1",
           *inputs, *_graph_arg(script), "-map", "[vout]", "-map", "0:a?",
           "-fps_mode", "cfr", "-r", fps, *vargs, *_audio_args(info, t0 > 0 or t1 < info.duration),
           "-movflags", "+faststart", "-t", f"{t1 - t0:.3f}", str(out)]
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
