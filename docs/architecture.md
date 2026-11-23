# Architecture de Moodify

1. Le questionnaire Next.js envoie les réponses à `POST /recommendations`.
2. FastAPI associe les choix du questionnaire aux catégories du catalogue et prépare le texte utilisateur.
3. Le moteur NLP compare les réponses aux vues du catalogue. Le module de recommandation combine les critères et renvoie jusqu’à dix morceaux classés avec leurs explications.
4. L’interface affiche le top 3, la liste de lecture et les moyennes du top 3 par critère.
5. La bibliothèque consulte `GET /tracks`. En mode démo ou si l’appel échoue, Next.js lit l’export JSON via `/api/tracks`.

Les formats HTTP sont détaillés dans les contrats [recommandations](../frontend/docs/api-contract.md) et [catalogue](../frontend/docs/dataset-contract.md).

## Répartition du travail

| Personne | Périmètre | Dossiers principaux |
| --- | --- | --- |
| 1 | Interface Next.js : questionnaire, résultats, visualisations et appel à l'API | `frontend/` |
| 2 | Jeu de données : collecte, descriptions textuelles, nettoyage et provenance | `data/`, `notebooks/` |
| 3 | Prétraitement, embeddings et similarité sémantique | `src/moodify/` |
| 4 | Formule de score, classement et critères contributifs | `backend/recommendation/` |
| 5 | API FastAPI, schémas de requête/réponse et intégration | `backend/main.py`, `backend/schemas/` |
| 6 | Profil des préférences, humeur et contexte d'écoute | `src/moodify/profile.py` |

Les tests dans `tests/` et la documentation dans `docs/` sont partagés par l'équipe. Chaque membre documente et vérifie le code dont il est responsable.
