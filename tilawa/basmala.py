"""The basmala recited by well-known reciters, to put before a recitation
whose reciter starts the surah without it (YouTube styles).

The recordings come from EveryAyah.com (verse 1:1 of each reciter), which
serves them freely but publishes no licence: they are not shipped with the
app. Each one is downloaded when a user chooses it, kept in the app's home
folder, its silences trimmed.
"""

from __future__ import annotations

import subprocess
import urllib.request
from pathlib import Path

from . import media

SOURCE = "https://everyayah.com/data/{folder}/001001.mp3"
HOME: Path | None = None  # where the recordings are kept (set by the app)

# id -> (reciter, EveryAyah folder)
RECITERS = {
    "alafasy": ("Mishary Rashid Alafasy", "Alafasy_128kbps"),
    "abdulbasit": ("Abdul Basit Abdus-Samad", "Abdul_Basit_Murattal_192kbps"),
    "sudais": ("Abdurrahman As-Sudais", "Abdurrahmaan_As-Sudais_192kbps"),
    "muaiqly": ("Maher Al-Muaiqly", "MaherAlMuaiqly128kbps"),
    "shuraim": ("Saud Ash-Shuraim", "Saood_ash-Shuraym_128kbps"),
    "dossari": ("Yasser Ad-Dossari", "Yasser_Ad-Dussary_128kbps"),
    "shatri": ("Abu Bakr Ash-Shatri", "Abu_Bakr_Ash-Shaatree_128kbps"),
    "husary": ("Mahmoud Khalil Al-Husary", "Husary_128kbps"),
    "minshawi": ("Muhammad Siddiq Al-Minshawi", "Minshawy_Murattal_128kbps"),
    "qatami": ("Nasser Al-Qatami", "Nasser_Alqatami_128kbps"),
}


def listing(home: Path) -> list[dict]:
    return [{"id": k, "name": name, "ready": file(home, k).is_file()} for k, (name, _) in RECITERS.items()]


def file(home: Path, rid: str) -> Path:
    return home / "basmala" / f"{rid}.wav"


def ensure(home: Path, rid: str) -> Path:
    """The trimmed recording of a reciter's basmala (downloaded the first time)."""
    if rid not in RECITERS:
        raise ValueError(f"Unknown reciter {rid}")
    out = file(home, rid)
    if out.is_file():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = out.with_suffix(".mp3")
    import certifi
    import ssl

    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(SOURCE.format(folder=RECITERS[rid][1]), timeout=60, context=ctx) as r:
        raw.write_bytes(r.read())
    # silence cut at both ends (a little air kept), 48 kHz stereo like the videos' sound
    trim = "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.08"
    subprocess.run([media.tools()[0], "-y", "-v", "error", "-i", str(raw), "-af",
                    f"{trim},areverse,{trim},areverse", "-ar", "48000", "-ac", "2", str(out)], check=True)
    raw.unlink(missing_ok=True)
    return out


def duration(path: Path) -> float:
    out = subprocess.run([media.tools()[1], "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())
