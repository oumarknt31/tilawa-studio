#!/bin/bash
# Tilawa Studio - lancement (Mac). Laisse cette fenêtre ouverte pendant l'utilisation.
cd "$(dirname "$0")" || exit 1
export PATH="$HOME/.local/bin:$PATH"
uv run --no-dev tilawa app
