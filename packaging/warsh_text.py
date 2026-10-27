"""Write tilawa/data/quran-warsh.txt: the Warsh 'an Nafi' text from Qur'anpedia.net.

    uv run python packaging/warsh_text.py

Source: Qur'anpedia.net's dump of its Warsh mushaf (mushaf 4: the King Fahd Complex's
printed Warsh mushaf), under the Qur'anpedia.net Data License
(https://api.quranpedia.net/dumps/LICENSE.md): free inside apps; republishing the data
needs a credit with a link and the dump's version, and the copy kept current (run this
again before a release: it says when the text changed). The text is copied verbatim;
the app adapts it when loading it (quran.py)."""

from __future__ import annotations

import gzip
import json
import sys
import urllib.request
from pathlib import Path

URL = "https://api.quranpedia.net/dumps/mushafs-4.json.gz"
OUT = Path(__file__).resolve().parent.parent / "tilawa" / "data" / "quran-warsh.txt"


def main() -> None:
    import certifi
    import ssl

    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 TilawaStudio"})
    with urllib.request.urlopen(req, timeout=120, context=ctx) as r:
        dump = json.loads(gzip.decompress(r.read()))
    data, version = dump["data"], dump["license"]["version"]
    surahs = data["surahs"]
    # the checks the rest of the app relies on
    assert [int(s["id"]) for s in surahs] == list(range(1, 115)), "114 surahs in order"
    hafs = json.loads((OUT.parent / "surahs.json").read_text(encoding="utf-8"))
    lines = [f"# {data['name']} — Qur'anpedia.net (https://quranpedia.net), dump mushafs-4, version {version}",
             f"# {data['description']}",
             "# Qur'anpedia.net Data License: https://api.quranpedia.net/dumps/LICENSE.md",
             f"# basmala|{data['bismillah'].strip()}",
             "# surah|verse (Warsh count)|the Hafs verses it covers|text"]
    for s in surahs:
        n = int(s["id"])
        assert [a["number"] for a in s["ayahs"]] == list(range(1, len(s["ayahs"]) + 1)), f"verses of {n} in order"
        covered = [h for a in s["ayahs"] for h in a["number_in_hafs"]]
        assert sorted(set(covered)) == list(range(1, hafs[n - 1]["verses"] + 1)), f"every Hafs verse of {n} covered"
        for a in s["ayahs"]:
            assert a["text"].strip() and "|" not in a["text"]
            lines.append(f"{n}|{a['number']}|{','.join(map(str, a['number_in_hafs']))}|{a['text'].strip()}")
    old = OUT.read_text(encoding="utf-8").splitlines()[5:] if OUT.exists() else []
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    total = sum(len(s["ayahs"]) for s in surahs)
    print(f"{OUT.name}: {total} verses, version {version}" + (" (text changed)" if old and old != lines[5:] else ""))


if __name__ == "__main__":
    sys.exit(main())
