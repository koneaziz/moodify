# Moodify : structure et responsabilités

Moodify est une application web de recommandation musicale fondée sur les descriptions en langage naturel de l'humeur et des préférences de l'utilisateur.

| Personne | Périmètre | Dossiers principaux |
| --- | --- | --- |
| 1 | Interface Next.js : questionnaire, résultats, visualisations et appel à l'API | `frontend/` |
| 2 | Jeu de données : collecte, descriptions textuelles, nettoyage et provenance | `data/`, `notebooks/` |
| 3 | Prétraitement, embeddings et similarité sémantique | `backend/nlp/` |
| 4 | Formule de score, classement et critères contributifs | `backend/recommendation/` |
| 5 | API FastAPI, schémas de requête/réponse et intégration | `backend/main.py`, `backend/api/`, `backend/schemas/` |
| 6 | Profil des préférences, humeur et contexte d'écoute | `backend/personalization/` |

Les tests dans `tests/` et la documentation dans `docs/` sont partagés par l'équipe. Chaque membre documente et vérifie le code dont il est responsable.

## Premier contrat à définir ensemble

Avant d'implémenter l'interface et le moteur séparément, définir dans `docs/api.md` :

1. Les champs du questionnaire : texte libre sur l'humeur, genres, artistes, activité/contexte et intensité des préférences.
2. Le schéma d'une entrée du catalogue : identifiant, titre, artiste, genre, humeur, description textuelle et mots-clés.
3. Le format de réponse : synthèse des préférences, recommandations classées, scores, critères contributifs et scores par catégorie.

Le jeu de référence doit comporter au moins 70 morceaux ou entrées de playlists, avec des descriptions textuelles assez riches pour permettre la comparaison sémantique. Le scoring et les explications doivent pouvoir fonctionner sans IA générative.
