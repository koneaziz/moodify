# Moodify

Moodify est un projet de NLP (ING5 Data & IA, ECE). L’application recommande de la musique selon l’humeur, le contexte d’écoute et les goûts de l’utilisateur. L’interface est en français et le catalogue de référence contient 684 morceaux.

| Page | Fonction |
| --- | --- |
| `/` | Questionnaire sur l’humeur, le contexte, les genres et les préférences |
| `/discover` | Top 3 expliqué, liste de lecture de dix titres au maximum, scores, lecteur et chat d’humeur |
| `/dataset` | Bibliothèque avec recherche, filtres et graphiques sur les données |

Les pochettes viennent du catalogue quand elles sont disponibles. Le lecteur utilise l’intégration officielle de Spotify pour les titres compatibles. Les réponses et les dernières recommandations sont gardées dans la session du navigateur.

## Lancer le projet

Prérequis : Python 3, Node.js 20.9 ou plus récent et npm. Ouvrez deux terminaux à la racine du dépôt.

**Terminal 1 · API FastAPI**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
MOODIFY_ENCODER=tfidf python -m uvicorn backend.main:app --port 8000
```

Sous Windows avec PowerShell, activez l’environnement avec `.venv\Scripts\Activate.ps1` et définissez `$env:MOODIFY_ENCODER = "tfidf"` avant de lancer Uvicorn.

TF-IDF permet de tester le parcours sans télécharger le modèle. Pour utiliser SBERT multilingue, relancez Uvicorn avec `MOODIFY_ENCODER=sbert`. Le premier lancement de SBERT télécharge le modèle et calcule les embeddings du catalogue.

**Terminal 2 · Interface Next.js**

```bash
cd frontend
npm ci
npm run dev
```

Ouvrez [Moodify](http://localhost:3000). La configuration de développement pointe vers [l’API locale](http://localhost:8000/docs). Pour essayer le questionnaire hors ligne avec des résultats fictifs, définissez `NEXT_PUBLIC_USE_MOCKS=true` dans `frontend/.env.local`.

## Calcul des recommandations

Le moteur compare le texte du questionnaire aux descriptions, aux humeurs et aux contextes du catalogue. Le score final est une moyenne pondérée des critères disponibles : texte (30 %), humeur (25 %), contexte (15 %), genre (15 %), énergie (10 %) et artiste (5 %). La liste garde au plus un morceau par artiste. Les explications reprennent les critères qui ont le plus contribué au score.

Les libellés affichés en français conservent les mêmes identifiants côté API. Les réponses libres en français sont analysées directement.

## Organisation du dépôt

| Chemin | Contenu |
| --- | --- |
| `frontend/` | Interface Next.js, lecteur, visualisations et services HTTP |
| `backend/` | API FastAPI, schémas, calcul des scores et classement |
| `src/moodify/` | Prétraitement, embeddings, similarité et modules exploratoires |
| `data/` | Catalogue CSV pour le moteur, export JSON pour la bibliothèque et données de référence |
| `dataset_builder/` | Préparation du catalogue et des pochettes |
| `notebooks/` | Expériences NLP et recommandation |
| `tests/` | Tests du moteur NLP |
| `docs/` | Architecture et document de conception initiale |

## Vérifications et documentation

- Depuis la racine, lancez `python -m pytest -q`.
- Depuis `frontend/`, lancez `npm run typecheck`, `npm run lint` et `npm run build`.
- [Architecture et responsabilités](docs/architecture.md) et [conception initiale](docs/conception-initiale.md).
- [Guide du frontend](frontend/README.md), [contrat de recommandation](frontend/docs/api-contract.md) et [contrat du catalogue](frontend/docs/dataset-contract.md).
- Notebooks [NLP sémantique](notebooks/02_nlp_semantique.ipynb) et [recommandation et API](notebooks/03_recommandation_api.ipynb).

## Auteurs

- Dossongui Kone (`koneaziz`)
- Houyem Jouini
- Maureen (`dimailigmaureen`)
- Messade Djabali
- Mohamed Mahdi Kharrat
