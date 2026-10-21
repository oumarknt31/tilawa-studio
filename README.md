# Tilawa Studio

Transforme une vidéo de récitation du Coran en Short sous-titré :
**nom de la sourate et du récitateur en haut, numéro du verset, traduction française,
texte arabe et phonétique**, chaque morceau apparaissant exactement quand le récitateur
le prononce. Pas besoin de lire l'arabe.

## Installation (une seule fois)

Il faut un **Mac Apple Silicon (M1 ou plus récent)** ou un **PC Windows 10/11**, environ
**5 Go d'espace libre** et une connexion internet pour l'installation.

- **Mac** : ouvre l'application *Terminal*, colle cette ligne et appuie sur Entrée :

  ```bash
  curl -LsSf https://raw.githubusercontent.com/oumarknt31/tilawa-studio/main/install.sh | bash
  ```

  Le logiciel s'installe dans `Tilawa Studio/Application` (dans ton dossier personnel) et le dossier
  s'ouvre à la fin. La même ligne sert aussi à **mettre à jour** (tes projets et vidéos sont conservés).

  Si tu as plutôt téléchargé le ZIP depuis GitHub : double-clic sur `Installer (Mac).command`.
  Si le Mac refuse de l'ouvrir : *Réglages Système* → *Confidentialité et sécurité* → *Ouvrir quand même*.
- **Windows** : télécharge le ZIP (bouton vert *Code* → *Download ZIP*), décompresse-le,
  puis double-clic sur `Installer (Windows).bat`.
  Si Windows affiche « Windows a protégé votre ordinateur » : *Informations complémentaires* → *Exécuter quand même*.

L'installation télécharge les composants, le modèle de reconnaissance de la récitation
(~1,2 Go) et ffmpeg. Compte 5 à 15 minutes selon la connexion.

## Utilisation

1. Lance `Tilawa Studio.command` (Mac) ou `Tilawa Studio.bat` (Windows).
   L'application s'ouvre dans le navigateur. **Laisse la fenêtre noire ouverte** pendant l'utilisation :
   la fermer arrête le logiciel (la page affiche alors « Tilawa Studio est fermé »).
2. **Nouvelle vidéo** : dépose le fichier vidéo (ou colle un lien YouTube / Instagram / TikTok),
   choisis la sourate, le premier verset récité (une approximation suffit), le nom du récitateur.
3. **Analyser** : le logiciel écoute la récitation et retrouve chaque mot (10 à 60 secondes).
4. **Vérifie et personnalise** dans l'éditeur. L'aperçu montre exactement le résultat final.
   - **Sous-titres** :
     - ▶ sur une carte pour réécouter ce passage ;
     - modifie la traduction directement dans la case ;
     - ✎ *Corriger* pour modifier l'arabe ou la phonétique (↺ pour revenir au texte d'origine) ;
     - clique sur un mot phonétique (✂) pour **couper** un sous-titre avant ce mot,
       ou *Fusionner avec le suivant* pour en réunir deux ;
     - −/+ pour décaler un sous-titre de 0,05 s, *⤓ ici* pour le caler sur la lecture ;
     - ✨ *Mise en valeur* pour les passages en couleurs (activé automatiquement pour « Subhana Allah »).
   - **Arrière-plan** : garde la vidéo d'origine, ou importe **tes photos et vidéos**
     (jpg, png, heic de l'iPhone, mp4, mov…) ; le son reste celui de la récitation.
     - Tu peux aussi mélanger les deux, dans l'ordre que tu veux, avec des fondus.
     - Pour chaque élément : zoom, position, *Remplir l'écran* / *Image entière*,
       et un zoom lent (avant ou arrière) pour les photos.
     - Fais glisser l'image sur l'aperçu pour la déplacer ; pince le trackpad (ou Ctrl + molette) pour zoomer.
     - *Assombrir* rend les textes plus lisibles sur une image claire.
   - **Textes** : fais glisser le titre ou les sous-titres sur l'aperçu pour les placer.
     Pince (ou Ctrl + molette) au-dessus d'un texte pour changer sa taille ; les curseurs font la même chose.
   - **Timeline** (en bas) :
     - tire les bords d'un sous-titre pour changer son horaire, et le bord d'un élément d'arrière-plan pour changer sa durée ;
     - les **poignées roses** coupent le début et la fin de la vidéo ;
     - Ctrl + molette pour zoomer.
   - **Export** : résolution, qualité, fondus du son au début et à la fin.
   - ↶ *Annuler* (⌘Z / Ctrl+Z) annule la dernière modification.
5. **Créer la vidéo**. Les vidéos sont enregistrées dans le dossier `Tilawa Studio/Videos`
   de ton dossier personnel.

Raccourcis dans l'éditeur : `Espace` lecture/pause, `←` `→` sous-titre précédent/suivant, `⌘Z` / `Ctrl+Z` annuler.

### Réglages de la vidéo

| Réglage | Conseil |
|---|---|
| Résolution *Native* | garde la résolution d'origine, sans perte (par défaut) |
| Résolution *4K* | agrandit en 2160 × 3840 et dessine le texte en 4K. YouTube réserve en général ses meilleurs encodages (VP9/AV1, débit plus élevé) aux mises en ligne en haute résolution : rendu souvent plus net après publication. Rendu ~5× plus long |
| Qualité *Maximale* | H.264 CRF 12, preset *slower* : visuellement identique à la source, lisible partout |
| Qualité *10-bit (H.265)* | encore plus fidèle (dégradés), fichiers plus légers, moins compatible avec les vieux appareils |
| *Master ProRes* | pour retravailler la vidéo dans CapCut / Premiere / Final Cut sans perte |
| Vidéo horizontale | onglet *Arrière-plan* : *Image entière* (fond flouté ou noir) ou *Remplir l'écran*, ou n'importe quel zoom |

Les vidéos HDR (iPhone) sont converties automatiquement pour que le texte garde la bonne luminosité.

## En ligne de commande

```bash
uv run tilawa make video.mp4 --surah 23 --from 84 --reciter "Muhammad Dibirov"
uv run tilawa make "https://youtube.com/shorts/..." --surah 67 --from 1 --size 2160x3840
```

## Comment ça marche

1. **Écoute** — un modèle wav2vec2 entraîné sur la récitation du Coran
   ([rabah2026/wav2vec2-large-xlsr-53-arabic-quran-v_final](https://huggingface.co/rabah2026/wav2vec2-large-xlsr-53-arabic-quran-v_final))
   donne, toutes les 20 ms, la probabilité de chaque lettre arabe.
2. **Alignement forcé** — comme le texte est connu, on cherche le meilleur chemin du texte
   à travers ces probabilités (`tilawa/align.py`). Le chemin accepte l'isti'adha et la basmala,
   les silences et paroles avant/après, une vidéo coupée au milieu d'un verset, un verset de départ
   approximatif, et les **répétitions** du récitateur.
3. **Découpage** (`tilawa/segment.py`) — un sous-titre par verset ; un nouveau à chaque
   **respiration** du récitateur (mesurée sur le son, pas sur les lettres, car les madd et
   ghunna laissent de longs blancs sans pause) ; les versets trop longs sont coupés au meilleur
   endroit (signes de pause, creux du son, ponctuation française). La traduction est coupée
   à l'endroit qui correspond à l'arabe, à l'aide de mots repères (قل → « Dis », سبحان → « Gloire »…).
4. **Rendu** (`tilawa/render.py`) — le texte est dessiné par Chromium (mise en forme arabe
   parfaite, contours, dégradés, émojis) directement à la résolution finale, puis ffmpeg pose
   ces images sur l'arrière-plan avec les fondus et encode une seule fois. Pour l'arrière-plan,
   seule la partie visible de chaque image est recadrée puis redimensionnée (un seul
   rééchantillonnage), et le zoom lent est calculé au sous-pixel près (pas de tremblement).
   Les photos sont importées sans perte : rotation de l'iPhone appliquée, couleurs Display P3
   converties en sRGB.

Tests : `uv run python -m pytest -q`

## Sources et licences

- Texte coranique : **Tanzil Project** (texte Uthmani, CC BY 3.0, copie à l'identique) — https://tanzil.net
- Traduction : **Muhammad Hamidullah**, via Tanzil (`fr.hamidullah`) — usage non commercial selon les conditions de Tanzil.
- Phonétique : **Tanzil** (`en.transliteration`).
- Noms des sourates : quran.com.
- Polices : **Amiri Quran** et **Comic Neue** (SIL Open Font License, voir `tilawa/fonts/`).
- Modèle de reconnaissance : Apache 2.0.

Les fichiers de `tilawa/data/` sont fournis tels quels, avec leurs mentions de droits.
Vérifie que tu as le droit de republier les vidéos de récitation que tu utilises.
