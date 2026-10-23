"""Messages shown to the user, in French and English (the interface's two languages).

Code raises UserError("key", ...); the server turns it into the text of the
language the interface is in (sent by the page with every request)."""

from __future__ import annotations

UI_LANGS = ("fr", "en")

MESSAGES = {
    "not_recognized": (
        "Je n'ai pas reconnu de passage du Coran dans cette vidéo. Choisis la sourate et le premier verset à la main.",
        "No passage of the Quran was recognised in this video. Choose the surah and first verse yourself."),
    "no_verse": (
        "Aucun verset du passage choisi n'a été trouvé dans l'audio. Vérifie la sourate et le premier verset.",
        "No verse of the chosen passage was found in the audio. Check the surah and first verse."),
    "bad_verse": ("Le verset {s}:{a} n'existe pas.", "Verse {s}:{a} does not exist."),
    "bad_surah": ("La sourate doit être entre 1 et 114.", "The surah must be between 1 and 114."),
    "bad_range": ("Versets {first} à {last} impossibles pour cette sourate ({total} versets).",
                  "Verses {first} to {last} are not possible for this surah ({total} verses)."),
    "bad_format_lang": ("Format ou langue inconnus.", "Unknown format or language."),
    "bad_format": ("Format inconnu.", "Unknown format."),
    "need_source": ("Choisis un fichier vidéo ou colle un lien.", "Choose a video file or paste a link."),
    "need_https": ("Le lien doit commencer par https://", "The link must start with https://"),
    "bad_source": ("Format non reconnu : choisis une vidéo ou un fichier audio ({exts}).",
                   "Unrecognised format: choose a video or an audio file ({exts})."),
    "unsupported_video": ("Format vidéo non pris en charge.", "Unsupported video format."),
    "no_video_stream": ("Ce fichier ne contient pas d'image.", "This file contains no picture."),
    "bad_media": ("Format non reconnu : choisis une photo (jpg, png, heic…) ou une vidéo.",
                  "Unrecognised format: choose a photo (jpg, png, heic…) or a video."),
    "unreadable_media": ("Impossible de lire ce fichier (photo ou vidéo abîmée, ou format non pris en charge).",
                         "This file can't be read (damaged photo or video, or unsupported format)."),
    "bad_font": ("Choisis un fichier de police .ttf ou .otf", "Choose a .ttf or .otf font file"),
    "unreadable_font": ("Impossible de lire cette police.", "This font can't be read."),
    "bad_logo": ("Choisis une image (png, jpg, heic…) pour le logo.", "Choose a picture (png, jpg, heic…) for the logo."),
    "nothing_to_render": ("Rien à exporter : il n'y a pas de sous-titres.", "Nothing to export: there are no subtitles."),
    "cannot_split": ("Impossible de couper ici.", "Can't split here."),
    "cannot_merge": ("Seules deux parties qui se suivent dans le même verset peuvent être réunies.",
                     "Only two consecutive parts of the same verse can be merged."),
}


def text(key: str, lang: str = "en", **kw) -> str:
    fr, en = MESSAGES[key]
    return (fr if lang == "fr" else en).format(**kw)


class UserError(ValueError):
    """An error the user can do something about, shown in their language."""

    def __init__(self, key: str, **kw):
        self.key, self.kw = key, kw
        super().__init__(text(key, "en", **kw))

    def text(self, lang: str) -> str:
        return text(self.key, lang, **self.kw)
