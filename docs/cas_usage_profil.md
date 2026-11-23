# Cas d'usage du profil utilisateur (partie 6)

Généré par `python -m backend.personalization.evaluation --encoder tfidf` (encodeur sémantique : **tfidf**).

- **Profil** : 50/50 critères conformes à l'attendu (100%).
- **Recommandations** : Precision@3 moyenne = **1.00** sur 15 cas (objectif du README : ≥ 0,7).
- **Exclusions respectées** : 15/15 cas.

**Apport de la partie 6** — mêmes cas, même moteur, avec le profil provisoire utilisé avant (affinités sémantiques seules) :

| | Avant (profil provisoire) | Avec le profil de la partie 6 |
|---|---|---|
| Precision@3 moyenne | 0.80 | 1.00 |
| Cas avec un genre refusé dans le top 3 | 0 | 0 |

Un morceau est jugé pertinent s'il partage un bloc d'humeur attendu, a une énergie dans la plage attendue et respecte la demande d'instrumental (`cas_usage.morceau_pertinent`). C'est une pré-annotation automatique : à confirmer par une relecture humaine (README §19).

| Cas | Situation | Piège testé | Profil | P@3 avant | P@3 partie 6 |
|---|---|---|---|---|---|
| C01 | Étudiante stressée qui veut se calmer pour réviser | stratégie « réguler » + exclusion + instrumental | 6/6 | 1.00 | 1.00 |
| C02 | Énervé qui veut se défouler à la salle | même émotion que C03, stratégie inverse (« accompagner ») | 4/4 | 1.00 | 1.00 |
| C03 | Énervée qui veut retrouver son calme | même émotion que C02, stratégie « réguler » | 3/3 | 1.00 | 1.00 |
| C04 | Chagrin d'amour, veut des chansons tristes | émotion négative sans stratégie explicite (par défaut : accompagner) | 3/3 | 1.00 | 1.00 |
| C05 | Triste mais veut qu'on lui remonte le moral | même émotion que C04, stratégie « réguler » | 3/3 | 0.00 | 1.00 |
| C06 | Fatigué mais PAS triste, veut se réveiller | négation (« pas triste ») : la tristesse ne doit pas être retenue | 4/4 | 0.00 | 1.00 |
| C07 | Soirée entre amis | joie + contexte écrit dans le texte | 3/3 | 1.00 | 1.00 |
| C08 | Dîner romantique | émotion positive : jamais « régulée » | 3/3 | 0.00 | 1.00 |
| C09 | Concentration au travail, sans paroles | aucune émotion, seulement une ambiance + instrumental écrit dans le texte | 4/4 | 1.00 | 1.00 |
| C10 | Nostalgique un jour de pluie | deux émotions proches (nostalgie, tristesse) + contexte « pluie » | 3/3 | 1.00 | 1.00 |
| C11 | Endormissement, pas de metal | exclusion formulée autrement (« je déteste le metal ») | 3/3 | 1.00 | 1.00 |
| C12 | Road trip ensoleillé | contexte uniquement dans le texte (rien de coché) | 2/2 | 1.00 | 1.00 |
| C13 | Utilisateur qui écrit en anglais | texte en anglais (l'interface est en anglais) | 4/4 | 1.00 | 1.00 |
| C14 | Paraphrase sans mot d'émotion connu | les règles ne trouvent rien : seul le sémantique (partie 3) peut aider | 2/2 | 1.00 | 1.00 |
| C15 | Fautes de frappe | orthographe approximative (« enervé », « defoulé », sans accents) | 3/3 | 1.00 | 1.00 |

## Détail par cas

### C01 — Étudiante stressée qui veut se calmer pour réviser

- **Texte** : « Je suis à bout avec les partiels, trop de pression, il faut que je me calme » · contexte coché : Studying · humeurs cochées : Stressed · préférences : « pas de rap »
- **Profil** : Vous vous sentez assez stressé(e) et voulez changer d'humeur : vous cherchez une ambiance « Calme & détente », pour un contexte « Étude & travail », énergie 2/5, genres : Lo-fi / Chill, Jazz / Blues, sans Hip-hop / Rap, plutôt instrumental.
- **Archétype** : Le Focus Chill · **indices** : a bout, pression, partiels, calme, me calm
  - ✅ emotion : obtenu `stress`, attendu `stress`
  - ✅ strategie : obtenu `réguler`, attendu `réguler`
  - ✅ contexte : obtenu `Étude & travail`, attendu `Étude & travail`
  - ✅ instrumental : obtenu `True`, attendu `True`
  - ✅ genres_exclus : obtenu `['Hip-hop / Rap']`, attendu `['Hip-hop / Rap']`
  - ✅ humeur : obtenu `['Calme & détente', 'Fête & danse']`, attendu `Calme & détente`
- **Top 3** (P@3 = 1.00) :
  - ✅ Peace Piece — Bill Evans (Jazz / Blues, énergie 1, Calme & détente)
  - ✅ Black Sands — Bonobo (Lo-fi / Chill, énergie 3, Calme & détente)
  - ✅ So What — Miles Davis (Jazz / Blues, énergie 2, Calme & détente|Mélancolie & introspection)

### C02 — Énervé qui veut se défouler à la salle

- **Texte** : « Je suis vraiment énervé contre tout le monde, j'ai besoin de me défouler ! » · contexte coché : Exercising · humeurs cochées : Energetic
- **Profil** : Vous vous sentez très énervé(e) et voulez rester dans cette émotion : vous cherchez une ambiance « Colère & défoulement », pour un contexte « Sport », énergie 5/5, genres : Rock.
- **Archétype** : Le Rebelle Cathartique · **indices** : enerve, defouler, defoule, me defouler
  - ✅ emotion : obtenu `colère`, attendu `colère`
  - ✅ strategie : obtenu `accompagner`, attendu `accompagner`
  - ✅ contexte : obtenu `Sport`, attendu `Sport`
  - ✅ humeur : obtenu `['Colère & défoulement', 'Énergie & motivation']`, attendu `Colère & défoulement`
- **Top 3** (P@3 = 1.00) :
  - ✅ Smells Like Teen Spirit — Nirvana (Rock, énergie 5, Colère & défoulement|Énergie & motivation)
  - ✅ Times Like These — Foo Fighters (Rock, énergie 5, Colère & défoulement|Énergie & motivation)
  - ✅ November Rain — Guns N' Roses (Rock, énergie 4, Énergie & motivation|Colère & défoulement)

### C03 — Énervée qui veut retrouver son calme

- **Texte** : « Je suis énervée, je veux juste me calmer et souffler un peu » · contexte coché : Relaxing
- **Profil** : Vous vous sentez énervé(e) et voulez changer d'humeur : vous cherchez une ambiance « Calme & détente », pour un contexte « Sommeil & méditation », énergie 1/5.
- **Archétype** : Le Focus Chill · **indices** : enerve, calme, me calm, calmer
  - ✅ emotion : obtenu `colère`, attendu `colère`
  - ✅ strategie : obtenu `réguler`, attendu `réguler`
  - ✅ humeur : obtenu `['Calme & détente', 'Mélancolie & introspection']`, attendu `Calme & détente`
- **Top 3** (P@3 = 1.00) :
  - ✅ She Is Love — Parachute (Indie / Folk / Country, énergie 1, Calme & détente)
  - ✅ Hold You in My Arms — Ray LaMontagne (Indie / Folk / Country, énergie 2, Calme & détente)
  - ✅ Norwegian Wood (This Bird Has Flown) — The Beatles (Indie / Folk / Country, énergie 2, Calme & détente)

### C04 — Chagrin d'amour, veut des chansons tristes

- **Texte** : « J'ai le cœur brisé depuis ma rupture, je suis triste ce soir » · humeurs cochées : Sad
- **Profil** : Vous vous sentez triste : vous cherchez une ambiance « Mélancolie & introspection », énergie 2/5, genres : Pop, Indie / Folk / Country.
- **Archétype** : L'Âme Mélancolique · **indices** : trist, rupture
  - ✅ emotion : obtenu `tristesse`, attendu `tristesse`
  - ✅ strategie : obtenu `accompagner`, attendu `accompagner`
  - ✅ humeur : obtenu `['Mélancolie & introspection', 'Joie & bonne humeur']`, attendu `Mélancolie & introspection`
- **Top 3** (P@3 = 1.00) :
  - ✅ Society — Eddie Vedder (Indie / Folk / Country, énergie 2, Mélancolie & introspection)
  - ✅ Whiskey Lullaby — Brad Paisley (Indie / Folk / Country, énergie 2, Mélancolie & introspection)
  - ✅ Girl Crush — Little Big Town (Indie / Folk / Country, énergie 2, Mélancolie & introspection)

### C05 — Triste mais veut qu'on lui remonte le moral

- **Texte** : « Je suis triste aujourd'hui, j'ai besoin d'un truc pour me remonter le moral » · humeurs cochées : Sad
- **Profil** : Vous vous sentez triste et voulez changer d'humeur : vous cherchez une ambiance « Joie & bonne humeur » / « Mélancolie & introspection », énergie 3/5.
- **Archétype** : L'Âme Mélancolique · **indices** : trist, me remonter, remonter le moral
  - ✅ emotion : obtenu `tristesse`, attendu `tristesse`
  - ✅ strategie : obtenu `réguler`, attendu `réguler`
  - ✅ humeur : obtenu `['Joie & bonne humeur', 'Mélancolie & introspection']`, attendu `Joie & bonne humeur`
- **Top 3** (P@3 = 1.00) :
  - ✅ Wake Me Up Before You Go-Go — Wham! (Pop, énergie 3, Joie & bonne humeur)
  - ✅ Take Five — Dave Brubeck Quartet (Jazz / Blues, énergie 3, Joie & bonne humeur)
  - ✅ Ooh La La — Faces (Rock, énergie 3, Joie & bonne humeur)

### C06 — Fatigué mais PAS triste, veut se réveiller

- **Texte** : « Je ne suis pas triste, juste crevé, il me faut un truc pour me réveiller le matin »
- **Profil** : Vous vous sentez fatigué(e) et voulez changer d'humeur : vous cherchez une ambiance « Énergie & motivation » / « Mélancolie & introspection », pour un contexte « Étude & travail », énergie 4/5.
- **Archétype** : Le Boost Énergie · **indices** : creve, me reveiller
  - ✅ emotion : obtenu `fatigue`, attendu `fatigue`
  - ✅ strategie : obtenu `réguler`, attendu `réguler`
  - ✅ emotions_niees : obtenu `['tristesse']`, attendu `['tristesse']`
  - ✅ humeur : obtenu `['Énergie & motivation', 'Mélancolie & introspection']`, attendu `Énergie & motivation`
- **Top 3** (P@3 = 1.00) :
  - ✅ La terre est ronde — Orelsan (Hip-hop / Rap, énergie 4, Énergie & motivation)
  - ✅ Unstoppable — Sia (Pop, énergie 4, Énergie & motivation)
  - ✅ Symphonie n°5 - Allegro con brio — Ludwig van Beethoven (Classique, énergie 4, Énergie & motivation)

### C07 — Soirée entre amis

- **Texte** : « Trop contente, on fait une soirée chez moi avec des amis ce soir, on veut danser » · contexte coché : Partying · humeurs cochées : Happy
- **Profil** : Vous vous sentez assez joyeux(se) : vous cherchez une ambiance « Fête & danse », pour un contexte « Soirée & fête », énergie 5/5, genres : Électro / House, Pop.
- **Archétype** : Le Fêtard Solaire · **indices** : content, danser, soiree
  - ✅ emotion : obtenu `joie`, attendu `joie`
  - ✅ contexte : obtenu `Soirée & fête`, attendu `Soirée & fête`
  - ✅ humeur : obtenu `['Fête & danse', 'Romance & sensualité']`, attendu `Fête & danse`
- **Top 3** (P@3 = 1.00) :
  - ✅ One More Time — Daft Punk (Électro / House, énergie 5, Fête & danse|Joie & bonne humeur)
  - ✅ Levitating — Dua Lipa (Pop, énergie 4, Joie & bonne humeur|Fête & danse)
  - ✅ Ciao Adios — Anne-Marie (Électro / House, énergie 5, Joie & bonne humeur|Fête & danse)

### C08 — Dîner romantique

- **Texte** : « Je prépare un dîner aux chandelles pour mon copain, ambiance romantique » · humeurs cochées : Romantic
- **Profil** : Vous vous sentez amoureux(se) : vous cherchez une ambiance « Romance & sensualité », pour un contexte « Moment à deux », énergie 2/5, genres : R&B / Soul / Funk.
- **Archétype** : Le Romantique Rêveur · **indices** : romanti, mon copain
  - ✅ emotion : obtenu `amour`, attendu `amour`
  - ✅ contexte : obtenu `Moment à deux`, attendu `Moment à deux`
  - ✅ humeur : obtenu `['Romance & sensualité', 'Joie & bonne humeur']`, attendu `Romance & sensualité`
- **Top 3** (P@3 = 1.00) :
  - ✅ Truly — Lionel Richie (R&B / Soul / Funk, énergie 2, Romance & sensualité|Mélancolie & introspection)
  - ✅ Words — Bee Gees (R&B / Soul / Funk, énergie 2, Romance & sensualité|Mélancolie & introspection)
  - ✅ Thinkin Bout You — Frank Ocean (R&B / Soul / Funk, énergie 2, Romance & sensualité|Mélancolie & introspection)

### C09 — Concentration au travail, sans paroles

- **Texte** : « Je dois coder toute l'après-midi, il me faut quelque chose sans paroles pour rester concentré » · contexte coché : Working · humeurs cochées : Focused
- **Profil** : Vous cherchez une ambiance « Concentration », pour un contexte « Étude & travail », énergie 2/5, plutôt instrumental.
- **Archétype** : Le Focus Chill · **indices** : concentr
  - ✅ emotion : obtenu `None`, attendu `None`
  - ✅ contexte : obtenu `Étude & travail`, attendu `Étude & travail`
  - ✅ instrumental : obtenu `True`, attendu `True`
  - ✅ humeur : obtenu `['Concentration', 'Fête & danse']`, attendu `Concentration`
- **Top 3** (P@3 = 1.00) :
  - ✅ So What — Miles Davis (Jazz / Blues, énergie 2, Calme & détente|Mélancolie & introspection)
  - ✅ Says — Nils Frahm (Ambient, énergie 2, Mélancolie & introspection|Rêverie & évasion)
  - ✅ Monday Loop — Tomppabeats (Lo-fi / Chill, énergie 2, Calme & détente|Rêverie & évasion)

### C10 — Nostalgique un jour de pluie

- **Texte** : « Il pleut, je regarde de vieilles photos, je suis nostalgique de mon enfance » · humeurs cochées : Melancholic
- **Profil** : Vous vous sentez nostalgique : vous cherchez une ambiance « Mélancolie & introspection », pour un contexte « Solitude & pluie », énergie 2/5.
- **Archétype** : L'Âme Mélancolique · **indices** : nostalg, enfance
  - ✅ emotion : obtenu `nostalgie`, attendu `nostalgie`
  - ✅ contexte : obtenu `Solitude & pluie`, attendu `Solitude & pluie`
  - ✅ humeur : obtenu `['Mélancolie & introspection', 'Romance & sensualité']`, attendu `Mélancolie & introspection`
- **Top 3** (P@3 = 1.00) :
  - ✅ Girl Crush — Little Big Town (Indie / Folk / Country, énergie 2, Mélancolie & introspection)
  - ✅ Why Go? — Faithless (Lo-fi / Chill, énergie 2, Mélancolie & introspection)
  - ✅ What Does Your Soul Look Like - Pt. 2 — DJ Shadow (Lo-fi / Chill, énergie 2, Mélancolie & introspection)

### C11 — Endormissement, pas de metal

- **Texte** : « J'ai du mal à dormir, je veux une musique très douce pour m'endormir » · contexte coché : Sleeping · préférences : « je déteste le metal »
- **Profil** : Vous cherchez une ambiance « Calme & détente », pour un contexte « Sommeil & méditation », énergie 1/5, sans Metal.
- **Archétype** : Le Focus Chill · **indices** : douce
  - ✅ contexte : obtenu `Sommeil & méditation`, attendu `Sommeil & méditation`
  - ✅ genres_exclus : obtenu `['Metal']`, attendu `['Metal']`
  - ✅ humeur : obtenu `['Calme & détente', 'Mélancolie & introspection']`, attendu `Calme & détente`
- **Top 3** (P@3 = 1.00) :
  - ✅ She Is Love — Parachute (Indie / Folk / Country, énergie 1, Calme & détente)
  - ✅ Let It Be Me — Ray LaMontagne (Indie / Folk / Country, énergie 2, Calme & détente)
  - ✅ Here, There And Everywhere — The Beatles (Pop, énergie 2, Calme & détente)

### C12 — Road trip ensoleillé

- **Texte** : « On part en road trip en voiture cet été, je veux des sons ensoleillés et optimistes »
- **Profil** : Vous cherchez une ambiance « Joie & bonne humeur », pour un contexte « Trajet », énergie 4/5.
- **Archétype** : Le Fêtard Solaire · **indices** : ensoleill, optimis
  - ✅ contexte : obtenu `Trajet`, attendu `Trajet`
  - ✅ humeur : obtenu `['Joie & bonne humeur', 'Rêverie & évasion']`, attendu `Joie & bonne humeur`
- **Top 3** (P@3 = 1.00) :
  - ✅ Halcyon and On and On — Orbital (Metal, énergie 4, Rêverie & évasion|Joie & bonne humeur)
  - ✅ California Love — 2Pac (Hip-hop / Rap, énergie 4, Fête & danse|Joie & bonne humeur)
  - ✅ Lovely Day — Bill Withers (R&B / Soul / Funk, énergie 4, Joie & bonne humeur)

### C13 — Utilisateur qui écrit en anglais

- **Texte** : « I'm so stressed about my exams, I need something to calm down » · contexte coché : Studying · humeurs cochées : Stressed
- **Profil** : Vous vous sentez assez stressé(e) et voulez changer d'humeur : vous cherchez une ambiance « Calme & détente », pour un contexte « Étude & travail », énergie 2/5.
- **Archétype** : Le Focus Chill · **indices** : down, stress, calm, calm down
  - ✅ emotion : obtenu `stress`, attendu `stress`
  - ✅ strategie : obtenu `réguler`, attendu `réguler`
  - ✅ contexte : obtenu `Étude & travail`, attendu `Étude & travail`
  - ✅ humeur : obtenu `['Calme & détente', 'Joie & bonne humeur']`, attendu `Calme & détente`
- **Top 3** (P@3 = 1.00) :
  - ✅ Peace Piece — Bill Evans (Jazz / Blues, énergie 1, Calme & détente)
  - ✅ Black Sands — Bonobo (Lo-fi / Chill, énergie 3, Calme & détente)
  - ✅ So What — Miles Davis (Jazz / Blues, énergie 2, Calme & détente|Mélancolie & introspection)

### C14 — Paraphrase sans mot d'émotion connu

- **Texte** : « La journée a été longue et lourde, j'ai la tête qui tourne, besoin de me poser »
- **Profil** : Vous cherchez une ambiance « Calme & détente », pour un contexte « Matin & quotidien », énergie 1/5.
- **Archétype** : Le Focus Chill · **indices** : me poser
  - ✅ strategie : obtenu `réguler`, attendu `réguler`
  - ✅ humeur : obtenu `['Calme & détente', 'Colère & défoulement']`, attendu `Calme & détente`
- **Top 3** (P@3 = 1.00) :
  - ✅ What's Going On — Marvin Gaye (R&B / Soul / Funk, énergie 2, Calme & détente)
  - ✅ Sunrise — Norah Jones (Jazz / Blues, énergie 2, Calme & détente)
  - ✅ Footsteps in the Dark, Pts. 1 & 2 — The Isley Brothers (R&B / Soul / Funk, énergie 2, Calme & détente)

### C15 — Fautes de frappe

- **Texte** : « chui trop enervé jveux me defouler a fond »
- **Profil** : Vous vous sentez assez énervé(e) et voulez rester dans cette émotion : vous cherchez une ambiance « Colère & défoulement », énergie 5/5, genres : Rock.
- **Archétype** : Le Rebelle Cathartique · **indices** : enerve, defouler, defoule, me defouler
  - ✅ emotion : obtenu `colère`, attendu `colère`
  - ✅ strategie : obtenu `accompagner`, attendu `accompagner`
  - ✅ humeur : obtenu `['Colère & défoulement', 'Concentration']`, attendu `Colère & défoulement`
- **Top 3** (P@3 = 1.00) :
  - ✅ Smells Like Teen Spirit — Nirvana (Rock, énergie 5, Colère & défoulement|Énergie & motivation)
  - ✅ Times Like These — Foo Fighters (Rock, énergie 5, Colère & défoulement|Énergie & motivation)
  - ✅ November Rain — Guns N' Roses (Rock, énergie 4, Énergie & motivation|Colère & défoulement)

