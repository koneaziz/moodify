# Profil utilisateur (partie 6)

Code : `backend/personalization/` · Tests : `tests/test_profile.py` · Cas d'usage : `backend/personalization/cas_usage.py`
· Rapport d'évaluation : [`cas_usage_profil.md`](./cas_usage_profil.md)

## Rôle

Le questionnaire du site donne des réponses brutes : un texte libre, des humeurs et un contexte cochés, des
genres, un niveau d'énergie, des artistes, une préférence de voix et des préférences libres. La partie 6 les
**interprète** pour produire un profil que le moteur de recommandation (partie 4) utilise directement.

```
questionnaire (front)
   │
   ├─ mood_analyzer.py ─────── émotions (colère, tristesse, stress…), négations, intensité,
   │                           stratégie « réguler » / « accompagner », blocs d'humeur visés
   │
   ├─ preference_profiler.py ─ + affinités sémantiques de la partie 3 (SBERT)
   │                           + contexte (case cochée + mots du texte)
   │                           + genres aimés / exclus, instrumental, artistes, archétype, synthèse
   ▼
profil ──> backend/recommendation/scoring.py (partie 4) ──> top 3 expliqué ──> API (partie 5)
```

## Ce que contient le profil

| Élément | Comment il est obtenu | Utilisé pour |
|---|---|---|
| Émotion dominante (+ émotions niées) | Lexique français/anglais, négation dans les 3 mots précédents (« pas triste ») | Choisir les blocs d'humeur visés |
| Intensité (1-3) | Intensifs (« très », « trop », « vraiment »…) et « ! » | Synthèse, API |
| Stratégie | « réguler » si l'utilisateur veut changer d'état (« me calmer », « me remonter le moral »), « accompagner » s'il veut rester dedans (« me défouler ») ; par défaut : accompagner | Règles de régulation de `data/blocks.json` |
| Blocs d'humeur | 50 % affinité sémantique (partie 3) + 50 % règles (émotion × stratégie, ambiances demandées) | Critère « humeur » du score |
| Blocs de contexte | 50 % sémantique + 50 % règles (case cochée = 1, mot du texte = 0,8) | Critère « contexte » du score |
| Genres aimés / exclus | Genres cochés ; exclusions repérées dans le texte (« pas de rap », « je déteste le metal ») | Critère « genre » ; genres exclus = score 0 |
| Instrumental | Case « Instrumental » ou « sans paroles » dans le texte | Morceaux chantés : score × 0,6 |
| Archétype | Couverture des 6 profils d'auditeur de `data/archetypes.json` : Σ(Wi·Si)/ΣWi | Affichage, synthèse |
| Synthèse | Phrase construite à partir des éléments ci-dessus (pas d'IA générative) | `profileSummary` de l'API |

### Pourquoi combiner règles et sémantique ?

- Les **règles** rendent le profil **explicable** et gèrent ce que la similarité cosinus gère mal :
  la **négation** (« je ne suis pas triste » est très proche de « je suis triste » en embeddings) et
  l'**intention** (« triste, je veux qu'on me remonte le moral » ≠ « triste, je veux pleurer »).
- La **similarité sémantique** de la partie 3 capte ce que les règles ne connaissent pas : paraphrases
  (« la journée a été lourde, besoin de me poser »), fautes de frappe, formulations inattendues.

### Stratégie de régulation

Règles de `data/blocks.json` (principe de régulation émotionnelle vs iso-musique) :

| Émotion | « réguler » (changer d'humeur) | « accompagner » (rester dedans) |
|---|---|---|
| colère | Calme & détente | Colère & défoulement |
| tristesse | Joie & bonne humeur | Mélancolie & introspection |
| stress | Calme & détente | Concentration |
| fatigue | Énergie & motivation | Calme & détente |

Seules les émotions négatives sont régulées : la joie ou l'amour restent toujours « accompagnés ».

## Intégration (parties 4 et 5)

- `scoring.construire_profil` appelle `construire_profil_utilisateur` (mêmes clés qu'avant, plus les ajouts).
  L'ancien format de requête reste accepté (notebook 03).
- `scoring.calculer_scores` applique les contraintes du profil : genres exclus et préférence instrumentale.
- `backend/main.py` transmet le questionnaire complet ; la réponse `profile` contient en plus
  `emotion`, `strategy`, `intensity`, `excludedGenres`, `instrumental` et `archetype`.

## Cas d'usage et évaluation

15 utilisateurs types (`cas_usage.py`) couvrent les situations du sujet et les cas pièges du README (§19) :
paraphrase, négation, même émotion avec stratégie inverse, exclusions, instrumental, anglais, fautes de frappe.

```bash
python -m pytest -q tests/test_profile.py                    # vérifie le profil de chaque cas
python -m backend.personalization.evaluation                 # rapport complet avec SBERT
python -m backend.personalization.evaluation --encoder tfidf # version rapide, sans téléchargement
```

L'évaluation compare le top 3 obtenu **avec** le profil de la partie 6 et **avec** le profil provisoire
utilisé avant (affinités sémantiques seules), sur les mêmes cas et le même moteur.

**Limites** (à mentionner) :
- la pertinence d'un morceau est pré-annotée automatiquement (bloc d'humeur + énergie + instrumental) :
  elle doit être confirmée par une relecture humaine et par un test utilisateur (README §19) ;
- les lexiques ont été écrits en même temps que les cas d'usage : de nouveaux cas, rédigés par d'autres
  membres de l'équipe, donneront une mesure plus objective ;
- le niveau d'énergie du curseur est pris tel quel (on ne sait pas si l'utilisateur l'a réglé ou laissé à 3).
