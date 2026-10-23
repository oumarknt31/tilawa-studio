# Tilawa Studio

[Français](README.fr.md) · **English**

Turns a Quran recitation (a video, a link or just an audio file) into a subtitled video:
**surah and reciter names at the top, verse number, translation, Arabic text and transliteration**,
each part appearing exactly when the reciter says it. The app **recognises the surah and verses
on its own**. No need to read Arabic.

Formats: vertical 9:16 (Shorts, Reels, TikTok), horizontal 16:9 (YouTube), square 1:1 and portrait 4:5,
from Full HD to 4K. Translations: French (Hamidullah, Rachid Maach or Noor International Center), English
(Saheeh International, Yusuf Ali or Pickthall), Spanish, German, Italian, Portuguese, Dutch,
Swedish, Turkish, Indonesian, Malay, Bosnian, Albanian, Russian, Urdu, or Arabic only.
The interface is in English or French (**FR | EN** switch at the top right).

## Installation (once)

You need an **Apple Silicon Mac (M1 or newer)** or a **Windows 10/11 PC**, about
**5 GB of free space** and an internet connection for the installation.

- **Mac**: open the *Terminal* app, paste this line and press Enter:

  ```bash
  curl -LsSf https://raw.githubusercontent.com/oumarknt31/tilawa-studio/main/install.sh | bash
  ```

  At the end, **Tilawa Studio** is in your Applications folder (Launchpad, Spotlight, and you can keep
  it in the Dock) and opens in its own window. Updates are then done **from inside the app**
  (a ✨ *Update* button appears when a new version is out); your projects and videos are kept.

  If you downloaded the ZIP from GitHub instead: double-click `Installer (Mac).command`.
  If the Mac refuses to open it: *System Settings* → *Privacy & Security* → *Open Anyway*.
- **Windows**: download the ZIP (green *Code* button → *Download ZIP*), unzip it,
  then double-click `Installer (Windows).bat`.
  If Windows shows "Windows protected your PC": *More info* → *Run anyway*.
  At the end, **Tilawa Studio** is in the Start menu and on the desktop.

The installation downloads the components, the recitation recognition model
(~1.2 GB) and ffmpeg. Allow 5 to 15 minutes depending on the connection.

## Use

1. Open **Tilawa Studio** like any app (Launchpad, Spotlight, Dock / Start menu, desktop).
   It opens in its own window; closing the window quits the app (it asks first if a video is being made).
   To use it in a browser instead: `Tilawa Studio.command` (Mac) or `Tilawa Studio.bat` (Windows),
   keeping the black window open.
2. **Drop a video** (or paste a YouTube / Instagram / TikTok link, or drop an mp3 / m4a… audio file),
   then choose the **format**, the **translation**, the **style** and the reciter's name.
   The surah and verses are **detected automatically** (you can also choose them yourself).
3. **Create my video**: the app listens to the recitation, recognises the passage and finds every word (10 to 60 seconds).
4. **Check and customise** in the editor (icons on the left). The preview shows exactly the final result.
   - **Subtitles**:
     - ▶ to listen to a passage again; edit the translation right in its box;
     - **Wrong verse?** under a subtitle: many verses repeat word for word or nearly (Ar-Rahman's refrain,
       similar verses in other surahs). The app lists those that read the same, says how well each matches what
       it hears, marks the one that follows the previous verse, and aligns that stretch again with the one chosen.
       If the whole passage is wrong, the other passages it recognised are offered at the top of the list;
     - correct the Arabic or the transliteration by clicking it (↺ *Original text* to undo);
     - click a transliterated word (✂) to **split** a subtitle before that word, *Merge* to join two;
     - −/+ to shift a subtitle by 0.05 s, *⤓ here* to set it at the playhead;
     - ✨ *Highlight* for passages in colour (automatic for "Subhana Allah").
   - **Background**: keep the original video, or import **your own photos and videos**
     (jpg, png, iPhone heic, mp4, mov…); the sound stays the recitation's.
     - **1 item**: it fills the whole video. **Several**: one per verse (the 2nd comes with the 2nd verse…),
       the last until the end. *Match the verses* / *Spread evenly* to redo the timing.
     - A video shorter than its slot plays **back and forth** (forward, then reversed): a loop with no jump.
     - For each item: X/Y position and scale (like in Premiere), *Fill the screen* / *Whole picture*,
       slow zoom, and **colour**: exposure, contrast, highlights, shadows, saturation, temperature, tint.
     - Drag the picture on the preview to move it; pinch the trackpad (or Ctrl + wheel) to zoom.
   - **Style**:
     - ready-made **themes** (Le Chemin des Pieux, Golden Mushaf, Modern, Soft, Elegant, Calligraphy);
       *Save my style* keeps it for all your videos, ★ makes it the default;
     - **fonts** for the title, the Arabic (Amiri Quran, Scheherazade — like the Medina Quran —, Noto Naskh,
       Amiri, Kufic, ruqʿa) and the translation; *Import a font* for your own (.ttf, .otf),
       for example the official King Fahd Complex Mushaf font;
     - **verse number** in its ornament at the end of the verse (۝١٢ or ﴿١٢﴾);
     - sizes, colours (title and reciter as gradients), X/Y positions to the pixel;
     - translation language and, in French and English, which translation (replaces the whole translation, split like the Arabic);
     - how the **transliteration** is written: *easy to read* (Wal yawmil maw'ood), the same with French spelling
       (maw'oud), *scholarly* (wa-l-yawmi l-mawʿūd) or Tanzil's. It is written from the Arabic, word by word, with the
       same rules everywhere (the article and sun letters, the connecting hamza, the pause at the end of a subtitle),
       so no part is ever missing and a cut or corrected passage always reads the same way;
     - **for YouTube (16:9)**, styles modelled on popular recitation channels: *Cinema* (Arabic on top,
       numbered translation in capitals with its key words in bold, light transliteration), *Le Chemin des
       Pieux — YouTube*, *Classic band*, *Headline band* (translation in the middle, Arabic and transliteration
       in a translucent band at the bottom), *Golden cinema*, *Minimal*;
     - **layout** (stacked, Arabic on top, band at the bottom); **key words** of the translation in bold or
       in colour, found automatically or chosen by putting *asterisks* around them; capitals or small caps;
       outline thickness (or just a soft shadow);
     - title and reciter at the top, as a small **label in a corner**, or as **intro cards** before the
       recitation (the surah, "Chapter 2 of the Noble Quran", "Recited by…"; ▶ *Preview the intro*);
     - your **logo** (channel, page): imported once, it goes on all your videos, in every format, at the
       best place for it: top left in vertical videos (below the top bar of TikTok, Reels and Shorts, clear
       of their buttons and caption, kept in Instagram's 4:5 preview), top right in 16:9 (YouTube puts its own
       watermark and the playback bar at the bottom right) and in square and portrait posts. It moves off the
       title if they would overlap. The *Logo* section shows the suggestions for the format with a small
       preview (hover over one to see it on the video); choose another corner, drag it on the preview, pinch
       to resize it, *No logo* for one video, or untick *On all my videos*.
   - **Audio**: start and end of the video (*Cut the silences* in one click), sound fades,
     **loudness optimised for social media** (−14 LUFS, the level of YouTube, TikTok and Instagram).
   - **Export**: format (or a copy of the project in another format), resolution, quality,
     full-resolution **image** (for a YouTube thumbnail), list of files already exported.
   - **Timeline** (bottom): drag the edges of a subtitle to change its timing, the edge of a
     background item to change its length; the **pink handles** cut the start and the end.
   - **App safe zones** (below the preview): shows where TikTok, Reels and Shorts put their buttons.
   - ↶ *Undo* (⌘Z / Ctrl+Z) undoes the last change. Everything is saved automatically.
5. **Create the video**. Videos are saved in the `Tilawa Studio/Videos` folder
   of your home folder.

Shortcuts: `Space` play/pause, `←` `→` previous/next subtitle, `⌘Z` / `Ctrl+Z` undo, `?` help.

### Video settings

| Setting | Advice |
|---|---|
| *Native* resolution | keeps the original resolution when the video already has the right shape (otherwise Full HD) |
| *4K* resolution | 2160 × 3840 vertical, 3840 × 2160 horizontal; the text is drawn in 4K. YouTube usually keeps its best encodings (VP9/AV1, higher bitrate) for high-resolution uploads: often sharper once published. ~3× longer to render |
| *Maximum* quality | H.264, visually identical to the source, plays everywhere. On a Mac it uses the Apple chip's video engine: a 2-minute video takes about 20 s in Full HD and 1 min in 4K (M4) |
| *10-bit (H.265)* quality | even more faithful (gradients), smaller files, less compatible with old devices |
| *ProRes master* | to keep editing in CapCut / Premiere / Final Cut without loss |
| *Cancel the export* | stops it at once (nothing is left half-made) |
| *Studio* quality | the same picture in a file about ⅓ smaller, with the slow software encoder (x264 *slower*): ~8× longer |
| Horizontal source video | *Background* tab: *Whole picture* (blurred or black behind) or *Fill the screen*, or any zoom |

HDR videos (iPhone) are converted automatically so the text keeps the right brightness.

## Command line

```bash
uv run tilawa make video.mp4 --reciter "Muhammad Dibirov"            # surah and verses detected
uv run tilawa make video.mp4 --surah 23 --from 84 --format 16:9 --lang en --style mushaf
uv run tilawa make "https://youtube.com/shorts/..." --size 4k
```

## How it works

1. **Listening** — a wav2vec2 model trained on Quran recitation
   ([rabah2026/wav2vec2-large-xlsr-53-arabic-quran-v_final](https://huggingface.co/rabah2026/wav2vec2-large-xlsr-53-arabic-quran-v_final))
   gives, every 20 ms, the probability of each Arabic letter.
   **Identification** (`tilawa/identify.py`): the most likely letters form a rough transcript,
   found in the whole Quran (6236 verses) by a vote of letter groups, then compared letter by letter
   with the best candidates.
2. **Forced alignment** — since the text is known, the best path of the text through those
   probabilities is searched (`tilawa/align.py`). The path allows the isti'adha and the basmala,
   silence and speech before/after, a video cut in the middle of a verse, an approximate starting
   verse, and the reciter's **repeats**.
3. **Splitting** (`tilawa/segment.py`) — one subtitle per verse; a new one at every **breath**
   of the reciter (measured on the sound, not on the letters, because madd and ghunna leave long
   gaps without a pause); verses that are too long are cut at the best place (pause marks, dips in the
   sound, punctuation). The translation is cut where it matches the Arabic, with the help of
   anchor words (قل → "Say" / "Dis" / "Di"…, سبحان → "Exalted"…).
4. **Rendering** (`tilawa/render.py`) — the text is drawn by Chromium (perfect Arabic shaping,
   outlines, gradients, emoji) directly at the final resolution, then ffmpeg lays those pictures
   over the background with the fades and encodes once. For the background, only the visible part
   of each picture is cropped, and it is coloured, darkened and crossfaded at the source's own resolution
   before a single enlargement to the final size: a 1080p video shown in 4K has no more detail, so this
   gives the same picture for a fraction of the work. The slow zoom is computed with sub-pixel precision
   (no jitter). Encoding uses the computer's video engine when there is one (Apple VideoToolbox, the way
   phone editing apps export fast), with settings chosen by VMAF measurements to match the quality of
   x264 at CRF 12; otherwise x264, and the software encoder takes over if the engine ever refuses a job. Photos are imported without loss: iPhone rotation applied,
   Display P3 colours converted to sRGB.

Tests: `uv run python -m pytest -q`

## Sources and licences

- Quran text: **Tanzil Project** (Uthmani text, CC BY 3.0, verbatim copy) — https://tanzil.net
- Translations, via Tanzil (`tilawa/data/trans/`, non-commercial use under Tanzil's terms):
  Muhammad Hamidullah (fr), Saheeh International (en), Julio Cortés (es), Bubenheim & Elyas (de),
  Hamza Roberto Piccardo (it), Samir El-Hayek (pt), Sofian S. Siregar (nl), Knut Bernström (sv),
  Diyanet İşleri (tr), Kementerian Agama RI (id), Abdullah Muhammad Basmeih (ms), Besim Korkut (bs),
  Sherif Ahmeti (sq), Elmir Kuliev (ru), Fateh Muhammad Jalandhry (ur).
- Transliteration: made from the Arabic by `tilawa/translit.py`; the *Tanzil* option is **Tanzil**'s
  (`en.transliteration`, three typos corrected).
- Translations from **QuranEnc.com**, republished unchanged under its terms (footnote markers and verse numbers
  left out for subtitles): Rachid Maach (`french_rashid`, version 1.0.3), Noor International Center, formerly
  Montada Islamic Foundation (`french_montada`, version 1.0.0). Also via Tanzil: Abdullah Yusuf Ali and
  Marmaduke Pickthall (en).
- Surah names: quran.com.
- Fonts (SIL Open Font License, see `tilawa/fonts/`): Amiri Quran, Amiri, Scheherazade New,
  Noto Naskh Arabic, Reem Kufi, Aref Ruqaa, Comic Neue, Poppins, Open Sans, Arimo, Oswald, Montserrat,
  Nunito, Baloo 2, Playfair Display, Lora, Cinzel.
- Recognition model: Apache 2.0.

The files in `tilawa/data/` are provided as is, with their copyright notices.
Make sure you have the right to republish the recitation videos you use.
