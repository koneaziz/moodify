# 🎧 Moodify — Recommandation musicale par analyse sémantique de l'humeur

> Projet NLP — ING5 Data & IA, ECE 2026-27
> **Thème : Recommandation de musique et de playlists selon l'humeur et les préférences**

*Nom de projet provisoire, vous pouvez le changer.*

---

## Sommaire

1. [Description du projet](#1-description-du-projet)
2. [Problématique](#2-problématique)
3. [Objectifs](#3-objectifs)
4. [Fonctionnalités](#4-fonctionnalités)
5. [Conformité aux exigences du sujet](#5-conformité-aux-exigences-du-sujet)
6. [Architecture et pipeline NLP](#6-architecture-et-pipeline-nlp)
7. [Jeu de données de référence](#7-jeu-de-données-de-référence)
8. [Questionnaire utilisateur](#8-questionnaire-utilisateur)
9. [Moteur d'analyse sémantique](#9-moteur-danalyse-sémantique)
10. [Mécanisme de scoring](#10-mécanisme-de-scoring)
11. [Système de recommandation et explications](#11-système-de-recommandation-et-explications)
12. [Dashboard et visualisations](#12-dashboard-et-visualisations-streamlit)
13. [Chatbot d'humeur](#13-chatbot-dhumeur)
14. [Communautés et concerts](#14-communautés-et-concerts)
15. [Bonus IA générative (optionnel)](#15-bonus-ia-générative-optionnel)
16. [Stack technique](#16-stack-technique)
17. [Structure du dépôt](#17-structure-du-dépôt)
18. [Installation et lancement](#18-installation-et-lancement)
19. [Évaluation et validation](#19-évaluation-et-validation)
20. [Feuille de route](#20-feuille-de-route)
21. [Répartition du travail](#21-répartition-du-travail)
22. [Livrables](#22-livrables)
23. [Limites, éthique et données](#23-limites-éthique-et-données)
24. [Références](#24-références)

---

## 1. Description du projet

**Moodify** est une application web qui recommande de la musique à partir de **ce que l'utilisateur
exprime avec ses propres mots** : son humeur, ce qu'il est en train de faire, ce qu'il ressent et ce
qu'il a envie d'entendre.

Au lieu de se baser uniquement sur l'historique d'écoute ou sur la popularité, le système **comprend le
sens** des phrases de l'utilisateur grâce au **NLP** et à l'**analyse sémantique**. Il transforme les
textes en vecteurs (embeddings SBERT), puis les compare par **similarité cosinus** aux descriptions
d'un catalogue de morceaux (humeur, contexte d'écoute, style, mots-clés).

Exemple :

> *« Aujourd'hui je ne suis pas dans le mood, je suis énervée et je veux entendre une musique calme. »*

→ le système détecte l'émotion actuelle (**colère**) et le souhait (**calme**). Il calcule le score
cosinus de **chaque morceau** du catalogue, classe les résultats et renvoie un **top 3 expliqué**, par
exemple *Peace Piece* (Bill Evans) ou *Clair de lune* (Debussy), avec les critères qui ont motivé chaque
choix.

L'application comprend :
- un **questionnaire / quiz** d'onboarding (questions ouvertes et fermées, plus des questions de
  personnalité) qui sert à construire le **profil musical** de l'utilisateur ;
- un **chatbot** où l'utilisateur écrit sa demande du moment en texte libre ;
- un **dashboard** (Streamlit) qui montre le profil, les scores, le top et les statistiques ;
- deux extensions sociales : les **communautés** de même goût (par ex. « Lofi Study Club ») et les
  **concerts à proximité** des artistes suivis ou proches.

---

## 2. Problématique

> **Comment recommander à une personne la musique qui correspond à ce qu'elle ressent *maintenant*, à
> partir d'une simple description en langage naturel, sans qu'elle perde du temps à chercher ?**

Ce que nous constatons :

| Problème | Conséquence pour l'utilisateur |
|---|---|
| ⏱️ **Temps perdu à chercher** le bon morceau : on « skippe », on fait défiler des playlists, on tape des mots-clés qui ne correspondent pas à ce qu'on ressent | Frustration ; on finit par écouter toujours la même chose |
| 📢 **Publicité et recommandations commerciales** : les plateformes mettent en avant des titres sponsorisés, des playlists éditoriales et des artistes déjà populaires | Les recommandations ne reflètent pas vraiment nos goûts ni notre état d'esprit |
| 🔁 **Bulle de filtre** : les algorithmes fondés sur l'historique proposent toujours le même style | Peu de découverte, aucune prise en compte de l'humeur du jour |
| 🧠 **L'humeur se dit en phrases, pas en mots-clés** : « je suis à bout et j'ai besoin de souffler » ne contient ni « calme » ni « piano » | La recherche par mots-clés échoue ; il faut comprendre le **sens** |
| 👥 **Isolement de l'écoute** : on écoute seul, sans savoir qui partage nos goûts | Peu d'échanges, peu de découvertes |
| 🎫 **Concerts ratés** : on apprend trop tard qu'un artiste qu'on écoute passait près de chez nous | Occasions manquées |

**Hypothèse du projet** : une analyse **sémantique et contextuelle** (embeddings de phrases +
similarité cosinus) des descriptions libres de l'utilisateur, comparées à des descriptions textuelles
riches des morceaux, donne des recommandations plus pertinentes et **explicables** qu'une simple
correspondance de mots-clés ou un calcul numérique.

---

## 3. Objectifs

### Objectifs pédagogiques (sujet)
- Appliquer une chaîne NLP complète : **prétraitement → tokenisation → vectorisation (embeddings) →
  similarité cosinus → scoring → recommandation**.
- Montrer la différence entre analyse **numérique / lexicale** (TF-IDF, mots-clés) et analyse
  **sémantique / contextuelle** (SBERT).
- Concevoir et **justifier** une formule de scoring (poids, agrégation par blocs, seuils).
- Livrer un prototype web fonctionnel de bout en bout et le présenter.

### Objectifs produit
1. **Comprendre l'humeur** de l'utilisateur à partir de son texte libre.
2. **Calculer pour chaque musique** du catalogue un score de similarité sémantique (cosinus) avec ce que
   l'utilisateur aime ou demande, puis produire un **top 3** (et un top 10 détaillé).
3. **Construire un profil** d'auditeur (humeurs dominantes, contextes, genres, personnalité).
4. **Expliquer** chaque recommandation (critères, score, mots-clés proches).
5. **Visualiser** dans un dashboard comment les genres et artistes recommandés s'alignent avec les
   préférences déclarées.
6. **Connecter** l'utilisateur à des communautés de même goût et à des concerts proches.

### Indicateurs de réussite
- Precision@3 ≥ 0,7 sur notre jeu de requêtes de test annotées (§19).
- SBERT meilleur que les baselines TF-IDF et Word2Vec sur les mêmes requêtes.
- Temps de réponse < 1 s par requête (embeddings du catalogue pré-calculés).

---

## 4. Fonctionnalités

| # | Fonctionnalité | Description | Statut |
|---|---|---|---|
| F1 | **Questionnaire / quiz** | Questions ouvertes (texte libre), choix multiples, cases à cocher, Likert, questions guidées, personnalité (TIPI) | Obligatoire |
| F2 | **Profil musical** | Humeurs dominantes, contextes, genres, artistes, personnalité, profil d'auditeur (archétype) | Obligatoire |
| F3 | **Recommandation sémantique** | Score cosinus pour chaque morceau → score composite → top 3 / top 10 | Obligatoire |
| F4 | **Explications** | Critères principaux, contribution de chaque critère, mots-clés les plus proches | Obligatoire |
| F5 | **Dashboard** | Radar d'humeurs, scores, top 3, agrégations par genre et par artiste, alignement avec les préférences, carte de similarité | Obligatoire |
| F6 | **Chatbot d'humeur** | Demande libre (« je suis énervée, je veux du calme ») → détection d'émotion et de souhait → recommandations | Bonus B (fonctionne sans LLM) |
| F7 | **Communautés** | Communautés au goût proche (Lofi Study Club, Run & Beats…) par similarité sémantique | Extension |
| F8 | **Concerts** | Concerts des artistes suivis ou sémantiquement proches, filtrés par distance | Extension |
| F9 | **LLM optionnel** | Reformulation, réponse plus naturelle du chatbot, explications enrichies | Bonus A/E (optionnel) |

---

## 5. Conformité aux exigences du sujet

| Exigence du sujet | Notre implémentation | Module |
|---|---|---|
| **E1 – Questionnaire** (ouvertes, Likert, guidées, QCM, cases à cocher, assez de texte libre) | 5 questions ouvertes + QCM genres et contextes + 3 Likert + 1 question guidée + 10 items TIPI + ville | `data/questionnaire.json`, `profile.py`, `app/` |
| **E2 – Jeu de données de référence** (catégories, attributs, descriptions, mots-clés, relations) | 84 morceaux (minimum demandé : 70) × 14 genres, avec humeur, contexte, énergie, description, mots-clés ; 9 blocs d'humeur, 8 blocs de contexte, 6 profils d'auditeur | `data/*.csv`, `data/*.json` |
| **E3 – Moteur sémantique** (prétraitement, embeddings de mots, embeddings contextuels, cosinus) | Nettoyage et tokenisation ; **SBERT multilingue** (principal) ; **Word2Vec / fastText** et **TF-IDF** (baselines comparatives) ; cosinus | `preprocessing.py`, `embeddings.py` |
| **E4 – Scoring justifié** (similarité, agrégation par catégorie, poids, seuils, contraintes) | Score composite pondéré par morceau ; affinité par bloc ; **score de couverture** Σ WᵢSᵢ / Σ Wᵢ ; seuils ; filtres sur les genres refusés | `scoring.py`, `config.py` |
| **E5 – Recommandations** (top 3, score, critères, explication par règles) | Top 3 diversifié, score, contribution de chaque critère, mots-clés les plus proches, phrase générée par modèle de texte | `explain.py` |
| **E6 – Visualisation** (profil, scores, couverture, classement, radar / barres / heatmap) | Dashboard Streamlit + Plotly | `app/` |
| **Score de couverture** | Couverture de chaque profil d'auditeur sur les blocs d'humeur (formule du sujet) | `scoring.analyze_profile` |
| **Bonus** (chatbot, LLM, RAG, agent) | Chatbot NLU sans LLM ; LLM optionnel par-dessus | `chatbot.py` |
| **Fonctionne sans IA générative** | ✅ tout le pipeline est autonome | — |

> 💡 **Correspondance avec l'exemple du sujet** (cartographie des compétences) :
> *blocs de compétences* → **blocs d'humeur et de contexte** ; *compétences* → **phrases prototypes** ;
> *profils de poste* → **profils d'auditeur** (archétypes) ; *recommandation de poste* → **recommandation
> de morceaux, de communautés et de concerts**.

---

## 6. Architecture et pipeline NLP

```
┌──────────────────────┐      ┌──────────────────────┐
│ Questionnaire / Quiz │      │   Chatbot (texte     │
│ (ouvert + fermé)     │      │   libre du moment)   │
└──────────┬───────────┘      └──────────┬───────────┘
           │ réponses JSON               │ message
           ▼                             ▼
┌──────────────────────────────────────────────────────┐
│ 1. PRÉTRAITEMENT  nettoyage, normalisation,          │
│    découpage en phrases, tokenisation (baselines)    │
├──────────────────────────────────────────────────────┤
│ 2. VECTORISATION  SBERT (contextuel)                 │
│    | Word2Vec/fastText | TF-IDF (baselines)          │
├──────────────────────────────────────────────────────┤
│ 3. SIMILARITÉ COSINUS  utilisateur × CHAQUE morceau  │
│    (vue globale, vue humeur, vue contexte),          │
│    × blocs d'humeur, × émotions, × communautés       │
├──────────────────────────────────────────────────────┤
│ 4. SCORING  composantes → score pondéré → seuils,    │
│    filtres, couverture par bloc et par archétype     │
├──────────────────────────────────────────────────────┤
│ 5. RECOMMANDATION  top-k diversifié + agrégation     │
│    genres / artistes + communautés + concerts        │
├──────────────────────────────────────────────────────┤
│ 6. EXPLICATION  critères, contributions, mots-clés   │
└──────────────────────────┬───────────────────────────┘
                           ▼
              ┌──────────────────────────┐
              │  Dashboard Streamlit     │
              │  (profil, top, stats)    │
              └──────────────────────────┘
          Stockage : réponses + profils + recos en JSON / SQLite
```

Les embeddings du catalogue sont **pré-calculés une seule fois** au démarrage (et mis en cache). Seul le
texte de l'utilisateur est encodé à chaque requête.

---

## 7. Jeu de données de référence

### 7.1 Fichiers

| Fichier | Contenu | Taille |
|---|---|---|
| `data/tracks.csv` | Catalogue de morceaux | 84 morceaux, 14 genres |
| `data/blocks.json` | Blocs d'humeur (9), blocs de contexte (8), prototypes d'émotions (8), règles de régulation | — |
| `data/archetypes.json` | Profils d'auditeur et blocs requis, avec poids | 6 |
| `data/communities.csv` | Communautés (nom, description, genres, humeurs, contextes) | 14 |
| `data/concerts_simules.csv` | Concerts **simulés** (artiste, ville, salle, date) | 35 |
| `data/cities.csv` | Coordonnées GPS des villes | 15 |
| `data/questionnaire.json` | Définition du questionnaire | 5 sections |
| `data/personality_music.json` | Lien personnalité → genres (modèle STOMP) | 4 dimensions |

### 7.2 Structure du catalogue (`tracks.csv`)

```
track_id | title | artist | genre | mood | context | energy | language | description | keywords
```

| Colonne | Rôle dans l'analyse |
|---|---|
| `genre` | Catégorie (agrégation par genre, filtres) |
| `mood` | Tags d'humeur multi-valués (`calme|rêveur`) → vue humeur |
| `context` | Contextes d'écoute (`étude|sommeil`) → vue contexte |
| `energy` | Attribut structuré 1-5 (rapproché de la réponse Likert) |
| `description` | **Texte en langage naturel** (cœur de l'analyse sémantique) |
| `keywords` | Mots-clés descriptifs → explications |

### 7.3 Origine et prétraitement (à documenter dans le notebook 01)
- Titres et artistes réels sélectionnés par l'équipe pour couvrir 14 genres et 9 humeurs.
- **Descriptions, humeurs et contextes rédigés par l'équipe** (texte original, pas de paroles de chansons).
  On pourra les enrichir avec les tags de l'API Last.fm (`track.getTopTags`, gratuite).
- ⚠️ À faire : faire relire chaque ligne par un membre de l'équipe (vérifier titre, artiste, genre).
- Prétraitement : normalisation Unicode, découpage des champs multi-valués, construction de trois
  **vues textuelles** par morceau (globale / humeur / contexte, voir §9.3).

---

## 8. Questionnaire utilisateur

Le questionnaire est défini dans `data/questionnaire.json` : l'interface est générée à partir de ce
fichier. Chaque question indique quel champ du profil elle alimente (`feeds`).

| Section | Exemples de questions | Type |
|---|---|---|
| **S1 – Univers musical** | « Décris la musique que tu aimes et ce qu'elle t'apporte » | 🟢 **Ouverte** |
| | « Quels genres écoutes-tu souvent ? » | QCM (cases à cocher) |
| | « Quels genres ne veux-tu jamais qu'on te propose ? » | QCM (filtre dur) |
| | « Cite tes artistes préférés » | Ouverte courte |
| | « Raconte un morceau qui t'a marqué et pourquoi » | 🟢 **Ouverte** |
| **S2 – Moments d'écoute** | « Quand écoutes-tu le plus de musique ? » | QCM |
| | « Dans quel contexte écoutes-tu de la musique ? Décris-le. » | 🟢 **Ouverte** |
| | « Écoutes-tu de la musique pour étudier ? » → si oui : « Quelle ambiance t'aide à te concentrer ? » | Guidée + ouverte |
| | « Calme (1) ↔ très énergique (5) » / importance des paroles / goût de la découverte | Likert 1-5 |
| **S3 – Musique et émotions** | « Avec ces artistes, quelles humeurs recherches-tu ? » | 🟢 **Ouverte** |
| | « Quand tu es triste ou énervé·e, tu préfères une musique qui **change** ton humeur ou qui **l'accompagne** ? » | Choix unique |
| | « Décris l'ambiance idéale d'un dimanche parfait » / « Que mets-tu pour te défouler ? » | 🟢 **Ouverte** |
| **S4 – Personnalité** | 10 items TIPI (« Je me vois comme quelqu'un d'ouvert, curieux… ») | Likert 1-7 |
| **S5 – Concerts** | Ville ; distance maximale acceptée | Choix unique + Likert |

> **Règle de conception** : chaque section contient au moins une question ouverte. Les réponses libres
> sont la matière première de l'analyse sémantique. Les questions fermées servent de **signaux
> structurés** (filtres, poids, contraintes) et ne remplacent jamais le texte.

Les réponses sont **stockées** en JSON (`storage/responses.jsonl`), puis en SQLite dans une deuxième
version, avec un horodatage, le profil calculé et les recommandations.

---

## 9. Moteur d'analyse sémantique

### 9.1 Prétraitement (`preprocessing.py`)

| Étape | Pour SBERT | Pour Word2Vec / TF-IDF |
|---|---|---|
| Normalisation Unicode, apostrophes, espaces, ponctuation répétée | ✅ | ✅ |
| Découpage en **phrases** (une réponse = plusieurs intentions) | ✅ | ✅ |
| Minuscules, tokenisation, élisions (*l'ambiance → ambiance*) | ❌ (le modèle a son propre tokenizer WordPiece) | ✅ |
| Suppression des stopwords | ❌ (on garde « pas », « ne », « sans » : la négation compte) | ✅ |
| Lemmatisation (spaCy `fr_core_news_sm`) | ❌ | Optionnel |
| Suppression des accents | Uniquement pour la correspondance exacte (artistes, genres) | |

**Pourquoi un prétraitement léger pour SBERT ?** Les modèles contextuels ont besoin des mots-outils, de
l'ordre des mots et de la négation pour saisir le sens. *« Je ne veux pas de musique triste »* perd tout
son sens si on retire « ne » et « pas ».

### 9.2 Vectorisation (`embeddings.py`)

Les trois encodeurs ont la même interface (`encode(textes) → vecteurs normalisés L2`) et sont donc
interchangeables. C'est ce qui permet de les comparer dans le notebook 02.

| Encodeur | Type | Rôle | Modèle |
|---|---|---|---|
| **SBERT** | Embeddings **contextuels** de phrases | ⭐ **Moteur principal** | `paraphrase-multilingual-MiniLM-L12-v2` (384 dim.) |
| Word2Vec / fastText | Embeddings **de mots** (moyenne) | Baseline « embeddings de mots » | fastText FR `cc.fr.300` réduit, ou Word2Vec entraîné sur le corpus |
| TF-IDF (mots + n-grammes de caractères) | Lexical / sac de mots | Baseline « mots-clés » et repli hors ligne | scikit-learn |

**Pourquoi SBERT multilingue ?**
1. Il encode des **phrases entières** en tenant compte du contexte : « je suis à bout » se rapproche de
   « je suis en colère » sans aucun mot commun.
2. Il est **multilingue** : l'utilisateur peut écrire en français, en anglais ou mélanger les deux.
3. Il est entraîné pour que le **cosinus** mesure la proximité sémantique (paraphrases).
4. Il est léger : il tourne sur CPU en quelques millisecondes par phrase.

Modèles alternatifs à comparer : `intfloat/multilingual-e5-base`, `dangvantuan/sentence-camembert-base`.

**Pourquoi la similarité cosinus ?** Elle mesure l'**angle** entre deux vecteurs, indépendamment de leur
norme (et donc de la longueur des textes). Avec des vecteurs normalisés, c'est un simple produit scalaire,
ce qui permet de calculer en une opération le score de **tous** les morceaux.

### 9.3 Vues textuelles des morceaux

Pour savoir **quel critère** fait remonter un morceau, on encode trois vues par morceau :

| Vue | Texte encodé | Comparée à |
|---|---|---|
| `text_full` | titre, artiste, genre, humeurs, contextes, description, mots-clés | tout le texte libre de l'utilisateur |
| `text_mood` | humeurs + description | humeur exprimée + blocs d'humeur ciblés |
| `text_context` | contextes d'écoute | contextes cochés ou détectés |

### 9.4 Analyses sémantiques réalisées

- **Utilisateur × chaque morceau** (3 vues) → matrice de similarités cosinus.
- **Utilisateur × blocs d'humeur et de contexte** → profil (radar).
- **Message × prototypes d'émotions** → détection d'émotion *zero-shot* (chatbot).
- **Profil × communautés** → communautés recommandées.
- **Artiste × artiste** (centroïdes) → artistes similaires (concerts).
- **Mots-clés du morceau × demande** → explications.
- *(Optionnel)* **Clustering** (KMeans sur les embeddings) et projection **UMAP / t-SNE** du catalogue
  pour la carte sémantique du dashboard.

---

## 10. Mécanisme de scoring

### 10.1 Score de similarité de chaque morceau (cœur du système)

Pour **chaque morceau t** du catalogue et chaque phrase u de l'utilisateur :

```
cos(u, t) = (E(u) · E(t)) / (‖E(u)‖ · ‖E(t)‖)
```

Comme l'utilisateur écrit plusieurs phrases, on agrège :

```
S_sem(t) = ½ · moyenne_u cos(u, t)  +  ½ · max_u cos(u, t)
```

- la **moyenne** mesure la correspondance avec l'ensemble de ce qu'a dit l'utilisateur ;
- le **max** garantit qu'un morceau qui correspond très bien à une seule phrase n'est pas noyé.

On calcule de la même façon `S_mood(t)` (vue humeur) et `S_ctx(t)` (vue contexte).

### 10.2 Score composite d'un morceau

> **Mise à jour (parties 4 et 5)** : la formule utilisée par l'API est celle de `backend/recommendation/scoring.py`, détaillée et justifiée dans `notebooks/03_recommandation_api.ipynb` (6 critères : description 0,30, humeur 0,25, contexte 0,15, genre 0,15, énergie 0,10, artiste 0,05, soit 70 % sémantique). Le tableau ci-dessous est la conception de départ.

```
Score(t) = Σ_k w_k · C_k(t) / Σ_k w_k        (sur les composantes k disponibles)
```

| Composante C_k | Calcul | Poids profil | Poids chatbot | Justification |
|---|---|---|---|---|
| `semantic` | cos(texte libre, `text_full`) | **0,30** | 0,30 | Cœur du sujet : sens global |
| `mood` | cos(vecteur d'humeur, `text_mood`) | **0,25** | **0,35** | Promesse produit : musique ↔ humeur |
| `artist` | max cos(morceaux des artistes favoris, t) ; 1 si l'artiste est suivi | 0,15 | 0,05 | Goûts établis (sémantique item-à-item) |
| `context` | cos(contextes, `text_context`) | 0,10 | 0,10 | Situation d'écoute |
| `genre` | 1 si genre coché, 0,4 sinon | 0,10 | 0,05 | Préférence déclarée (signal fermé) |
| `energy` | 1 − \|énergie(t) − cible\| / 4 | 0,05 | 0,10 | Attribut numérique, volontairement faible |
| `personality` | a priori STOMP du genre | 0,05 | 0,05 | Corrélations faibles dans la littérature |

- Les composantes cosinus sont **normalisées min-max sur le catalogue** pour être comparables entre
  elles. Le classement n'est pas modifié ; seules les échelles sont alignées.
- Les **composantes sémantiques représentent environ 80 % du poids**. Les signaux numériques restent
  minoritaires, comme l'exige le sujet.
- **Contraintes dures** : les genres refusés (quiz ou « pas de rap » dans le chat) sont exclus.
- **Diversité** : un seul morceau par artiste dans le top-k.
- Les poids sont centralisés dans `config.py`. Ils seront **ajustés et justifiés** dans le notebook 03
  (étude d'ablation : on retire une composante et on mesure la variation de Precision@3).

### 10.3 Affinité par bloc et score de couverture (formule du sujet)

Pour chaque bloc d'humeur i (par ex. « Calme & détente », décrit par 3 phrases prototypes p) :

```
S_i = ½ · moyenne_u max_p cos(u, p)  +  ½ · max_u max_p cos(u, p)
```

puis, pour chaque **profil d'auditeur** A (ex. « Le Focus Chill » = Concentration ×2, Calme ×1,5,
Rêverie ×1) :

```
Couverture(A) = Σ_{i ∈ A} W_i · S_i  /  Σ_{i ∈ A} W_i
```

→ le profil d'auditeur attribué est celui qui a la plus forte couverture. Cela reproduit la logique
« blocs de compétences → profil de poste » du sujet.

**Calibration** : les cosinus SBERT bruts se situent environ entre 0,1 (sans rapport) et 0,8
(paraphrase). Pour l'affichage, on les rescale linéairement de [0,10 ; 0,70] vers [0 ; 100 %]. Ces bornes
sont à recalibrer sur la distribution observée (notebook 03).

### 10.4 Agrégations pour le matching (genres, artistes)

À partir des scores de tous les morceaux :

```
Score_genre(g)   = moyenne des 3 meilleurs Score(t) des morceaux du genre g
Score_artiste(a) = moyenne des Score(t) des morceaux de l'artiste a
Alignement       = part des genres du top-k qui font partie des genres déclarés
Cos_genre(g)     = cos(profil utilisateur, centroïde des morceaux du genre g)
```

On peut ainsi **recommander des genres et des artistes**, pas seulement des morceaux, et montrer dans le
dashboard l'écart entre « ce que l'utilisateur dit aimer » (QCM) et « ce que son texte exprime »
(sémantique). Cet écart est souvent intéressant et permet des découvertes.

---

## 11. Système de recommandation et explications

Chaque recommandation contient :

| Champ | Exemple |
|---|---|
| Élément | *Peace Piece* – Bill Evans (Jazz) |
| Score de correspondance | 0,87 (similarité sémantique brute 0,62 → 87 % calibré) |
| Critères principaux | ambiance (0,33), description (0,27), énergie (0,09) |
| Mots-clés les plus proches | « apaisement », « méditation » |
| Explication | « *Peace Piece* est recommandé car son ambiance correspond à l'humeur recherchée et sa description est proche de ce que tu as écrit. Mots-clés les plus proches : apaisement, méditation. » |

Les explications sont générées **par règles et modèles de phrases** à partir des résultats NLP
(contribution `w_k · C_k` de chaque critère, et cosinus entre chaque mot-clé et la demande). Le système
est donc transparent et n'a pas besoin de LLM.

---

## 12. Dashboard et visualisations (Streamlit)

### Pages de l'application

| Page | Contenu |
|---|---|
| 🏠 **Accueil** | Présentation, connexion par pseudo |
| 📝 **Quiz** | Questionnaire par sections (barre de progression, navigation précédent / suivant) |
| 👤 **Mon profil** | Synthèse du profil, archétype, radar d'humeurs, personnalité |
| 🎵 **Recommandations** | Top 3 en cartes avec explication + top 10 en tableau |
| 💬 **Chat mood** | Chatbot ; chaque réponse affiche émotion détectée, cible et top 3 |
| 📊 **Dashboard / statistiques** | Visualisations détaillées ci-dessous |
| 👥 **Communautés** | Communautés recommandées et raisons |
| 🎫 **Concerts** | Concerts proches (carte + liste) |
| 🔬 **Labo NLP** *(démo soutenance)* | Comparaison SBERT / Word2Vec / TF-IDF sur la même phrase, matrices de cosinus |

### Visualisations prévues (Plotly)

| Visuel | Ce qu'il montre |
|---|---|
| 🕸️ **Radar des blocs d'humeur** | Affinité S_i de l'utilisateur pour les 9 blocs |
| 📊 **Barres de couverture des archétypes** | Couverture(A) pour les 6 profils d'auditeur |
| 🏆 **Barres empilées du top 3 / top 10** | Score de chaque morceau décomposé par critère (w_k · C_k) |
| 🔥 **Heatmap de similarité** | Phrases de l'utilisateur × morceaux du top 10 (cosinus) |
| 🎼 **Score par genre** | Score_genre(g), avec les genres déclarés mis en évidence → alignement |
| 🎤 **Score par artiste** | Top artistes agrégés |
| 🗺️ **Carte sémantique du catalogue** | Projection UMAP / t-SNE des embeddings, couleur = genre, position de l'utilisateur et du top 3 |
| 📈 **Distribution des scores** | Histogramme des cosinus sur tout le catalogue (montre que le top se détache) |
| 🎯 **Indicateurs** | Taux d'alignement genres, nombre de genres découverts, énergie moyenne du top |

---

## 13. Chatbot d'humeur

L'utilisateur écrit sa demande du moment ; le chatbot s'appuie sur le moteur sémantique et ne le
remplace pas.

**Pipeline NLU (sans LLM)** :
1. **Exclusions** par règles : « pas de rap », « sans metal » → genres retirés.
2. **Séparation état / souhait** grâce aux marqueurs de désir (« je veux », « envie de », « besoin de »…).
3. **Émotion actuelle** : classification *zero-shot* par cosinus avec des prototypes d'émotions
   (colère, tristesse, stress, fatigue, joie, ennui, amour, nostalgie).
4. **Humeur cible** :
   - si un souhait est exprimé → bloc d'humeur le plus proche du souhait ;
   - sinon → **stratégie du profil** (question Q11) : *réguler* (énervé → calme) ou *accompagner*
     (énervé → défoulement), en référence au principe d'iso-musique en musicothérapie.
5. **Contexte** détecté (étude, sport, sommeil…) par similarité.
6. Scoring de tous les morceaux avec les poids « chat », puis top 3 et réponse générée par modèle de texte.
7. **Clarification** : si l'émotion est incertaine (cosinus sous le seuil), le bot pose une question
   (« Tu préfères quelque chose de calme, d'énergique, de festif ou de mélancolique ? »).
8. Chaque message enrichit l'historique du profil (humeurs fréquentes).

**Exemple** : *« Je suis énervée, je veux une musique calme, pas de rap »*
→ émotion : colère · cible : Calme & détente (souhait exprimé) · exclus : Rap FR
→ top 3 : morceaux calmes de jazz, piano ou ambient, avec leurs scores.

---

## 14. Communautés et concerts

### Communautés
```
Score(c) = 0,6 · cos(profil, description_c)  +  0,2 · Jaccard(genres aimés, genres_c)
         + 0,2 · recouvrement(top 3 humeurs, humeurs_c)
```
Exemple : un utilisateur qui écrit *« j'écoute du lofi pour réviser »* se voit proposer
**Lofi Study Club**, avec les raisons affichées.

### Concerts
1. **Artistes candidats** : artistes suivis (affinité 1), artistes écoutés ou recommandés, et artistes
   **sémantiquement proches** (cosinus entre centroïdes d'artistes ≥ 0,55).
2. Distance à la ville de l'utilisateur (**haversine**) et filtre par rayon (question Q15).
3. `Score = 0,6 · affinité + 0,4 · (1 − distance / rayon)`, puis tri.

> ⚠️ Les concerts du fichier `concerts_simules.csv` sont **fictifs** (démonstration).
> Pour des données réelles, il faudra brancher l'API **Ticketmaster Discovery** (gratuite, avec clé).
> Le moteur ne change pas, seule la source des données change.

---

## 15. Bonus IA générative (optionnel)

Le système est **entièrement fonctionnel sans IA générative**. En option :

| Bonus | Usage | Outil gratuit |
|---|---|---|
| A – Explications | Le LLM reçoit profil, scores, top 3 et critères, et rédige une explication fidèle | Ollama (Mistral / Llama 3) ou Gemini (offre gratuite) |
| B – Chatbot | Reformuler une demande ambiguë, réponses plus naturelles | idem |
| C – RAG | Récupérer les fiches de morceaux (FAISS / Chroma sur nos embeddings) pour ancrer les réponses | FAISS |
| E – Synthèse | Résumé du profil en 3 phrases, sans inventer de préférences | idem |

Garde-fou : le LLM ne peut citer **que** des morceaux renvoyés par le moteur.

---

## 16. Stack technique

| Couche | Outils |
|---|---|
| Langage | Python 3.11+ |
| NLP | `sentence-transformers`, `gensim` (Word2Vec / fastText), `scikit-learn` (TF-IDF, KMeans, t-SNE), `spaCy` (lemmatisation, optionnel), `umap-learn` |
| Données | `pandas`, `numpy` |
| Interface et dashboard | **Streamlit** (prototype) + **Plotly** ; interface plus travaillée dans un second temps (React + FastAPI possible, le moteur étant indépendant de l'interface) |
| Stockage | JSONL, puis SQLite |
| Notebooks | Jupyter / Colab (documentation demandée par le sujet) |
| Bonus | Ollama / Gemini, LangChain, FAISS |
| Qualité | `pytest`, `ruff` |

---

## 17. Structure du dépôt

```
moodmatch/
├── README.md
├── requirements.txt
├── data/
│   ├── tracks.csv               # catalogue (84 morceaux)
│   ├── blocks.json              # blocs humeur / contexte, émotions, régulation
│   ├── archetypes.json          # profils d'auditeur (couverture)
│   ├── communities.csv
│   ├── concerts_simules.csv
│   ├── cities.csv
│   ├── questionnaire.json
│   └── personality_music.json
├── src/moodmatch/
│   ├── preprocessing.py         # nettoyage, phrases, tokenisation
│   ├── embeddings.py            # SBERT / Word2Vec / TF-IDF + cosinus
│   ├── reference.py             # chargement des données + embeddings pré-calculés
│   ├── profile.py               # réponses du quiz → profil utilisateur
│   ├── config.py                # poids, seuils, calibration
│   ├── scoring.py               # cosinus par morceau, score composite, couverture, agrégations
│   ├── explain.py               # explications par règles
│   ├── chatbot.py               # NLU humeur / souhait / exclusions
│   ├── social.py                # communautés + concerts
│   ├── engine.py                # façade unique utilisée par l'interface
│   └── storage.py               # sauvegarde des réponses / profils / recos
├── app/
│   ├── streamlit_app.py         # point d'entrée
│   └── pages/                   # Quiz, Profil, Recos, Chat, Dashboard, Communautés, Concerts, Labo NLP
├── notebooks/
│   ├── 01_dataset.ipynb               # construction et exploration du jeu de données
│   ├── 02_embeddings_comparaison.ipynb # TF-IDF vs Word2Vec vs SBERT
│   ├── 03_scoring_calibration.ipynb    # poids, seuils, ablation
│   └── 04_evaluation.ipynb             # Precision@3, NDCG, cas d'usage
├── tests/
│   └── test_pipeline.py
└── storage/                     # réponses utilisateurs (non versionné)
```

---

## 18. Installation et lancement

```bash
git clone <url-du-repo> && cd moodmatch
python -m venv .venv && source .venv/bin/activate     # Windows : .venv\Scripts\activate
pip install -r requirements.txt

# (optionnel) modèle spaCy pour la lemmatisation des baselines
python -m spacy download fr_core_news_sm

# Tests du moteur
pytest -q

# Application
streamlit run app/streamlit_app.py
```

Au premier lancement, le modèle SBERT (~470 Mo) est téléchargé depuis Hugging Face, puis mis en cache.
Sans accès internet, le moteur bascule automatiquement sur la baseline TF-IDF et l'indique.

`requirements.txt` (minimum) :
```
sentence-transformers>=3.0
pandas>=2.0
numpy>=1.26
scikit-learn>=1.4
gensim>=4.3
streamlit>=1.38
plotly>=5.20
umap-learn>=0.5
pytest>=8.0
```

---

## 19. Évaluation et validation

1. **Jeu de requêtes de test** (30 à 40 phrases annotées par l'équipe) : pour chaque phrase, liste des
   morceaux jugés pertinents. Exemple : *« musique calme pour réviser tard le soir »* → {Aruarian Dance,
   i'm closing my eyes, Gymnopédie n°1, Peace Piece…}.
2. **Métriques** : Precision@3, Recall@10, NDCG@10, MRR.
3. **Comparaison des encodeurs** : TF-IDF vs Word2Vec / fastText vs SBERT (vs E5 / CamemBERT) sur les
   mêmes requêtes → **démonstration chiffrée de l'apport sémantique**.
4. **Cas pièges** : paraphrases sans mot commun (« je suis à bout » → calme), négations (« pas triste »),
   phrases mélangeant français et anglais, fautes de frappe.
5. **Ablation** des composantes du score (§10.2) pour justifier les poids.
6. **Test utilisateurs** : 5 à 10 personnes passent le quiz et notent la pertinence du top 3 de 1 à 5.

---

## 20. Feuille de route

### Phase 1 — Fondations NLP *(en cours)*
- [x] Choix du thème, problématique, README
- [x] Jeu de données de référence v1 (84 morceaux, blocs, archétypes, communautés, concerts simulés)
- [x] Définition du questionnaire (`questionnaire.json`)
- [x] Prétraitement + encodeurs interchangeables (SBERT / Word2Vec / TF-IDF)
- [x] Scoring : cosinus par morceau, score composite, couverture, profil
- [x] Explications par règles, chatbot NLU, communautés, concerts
- [ ] `engine.py` (façade), `storage.py`, tests `pytest`
- [ ] Relecture et enrichissement du dataset (vérification, tags Last.fm)

### Phase 2 — Validation de l'analyse sémantique
- [ ] Notebook 01 : exploration du dataset
- [ ] Notebook 02 : comparaison des embeddings (heatmaps, exemples de paraphrases)
- [ ] Notebook 03 : calibration des cosinus, ajustement des poids, ablation
- [ ] Notebook 04 : évaluation (Precision@3, NDCG)

### Phase 3 — Application Streamlit et dashboard
- [ ] Quiz multi-pages + stockage des réponses
- [ ] Pages Profil / Recommandations / Chat
- [ ] Dashboard : radar, barres empilées, heatmap, scores par genre et artiste, carte UMAP
- [ ] Pages Communautés et Concerts

### Phase 4 — Finitions et bonus
- [ ] Interface plus soignée (thème, design ; éventuellement React)
- [ ] LLM optionnel (Ollama / Gemini) pour le chatbot et les explications
- [ ] Support de présentation + scénario de démonstration
- [ ] Documentation PDF (optionnelle)

---

## 21. Répartition du travail

*(À adapter selon la taille du groupe, 6 personnes maximum.)*

| Rôle | Responsabilités |
|---|---|
| **Data** | Dataset (relecture, enrichissement), notebook 01 |
| **NLP 1** | Prétraitement, encodeurs, comparaison des embeddings (notebook 02) |
| **NLP 2** | Scoring, calibration, évaluation (notebooks 03-04) |
| **Chatbot / social** | Chatbot NLU, communautés, concerts, bonus LLM |
| **Front 1** | Quiz Streamlit, stockage, navigation |
| **Front 2** | Dashboard et visualisations, support de présentation |

Tout le monde participe à la soutenance (évaluation individuelle) : chacun présente la partie dont il est
responsable.

---

## 22. Livrables

À déposer sur **Boostcamp** :
- [ ] Dépôt du code source fonctionnel, commenté à chaque étape
- [ ] Notebooks de documentation (choix de conception, algorithmes, bibliothèques)
- [ ] Support de présentation (mettre en avant **l'analyse sémantique**, pas seulement le scoring
      numérique, et présenter les difficultés rencontrées et leurs solutions)
- [ ] *(optionnel)* Documentation PDF

---

## 23. Limites, éthique et données

- **Concerts simulés** : données fictives clairement marquées (`source = simulé`).
- **Personnalité** : les liens personnalité → musique sont statistiquement faibles. Ils servent d'a priori
  léger (poids 0,05), jamais de critère de décision, et le quiz de personnalité est facultatif.
- **Émotions** : le système **ne fait aucun diagnostic psychologique** ; il détecte une humeur pour
  choisir de la musique. Si un message évoque une détresse importante, l'interface affichera un message
  de soutien et des ressources (par ex. le 3114 en France).
- **Données personnelles (RGPD)** : pseudonyme, pas de données sensibles, réponses stockées en local,
  suppression possible.
- **Biais du dataset** : catalogue limité (84 titres, surtout occidental et francophone) → à élargir.
- **Droits** : aucune parole de chanson n'est stockée ; les descriptions sont rédigées par l'équipe.

---

## 24. Références

- Reimers & Gurevych (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*.
- Mikolov et al. (2013). *Efficient Estimation of Word Representations in Vector Space* (Word2Vec).
- Bojanowski et al. (2017). *Enriching Word Vectors with Subword Information* (fastText).
- Rentfrow & Gosling (2003). *The Do Re Mi's of Everyday Life: The Structure and Personality Correlates
  of Music Preferences* (modèle STOMP).
- Gosling, Rentfrow & Swann (2003). *A Very Brief Measure of the Big-Five Personality Domains* (TIPI).
- Documentation : sbert.net · docs.streamlit.io · plotly.com/python · radimrehurek.com/gensim
- Référentiel de compétences et sujet : *Projet – Analyse sémantique et systèmes intelligents de
  recommandation contextuelle*, S. Malaeb, ECE 2026-27.
