#!/bin/bash
# Tilawa Studio - installation (Mac). Double-clic, une seule fois.
cd "$(dirname "$0")" || exit 1
export PATH="$HOME/.local/bin:$PATH"
echo "== Installation de Tilawa Studio =="
if [ "$(uname -m)" != "arm64" ]; then
  echo "Ce Mac a un processeur Intel : Tilawa Studio demande un Mac Apple Silicon (M1 ou plus récent)."
  read -r -p "Appuie sur Entrée pour fermer."
  exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "-> Installation de uv (gestionnaire Python)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh || exit 1
  export PATH="$HOME/.local/bin:$PATH"
fi
echo "-> Installation des composants (quelques minutes)..."
uv sync --no-dev || exit 1
echo "-> Installation du moteur de rendu du texte..."
uv run playwright install chromium || exit 1
echo "-> Téléchargement du modèle de récitation (~1,2 Go) et de ffmpeg..."
uv run python -c "from tilawa import media, align; media.tools(); align.get_model()" || exit 1
chmod +x "Tilawa Studio.command"
echo ""
echo "Installation terminée. Lance « Tilawa Studio.command »."
read -r -p "Appuie sur Entrée pour fermer." || true
