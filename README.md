# Tilawa Studio

[Français](README.fr.md) · **English**

Turns a Quran recitation (a video, a link or just an audio file) into a subtitled video:
**surah and reciter names at the top, verse number, translation, Arabic text and transliteration**,
each part appearing exactly when the reciter says it. The app **recognises the surah and verses
on its own**, even several surahs in one video (a prayer: Al-Fatiha then another surah; the last
three surahs in a row). No need to read Arabic.

Formats: vertical 9:16 (Shorts, Reels, TikTok), horizontal 16:9 (YouTube), square 1:1 and portrait 4:5,
from Full HD to 4K. Translations: French (Hamidullah, Rachid Maach or Noor International Center), English
(Saheeh International, Yusuf Ali or Pickthall), Spanish, German, Italian, Portuguese, Dutch,
Swedish, Turkish, Indonesian, Malay, Bosnian, Albanian, Russian, Urdu, or Arabic only.
The interface is in English or French (**FR | EN** switch at the top right).

## Installation (once)

You need an **Apple Silicon Mac (M1 or newer)** or a **Windows 10/11 PC**, about **4 GB of free space**
and an internet connection. Nothing else to install: the app comes ready to use.

**On a Mac**

1. Open the **Terminal** app: press ⌘ (command) + Space, type `Terminal`, press Enter.
2. Copy this line, paste it in the Terminal window (⌘ + V) and press Enter:

   ```bash
   curl -LsSf https://raw.githubusercontent.com/oumarknt31/tilawa-studio/main/install.sh | bash
   ```

**On Windows**

1. Open **PowerShell**: click the Start menu, type `PowerShell`, press Enter.
2. Copy this line, paste it in the PowerShell window (right-click or Ctrl + V) and press Enter:

   ```powershell
   irm https://raw.githubusercontent.com/oumarknt31/tilawa-studio/main/install.ps1 | iex
   ```

The installation downloads the app (~500 MB) and, the first time only, the recitation recognition
model (~1.2 GB): allow 5 to 15 minutes depending on the connection, and keep the window open until
"Tilawa Studio is installed". The app then opens by itself.

Afterwards, **Tilawa Studio** is in your Applications folder (Launchpad, Spotlight; you can keep it in the
Dock) or in the Start menu and on the desktop. **Updates are done from inside the app**: when a new
version is out, a ✨ *Update* button appears at the top; one click and the app restarts on the new version.
Your projects and videos are kept. (Running the same line again also installs the latest version.)

No security warning appears: the line downloads the app the way macOS and Windows trust, unlike a file
downloaded in a browser.

## Use

1. Open **Tilawa Studio** like any app (Launchpad, Spotlight, Dock / Start menu, desktop).
   It opens in its own window; closing the window quits the app (it asks first if a video is being made).
2. **Drop a video** (or paste a YouTube / Instagram / TikTok link, or drop an mp3 / m4a… audio file),
   then choose the **format**, the **translation**, the **style** and the reciter's name.
   The surah and verses are **detected automatically** (you can also choose them yourself).
   So is the **reading** (riwaya): **Hafs** or **Warsh** (Morocco, Algeria, West Africa), or choose it yourself.
   In Warsh the subtitles show the Warsh text, its pronunciation in the phonetic line, and its verse numbers
   (Warsh counts some verses differently: Al-Fatiha's basmala is not a verse, 2:1 and 2:2 are one verse…).
3. **Create my video**: the app listens to the recitation, recognises the passage and finds every word (10 to 60 seconds).
4. **Check and customise** in the editor (icons on the left). The preview shows exactly the final result.
   - **Subtitles**:
     - ▶ to listen to a passage again; edit the translation right in its box;
     - **Wrong verse?** under a subtitle: many verses repeat word for word or nearly (Ar-Rahman's refrain,
       similar verses in other surahs). The app lists those that read the same, says how well each matches what
       it hears, marks the one that follows the previous verse, and aligns that stretch again with the one chosen.
       If a whole passage is wrong, choose the surah yourself in *Export* → *Recitation analysis*;
     - correct the Arabic or the transliteration by clicking it (↺ *Original text* to undo);
     - click a transliterated word (✂) to **split** a subtitle before that word, *Merge* to join two;
     - −/+ to shift a subtitle by 0.05 s, *⤓ here* to set it at the playhead;
     - ✨ *Highlight* for passages in colour (automatic for "Subhana Allah").
   - **Background**: keep the original video, or import **your own photos and videos**
     (jpg, png, iPhone heic, mp4, mov…); the sound stays the recitation's.
     - **1 item**: it fills the whole video. **Several**: one per verse (the 2nd comes with the 2nd verse…),
       the last until the end. **Fewer items than verses**: they come back in order (lava, rain, snow, lava…);
       items added later join that order. **More items than verses**: one per verse, the others wait in the
       **reserve**, at the end of the timeline. *Match the verses* / *Spread evenly* to redo the timing.
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
     - the **items of the block** (number, translation, Arabic, transliteration): × to take one out, whatever
       the style; on the preview the block moves as a whole, or each item on its own with *Move the items one
       by one* (or ⌥ + drag) — click to choose it, pinch to change its size;
     - **layout** (stacked, Arabic on top, band at the bottom); **key words** of the translation in bold or
       in colour, found automatically or chosen by putting *asterisks* around them; capitals or small caps;
       outline thickness (or just a soft shadow);
     - title and reciter at the top, as a small **label in a corner**, or as **intro cards** before the
       recitation (the surah, "Chapter 2 of the Noble Quran", "Recited by…"; ▶ *Preview the intro*);
     - in the YouTube styles, the **basmala** before the recitation: when the reciter says it, his own is used;
       when he starts a surah without it, the app recommends adding it after the intro cards, in the voice of one
       of 10 well-known reciters (▶ to listen; optional for a passage in the middle of a surah, never for
       At-Tawbah). The recordings come from EveryAyah.com and are downloaded when chosen;
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
     Horizontal videos can be **repeated** (10 times by default, or any number): the recitation
     plays again and again to learn it by heart, the title cards and added basmala only once, at the start.
   - **Timeline** (bottom), with the tools of Premiere and DaVinci:
     - **Selection** (V): drag a clip onto another to swap them, a clip of the reserve or a media of the
       library onto a clip to put it there; drag an edge to move the cut (Shift: what follows moves too),
       a subtitle to move it, its edges to change its timing.
     - **Blade** (B) cuts where you click (a subtitle: between the nearest words); **S** or **⌘K** at the playhead.
     - **Slip** (Y, or ⌥ + drag): which part of a video its clip shows.
     - **Replace** (R): another media from the library, or a new file, in place of a clip (and its repeats if you like).
     - ⌘C / ⌘V a clip in place of another (⌥⌘V: its look only), **Delete**, **right click** for every tool.
     - **Magnet** (N): what you drag locks onto the verses and subtitles, the background cuts, the start and
       end of the video and the playhead, across tracks; a gold line and a label show what it locked onto.
       A moved subtitle locks by either end. Hold ⌘ while dragging to move freely.
     - J K L to play backwards / pause / forwards, ← → one frame, ↑ ↓ previous / next cut,
       I / O for the start and end of the exported video (the **pink handles**), + − \ to zoom.
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

## For developers

From the source code (needs [uv](https://docs.astral.sh/uv/)): `uv sync`, then `uv run tilawa desktop`
(or `uv run tilawa` for the browser). A version tag (`git tag v1.2.0 && git push origin v1.2.0`) makes
GitHub build the app for macOS and Windows, test it with the installers, and publish it as a release
(`.github/workflows/release.yml`, `packaging/build.py`); the apps already installed then offer the update.

Command line:

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
   followed through the whole Quran (6236 verses): windows of letters are located by a vote of letter
   groups, compared letter by letter, and chained by a Viterbi search that reads on, accepts repeats
   and jumps to another place only when the letters say so. A recording holding several passages
   (a prayer, a surah recited again, surahs in reverse order) is found passage by passage, with the
   basmala between them.
2. **Forced alignment** — since the text is known, the best path of the text through those
   probabilities is searched (`tilawa/align.py`), for all the passages at once, each only around
   when it was heard (so talk or music next to a passage gets no verse). The path allows the
   isti'adha and the basmala before each passage, silence and speech before/after/between, a video cut
   in the middle of a verse, an approximate starting verse, and the reciter's **repeats** (where a
   word seems to last too long, the model listens again with shorter windows: it may not hear a
   verse said twice in a row). Long recordings are aligned in overlapping pieces.
   `tests/detection_bench.py` checks all this on 31 recitations stitched from verse-by-verse recordings.
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
- Warsh text: **Qur'anpedia.net** (https://quranpedia.net), its Warsh mushaf (the King Fahd Complex's printed
  Warsh mushaf), dump `mushafs-4` version 2026-10-26, under the Qur'anpedia.net Data License
  (https://api.quranpedia.net/dumps/LICENSE.md); `tilawa/data/quran-warsh.txt`, copied verbatim and kept current
  by `packaging/warsh_text.py`.
- Fonts (SIL Open Font License, see `tilawa/fonts/`): Amiri Quran, Amiri, Scheherazade New,
  Noto Naskh Arabic, Reem Kufi, Aref Ruqaa, Comic Neue, Poppins, Open Sans, Arimo, Oswald, Montserrat,
  Nunito, Baloo 2, Playfair Display, Lora, Cinzel.
- Recognition model: Apache 2.0.

The files in `tilawa/data/` are provided as is, with their copyright notices.
Make sure you have the right to republish the recitation videos you use.
