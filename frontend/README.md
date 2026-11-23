# Interface Moodify

Le frontal Next.js propose le questionnaire (`/`), les recommandations et la liste de lecture (`/discover`), ainsi que la bibliothèque musicale (`/dataset`).

## Développement

Suivez les étapes du [README principal](../README.md#lancer-le-projet) pour démarrer FastAPI. Depuis ce dossier, utilisez `npm ci` et `npm run dev`. La configuration versionnée dans `.env.development` pointe vers l’API locale.

Pour essayer le questionnaire hors ligne avec les données de démonstration, définissez `NEXT_PUBLIC_USE_MOCKS=true` dans `.env.local`. Git ignore ce fichier. En mode démo, la bibliothèque utilise toujours le catalogue du dépôt via `/api/tracks`.

## Fichiers principaux

- `app/` contient les routes et les styles globaux.
- `components/` contient le questionnaire, les recommandations, la bibliothèque et le lecteur.
- `services/` sélectionne les services HTTP ou de démonstration.
- `lib/labels-fr.ts` définit les libellés français des choix et des graphiques.
- `lib/session.ts` gère les réponses et les résultats de l’onglet courant.

Consultez les contrats [recommandations](docs/api-contract.md) et [catalogue](docs/dataset-contract.md). Pour vérifier le frontal, utilisez `npm run typecheck`, `npm run lint` et `npm run build`.
