#!/bin/bash
# Tilawa Studio - installation ou mise à jour en une commande (Mac), à coller dans le Terminal :
# Tilawa Studio - one-line install or update (Mac), to paste in the Terminal:
#   curl -LsSf https://raw.githubusercontent.com/oumarknt31/tilawa-studio/main/install.sh | bash
# (les fichiers téléchargés par curl ne sont pas bloqués par macOS, contrairement à un ZIP /
#  files downloaded by curl are not blocked by macOS, unlike a ZIP)
set -e
DIR="$HOME/Tilawa Studio/Application"
echo "== Téléchargement de Tilawa Studio dans / Downloading Tilawa Studio to « $DIR » =="
mkdir -p "$DIR"
# the exact version installed is remembered, for the updates from inside the app
SHA=$(curl -fsSL https://api.github.com/repos/oumarknt31/tilawa-studio/commits/main 2>/dev/null | sed -n 's/^  "sha": "\([0-9a-f]*\)",$/\1/p' | head -1)
curl -LsSf "https://codeload.github.com/oumarknt31/tilawa-studio/tar.gz/${SHA:-main}" | tar xz -C "$DIR" --strip-components 1
cd "$DIR"
echo "${SHA:-unknown}" > .version
bash "Installer (Mac).command" < /dev/null
open "$HOME/Applications/Tilawa Studio.app"
