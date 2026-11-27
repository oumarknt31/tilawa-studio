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
   La **lecture** (riwaya) aussi : **Hafs** ou **Warsh** (Maroc, Algérie, Afrique de l'Ouest), ou choisis-la toi-même.
   En Warsh, les sous-titres montrent le texte Warsh, sa prononciation dans la ligne phonétique et ses numéros de
   versets (Warsh compte certains versets autrement : la basmala d'Al-Fatiha n'est pas un verset, 2:1 et 2:2 n'en font qu'un…).
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
       le dernier jusqu'à la fin. **Moins de médias que de versets** : ils reviennent dans l'ordre (lave, pluie,
       neige, lave…) ; ceux ajoutés plus tard prennent leur place dans la suite. **Plus de médias que de versets** :
       un par verset, les autres attendent dans la **réserve**, au bout de la timeline.
       *Caler sur les versets* / *Répartir également* pour refaire le minutage.
     - **✨ Une image par verset** (avec ta propre clé d'API OpenAI, séparée d'un abonnement ChatGPT ; environ
       0,04 $ l'image, payés sur ton compte OpenAI) : l'appli demande au modèle d'images d'OpenAI (gpt-image-2,
       qualité moyenne) une image du sens de chaque verset, d'après sa traduction anglaise : par défaut **un
       dessin** sur papier crème qui montre une seule idée, ou **une peinture** (un paysage) ; jamais de personnes,
       d'animaux, de figures religieuses ni d'écriture. L'image laisse vide la place des sous-titres (papier uni,
       ou plus sombre pour une peinture), où qu'ils soient à l'écran ; sous la ligne de texte d'un style (Papier crème),
       le dessin **remplit toute la zone sous cette ligne**, pareil à chaque verset : demandé comme un panorama large
       et centré qui touche les deux bords, puis agrandi pour couvrir la zone d'un bord à l'autre et de la ligne
       jusqu'en bas (centré sur le dessin, un peu zoomé si le modèle l'a fait plus fin), sur le papier de la vidéo,
       jamais au-dessus de la ligne ni zoomé pendant le verset ; l'image dessinée par le modèle est gardée, pour la
       remettre en page sans repayer. Son style peut être réécrit une fois pour toutes. Chaque image va sur son verset ; un verset redit reprend son image ; clic droit sur
       un clip pour refaire son image (sa consigne peut être changée). La clé reste dans le dossier Tilawa Studio.
       Vérifie chaque image avant de publier.
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
     - **Paper Dawn** (16:9 et 9:16, d'après le dossier Paper Dawn et son module portrait) : une page indigo qui s'ouvre sur des décors en papier
       découpé, l'arabe, la phonétique et la traduction dans sa zone de lecture, le mot lu en or dans chaque texte
       coché. La page dessine toute l'image à partir du temps de la récitation : l'aperçu, une image et l'export
       sont pareils à chaque instant. Chaque sous-titre peut choisir sa **scène à droite** (onglet Sous-titres) :
       l'arbre, la montagne ou les ciels superposés du dossier (avec leurs gestes en papier : la feuille qui
       s'ouvre, la pluie, les étoiles qui brillent, au mot choisi), une image importée avec son cadrage, ou **✨ Nouvelle
       scène (IA)** : une scène carrée en papier découpé faite par OpenAI (haute qualité, environ 0,24 $) d'après les
       mots du sous-titre et une idée visuelle facultative, avec la consigne du dossier et ses scènes comme référence
       de papier et de lumière ; les répétitions des mêmes mots la reprennent. Une
       nouvelle image dans un verset arrive par un volet, un nouveau verset avec la page qui tourne (le numéro et
       le texte changent pendant que la page les couvre). Les versets sont coupés là où le texte toucherait le pli
       de la page (l'arabe en 115 px, ou 100 px pour une ligne plus longue) ; 24 images/s, 4K par défaut. Ses
       polices (P052, Open Sans, Noto Naskh Arabic, avec leurs licences) et poses sont dans `tilawa/web/paperdawn/` ;
       ses images (décor, scènes, pièces de papier, logo Ayatelier) ne sont pas livrées avec l'appli : elles sont
       lues dans `~/Tilawa Studio/paperdawn/art/` (`packaging/paper_dawn.py <dossier> [dossier portrait]` les y met).
       En **9:16**, la feuille indigo est en haut, avec le logo, le titre, le récitateur, le verset et les trois
       textes centrés dans la zone sûre des réseaux (90, 360)–(874, 1200), et la scène carrée en dessous (l'arbre
       propre au module) ; l'arabe sur une ligne (89 ou 77 px), ou sur deux (85 px) coupé entre deux groupes de
       sens ; les scènes, gestes et textes suivis du projet sont les mêmes dans les deux formats, une image gardant
       un cadrage pour chacun. Changer de format (onglet Export) ou en faire une copie les garde ; « Zones des
       applis » montre le guide du module sur l'aperçu (jamais dans la vidéo). Le master fait 2160 × 3840 ;
     - **Paper Dawn · Récitateur** (16:9 et 9:16) : la même page avec **le récitateur filmé** dans la fenêtre à la
       place des scènes (onglet Arrière-plan : « 🎥 Le récitateur filmé », ou la scène d'un sous-titre). Son visage
       est trouvé sur quelques images de la vidéo (YuNet, le petit détecteur de visages d'OpenCV, sur l'ordinateur)
       et la fenêtre est cadrée dessus là où la page la laisse le plus ouverte ; le cadrage se déplace (un par
       format). Entre deux versets, un **effet** sur la vidéo : fondu indigo, la page qui tourne, flou doux, lumière
       chaude, noir et blanc, plan rapproché alterné, ou aucun ; choisi pour le projet, et si on veut pour un
       verset (son sous-titre), avec sa durée et « ▶ Voir ». La page laisse la fenêtre transparente et ffmpeg met
       la vidéo cadrée, avec ses effets, dessous ; l'éditeur montre la même chose en direct. Pas pour un projet
       fait à partir d'un son ;
     - **Papier crème** (16:9 et vertical), fait pour les dessins sur papier crème (images par verset) : texte
       plat sans contour, arabe bleu canard, traduction en serif de livre avec son numéro en bleu, phonétique
       prune, titre dans un cadre, et **un seul mot important en rouge** ; versets entiers, coupés seulement s'ils ne tiennent pas (chaque partie gardant son
       sens), l'arabe et la phonétique toujours sur une ligne, la traduction sur deux au plus, et le texte jamais sous une ligne à
       60 % de la hauteur (62 % en vertical), en pointillés sur l'aperçu, où va le dessin ; les tailles ne changent jamais
       d'un sous-titre à l'autre : les versets sont coupés pour que chaque partie respecte ces règles (entoure aussi un mot de l'arabe
       d'*astérisques* pour le colorer). Texte foncé : pour les fonds clairs ;
     - **suivi des mots** (onglet Style, *Suivi des mots*) : l'arabe, la phonétique et la traduction peuvent chacun
       suivre la récitation mot à mot, dans n'importe quelle combinaison, chacun avec son effet et sa couleur (ou un
       effet pour tous), parmi 36 en six familles (sobres, encre et papier, cadres, lumière, traces, mouvement).
       L'arabe se colore mot entier par mot entier (liaisons et toutes les voyelles gardées), aux temps mesurés de
       chaque mot récité ; la phonétique a un mot par mot récité. La traduction n'a pas d'alignement mot à mot :
       elle est suivie par groupes de sens (coupés à sa ponctuation), chacun commençant au mot arabe qui l'ouvre
       (« et » pour وَ, « Dis » pour قُلْ…) ou à la place que sa longueur indique ; écris « | » dans un sous-titre pour
       couper un groupe, « |4 » pour qu'il commence au 4e mot arabe. *Après le dernier mot* : le suivi s'efface une fois
       le dernier mot récité, ou **reste sur le dernier mot** jusqu'au sous-titre suivant, qui commence directement
       sur son premier mot. L'aperçu suit la timeline (lecture, pause,
       glisser, vitesse) et l'export dessine la même page au temps de chaque image : les deux sont identiques ; une
       vidéo avec suivi est plus longue à exporter (environ 1,5 s par seconde de sous-titres suivis) ;
     - l'**arabe et la phonétique toujours sur une ligne**, pas plus large que la colonne du style (une ligne facile
       à lire, pas tout l'écran), la traduction sur deux au plus, jamais rapetissés : les mêmes tailles dans toute la
       vidéo, les sous-titres coupés pour tenir ;
     - **longueur des sous-titres** (onglet Sous-titres) : versets entiers (coupés seulement quand un sous-titre ne
       respecterait pas les règles : mesuré sur la page elle-même, aux tailles du style et dans le format du projet), normaux (coupés aussi à chaque respiration) ou courts, recoupés d'après la récitation déjà
       entendue ; une partie ne finit jamais sur un petit mot qui s'appuie sur la suite (« de », « la », مِن, فِى, لَهُم…) et ne
       laisse jamais un mot seul ; un verset est coupé le moins possible, aux endroits qui se lisent le mieux (signes de
       pause, respirations du récitateur, avant فَ « donc ») ;
     - les **éléments du bloc** (numéro, traduction, arabe, phonétique) : × pour en retirer un, quel que soit
       le style ; sur l'aperçu, le bloc se déplace d'un seul tenant, ou chaque élément séparément avec *Déplacer
       les éléments un par un* (ou ⌥ + glisser) — clique pour le choisir, pince pour changer sa taille ;
     - **disposition** (empilée, arabe en haut, bandeau en bas) ; **mots importants** de la traduction en gras,
       en couleurs ou un seul, trouvés automatiquement ou choisis en les entourant d'*astérisques* ; majuscules ou
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
   - **Timeline** (en bas), avec les outils de Premiere et DaVinci :
     - **Choisir** : un clic choisit un clip ou un sous-titre sans bouger la tête de lecture (double-clic : y aller ;
       la règle en haut déplace la tête de lecture) ; ⇧ ou ⌘ + clic, ou un cadre tracé depuis un espace vide, en
       choisit plusieurs ; ⌘A tous, Échap aucun. **Sélection vers l'avant** (A) : un élément et tout ce qui le suit
       sur sa piste (Maj : sur toutes les pistes).
     - **Modifier ce qui est choisi** : ⌘C copier, ⌘X couper, ⌘V coller à la tête de lecture (ce qui était dessous
       laisse la place, comme dans Premiere), ⌘D dupliquer juste après, **Suppr** (un sous-titre laisse son temps vide ;
       le temps d'un clip d'arrière-plan va à son voisin), ⌥ ← → une image plus tôt / plus tard (⇧ : dix). Glisser
       plusieurs sous-titres les déplace ensemble.
     - **Texte** (T) : trace un nouveau sous-titre sur la piste des sous-titres (ou *Nouveau* dans l'onglet
       Sous-titres) et écris-le, ou *Remplir avec* un verset (numéroté comme la lecture le numérote), la basmala ou
       l'isti'adha ; puis *🎧 Caler sur la récitation* trouve ce verset dans l'audio en dessous et le cale mot par mot,
       comme l'analyse. Une vidéo peut ainsi être sous-titrée entièrement à la main quand l'analyse s'est trompée.
     - **Boutons des pistes** : 🔒 verrouille une piste (plus rien n'y change par erreur) ; l'œil des sous-titres les
       masque dans l'aperçu et dans la vidéo exportée. **Main** (H) : faire défiler la timeline.
     - **Sélection** (V) : glisse un clip sur un autre pour les échanger, un clip de la réserve ou un média de la
       bibliothèque sur un clip pour l'y mettre ; tire un bord pour déplacer la coupe (Maj : la suite se décale),
       un sous-titre pour le déplacer, ses bords pour changer son horaire.
     - **Lame** (B) : coupe là où tu cliques (un sous-titre : entre les mots les plus proches) ; **S** ou **⌘K** à la tête de lecture.
     - **Décaler** (Y, ou ⌥ + glisser) : le passage d'une vidéo montré dans son clip.
     - **Remplacer** (R) : un autre média de la bibliothèque, ou un nouveau fichier, à la place d'un clip (et de ses répétitions si tu veux).
     - *Coller à la place* met un clip copié à la place d'un autre (⌥⌘V : son apparence seulement) ; **clic droit** pour tous les outils.
     - **Magnétisme** (N) : ce que tu glisses s'aimante aux versets et sous-titres, aux coupes de l'arrière-plan, au début
       et à la fin de la vidéo et à la tête de lecture, d'une piste à l'autre ; une ligne dorée et une étiquette montrent
       à quoi. Un sous-titre déplacé s'aimante par l'un ou l'autre bout. ⌘ en glissant : sans aimant.
     - J K L pour lire en arrière / pause / en avant, ← → une image, ↑ ↓ coupe précédente / suivante,
       I / O pour le début et la fin de la vidéo exportée (les **poignées roses**), + − \ pour zoomer.
   - **Zones des applis** (sous l'aperçu) : montre où TikTok, Reels et Shorts posent leurs boutons.
   - ↶ *Annuler* (⌘Z / Ctrl+Z) annule la dernière modification. Tout est enregistré automatiquement.
5. **Créer la vidéo**. Les vidéos sont enregistrées dans le dossier `Tilawa Studio/Videos`
   de ton dossier personnel.

Raccourcis : `Espace` lecture/pause, `←` `→` sous-titre précédent/suivant, `⌘Z` / `Ctrl+Z` annuler, `?` aide.

### Séries de récitation et de création

Sur l'écran d'accueil, deux séries, comptées sur la journée de ton ordinateur (de minuit à minuit) :
- **Série de récitation** : *🎙️ Réciter* t'enregistre au micro (ou *Importer un enregistrement* fait avec un
  téléphone) ; les versets récités sont reconnus à l'écoute (« Al-Mulk 1–10 »), et une journée avec au moins un
  verset compte. N'importe quelle longueur : un verset, quelques-uns, une sourate. Un seul verset court est
  reconnu aussi, s'il est bien entendu en grande partie. Les enregistrements restent sur ton ordinateur
  (`Tilawa Studio/Récitations`).
- **Série de création** : une journée avec une vidéo exportée compte.
- **Deux en un** : *🎬 En faire une vidéo* transforme une récitation en projet (les versets déjà connus) ;
  exportée, elle compte aussi pour la série de création.

Faites comme les meilleures applis d'habitude l'ont appris (les expériences publiées par Duolingo, Apple Fitness,
Quran.com), pour la pratique du Coran (« les œuvres les plus aimées d'Allah sont les plus constantes, même si elles sont
peu nombreuses », al-Bukhari 6464, Muslim 783) :
- **Un verset garde la journée ; l'objectif est à part** : un objectif du jour (1 à 40 versets, 5 par défaut) en
  anneau ; une journée à l'objectif est un *jour parfait*, mais un seul verset suffit pour la série.
- **🛡️ Protections** : une semaine parfaite (l'objectif 7 jours de suite) en gagne une, 2 au plus ; un jour
  manqué en utilise une et la série continue.
- **🩹 Réparation** : une série cassée par un ou deux jours manqués revient avec une journée au double de
  l'objectif (deux vidéos pour la série de création) dans les 3 jours qui suivent.
- **⏸ Pause** : de 1 à 30 jours (voyage, maladie, toute autre raison, jamais demandée) : la série reste telle quelle.
- **Paliers** (3, 7, 14, 30, 50, 100… jours) fêtés une fois, sans son ; **Détails** : le calendrier de l'année
  (parfait, fait, protégé, réparé, en pause, manqué), les statistiques, les paliers, les choix.
- **Rappels, avec la voix du prof que tout le monde adore** (chaleureux, taquin, un peu sarcastique, sérieux quand
  il le faut ; les blagues portent sur le téléphone et le canapé, jamais sur le Coran, Allah ou les Prophètes ﷺ, et un
  hadith ou un verset toujours avec sa référence) : à l'heure choisie ou **après une prière** (de Fajr à Isha,
  calculée sur l'ordinateur pour ta ville : UOIF, MWL, ISNA, Maroc, Algérie, Tunisie, Umm al-Qura… à deux minutes
  près d'Aladhan ; Asr shafi'i ou hanafi), seulement si rien n'a été récité ; **deux heures avant minuit** si la
  série est en jeu ; **après une absence** les jours 2, 3, 5, 7, 14 et 30, puis le silence ; Al-Kahf le vendredi, une
  réparation quand elle est possible, un palier à portée, la muraja'a du jour. Jamais plus de deux par jour, rien
  pendant une pause. **Même quand l'appli est fermée** si tu le coches : un petit assistant que le système lance
  toutes les 15 minutes (agent sur macOS, tâche planifiée sur Windows), le décocher l'enlève ; rien ne quitte
  l'ordinateur.
- **🔁 Muraja'a** : chaque verset récité revient après 1, 3, 7, 14, 30, 60 puis 120 jours (récité quand il
  revient, il passe à l'étape suivante) ; les passages du jour sont sur l'accueil, et la **carte du Coran**
  montre chaque sourate selon la part de ses versets récités et la tenue de leurs révisions.
- **📤 Partager ma série** : une image 1080 × 1920 (le nombre, les cinq dernières semaines, le hadith) dans le
  dossier des vidéos, à publier si tu veux ; rien n'est envoyé.

Les séries avec des amis (une série partagée par des amis qui pratiquent chacun le même jour) demandent un petit
serveur et arrivent ensuite.

### Hadiths, rappels, calendrier et prières

Sur l'écran d'accueil, sous les séries :
- **Hadith du jour** et **bibliothèque de hadiths** (📚) : l'Encyclopédie des hadiths prophétiques traduits
  ([HadeethEnc.com](https://hadeethenc.com)), par catégorie, en français, anglais ou arabe, chacun avec qui l'a
  rapporté, son degré (authentique ou bon), l'explication des savants et ses enseignements ; ★ favoris. Ses
  conditions permettent de republier sans modification, avec la source, à jour : l'appli lit son API sur ton
  ordinateur (rien n'est livré), en garde une copie un mois (lisible hors ligne), et ne change jamais un mot.
- **📝 Créer un rappel** : une carte à partir d'un hadith, de versets (10 au plus, arabe et traduction, avec le nom
  du traducteur) ou de tes propres mots (toujours présentés comme un rappel, jamais comme un hadith), en 9:16,
  4:5 ou 1:1, quatre thèmes (Nuit, Crème, Émeraude, Aube) ou ta propre image sous un voile, ton logo si tu veux.
  Un texte long devient un **carrousel**, coupé seulement entre deux phrases, mot pour mot, avec la source et le
  degré sur la dernière image ; une **vidéo sans son** (MP4, un fondu entre les images, le temps de lire chacune)
  si tu la coches. Dans `Vidéos/Rappels`.
- **Calendrier** : la date de l'Hégire (Umm al-Qura) et les occasions (nouvel an, Achoura, Ramadan, les dix
  dernières nuits, l'Aïd al-Fitr, les dix jours de Dhou al-Hijja, Arafat, l'Aïd al-Adha, les jours blancs, le
  vendredi), chacune avec ce qui lui va et sa source (Al-Kahf le vendredi, Al-Qadr les dix dernières nuits…) et
  une carte ou une récitation en un clic. Les dates sont marquées « à confirmer » et se décalent d'un ou deux
  jours pour suivre ta mosquée (le CFCM et la Grande Mosquée de Paris différaient en 2026). Le Mawlid, discuté,
  n'est pas inclus.
- **Prières** : les cinq prières du jour pour ta ville, la prochaine et le temps restant, et la direction de
  la **Qibla** (calculées sur l'ordinateur, comme pour les rappels).
- **🎶 Nasheed (voix seule)** : un projet à partir de ton enregistrement (audio ou vidéo, ou un lien) et de ses
  paroles (un bloc par sous-titre : la ligne en arabe, la traduction, la phonétique), avec les mêmes styles, fonds,
  formats et export qu'une récitation. Les paroles sont réparties sur l'enregistrement, puis synchronisées à
  l'oreille dans l'onglet Sous-titres : lance la lecture et tape Espace au début de chaque ligne (Retour arrière
  annule, Échap arrête). Tu confirmes que l'enregistrement est en voix seule et que tu as le droit de l'utiliser ;
  l'appli ne fournit aucune musique (les savants divergent même sur les nasheeds en voix seule). Un nasheed n'est
  jamais analysé comme une récitation et ne reçoit jamais de basmala ajoutée.

Les rappels du prof suivent aussi les occasions : le premier jour de Ramadan, les dix dernières nuits, les dix
jours de Dhou al-Hijja, Arafat, les deux Aïds, Achoura, le nouvel an.

### Duas, qunoot, nasheeds, hadiths lus, rappels

**✨ Nouveau contenu** sur l'accueil fait de chacun un projet édité exactement comme une récitation (sous-titres,
timeline, suivi des mots, styles, fonds, formats, export, mémorisation) :
- **🤲 Dua** : du **Coran** (39 de ses invocations, de Rabbana atina aux anges porteurs du Trône, chacune vérifiée sur
  le texte : l'enregistrement est aligné comme la récitation de ces versets), de la **Sunnah** (les catégories
  d'invocations de HadeethEnc : matin et soir, adversité, entrer chez soi… ; l'invocation est citée mot pour mot de son
  hadith, sa source ajoutée en dernier sous-titre), ou ton propre texte.
- **🌙 Qunoot** : le qunoot du witr (les paroles que le Prophète ﷺ enseigna à al-Hasan : Abou Dawoud 1425, at-Tirmidhi
  464, an-Nasa'i 1745), au singulier ou au pluriel des imams (« guide-nous… »), suivi des invocations de l'imam ; son
  français et son anglais sont des traductions de travail, à vérifier et modifier.
- **🎶 Nasheed** (voix seule, confirmé par toi), **📜 un hadith lu** (de la bibliothèque, lu en arabe ou dans sa
  traduction), **💬 un rappel** (ton texte, parlé ou sans son).
- Tout texte **arabe** est synchronisé sur l'enregistrement **mot à mot** par le modèle de récitation (chaque ligne est
  un « verset » à elle pour l'aligneur : les répétitions deviennent de nouveaux sous-titres, le bruit et une basmala
  avant sont écartés ; un texte qui ne correspond pas à l'enregistrement est signalé, jamais forcé). Les lignes dans
  une autre langue sont réparties, puis synchronisées à l'oreille (Espace à chaque ligne). La phonétique des lignes
  arabes est écrite automatiquement.
- Contenus **sans son** (sans enregistrement) : le texte sur le fond, le temps de le lire.
- Dans l'éditeur : **🎧 Synchroniser automatiquement** à nouveau après avoir corrigé le texte, une ligne synchronisée
  se **coupe** à n'importe quel mot (sa traduction coupée au même endroit) et les lignes se fusionnent, et la liste des
  projets montre le type de chaque contenu.

### Mémorisation : « répète après moi »

Dans l'onglet Export, **🧠 Exporter pour mémoriser** fait la vidéo où le maître lit et l'enfant répète : chaque verset
est entendu, puis l'image s'arrête en silence avec « À TOI ! 1/3 » pour le répéter (une pause aussi longue que le
verset, ou 1,5× ou 2×), de 1 à 5 fois, avant le verset suivant. La vidéo garde le style, les fonds et le suivi des
mots du projet ; les cartes de titre, la basmala ajoutée et le logo animé du début et de la fin ne reviennent pas
à chaque verset. Elle compte pour la série de création.

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
- Texte Warsh : **Qur'anpedia.net** (https://quranpedia.net), son mushaf Warsh (le mushaf Warsh imprimé du
  Complexe du roi Fahd), dump `mushafs-4` version 2026-10-26, sous la licence de données de Qur'anpedia.net
  (https://api.quranpedia.net/dumps/LICENSE.md) ; `tilawa/data/quran-warsh.txt`, copié tel quel et tenu à jour
  par `packaging/warsh_text.py`.
- Polices (SIL Open Font License, voir `tilawa/fonts/`) : Amiri Quran, Amiri (Regular et Bold), Scheherazade New,
  Noto Naskh Arabic, Reem Kufi, Aref Ruqaa, Comic Neue, Poppins, Open Sans, Arimo, Oswald, Montserrat, Nunito, Baloo 2,
  Playfair Display, Source Serif 4, Lora, Cinzel.
- Modèle de reconnaissance : Apache 2.0.

Les fichiers de `tilawa/data/` sont fournis tels quels, avec leurs mentions de droits.
Vérifie que tu as le droit de republier les vidéos de récitation que tu utilises.

Tilawa Studio lui-même : gratuit à utiliser, tous droits réservés (voir [LICENSE](LICENSE)).
