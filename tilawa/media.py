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
        raise ValueError(f"{path}: format vidéo non pris en charge")
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    if v is None:
        raise ValueError(f"{path} has no video stream")
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


def download(url: str, dest_dir: Path, progress=None) -> Path:
    """Download the best available quality of a video URL with yt-dlp."""
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
        "outtmpl": str(dest_dir / "source.%(ext)s"),
        "quiet": True,
        "noprogress": True,
        "progress_hooks": [hook],
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = Path(ydl.prepare_filename(info)).with_suffix(".mkv")
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
