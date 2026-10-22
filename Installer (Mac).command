#!/bin/bash
# Tilawa Studio - installation (Mac). Double-clic, une seule fois / Double-click, once.
cd "$(dirname "$0")" || exit 1
export PATH="$HOME/.local/bin:$PATH"
echo "== Installation de Tilawa Studio / Installing Tilawa Studio =="
if [ "$(uname -m)" != "arm64" ]; then
  echo "Ce Mac a un processeur Intel : Tilawa Studio demande un Mac Apple Silicon (M1 ou plus récent)."
  echo "This Mac has an Intel processor: Tilawa Studio needs an Apple Silicon Mac (M1 or newer)."
  read -r -p "Entrée pour fermer / Enter to close." || true
  exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "-> Installation de uv / Installing uv (Python manager)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh || exit 1
  export PATH="$HOME/.local/bin:$PATH"
fi
echo "-> Composants (quelques minutes) / Components (a few minutes)..."
uv sync --no-dev || exit 1
echo "-> Moteur de rendu du texte / Text rendering engine..."
uv run playwright install chromium || exit 1
echo "-> Modèle de récitation (~1,2 Go) et ffmpeg / Recitation model (~1.2 GB) and ffmpeg..."
uv run python -c "from tilawa import media, align; media.tools(); align.get_model()" || exit 1
chmod +x "Tilawa Studio.command"
echo ""
echo "Installation terminée. Lance « Tilawa Studio.command »."
echo "Installation complete. Open « Tilawa Studio.command »."
read -r -p "Entrée pour fermer / Enter to close." || true
