# Moodify — État du projet (à lire en premier)

> Projet NLP ING5 — Thème 4 : recommandation musicale par analyse sémantique de l'humeur.
> Ce fichier résume ce qui existe déjà dans le zip, comment le lancer et ce qu'il reste à faire.
> Le détail de la conception (problématique, formules de score, dashboard prévu…) est dans `README.md`.

---

## 1. En une phrase

L'utilisateur décrit son humeur en texte libre (« je suis énervée, je veux une musique calme ») ;
le système transforme ce texte en vecteurs avec **SBERT**, calcule la **similarité cosinus avec
chaque morceau** du catalogue, combine plusieurs critères dans un score et renvoie un **top 3
expliqué**.

S'y ajoutent un quiz pour construire le profil de l'utilisateur, des **communautés** de même goût
et des **concerts** à proximité.

---

## 2. Ce qui est fait ✅ / ce qui reste à faire ⏳

| Partie | État | Où |
|---|---|---|
| README complet (problématique, objectifs, conformité au sujet, formules, feuille de route) | ✅ | `README.md` |
| Jeu « gold » de 84 morceaux décrits à la main + fichiers de référence (blocs d'humeur, profils d'auditeur, questionnaire, communautés, villes) | ✅ | `data/` |
| Moteur NLP : prétraitement, embeddings (SBERT / Word2Vec / TF-IDF), scoring, explications, chatbot, communautés, concerts | ✅ testé avec SBERT via `demo.py` | `src/moodify/` |
| Pipeline de construction du grand dataset (Spotify + MuSe + Last.fm), 20 phases | ✅ testé sur des données factices seulement | `dataset_builder/` |
| **Dataset final fusionné** (609 morceaux du collègue + 84 gold → 684), tags nettoyés, humeur / contexte, descriptions FR | ✅ | `data/moodify_dataset.csv` (script : `dataset_builder/merge_datasets.py`) |
| **Partie NLP (Houyem)** : prétraitement (2 pipelines), embeddings (TF-IDF, Word2Vec, fastText, SBERT ×3), similarité cosinus par morceau, affinités humeur / genre | ✅ module + notebook (à exécuter avec SBERT) | `src/moodify/semantic.py`, `notebooks/02_nlp_semantique.ipynb`, `tests/test_semantic.py` |
| Lancement du pipeline sur les **vrais** CSV | ⏳ (remplacé par le dataset fusionné) | — |
| Brancher le moteur sur le grand dataset (`data/processed/`) | ⏳ | — |
| Interface Streamlit (quiz, chat, recommandations, dashboard, communautés, concerts) | ⏳ (dossier `app/` vide) | `app/` |
| Notebooks de documentation (01 à 04) | ⏳ (dossier vide) | `notebooks/` |
| `engine.py` (façade), `storage.py`, tests `pytest` | ⏳ | `src/moodify/`, `tests/` |
| Évaluation (Precision@3, comparaison SBERT / Word2Vec / TF-IDF) | ⏳ | — |
| Support de soutenance | ⏳ | — |

---

## 3. Structure du dossier

```
moodify/
├── README.md                ← conception complète du projet
├── CE_QUI_A_ETE_FAIT.md     ← ce fichier
├── requirements.txt
├── demo.py                  ← test rapide du chatbot dans le terminal
├── data/                    ← jeu gold (84 morceaux) + fichiers de référence
│   ├── tracks.csv              catalogue gold
│   ├── blocks.json             9 blocs d'humeur, 8 blocs de contexte, prototypes d'émotions
│   ├── archetypes.json         6 profils d'auditeur (score de couverture)
│   ├── questionnaire.json      définition du quiz (questions ouvertes + fermées + personnalité)
│   ├── communities.csv         14 communautés éditoriales
│   ├── concerts_simules.csv    35 concerts FICTIFS
│   ├── cities.csv
│   └── personality_music.json  lien personnalité → genres (modèle STOMP)
├── src/moodify/           ← moteur NLP
│   ├── preprocessing.py        nettoyage, découpage en phrases, tokenisation
│   ├── embeddings.py           SBERT (principal), Word2Vec, TF-IDF + cosinus
│   ├── reference.py            chargement des données + embeddings pré-calculés
│   ├── profile.py              réponses au quiz → profil utilisateur
│   ├── config.py               poids du score, seuils, calibration
│   ├── scoring.py              cosinus par morceau, score composite, couverture par bloc
│   ├── explain.py              explications par règles (critères, mots-clés proches)
│   ├── chatbot.py              détection émotion / souhait / contexte / exclusions
│   └── social.py               communautés + concerts (distance haversine)
├── dataset_builder/         ← pipeline du dataset (1 fichier = 1 phase)
│   ├── README.md               mode d'emploi détaillé
│   ├── config.py, lexicon.py   seuils et lexiques
│   └── p01_... à p20_...
├── tests/fixtures/make_mock_raw.py   ← génère de FAUX CSV pour tester le pipeline
├── app/                     ← (vide) interface Streamlit à venir
├── notebooks/               ← (vide) notebooks à venir
└── storage/                 ← base SQLite générée par le pipeline
```

---

## 4. Installation (Windows, VS Code)

1. **Décompresser** le zip, puis ouvrir dans VS Code le dossier qui contient `requirements.txt`.
   ⚠ Si vous décompressez dans un dossier déjà nommé `moodify`, vous obtenez
   `moodify\moodify\` : il faut alors aller dans le dossier intérieur.
2. Ouvrir le terminal (**Ctrl + `**) et créer l'environnement :
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
   Si PowerShell bloque les scripts : `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
3. Installer les dépendances. **Utiliser `python -m pip`**, car `pip.exe` peut être bloqué par
   la politique de sécurité de Windows :
   ```powershell
   python -m pip install -r requirements.txt
   ```
4. Mac / Linux : `python3 -m venv .venv && source .venv/bin/activate`, puis la même installation.

---

## 5. Tester le moteur

```powershell
python demo.py "je suis énervée et je veux une musique calme, pas de rap"
```

- Le **premier lancement télécharge le modèle SBERT** (environ 470 Mo, 1 à 2 minutes) ; ensuite
  la réponse arrive en quelques secondes.
- Les avertissements « symlinks » et `HF_TOKEN` sont sans conséquence.

Résultat obtenu lors de notre test :

```
J'ai l'impression que tu te sens plutôt colère (confiance 0.99).
Je vise une ambiance Calme & détente (souhait exprimé).
J'ai exclu : Rap FR.
1. Solitude – Jinsang (Lo-fi)         2. Peace Piece – Bill Evans (Jazz)
3. Gymnopédie No.1 – Erik Satie (Classique)
  + une explication par morceau (critères, mots-clés proches, similarité sémantique)
```

---

## 6. Comment marche le moteur (résumé)

1. **Prétraitement** : nettoyage léger pour SBERT (on garde la négation et les mots-outils) ;
   tokenisation et stopwords pour les comparaisons Word2Vec / TF-IDF.
2. **Vectorisation** : SBERT multilingue `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions).
   Chaque morceau a 3 « vues » encodées : globale, humeur, contexte.
3. **Similarité cosinus** entre le texte de l'utilisateur et chaque morceau, pour chaque vue.
4. **Score composite** :
   `Score = Σ wₖ · Cₖ / Σ wₖ`, avec sémantique 0,30, humeur 0,25, artistes 0,15, contexte 0,10,
   genre 0,10, énergie 0,05, personnalité 0,05.
   Environ 80 % du poids vient des critères sémantiques. Les poids sont dans `src/moodify/config.py`.
5. **Score de couverture** (formule du sujet `Σ WᵢSᵢ / Σ Wᵢ`) : affinité de l'utilisateur avec
   9 blocs d'humeur, puis attribution d'un profil d'auditeur parmi 6.
6. **Chatbot** : sépare l'état actuel (« je suis énervée ») du souhait (« je veux du calme ») ;
   détecte l'émotion par similarité avec des phrases prototypes (sans LLM) et gère « pas de rap ».
   Sans souhait exprimé, il applique la préférence du quiz : changer d'humeur ou l'accompagner.
7. **Explications** : contribution de chaque critère + mots-clés du morceau les plus proches de
   la demande.

---

## 7. Le pipeline du dataset (`dataset_builder/`)

**Pourquoi un pipeline :** le dataset Spotify Kaggle (114 000 morceaux) n'a **aucun texte**, seulement
des valeurs numériques. Or le sujet exige une analyse sémantique de descriptions textuelles.
On le croise donc avec **MuSe** (tags d'émotion écrits par les auditeurs) et **Last.fm** (tags
et biographies), puis on **génère des descriptions en français**.

**À faire pour le lancer sur les vraies données :**
1. Télécharger les deux fichiers et les placer dans `data/raw/` :
   - `dataset.csv` de kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset, renommé
     **`spotify_tracks.csv`** ;
   - le CSV MuSe (zenodo.org/record/4281165 ou copie Kaggle), renommé **`muse_v3.csv`**.
2. *(Optionnel)* clé Last.fm gratuite : `$env:LASTFM_API_KEY="..."`.
3. Lancer `python -m dataset_builder.run_pipeline`.
   - `--list` affiche les phases ;
   - `--from 8` reprend à la phase 8 ;
   - `--only 11` relance une seule phase.

**Les 20 phases :**

| Phases | Rôle |
|---|---|
| 1-2 | Collecte, exploration (statistiques + graphiques) |
| 3-4 | Nettoyage Spotify (doublons, versions « Remastered », filtres, 125 genres → 14 macro-genres), échantillon d'environ 2 000 morceaux |
| 5-6 | Préparation MuSe et jointure avec Spotify (identifiant, puis clé normalisée, puis correspondance approximative) |
| 7-8 | Tags Last.fm, nettoyage et classification sémantique des tags |
| 9-11 | Caractéristiques audio → mots, colonnes humeur / contexte, **descriptions en français** |
| 12-14 | Contrôle qualité, tables finales, fiche du dataset (`reports/DATASET_CARD.md`) |
| 15 | 30 requêtes d'évaluation pré-annotées (à relire) |
| 16 | Alignement du quiz, des blocs et des profils d'auditeur sur le nouveau catalogue |
| 17 | Communautés obtenues par clustering sémantique |
| 18 | 150 utilisateurs **simulés** + « voisins de goût » |
| 19 | Artistes similaires, villes, concerts (simulés ou API Ticketmaster) |
| 20 | Base SQLite + 30 messages de test du chatbot |

**Résultats :**
- `data/processed/` : catalogue final et tables ;
- `reports/` : fiche du dataset, graphiques, fichiers à relire ;
- `storage/moodify.db` : base SQLite.

Le pipeline a été **testé de bout en bout uniquement sur des données factices**
(`tests/fixtures/make_mock_raw.py`). Il reste à le lancer sur les vrais fichiers.

---

## 8. Points d'attention

- **Données simulées** : les concerts et les utilisateurs simulés sont marqués `source = simulé`. À dire
  en soutenance.
- **Noms de genres** : le pipeline utilise 14 macro-genres renommés (« Hip-hop / Rap »,
  « Jazz / Blues »…), alors que le moteur et le jeu gold utilisent encore les anciens (« Rap FR »,
  « Jazz »…). Il faudra aligner le moteur quand on le branchera sur `data/processed/`.
- **Vérification du jeu gold** : les 84 morceaux ont été écrits à la main. Il faut vérifier titre,
  artiste et genre.
- **Relectures manuelles** demandées après le lancement du pipeline :
  - `reports/join_review.csv` ;
  - `reports/manual_review.csv` ;
  - `data/processed/eval_queries.json`.
- **Ne pas versionner** `data/raw/`, `data/interim/` ni `data/cache/` (déjà dans `.gitignore`).

---

## 9. Prochaines étapes proposées

| # | Tâche | Qui ? |
|---|---|---|
| 1 | Télécharger les CSV et lancer le pipeline sur les vraies données ; relire les rapports | |
| 2 | Vérifier le jeu gold (84 morceaux) | |
| 3 | Brancher le moteur sur `data/processed/` + aligner les noms de genres | |
| 4 | Interface Streamlit : quiz + profil + recommandations + chat | |
| 5 | Dashboard (radar, scores par genre / artiste, heatmap, carte sémantique) | |
| 6 | Notebooks 01 à 04 (dataset, comparaison des embeddings, calibration des poids, évaluation) | |
| 7 | Évaluation : Precision@3, SBERT vs Word2Vec vs TF-IDF | |
| 8 | Support de soutenance | |
