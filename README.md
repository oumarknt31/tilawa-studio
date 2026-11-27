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
     - **✨ A picture per verse** (with your own OpenAI API key, separate from a ChatGPT subscription; about
       $0.04 a picture, paid on your OpenAI account): the app asks OpenAI's image model (gpt-image-2, medium
       quality) for a picture of each verse's meaning, from its English translation: by default **a drawing**
       on cream paper showing a single idea, or **a painting** (a landscape); never people, animals, religious
       figures or writing. The picture leaves the place of the subtitles empty (plain paper, or darker for a
       painting), wherever they are on screen; under a style's text line (Cream paper) the drawing
       **fills the whole area under it**, the same in every verse: asked as a wide, centred panorama reaching
       both sides, then made to cover the area from side to side and from the line to the bottom (centred on
       the drawing, zoomed in a little if the model drew it thinner), on the video's own paper, never above the
       line and never zoomed during the verse; the picture as drawn by the model is kept, to lay it out again
       for free. Its style can be rewritten once for all pictures.
       Each picture goes on its verse; a verse said again shows its picture again; right click a clip to
       redo its picture (its prompt can be changed). The key stays in the Tilawa Studio folder. Check every
       picture before posting.
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
     - **Paper Dawn** (16:9 and 9:16, from the Paper Dawn handoff and its portrait add-on): an indigo page curling open on cut-paper scenes, the
       Arabic, transliteration and translation in its reading area, the word read in gold in each ticked track.
       The page draws the whole frame from the recitation's clock, so the preview, a still and the export agree
       at any time. Each subtitle can choose its **right-hand scene** (Subtitles tab): the pack's tree, mountain
       or layered skies (with their paper gestures: the leaf opening, the rain, the star glints, at a chosen
       word), any imported picture with its crop, or **✨ New scene (AI)**: a square cut-paper scene made by OpenAI
       (high quality, about $0.24) from the subtitle's words and an optional visual idea, with the pack's brief
       and its scenes sent as the reference of paper and light; the repeats of the same words take it too. A new picture within a verse comes in with a stepped wipe,
       a new verse with the page turn (the verse number and text change while the page covers them). Verses
       are cut where the text would reach the page's fold (the Arabic at 115 px, or 100 px for a longer line);
       24 fps, 4K by default. Its fonts (P052, Open Sans, Noto Naskh Arabic, with their notices) and poses are in
       `tilawa/web/paperdawn/`; its art (stage, scenes, paper pieces, the Ayatelier mark) is not shipped: it is
       read from `~/Tilawa Studio/paperdawn/art/` (`packaging/paper_dawn.py <pack folder> [portrait folder]` puts it there).
       In **9:16** the indigo sheet is above, with the logo, title, reciter, verse and the three texts centred in
       the social safe zone (90, 360)–(874, 1200), and the square scene below it (the add-on's own tree); the Arabic
       on one line (89 or 77 px), or on two lines (85 px) cut between two meaning groups; the project's scenes,
       gestures and followed tracks are the same in both formats, a picture keeping a framing for each. Changing
       the format (Export tab) or making a copy in the other one keeps them; "App safe zones" shows the add-on's
       guide over the preview (never in the video). The master is 2160 × 3840;
     - **Paper Dawn · Récitateur** (16:9 and 9:16): the same page with **the reciter filmed** in the window instead
       of the scenes (Background tab: "🎥 The filmed reciter", or a subtitle's scene). The reciter's face is found
       on a few frames of the video (YuNet, OpenCV's small face detector, on the computer) and the window is framed
       on it where the page leaves it open widest; the framing can be moved (one for each format). Between two
       verses, an **effect** on the video: indigo dip, the page turn, soft blur, warm light, black and white,
       alternating close-up, or none; chosen for the project, and if wanted for one verse (its subtitle), with
       its length and a "▶ Preview". The page leaves the window transparent and ffmpeg puts the framed video,
       with its effects, under it; the editor shows the same live. Not for a project made from a sound file;
     - **Cream paper** (16:9 and vertical), made for the drawings on cream paper (pictures per verse): flat
       text without outline, teal Arabic, a book serif translation with its verse number in teal, plum
       transliteration, a boxed title, and **a single key word in red**; whole verses, cut only when one would not fit (each part keeping its meaning), the Arabic and the
       transliteration always on one line, the translation on two at most, and the text never below a line at 60 %
       of the height (62 % vertical), shown dashed on the preview, where the drawing goes; the sizes never change
       from one subtitle to the next: the verses are cut so that every part keeps these rules (put *asterisks* around a word of
       the Arabic, too, to colour it). Dark text: for light backgrounds;
     - **word tracking** (Style tab, *Word tracking*): the Arabic, the transliteration and the translation can each
       follow the recitation word by word, in any combination, each with its own effect and colour (or one effect
       applied to all), among 36 in six families (clean, ink & paper, frames, light, trails, motion). The Arabic
       is coloured whole word by whole word (joins and every mark kept), at the times measured for each recited
       word; the transliteration has one word per recited word. The translation has no word-for-word alignment:
       it is followed by meaning groups (cut at its punctuation), each starting with the Arabic word that opens it
       ("et" for وَ, "Dis" for قُلْ...) or where its length points; write "|" in a subtitle to cut a group yourself,
       "|4" to make it start with the 4th Arabic word. *After the last word*: the tracking fades once the last
       word is recited, or **stays on the last word** until the next subtitle, which starts right on its first
       word. The preview follows the timeline (play, pause, scrub, speed)
       and the export draws the same page at each frame's time, so both look the same; a tracked video takes
       longer to export (about 1.5 s per second of tracked subtitles);
     - **subtitle length** (Subtitles tab): whole verses (cut only when a subtitle would not keep the rules:
       measured on the page itself, at the style's sizes and in the project's format), normal (also cut at every breath) or short, cut again from the recitation already heard; a part never ends on a small
       word that leans on the next one ("of", "the", مِن, فِى, لَهُم…) and never leaves a lone word; a verse is cut as few
       times as possible, at the places that read best (pause marks, the reciter's breaths, before فَ "so");
     - the **Arabic and the transliteration are always on one line**, no wider than the style's column (a line still
       easy to read, not the whole screen), the translation on two at most, never made smaller: the same sizes in the
       whole video, the subtitles cut to fit;
     - the **items of the block** (number, translation, Arabic, transliteration): × to take one out, whatever
       the style; on the preview the block moves as a whole, or each item on its own with *Move the items one
       by one* (or ⌥ + drag) — click to choose it, pinch to change its size;
     - **layout** (stacked, Arabic on top, band at the bottom); **key words** of the translation in bold, in
       colour or a single one, found automatically or chosen by putting *asterisks* around them; capitals or small caps;
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
     - **Choosing**: a click chooses a clip or a subtitle without moving the playhead (double-click: go there;
       the ruler at the top moves the playhead); ⇧ or ⌘ + click, or a box drawn from an empty space, chooses
       several; ⌘A all of them, Esc none. **Track select forward** (A): an item and everything after it on its
       track (Shift: on every track).
     - **Editing what is chosen**: ⌘C copy, ⌘X cut, ⌘V paste at the playhead (what was under it makes room, as in
       Premiere), ⌘D duplicate right after, **Delete** (a subtitle leaves its time empty; a background clip's time goes
       to its neighbour), ⌥ ← → one frame earlier / later (⇧: ten). Dragging several subtitles moves them together.
     - **Type** (T): draw a new subtitle on the subtitles track (or *New* in the Subtitles tab) and write it there,
       or *Fill with* a verse (as the reading numbers it), the basmala or the isti'adha; then *🎧 Fit to the
       recitation* finds that verse in the audio under it and times it word by word, as the analysis does. So a
       video can be subtitled entirely by hand when the analysis got it wrong.
     - **Track buttons**: 🔒 locks a track (nothing on it can change by mistake); the subtitles' eye hides them in
       the preview and in the exported video. **Hand** (H) scrolls the timeline.
     - **Selection** (V): drag a clip onto another to swap them, a clip of the reserve or a media of the
       library onto a clip to put it there; drag an edge to move the cut (Shift: what follows moves too),
       a subtitle to move it, its edges to change its timing.
     - **Blade** (B) cuts where you click (a subtitle: between the nearest words); **S** or **⌘K** at the playhead.
     - **Slip** (Y, or ⌥ + drag): which part of a video its clip shows.
     - **Replace** (R): another media from the library, or a new file, in place of a clip (and its repeats if you like).
     - *Paste in its place* puts a copied clip in place of another (⌥⌘V: its look only); **right click** for every tool.
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

### Recitation and creation streaks

On the home screen, two streaks, counted on your computer's own day (midnight to midnight):
- **Recitation streak**: *🎙️ Recite* records you with the microphone (or *Import a recording* made with
  a phone); the verses recited are recognised by listening ("Al-Mulk 1–10"), and a day with at least one
  verse counts. Any length: a verse, a few, a surah. Short single verses are recognised too, as long as
  most of the verse is heard clearly. The recordings stay on your computer (`Tilawa Studio/Récitations`).
- **Creation streak**: a day with a video exported counts.
- **Two in one**: *🎬 Make a video* turns a recitation into a project (the verses already known); exported,
  it counts for the creation streak too.

Made the way the best habit apps learned to (Duolingo's published experiments, Apple Fitness, Quran.com), for a
Quran practice ("the most beloved deeds to Allah are the most constant, even if small", al-Bukhari 6464, Muslim 783):
- **A verse keeps the day; the goal is apart**: a daily goal (1 to 40 verses, 5 by default) shown as a ring;
  a day at the goal is a *perfect day*, but a single verse is enough for the streak.
- **🛡️ Protections**: a perfect week (the goal 7 days in a row) earns one, 2 held at most; a missed day uses one
  and the streak goes on.
- **🩹 Repair**: a streak broken by a gap of one or two days comes back with a day at twice the goal (two videos
  for the creation streak) within the 3 days that follow.
- **⏸ Pause**: 1 to 30 days (travel, illness, any reason, never asked): the streak stays as it is.
- **Milestones** (3, 7, 14, 30, 50, 100... days) celebrated once, without sound; **Details**: the year's
  calendar (perfect, done, protected, repaired, paused, missed), statistics, milestones, the choices.
- **Reminders, in the voice of the teacher everyone loves** (warm, teasing, a bit sarcastic, serious when it
  matters; the jokes are about the phone and the couch, never about the Quran, Allah or the Prophets ﷺ, and a
  hadith or verse always with its reference): at the time chosen or **after a prayer** (Fajr to Isha, computed on
  the computer for your city: UOIF, MWL, ISNA, Morocco, Algeria, Tunisia, Umm al-Qura… within two minutes of
  Aladhan; Shafi'i or Hanafi Asr), only if nothing was recited; **two hours before midnight** if the streak is at
  stake; **after an absence** on days 2, 3, 5, 7, 14 and 30, then silence; Al-Kahf on Fridays, a repair when one is
  possible, a milestone within reach, the muraja'a due. Never more than two a day, nothing during a pause.
  **Even when the app is closed** if you tick it: a small helper the system runs every 15 minutes (a launch
  agent on macOS, a scheduled task on Windows), unticking removes it; nothing leaves the computer.
- **🔁 Muraja'a**: each verse recited comes back after 1, 3, 7, 14, 30, 60 then 120 days (recited again when
  it comes back, it moves to the next step); the passages due today are on the home screen, and the
  **Quran map** shows each surah by the share of its verses recited and how well their reviews were kept.
- **📤 Share my streak**: a 1080 × 1920 picture (the count, the last five weeks, the hadith) in the videos
  folder, to post if you wish; nothing is sent anywhere.

Streaks with friends (a streak shared by friends who each practise the same day) need a small server and are next.

### Hadiths, reminders, calendar and prayers

On the home screen, below the streaks:
- **Hadith of the day** and the **hadith library** (📚): the Encyclopedia of Translated Prophetic Hadiths
  ([HadeethEnc.com](https://hadeethenc.com)), by category, in French, English or Arabic, each with who reported
  it, its grade (authentic or good), the scholars' explanation and lessons; ★ favourites. Its terms allow
  republishing without modification and with credit, kept up to date: the app reads its API on your
  computer (nothing shipped), keeps a copy for a month (still readable offline), and never changes a word.
- **📝 Make a reminder**: a card from a hadith, verses (up to 10, Arabic and translation, with the translator's
  name) or your own words (always labelled as a reminder, never as a hadith), in 9:16, 4:5 or 1:1, four themes
  (Night, Cream, Emerald, Dawn) or your own picture behind a veil, your logo if you wish. A long text becomes a
  **carousel**, cut only between sentences, word for word, with the source and the grade on the last slide; a
  **silent video** (MP4, a fade between slides, time to read each) if you tick it. In `Videos/Rappels`.
- **Calendar**: the Hijri date (Umm al-Qura) and the occasions (Islamic New Year, Ashura, Ramadan, the last ten
  nights, Eid al-Fitr, the ten days of Dhu al-Hijjah, Arafah, Eid al-Adha, the white days, Friday), each with
  what fits it and its source (Al-Kahf on Friday, Al-Qadr in the last ten nights…) and a card or recitation in
  one click. Dates are marked provisional and can be moved a day or two to follow your mosque (the CFCM and
  the Grande Mosquée de Paris differed in 2026). The Mawlid, contested, is left out.
- **Prayers**: today's five prayers for your city, the next one and the time left, and the **Qibla**
  direction (computed on the computer, as for the reminders).
- **🎶 Nasheed (voice only)**: a project from your own recording (audio or video, or a link) and its lyrics
  (one block per subtitle: the Arabic line, the translation, the phonetics), with the same styles, backgrounds,
  formats and export as a recitation. The lyrics are spread over the recording, then synced by ear in the
  Subtitles tab: play, and tap Space at the start of each line (Backspace undoes, Escape stops). You confirm the
  recording is voice only and that you may use it; the app ships no music (scholars differ even on vocal
  nasheeds). A nasheed is never analysed as a recitation and never gets an added basmala.

The teacher's reminders follow the occasions too: the first day of Ramadan, the last ten nights, the ten days
of Dhu al-Hijjah, Arafah, the two Eids, Ashura, the new year.

### Duas, qunoot, nasheeds, hadiths read aloud, reminders

**✨ New content** on the home screen makes each of these a project edited exactly like a recitation (subtitles,
timeline, word tracking, styles, backgrounds, formats, export, memorisation):
- **🤲 Dua**: from the **Quran** (39 of its invocations, from Rabbana atina to the angels who bear the Throne,
  each checked against the text: the recording is aligned as the recitation of those verses), from the
  **Sunnah** (the invocation categories of HadeethEnc: morning and evening, adversity, entering the house…; the
  invocation is quoted word for word from its hadith, its source added as the last subtitle), or your own text.
- **🌙 Qunoot**: the qunoot of witr (the words the Prophet ﷺ taught al-Hasan: Abu Dawud 1425, at-Tirmidhi 464,
  an-Nasa'i 1745), in the singular or the imams' plural (« guide us… »), followed by the imam's own invocations;
  its French and English are working translations, to check and change.
- **🎶 Nasheed** (voice only, confirmed by you) and **📜 a hadith read aloud** (from the library, read in Arabic or
  in its translation), **💬 a reminder** (your text, spoken or silent).
- Any **Arabic** text is synced to the recording **word by word** by the recitation model (each line is a
  "verse" of its own for the aligner: repeats become new subtitles, noise and a basmala before are left out;
  a text that doesn't match the recording is reported, never forced). Lines in another language are spread,
  then synced by ear (tap Space at each line). The phonetics of Arabic lines are written automatically.
- **Silent** contents (no recording): the text over the background, as long as reading it takes.
- In the editor: **🎧 Sync automatically** again after correcting the text, a synced line can be **split** at
  any word (its translation cut at the matching place) and lines merged, and the project list shows each
  content's type.

### Memorisation: "repeat after me"

In the Export tab, **🧠 Export to memorise** makes the teacher-reads, child-repeats video: each verse is heard,
then the picture holds still in silence with « YOUR TURN 1/3 » for the listener to say it back (a pause as long
as the verse, or 1.5× or 2×), 1 to 5 times, before the next verse. The video keeps the project's style,
backgrounds and word tracking; the title cards, the added basmala and the logo's intro and ending don't come
back at every verse. It counts for the creation streak.

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
- Fonts (SIL Open Font License, see `tilawa/fonts/`): Amiri Quran, Amiri (Regular and Bold), Scheherazade New,
  Noto Naskh Arabic, Reem Kufi, Aref Ruqaa, Comic Neue, Poppins, Open Sans, Arimo, Oswald, Montserrat,
  Nunito, Baloo 2, Playfair Display, Source Serif 4, Lora, Cinzel.
- Recognition model: Apache 2.0.

The files in `tilawa/data/` are provided as is, with their copyright notices.
Make sure you have the right to republish the recitation videos you use.

Tilawa Studio itself: free to use, all rights reserved (see [LICENSE](LICENSE)).
