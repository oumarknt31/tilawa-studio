"""Background pictures made by OpenAI's image model, one per verse: the meaning of the verse
shown with landscapes, light and symbols, never people, animals, religious figures or writing.

Only for whoever puts their own OpenAI API key in the app (kept in the Tilawa Studio folder,
never sent anywhere but to OpenAI). The images are paid on that account, per image."""

from __future__ import annotations

import base64
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import quran
from .i18n import UserError

API = os.environ.get("TILAWA_OPENAI_URL", "https://api.openai.com/v1")  # (tests: a local stand-in)
MODEL = "gpt-image-2"
QUALITY = "medium"
PRICE = 0.04  # US$ per medium portrait image (gpt-image-2, OpenAI's pricing, November 2026)
SIZES = {"9:16": "1024x1536", "4:5": "1024x1536", "1:1": "1024x1024", "16:9": "1536x1024"}
SHAPES = {"9:16": "vertical", "4:5": "vertical", "1:1": "square", "16:9": "horizontal"}
STYLE = ("cinematic digital painting, soft golden-hour light, gentle haze, rich but muted colours, "
         "serene and majestic atmosphere")


def prompt(s: int, a: int, fmt: str = "9:16", style: str = "") -> str:
    """What the image model is asked for a verse (s:a, its Hafs key), from its English meaning."""
    name = quran.surah(s)["name"]
    meaning = quran.translation("en", s, a) or quran.translation("fr", s, a)
    return (f"A {SHAPES.get(fmt, 'vertical')} background picture for a video of a Quran recitation, "
            f"expressing the meaning of this verse (Surah {name}, verse {a}): \"{meaning}\"\n\n"
            "Show the meaning through nature, light, sky, water, landscapes, places or symbolic objects, "
            "as one calm, evocative scene.\n"
            "Never show people, faces, hands, silhouettes, animals or any living being. Never depict God, "
            "prophets, angels, Paradise or Hell literally: only suggest them through light and landscape.\n"
            "No text, letters, calligraphy, numbers or logos anywhere in the image.\n"
            "Keep the main subject in the centre, with calm, darker areas where subtitles will be written; "
            "avoid busy detail.\n"
            f"Style: {(style or STYLE).strip()}")


# ---------------------------------------------------------------- the key, on this computer only

def key_file(home: Path) -> Path:
    return Path(home) / "openai_key"


def load_key(home: Path) -> str:
    try:
        return key_file(home).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def save_key(home: Path, key: str) -> None:
    f = key_file(home)
    if not key:
        f.unlink(missing_ok=True)
        return
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(key.strip(), encoding="utf-8")
    try:
        os.chmod(f, 0o600)  # readable by its owner only
    except OSError:
        pass


# ---------------------------------------------------------------- OpenAI

def _context() -> ssl.SSLContext:
    import certifi

    return ssl.create_default_context(cafile=certifi.where())


def _call(key: str, path: str, body: dict | None = None, timeout: float = 240) -> dict:
    req = urllib.request.Request(f"{API}/{path}", data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                                 method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_context() if API.startswith("https") else None) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read()).get("error") or {}
        except ValueError:
            err = {}
        code, msg = err.get("code") or "", err.get("message") or str(e)
        if e.code == 401:
            raise UserError("openai_key") from e
        if code == "insufficient_quota" or "billing" in msg.lower():
            raise UserError("openai_credit") from e
        if code in ("moderation_blocked", "content_policy_violation") or "safety" in msg.lower():
            raise UserError("openai_refused") from e
        if e.code == 429:
            raise _Busy(msg) from e
        raise UserError("openai_failed", msg=msg) from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise UserError("download_failed") from e


class _Busy(Exception):
    """Too many requests at once: wait and ask again."""


def check_key(key: str) -> None:
    """Refused here if OpenAI does not know the key (it costs nothing)."""
    _call(key, "models", timeout=30)


def generate(key: str, text: str, fmt: str = "9:16", tries: int = 4) -> bytes:
    """One picture (PNG or JPEG bytes) for a prompt."""
    for k in range(tries):
        try:
            r = _call(key, "images/generations", {"model": MODEL, "prompt": text, "size": SIZES.get(fmt, "1024x1536"),
                                                  "quality": QUALITY, "n": 1})
            return base64.b64decode(r["data"][0]["b64_json"])
        except _Busy:
            if k == tries - 1:
                raise UserError("openai_failed", msg="rate limit")
            time.sleep(10 * (k + 1))
    raise UserError("openai_failed", msg="")
