"""How likely a video taken from a link is to be claimed for copyright once posted.

Nobody can know for sure before uploading: YouTube (Content ID), TikTok and Meta
(Rights Manager) compare each upload's sound with the recordings their rights
holders registered, and none of them lets an app ask in advance. So this is an
estimate from what the link says about itself: its licence, rights notices in
its title and description, whether it comes from an official or large channel,
and on TikTok whether its sound is the poster's own. The page explains what each
platform does with a claim (index.html, rightsCard)."""

from __future__ import annotations

import re

# rights notices (several languages); "copyright free" and the like are looked for first
_FREE = re.compile(r"(no|free of|without|sans|bebas)\s*-?\s*copyright|copyright[ -]?free|libre de droits|sans droits"
                   r"|بدون حقوق|بدون حقوق نشر|free to use|royalty[ -]?free", re.I)
_NOTICE = re.compile(r"©|℗|all rights reserved|tous droits réservés|جميع الحقوق محفوظة|حقوق النشر|copyright"
                     r"|licensed to youtube|exclusive|حصري|official (audio|video|channel)", re.I)
_ORIGINAL_SOUND = re.compile(r"original sound|son original|sonido original|الصوت الأصلي|suara asli|orijinal ses", re.I)

BIG_CHANNEL = 500_000  # followers: channels this large usually have their recordings registered


def assess(info: dict) -> dict:
    """{site, title, channel, level: "high" | "medium" | "low", reasons: [{key, ...}]} from yt-dlp's info.
    reasons keys: cc, says_free, notice, official, big, music, original_sound, someone_else."""
    site = (info.get("extractor_key") or info.get("extractor") or "").lower()
    site = next((s for s in ("youtube", "tiktok", "instagram", "facebook") if s in site), site or "web")
    channel = info.get("channel") or info.get("uploader") or ""
    text = " ".join(str(info.get(k) or "") for k in ("title", "description"))
    followers = info.get("channel_follower_count") or 0
    reasons, level = [], "medium"
    track, artist = info.get("track"), info.get("artist")
    if info.get("license") and "creative commons" in str(info["license"]).lower():
        reasons.append({"key": "cc", "license": info["license"]})
        level = "low"
    elif _FREE.search(text):
        reasons.append({"key": "says_free"})  # the uploader's word: not a licence
    if track and not _ORIGINAL_SOUND.search(f"{track} {artist or ''}"):
        reasons.append({"key": "music", "track": track, "artist": artist or ""})
        level = "high"
    elif track:
        reasons.append({"key": "original_sound"})
    if _NOTICE.search(text) and not _FREE.search(text):
        reasons.append({"key": "notice"})
        level = "high"
    if re.search(r"official|رسمي|الرسمية", channel, re.I):
        reasons.append({"key": "official", "channel": channel})
        level = "high"
    elif followers >= BIG_CHANNEL or info.get("channel_is_verified"):
        reasons.append({"key": "big", "channel": channel, "followers": followers})
        if level != "low":
            level = "high"
    reasons.append({"key": "someone_else", "channel": channel})
    return {"site": site, "title": info.get("title") or "", "channel": channel, "level": level, "reasons": reasons}
