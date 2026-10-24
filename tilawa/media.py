"""ffmpeg / ffprobe / yt-dlp helpers."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from .i18n import UserError


def _capabilities(ff: str) -> set[str]:
    out = subprocess.run([ff, "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    out += subprocess.run([ff, "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    return {line.split()[1] for line in out.splitlines() if len(line.split()) > 1 and line.startswith(" ")}


@lru_cache(maxsize=None)
def tools() -> tuple[str, str]:
    """Paths to ffmpeg and ffprobe. A system install is used if it has
    everything we need (x264 + zscale for HDR sources); otherwise the static
    build shipped with static-ffmpeg, which has both."""
    ff, fp = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if ff and fp and {"libx264", "zscale"} <= _capabilities(ff):
        return ff, fp
    try:
        import static_ffmpeg.run

        return static_ffmpeg.run.get_or_fetch_platform_executables_else_raise()
    except Exception:
        if ff and fp:
            return ff, fp
        raise


@lru_cache(maxsize=None)
def encoders() -> set[str]:
    """Encoders and filters available in the chosen ffmpeg."""
    return _capabilities(tools()[0])


@dataclass
class VideoInfo:
    path: Path
    width: int  # display width (rotation applied)
    height: int
    fps: float
    fps_str: str
    duration: float
    vcodec: str
    pix_fmt: str
    bit_depth: int
    color_primaries: str | None
    color_transfer: str | None
    color_space: str | None
    color_range: str | None
    acodec: str | None
    asample_rate: int | None
    achannels: int | None

    @property
    def is_hdr(self) -> bool:
        return self.color_transfer in ("smpte2084", "arib-std-b67")


VIDEO_FORMATS = {"mov", "mp4", "matroska", "webm", "avi", "mpegts", "flv", "mpeg", "3gp"}


def probe(path: str | Path) -> VideoInfo:
    out = subprocess.run(
        [tools()[1], "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    d = json.loads(out)
    # playlist-like formats (hls, concat...) can pull in other files from the disk: real video containers only
    if not set(d.get("format", {}).get("format_name", "").split(",")) & VIDEO_FORMATS:
        raise UserError("unsupported_video")
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    if v is None:
        raise UserError("no_video_stream")
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list", []):
        if "rotation" in sd:
            rot = int(sd["rotation"])
    if abs(rot) % 180 == 90:
        w, h = h, w
    fps_str = v.get("avg_frame_rate") or v.get("r_frame_rate") or "30/1"
    if fps_str in ("0/0", "0/1"):
        fps_str = v.get("r_frame_rate", "30/1")
    num, den = (int(x) for x in fps_str.split("/"))
    pix = v.get("pix_fmt", "yuv420p")
    depth = int(v.get("bits_per_raw_sample") or (10 if "10" in pix else 12 if "12" in pix else 8))
    dur = float(d["format"].get("duration") or v.get("duration") or 0)
    return VideoInfo(
        Path(path), w, h, num / den, fps_str, dur, v["codec_name"], pix, depth,
        v.get("color_primaries"), v.get("color_transfer"), v.get("color_space"), v.get("color_range"),
        a["codec_name"] if a else None, int(a["sample_rate"]) if a else None, int(a.get("channels", 2)) if a else None,
    )


def load_audio(path: str | Path, sr: int = 16000) -> np.ndarray:
    """Mono float32 audio at `sr` Hz."""
    out = subprocess.run(
        [tools()[0], "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
        capture_output=True, check=True,
    ).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def _js_runtimes() -> dict:
    try:
        from playwright._impl._driver import compute_driver_executable

        node = Path(compute_driver_executable()[0])
        if node.exists():
            return {"node": {"path": str(node)}}
    except Exception:
        pass
    return {"deno": {}}


def link_info(url: str) -> dict:
    """What a video link says about itself (title, channel, licence...), without downloading it."""
    import certifi
    import yt_dlp

    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "noplaylist": True, "js_runtimes": _js_runtimes()}) as ydl:
        return ydl.extract_info(url, download=False)


def download(url: str, dest_dir: Path, progress=None, info: dict | None = None) -> Path:
    """Download the best available quality of a video URL with yt-dlp (info: filled with what
    the link says about itself)."""
    import certifi
    import yt_dlp

    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    dest_dir.mkdir(parents=True, exist_ok=True)

    def hook(d):
        if progress and d.get("status") == "downloading" and d.get("total_bytes"):
            progress(d["downloaded_bytes"] / d["total_bytes"])

    opts = {
        # best video + best audio; prefer higher resolution, then higher fps, then bitrate
        "format": "bv*+ba/b",
        "format_sort": ["res", "fps", "hdr:12", "vbr", "abr"],
        "merge_output_format": "mkv",  # mkv holds any codec combination without re-encoding
        # the app's own ffmpeg (yt-dlp would look on the PATH, where there is none on most computers)
        "ffmpeg_location": str(Path(tools()[0]).parent),
        # YouTube asks to solve a JavaScript challenge: with the Node.js that comes with Playwright
        # (and the yt-dlp-ejs solver), so nothing has to be installed
        "js_runtimes": _js_runtimes(),
        "outtmpl": str(dest_dir / "source.%(ext)s"),
        "quiet": True,
        "noprogress": True,
        "progress_hooks": [hook],
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        got = ydl.extract_info(url, download=True)
        path = Path(ydl.prepare_filename(got)).with_suffix(".mkv")
    if info is not None:
        info.update(got)
    if not path.exists():
        matches = sorted(dest_dir.glob("source.*"))
        if not matches:
            raise RuntimeError("Download failed")
        path = matches[0]
    return path


def make_preview(src: Path, dst: Path) -> Path:
    """Small H.264 copy that every browser can play, for the editor only."""
    subprocess.run(
        [tools()[0], "-y", "-v", "error", "-i", str(src), "-vf", "scale=-2:'min(960,ih)'", "-c:v", "libx264",
         "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p", "-g", "30", "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", str(dst)],
        check=True,
    )
    return dst


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".avif", ".tif", ".tiff", ".bmp"}


def import_image(src: Path, dst: Path) -> tuple[int, int]:
    """Normalise a photo for the renderer and the browser alike: EXIF rotation
    applied, colour profile converted to sRGB (iPhone photos are Display P3),
    transparency flattened on black, saved losslessly as PNG."""
    import io

    import pillow_heif
    from PIL import Image, ImageCms, ImageOps

    pillow_heif.register_heif_opener()
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        icc = im.info.get("icc_profile")
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            flat = Image.new("RGB", im.size, "black")
            flat.paste(im, mask=im.getchannel("A"))
            im = flat
        elif im.mode != "RGB":
            im = im.convert("RGB")
        if icc:
            try:
                im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)),
                                               ImageCms.createProfile("sRGB"), outputMode="RGB")
            except Exception:
                pass  # broken profile: keep the pixels as they are
        im.save(dst, "PNG", compress_level=3)
        return im.size


def pingpong(src: Path, dst: Path, preview: bool = False) -> Path:
    """One back-and-forth cycle of a video (forward, then backward), which
    loops without a jump. The turning frames are not repeated. Reversing
    needs the frames in memory, so the backward half is made in short
    chunks. Full quality: 10-bit x264 at CRF 8 (visually lossless)."""
    info = probe(src)
    fps = info.fps_str
    rate = info.fps
    work = dst.parent / f".{dst.stem}-parts"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    if preview:
        enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", "-g", "15"]
    else:
        tags = []
        for opt, val in (("-color_primaries", info.color_primaries), ("-color_trc", info.color_transfer),
                         ("-colorspace", info.color_space), ("-color_range", info.color_range)):
            if val and val != "unknown":
                tags += [opt, val]
        enc = ["-c:v", "libx264", "-preset", "fast", "-crf", "8",
               "-pix_fmt", "yuv420p10le" if info.bit_depth > 8 else "yuv420p", *tags]
    ff = [tools()[0], "-y", "-v", "error"]
    fwd = work / "0000.mkv"
    subprocess.run([*ff, "-i", str(src), "-an", "-vf", "setpts=PTS-STARTPTS", "-fps_mode", "cfr", "-r", fps, *enc,
                    str(fwd)], check=True)
    n = round(probe(fwd).duration * rate)
    # frames n-2 .. 1, newest chunk first
    chunk = max(8, min(120, int(4e8 / max(1, info.width * info.height * 3))))
    parts = [fwd]
    b = n - 1
    while b > 1:
        a = max(1, b - chunk)
        out = work / f"{len(parts):04d}.mkv"
        subprocess.run([*ff, "-copyts", "-ss", f"{max(0.0, a / rate - 1):.3f}", "-i", str(fwd), "-an",
                        "-vf", f"trim=start={(a - 0.5) / rate:.4f}:end={(b - 0.5) / rate:.4f},setpts=PTS-STARTPTS,reverse",
                        "-fps_mode", "cfr", "-r", fps, *enc, str(out)], check=True)
        parts.append(out)
        b = a
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    subprocess.run([*ff, "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(dst)], check=True)
    shutil.rmtree(work, ignore_errors=True)
    return dst


def loudnorm_filter(src: Path, t0: float, t1: float, target: float = -14.0) -> str:
    """Two-pass loudness normalisation: measure the passage, then return the
    filter that brings it to `target` LUFS (true peak -1 dBTP) with one
    constant gain, so the recitation's dynamics stay untouched."""
    out = subprocess.run([tools()[0], "-hide_banner", "-nostats", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", str(src),
                          "-vn", "-af", f"loudnorm=I={target}:TP=-1:LRA=20:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = json.loads(out[out.rindex("{"): out.rindex("}") + 1])
    return (f"loudnorm=I={target}:TP=-1:LRA=20:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
            f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")


AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg", ".opus"}


def has_video(path: str | Path) -> bool:
    out = subprocess.run([tools()[1], "-v", "error", "-select_streams", "v", "-show_entries", "stream=codec_type",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout
    return "video" in out


def audio_to_video(src: Path, dst: Path, width: int, height: int) -> Path:
    """A recitation without picture: a plain dark frame carrying the sound,
    to be covered by the user's own photos and videos."""
    acodec = subprocess.run([tools()[1], "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name",
                             "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout.strip()
    enc = "aac_at" if "aac_at" in encoders() else "aac"
    audio = ["-c:a", "copy"] if acodec == "aac" else ["-c:a", enc, "-b:a", "320k"]
    subprocess.run([tools()[0], "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=0x0f1418:s={width}x{height}:r=30",
                    "-i", str(src), "-map", "0:v", "-map", "1:a", "-shortest", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "18", "-tune", "stillimage", "-pix_fmt", "yuv420p", *audio, "-movflags", "+faststart", str(dst)],
                   check=True)
    return dst
