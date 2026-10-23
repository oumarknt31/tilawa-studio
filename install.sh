#!/bin/bash
# Tilawa Studio - installation ou mise à jour en une ligne (Mac), à coller dans le Terminal :
# Tilawa Studio - one-line install or update (Mac), to paste in the Terminal:
#   curl -LsSf https://raw.githubusercontent.com/oumarknt31/tilawa-studio/main/install.sh | bash
#
# Downloads the latest release (the app, ready to use: nothing to compile), checks it against
# the release's SHA256SUMS.txt, puts it in ~/Applications, gets the recitation model and the text
# drawing engine once, and opens it. Files downloaded by curl are not quarantined, so macOS does
# not block the (not yet signed) app. Projects and videos (~/Tilawa Studio) are never touched.
set -euo pipefail

BASE="${TILAWA_RELEASE_URL:-https://github.com/oumarknt31/tilawa-studio/releases/latest/download}"
DEST="${TILAWA_DEST:-$HOME/Applications}"
FILE="TilawaStudio-macOS.zip"
APP="$DEST/Tilawa Studio.app"
OLD="$HOME/Tilawa Studio/Application"   # earlier installs (source code + environment)

say() { printf '\n== %s\n   %s\n' "$1" "$2"; }
fail() { printf '\n!! %s\n   %s\n' "$1" "$2" >&2; exit 1; }

if [ "$(sysctl -n hw.optional.arm64 2>/dev/null || echo 0)" != "1" ]; then
  fail "Tilawa Studio demande un Mac Apple Silicon (M1 ou plus récent)." \
       "Tilawa Studio needs an Apple Silicon Mac (M1 or newer)."
fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

say "Téléchargement de Tilawa Studio (~500 Mo)..." "Downloading Tilawa Studio (~500 MB)..."
curl -fL --progress-bar "$BASE/$FILE" -o "$tmp/$FILE" \
  || fail "Téléchargement impossible : vérifie ta connexion internet et réessaie." \
          "Download failed: check your internet connection and try again."
curl -fsSL "$BASE/SHA256SUMS.txt" -o "$tmp/SHA256SUMS.txt" \
  || fail "Téléchargement impossible, réessaie dans un instant." "Download failed, try again in a moment."
expected=$(awk -v f="$FILE" '{ sub(/^\*/, "", $2) } $2 == f { print $1 }' "$tmp/SHA256SUMS.txt")  # "*" = binary mode
actual=$(shasum -a 256 "$tmp/$FILE" | awk '{ print $1 }')
[ -n "$expected" ] && [ "$expected" = "$actual" ] \
  || fail "Le téléchargement est abîmé, réessaie." "The download is damaged, try again."
ditto -x -k "$tmp/$FILE" "$tmp/unpacked"
[ -d "$tmp/unpacked/Tilawa Studio.app" ] || fail "Le téléchargement ne contient pas l'app." "The download doesn't contain the app."

# never close the app for the user: wait until it is quit
running() { pgrep -f "Tilawa Studio.app/Contents/MacOS/tilawa-python" >/dev/null 2>&1 || pgrep -f "tilawa.cli desktop" >/dev/null 2>&1; }
if running; then
  say "Tilawa Studio est ouvert : quitte-le (Cmd-Q) pour continuer. J'attends 3 minutes..." \
      "Tilawa Studio is open: quit it (Cmd-Q) to continue. Waiting 3 minutes..."
  for _ in $(seq 1 90); do running || break; sleep 2; done
  running && fail "Tilawa Studio est encore ouvert. Quitte-le, puis relance cette commande." \
                  "Tilawa Studio is still open. Quit it, then run this command again."
fi

say "Installation dans $DEST..." "Installing into $DEST..."
mkdir -p "$DEST"
staged="$DEST/.Tilawa Studio-new.app"
rm -rf "$staged" "$APP.old"
ditto "$tmp/unpacked/Tilawa Studio.app" "$staged"
xattr -dr com.apple.quarantine "$staged" 2>/dev/null || true
[ -e "$APP" ] && mv "$APP" "$APP.old"
mv "$staged" "$APP"
rm -rf "$APP.old"
# the earlier kind of install, replaced by this one
if [ -d "$OLD/tilawa" ] && [ -f "$OLD/pyproject.toml" ]; then
  rm -rf "$OLD"
fi
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$APP" >/dev/null 2>&1 || true

if [ -z "${TILAWA_NO_SETUP:-}" ]; then
  say "Modèle de reconnaissance et moteur du texte (une seule fois, ~1,3 Go)..." \
      "Recognition model and text engine (once, ~1.3 GB)..."
  PYTHONHOME="$APP/Contents/Resources/python" PYTHONNOUSERSITE=1 "$APP/Contents/MacOS/tilawa-python" -m tilawa.cli setup \
    || fail "La préparation a échoué : relance cette commande." "Setup failed: run this command again."
fi

say "Tilawa Studio est installé : il est dans tes Applications (Launchpad, Spotlight)." \
    "Tilawa Studio is installed: it's in your Applications (Launchpad, Spotlight)."
[ -n "${TILAWA_NO_OPEN:-}" ] || open "$APP"
