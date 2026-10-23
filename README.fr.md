# Tilawa Studio

**Français** · [English](README.md)

Transforme une récitation du Coran (vidéo, lien ou simple fichier audio) en vidéo sous-titrée :
**nom de la sourate et du récitateur en haut, numéro du verset, traduction, texte arabe et phonétique**,
chaque morceau apparaissant exactement quand le récitateur le prononce. Le logiciel **reconnaît tout seul
la sourate et les versets** récités. Pas besoin de lire l'arabe.

Formats : vertical 9:16 (Shorts, Reels, TikTok), horizontal 16:9 (YouTube), carré 1:1 et portrait 4:5,
de la Full HD à la 4K. Traductions : français, anglais, espagnol, allemand, italien, portugais,
néerlandais, suédois, turc, indonésien, malais, bosnien, albanais, russe, ourdou, ou arabe seul.
L'interface est en français ou en anglais (bouton **FR | EN** en haut à droite).

## Installation (une seule fois)

Il faut un **Mac Apple Silicon (M1 ou plus récent)** ou un **PC Windows 10/11**, environ
**5 Go d'espace libre** et une connexion internet pour l'installation.

- **Mac** : ouvre l'application *Terminal*, colle cette ligne et appuie sur Entrée :

  ```bash
  curl -LsSf https://raw.githubusercontent.com/oumarknt31/tilawa-studio/main/install.sh | bash
  ```

  À la fin, **Tilawa Studio** est dans ton dossier Applications (Launchpad, Spotlight, et tu peux le garder
  dans le Dock) et s'ouvre dans sa propre fenêtre. Les mises à jour se font ensuite **depuis l'app**
  (un bouton ✨ *Mise à jour* apparaît quand une nouvelle version sort) ; tes projets et vidéos sont conservés.

  Si tu as plutôt téléchargé le ZIP depuis GitHub : double-clic sur `Installer (Mac).command`.
  Si le Mac refuse de l'ouvrir : *Réglages Système* → *Confidentialité et sécurité* → *Ouvrir quand même*.
- **Windows** : télécharge le ZIP (bouton vert *Code* → *Download ZIP*), décompresse-le,
  puis double-clic sur `Installer (Windows).bat`.
  Si Windows affiche « Windows a protégé votre ordinateur » : *Informations complémentaires* → *Exécuter quand même*.
  À la fin, **Tilawa Studio** est dans le menu Démarrer et sur le bureau.

L'installation télécharge les composants, le modèle de reconnaissance de la récitation
(~1,2 Go) et ffmpeg. Compte 5 à 15 minutes selon la connexion.

## Utilisation

1. Ouvre **Tilawa Studio** comme n'importe quelle app (Launchpad, Spotlight, Dock / menu Démarrer, bureau).
   Il s'ouvre dans sa propre fenêtre ; fermer la fenêtre quitte l'app (elle demande d'abord si une vidéo est en cours).
   Pour l'utiliser plutôt dans un navigateur : `Tilawa Studio.command` (Mac) ou `Tilawa Studio.bat` (Windows),
   en laissant la fenêtre noire ouverte.
2. **Dépose une vidéo** (ou colle un lien YouTube / Instagram / TikTok, ou dépose un audio mp3 / m4a…),
   puis choisis le **format**, la **traduction**, le **style** et le nom du récitateur.
   La sourate et les versets sont **détectés automatiquement** (tu peux aussi les choisir toi-même).
3. **Créer ma vidéo** : le logiciel écoute la récitation, reconnaît le passage et retrouve chaque mot (10 à 60 secondes).
4. **Vérifie et personnalise** dans l'éditeur (les icônes à gauche). L'aperçu montre exactement le résultat final.
   - **Sous-titres** :
     - ▶ pour réécouter un passage ; modifie la traduction directement dans la case ;
     - corrige l'arabe ou la phonétique en cliquant dessus (↺ *Texte d'origine* pour annuler) ;
     - clique sur un mot phonétique (✂) pour **couper** un sous-titre avant ce mot, *Fusionner* pour en réunir deux ;
     - −/+ pour décaler un sous-titre de 0,05 s, *⤓ ici* pour le caler sur la lecture ;
     - ✨ *Mise en valeur* pour les passages en couleurs (automatique pour « Subhana Allah »).
   - **Arrière-plan** : garde la vidéo d'origine, ou importe **tes photos et vidéos**
     (jpg, png, heic de l'iPhone, mp4, mov…) ; le son reste celui de la récitation.
     - **1 média** : il remplit toute la vidéo. **Plusieurs** : un par verset (le 2e arrive avec le 2e verset…),
       le dernier jusqu'à la fin. *Caler sur les versets* / *Répartir également* pour refaire le minutage.
     - Une vidéo plus courte que sa place est jouée en **aller-retour** (avant puis à l'envers) : boucle sans saut.
     - Pour chaque élément : position X/Y et échelle (comme dans Premiere), *Remplir l'écran* / *Image entière*,
       zoom lent, et **couleur** : exposition, contraste, hautes lumières, ombres, saturation, température, teinte.
     - Fais glisser l'image sur l'aperçu pour la déplacer ; pince le trackpad (ou Ctrl + molette) pour zoomer.
   - **Style** :
     - **Thèmes** prêts à l'emploi (Le Chemin des Pieux, Mushaf doré, Moderne, Douceur, Élégant, Calligraphie) ;
       *Enregistrer mon style* le garde pour toutes tes vidéos, ★ en fait le style par défaut ;
     - **polices** du titre, de l'arabe (Amiri Quran, Scheherazade — comme le Coran de Médine —, Noto Naskh,
       Amiri, coufique, ruqʿa) et de la traduction ; *Importer une police* pour la tienne (.ttf, .otf),
       par exemple la police officielle du Mushaf du Complexe Roi Fahd ;
     - **numéro de verset** dans son ornement à la fin du verset (۝١٢ ou ﴿١٢﴾) ;
     - tailles, couleurs (titre et récitateur en dégradé), positions X/Y au pixel ;
     - langue de la traduction (change toute la traduction, coupée comme l'arabe) ;
     - **pour YouTube (16:9)**, des styles inspirés des chaînes de récitation connues : *Cinéma* (arabe en haut,
       traduction numérotée en majuscules avec ses mots importants en gras, phonétique légère), *Le Chemin des
       Pieux — YouTube*, *Bandeau classique*, *Bandeau titre* (traduction au milieu, arabe et phonétique dans
       un bandeau translucide en bas), *Cinéma doré*, *Minimal* ;
     - **disposition** (empilée, arabe en haut, bandeau en bas) ; **mots importants** de la traduction en gras
       ou en couleurs, trouvés automatiquement ou choisis en les entourant d'*astérisques* ; majuscules ou
       petites capitales ; épaisseur du contour (ou simple ombre douce) ;
     - titre et récitateur en haut, en petite **étiquette dans un coin**, ou en **cartes d'intro** avant la
       récitation (la sourate, « Chapitre 2 du noble Coran », « Récitée par… » ; ▶ *Voir l'intro*) ;
     - ton **logo** (chaîne, page) : importé une fois, il va sur toutes tes vidéos, dans tous les formats, au
       meilleur endroit : en haut à gauche en vertical (sous la barre du haut de TikTok, Reels et Shorts, loin
       de leurs boutons et de la légende, gardé dans l'aperçu 4:5 d'Instagram), en haut à droite en 16:9 (YouTube
       met son propre filigrane et la barre de lecture en bas à droite) et dans les posts carrés et portrait.
       Il se décale si le titre est sur son chemin. La section *Logo* montre les suggestions pour le format avec
       un petit aperçu (survole-en une pour la voir sur la vidéo) ; choisis un autre coin, fais-le glisser sur
       l'aperçu, pince pour changer sa taille, *Pas de logo* pour une vidéo, ou décoche *Sur toutes mes vidéos*.
   - **Audio** : début et fin de la vidéo (*Couper les silences* en un clic), fondus du son,
     **volume optimisé pour les réseaux** (−14 LUFS, le niveau de YouTube, TikTok et Instagram).
   - **Export** : format (ou une copie du projet dans un autre format), résolution, qualité,
     **image** pleine résolution (pour une miniature YouTube), liste des fichiers déjà exportés.
   - **Timeline** (en bas) : tire les bords d'un sous-titre pour changer son horaire, le bord d'un
     élément d'arrière-plan pour changer sa durée ; les **poignées roses** coupent le début et la fin.
   - **Zones des applis** (sous l'aperçu) : montre où TikTok, Reels et Shorts posent leurs boutons.
   - ↶ *Annuler* (⌘Z / Ctrl+Z) annule la dernière modification. Tout est enregistré automatiquement.
5. **Créer la vidéo**. Les vidéos sont enregistrées dans le dossier `Tilawa Studio/Videos`
   de ton dossier personnel.

Raccourcis : `Espace` lecture/pause, `←` `→` sous-titre précédent/suivant, `⌘Z` / `Ctrl+Z` annuler, `?` aide.

### Réglages de la vidéo

| Réglage | Conseil |
|---|---|
| Résolution *Native* | garde la résolution d'origine si la vidéo a déjà la bonne forme (sinon Full HD) |
| Résolution *4K* | 2160 × 3840 en vertical, 3840 × 2160 en horizontal ; le texte est dessiné en 4K. YouTube réserve en général ses meilleurs encodages (VP9/AV1, débit plus élevé) aux mises en ligne en haute résolution : rendu souvent plus net après publication. Rendu ~3× plus long |
| Qualité *Maximale* | H.264, visuellement identique à la source, lisible partout. Sur Mac, elle utilise le moteur vidéo de la puce Apple : une vidéo de 2 minutes prend environ 20 s en Full HD et 1 min en 4K (M4) |
| Qualité *10-bit (H.265)* | encore plus fidèle (dégradés), fichiers plus légers, moins compatible avec les vieux appareils |
| *Master ProRes* | pour retravailler la vidéo dans CapCut / Premiere / Final Cut sans perte |
| Qualité *Studio* | la même image dans un fichier environ ⅓ plus léger, avec l'encodeur logiciel lent (x264 *slower*) : ~8× plus long |
| Vidéo horizontale | onglet *Arrière-plan* : *Image entière* (fond flouté ou noir) ou *Remplir l'écran*, ou n'importe quel zoom |

Les vidéos HDR (iPhone) sont converties automatiquement pour que le texte garde la bonne luminosité.

## En ligne de commande

```bash
uv run tilawa make video.mp4 --reciter "Muhammad Dibirov"            # sourate et versets détectés
uv run tilawa make video.mp4 --surah 23 --from 84 --format 16:9 --lang en --style mushaf
uv run tilawa make "https://youtube.com/shorts/..." --size 4k
```

## Comment ça marche

1. **Écoute** — un modèle wav2vec2 entraîné sur la récitation du Coran
   ([rabah2026/wav2vec2-large-xlsr-53-arabic-quran-v_final](https://huggingface.co/rabah2026/wav2vec2-large-xlsr-53-arabic-quran-v_final))
   donne, toutes les 20 ms, la probabilité de chaque lettre arabe.
   **Identification** (`tilawa/identify.py`) : les lettres les plus probables forment une transcription
   approximative, retrouvée dans tout le Coran (6236 versets) par vote de groupes de lettres, puis
   comparée lettre à lettre aux meilleurs candidats.
2. **Alignement forcé** — comme le texte est connu, on cherche le meilleur chemin du texte
   à travers ces probabilités (`tilawa/align.py`). Le chemin accepte l'isti'adha et la basmala,
   les silences et paroles avant/après, une vidéo coupée au milieu d'un verset, un verset de départ
   approximatif, et les **répétitions** du récitateur.
3. **Découpage** (`tilawa/segment.py`) — un sous-titre par verset ; un nouveau à chaque
   **respiration** du récitateur (mesurée sur le son, pas sur les lettres, car les madd et
   ghunna laissent de longs blancs sans pause) ; les versets trop longs sont coupés au meilleur
   endroit (signes de pause, creux du son, ponctuation). La traduction est coupée à l'endroit
   qui correspond à l'arabe, à l'aide de mots repères (قل → « Dis » / « Say » / « Di »…, سبحان → « Gloire »…).
4. **Rendu** (`tilawa/render.py`) — le texte est dessiné par Chromium (mise en forme arabe
   parfaite, contours, dégradés, émojis) directement à la résolution finale, puis ffmpeg pose
   ces images sur l'arrière-plan avec les fondus et encode une seule fois. Pour l'arrière-plan,
   seule la partie visible de chaque image est recadrée, puis colorée, assombrie et fondue à la
   résolution de la source, avant un seul agrandissement à la taille finale : une vidéo 1080p affichée
   en 4K n'a pas plus de détails, l'image est donc la même pour une fraction du travail. Le zoom lent
   est calculé au sous-pixel près (pas de tremblement). L'encodage utilise le moteur vidéo de
   l'ordinateur quand il y en a un (Apple VideoToolbox, comme les applis de montage sur téléphone),
   avec des réglages choisis par mesures VMAF pour égaler la qualité de x264 en CRF 12 ; sinon x264,
   et l'encodeur logiciel prend le relais si le moteur refuse un travail.
   Les photos sont importées sans perte : rotation de l'iPhone appliquée, couleurs Display P3
   converties en sRGB.

Tests : `uv run python -m pytest -q`

## Sources et licences

- Texte coranique : **Tanzil Project** (texte Uthmani, CC BY 3.0, copie à l'identique) — https://tanzil.net
- Traductions, via Tanzil (`tilawa/data/trans/`, usage non commercial selon les conditions de Tanzil) :
  Muhammad Hamidullah (fr), Saheeh International (en), Julio Cortés (es), Bubenheim & Elyas (de),
  Hamza Roberto Piccardo (it), Samir El-Hayek (pt), Sofian S. Siregar (nl), Knut Bernström (sv),
  Diyanet İşleri (tr), Kementerian Agama RI (id), Abdullah Muhammad Basmeih (ms), Besim Korkut (bs),
  Sherif Ahmeti (sq), Elmir Kuliev (ru), Fateh Muhammad Jalandhry (ur).
- Phonétique : **Tanzil** (`en.transliteration`).
- Noms des sourates : quran.com.
- Polices (SIL Open Font License, voir `tilawa/fonts/`) : Amiri Quran, Amiri, Scheherazade New,
  Noto Naskh Arabic, Reem Kufi, Aref Ruqaa, Comic Neue, Poppins, Open Sans, Arimo, Oswald, Montserrat, Nunito, Baloo 2,
  Playfair Display, Lora, Cinzel.
- Modèle de reconnaissance : Apache 2.0.

Les fichiers de `tilawa/data/` sont fournis tels quels, avec leurs mentions de droits.
Vérifie que tu as le droit de republier les vidéos de récitation que tu utilises.
