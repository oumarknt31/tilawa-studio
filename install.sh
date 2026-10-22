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
curl -LsSf https://github.com/oumarknt31/tilawa-studio/archive/refs/heads/main.tar.gz | tar xz -C "$DIR" --strip-components 1
cd "$DIR"
bash "Installer (Mac).command" < /dev/null
open "$DIR"
