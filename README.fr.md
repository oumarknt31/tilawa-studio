# Tilawa Studio

**Français** · [English](README.md)

Transforme une récitation du Coran (vidéo, lien ou simple fichier audio) en vidéo sous-titrée :
**nom de la sourate et du récitateur en haut, numéro du verset, traduction, texte arabe et phonétique**,
chaque morceau apparaissant exactement quand le récitateur le prononce. Le logiciel **reconnaît tout seul
la sourate et les versets** récités, même plusieurs sourates dans une vidéo (une prière : Al-Fatiha puis une
autre sourate ; les trois dernières sourates à la suite). Pas besoin de lire l'arabe.

Formats : vertical 9:16 (Shorts, Reels, TikTok), horizontal 16:9 (YouTube), carré 1:1 et portrait 4:5,
de la Full HD à la 4K. Traductions : français (Hamidullah, Rachid Maach ou Centre international Noor), anglais
(Saheeh International, Yusuf Ali ou Pickthall), espagnol, allemand, italien, portugais,
néerlandais, suédois, turc, indonésien, malais, bosnien, albanais, russe, ourdou, ou arabe seul.
L'interface est en français ou en anglais (bouton **FR | EN** en haut à droite).

## Installation (une seule fois)

Il faut un **Mac Apple Silicon (M1 ou plus récent)** ou un **PC Windows 10/11**, environ **4 Go d'espace libre**
et une connexion internet. Rien d'autre à installer : l'app arrive prête à l'emploi.

**Sur Mac**

1. Ouvre l'application **Terminal** : appuie sur ⌘ (cmd) + Espace, tape `Terminal`, appuie sur Entrée.
2. Copie cette ligne, colle-la dans la fenêtre du Terminal (⌘ + V) et appuie sur Entrée :

   ```bash
   curl -LsSf https://raw.githubusercontent.com/oumarknt31/tilawa-studio/main/install.sh | bash
   ```

**Sur Windows**

1. Ouvre **PowerShell** : clique sur le menu Démarrer, tape `PowerShell`, appuie sur Entrée.
2. Copie cette ligne, colle-la dans la fenêtre PowerShell (clic droit ou Ctrl + V) et appuie sur Entrée :

   ```powershell
   irm https://raw.githubusercontent.com/oumarknt31/tilawa-studio/main/install.ps1 | iex
   ```

L'installation télécharge l'app (~500 Mo) et, la première fois seulement, le modèle de reconnaissance de la
récitation (~1,2 Go) : compte 5 à 15 minutes selon la connexion, et garde la fenêtre ouverte jusqu'à
« Tilawa Studio est installé ». L'app s'ouvre ensuite toute seule.

Ensuite, **Tilawa Studio** est dans ton dossier Applications (Launchpad, Spotlight ; tu peux le garder dans le
Dock) ou dans le menu Démarrer et sur le bureau. **Les mises à jour se font depuis l'app** : quand une nouvelle
version sort, un bouton ✨ *Mettre à jour* apparaît en haut ; un clic et l'app redémarre sur la nouvelle version.
Tes projets et vidéos sont conservés. (Relancer la même ligne installe aussi la dernière version.)

Aucun avertissement de sécurité n'apparaît : la ligne télécharge l'app d'une façon à laquelle macOS et Windows
font confiance, contrairement à un fichier téléchargé dans un navigateur.

## Utilisation

1. Ouvre **Tilawa Studio** comme n'importe quelle app (Launchpad, Spotlight, Dock / menu Démarrer, bureau).
   Il s'ouvre dans sa propre fenêtre ; fermer la fenêtre quitte l'app (elle demande d'abord si une vidéo est en cours).
2. **Dépose une vidéo** (ou colle un lien YouTube / Instagram / TikTok, ou dépose un audio mp3 / m4a…),
   puis choisis le **format**, la **traduction**, le **style** et le nom du récitateur.
   La sourate et les versets sont **détectés automatiquement** (tu peux aussi les choisir toi-même).
   Avec un lien, l'appli dit aussi à quel point la vidéo risque une **réclamation de droits d'auteur** sur les
   plateformes où tu publies (YouTube, TikTok, Instagram, Facebook), et ce qui arriverait : son coupé, vidéo
   bloquée, revenus des publicités pour le propriétaire. C'est une estimation d'après ce que dit la vidéo
   (licence, mentions de droits, chaîne officielle ou grande) : aucune appli ne peut savoir à l'avance si une
   plateforme reconnaîtra un son.
3. **Créer ma vidéo** : le logiciel écoute la récitation, reconnaît le passage et retrouve chaque mot (10 à 60 secondes).
4. **Vérifie et personnalise** dans l'éditeur (les icônes à gauche). L'aperçu montre exactement le résultat final.
   - **Sous-titres** :
     - ▶ pour réécouter un passage ; modifie la traduction directement dans la case ;
     - **Pas le bon verset ?** sous un sous-titre : beaucoup de versets se répètent mot pour mot ou presque (le refrain
       d'Ar-Rahman, des versets proches dans d'autres sourates). L'appli liste ceux qui se lisent pareil, dit à quel
       point chacun correspond à ce qu'elle entend, signale celui qui suit le verset précédent, et recale ce passage
       sur celui choisi. Si tout un passage est faux, choisis toi-même la sourate dans *Exporter* → *Analyse de la récitation* ;
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
     - langue de la traduction et, en français et en anglais, quelle traduction (change toute la traduction, coupée comme l'arabe) ;
     - **écriture de la phonétique** : *lisible* (Wal yawmil maw'ood), la même à la française (maw'oud), *savante*
       (wa-l-yawmi l-mawʿūd) ou celle de Tanzil. Elle est écrite d'après l'arabe, mot par mot, avec les mêmes règles
       partout (article et lettres solaires, hamza de liaison, pause en fin de sous-titre) : aucune partie ne manque,
       et un passage coupé ou corrigé se lit toujours de la même façon ;
     - **pour YouTube (16:9)**, des styles inspirés des chaînes de récitation connues : *Cinéma* (arabe en haut,
       traduction numérotée en majuscules avec ses mots importants en gras, phonétique légère), *Le Chemin des
       Pieux — YouTube*, *Bandeau classique*, *Bandeau titre* (traduction au milieu, arabe et phonétique dans
       un bandeau translucide en bas), *Cinéma doré*, *Minimal* ;
     - **disposition** (empilée, arabe en haut, bandeau en bas) ; **mots importants** de la traduction en gras
       ou en couleurs, trouvés automatiquement ou choisis en les entourant d'*astérisques* ; majuscules ou
       petites capitales ; épaisseur du contour (ou simple ombre douce) ;
     - titre et récitateur en haut, en petite **étiquette dans un coin**, ou en **cartes d'intro** avant la
       récitation (la sourate, « Chapitre 2 du noble Coran », « Récitée par… » ; ▶ *Voir l'intro*) ;
     - dans les styles YouTube, la **basmala** avant la récitation : quand le récitateur la dit, c'est la sienne ;
       quand il commence une sourate sans elle, l'appli recommande de l'ajouter après les cartes d'intro, avec la voix
       d'un de 10 récitateurs connus (▶ pour écouter ; facultatif pour un passage au milieu d'une sourate, jamais pour
       At-Tawbah). Les enregistrements viennent d'EveryAyah.com et sont téléchargés quand on en choisit un ;
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
     Les vidéos horizontales peuvent être **répétées** (10 fois par défaut, ou le nombre choisi) : la récitation
     revient encore et encore pour l'apprendre par cœur, les cartes de titre et la basmala ajoutée une seule fois, au début.
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
| *Annuler l'export* | l'arrête aussitôt (rien de laissé à moitié fait) |
| Qualité *Studio* | la même image dans un fichier environ ⅓ plus léger, avec l'encodeur logiciel lent (x264 *slower*) : ~8× plus long |
| Vidéo horizontale | onglet *Arrière-plan* : *Image entière* (fond flouté ou noir) ou *Remplir l'écran*, ou n'importe quel zoom |

Les vidéos HDR (iPhone) sont converties automatiquement pour que le texte garde la bonne luminosité.

## Pour les développeurs

Depuis le code source (il faut [uv](https://docs.astral.sh/uv/)) : `uv sync`, puis `uv run tilawa desktop`
(ou `uv run tilawa` pour le navigateur). Une étiquette de version (`git tag v1.2.0 && git push origin v1.2.0`)
fait construire l'app par GitHub pour macOS et Windows, la teste avec les installateurs et la publie
(`.github/workflows/release.yml`, `packaging/build.py`) ; les apps déjà installées proposent alors la mise à jour.

En ligne de commande :

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
   approximative, suivie dans tout le Coran (6236 versets) : des fenêtres de lettres sont situées par vote de
   groupes de lettres, comparées lettre à lettre, et enchaînées par une recherche de Viterbi qui préfère lire la
   suite, accepte les répétitions et ne saute ailleurs que quand les lettres le disent. Un enregistrement de
   plusieurs passages (une prière, une sourate récitée de nouveau, des sourates dans l'ordre inverse) est
   reconnu passage par passage, avec la basmala entre eux.
2. **Alignement forcé** — comme le texte est connu, on cherche le meilleur chemin du texte
   à travers ces probabilités (`tilawa/align.py`), pour tous les passages à la fois, chacun seulement
   autour du moment où il a été entendu (une parole ou une musique à côté d'un passage ne reçoit aucun verset).
   Le chemin accepte l'isti'adha et la basmala avant chaque passage, les silences et paroles avant/après/entre,
   une vidéo coupée au milieu d'un verset, un verset de départ approximatif, et les **répétitions** du
   récitateur (là où un mot semble durer trop longtemps, le modèle réécoute avec des fenêtres plus courtes :
   il peut ne pas entendre un verset dit deux fois de suite). Les longs enregistrements sont alignés en
   morceaux qui se chevauchent. `tests/detection_bench.py` vérifie tout cela sur 31 récitations assemblées à
   partir d'enregistrements verset par verset.
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
- Phonétique : écrite d'après l'arabe par `tilawa/translit.py` ; l'option *Tanzil* est celle de **Tanzil**
  (`en.transliteration`, trois coquilles corrigées).
- Traductions de **QuranEnc.com**, republiées sans modification selon ses conditions (renvois de notes et numéros de
  versets retirés pour les sous-titres) : Rachid Maach (`french_rashid`, version 1.0.3), Centre international Noor,
  anciennement Montada Islamic Foundation (`french_montada`, version 1.0.0). Aussi via Tanzil : Abdullah Yusuf Ali
  et Marmaduke Pickthall (en).
- Noms des sourates : quran.com.
- Polices (SIL Open Font License, voir `tilawa/fonts/`) : Amiri Quran, Amiri, Scheherazade New,
  Noto Naskh Arabic, Reem Kufi, Aref Ruqaa, Comic Neue, Poppins, Open Sans, Arimo, Oswald, Montserrat, Nunito, Baloo 2,
  Playfair Display, Lora, Cinzel.
- Modèle de reconnaissance : Apache 2.0.

Les fichiers de `tilawa/data/` sont fournis tels quels, avec leurs mentions de droits.
Vérifie que tu as le droit de republier les vidéos de récitation que tu utilises.
