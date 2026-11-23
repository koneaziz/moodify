# Dataset API contract

The music library page (`/dataset`) displays the team's reference dataset (`moodify_dataset.json` / `moodify_dataset.csv`, 684 tracks, 29 columns).

## Today (Demo Mode)

The dataset is **not copied** into the frontend. The Next.js route `app/api/tracks/route.ts` reads `data/moodify_dataset.json` at the repository root and returns it unchanged, so the page always shows the data team's latest version. Run the frontend from the `frontend/` folder (`npm run dev`); set `MOODIFY_DATASET_PATH` if the file moves.

This route only works when the frontend runs from a full clone of the repository. Once FastAPI serves `GET /tracks`, set `NEXT_PUBLIC_USE_MOCKS=false` and the route is no longer used.

## Proposed route

`GET /tracks`, no parameters. The backend can return the rows **exactly as exported**, either as a bare array or wrapped:

```json
{ "tracks": [ { "track_id": "5XeFesFbtLpXzIVDNQP22n", "title": "I Wanna Be Yours", "...": "..." } ], "source": "Moodify dataset v1", "updatedAt": "2026-11-23" }
```

The frontend converts each row in `lib/catalog-normalizer.ts`. If the backend changes the shape, adapt only that file and `services/dataset-service.ts`.

## Columns used by the interface

| Column | Use |
| --- | --- |
| `track_id` | Unique ID; when it is a 22-character Spotify ID, the details dialog shows the official Spotify player |
| `title`, `artist`, `featured_artists`, `album` | Card and details |
| `genre`, `sub_genres` | Genre filter and chart, tags |
| `mood`, `mood_blocks` | Mood tags; mood-block filter and chart |
| `context`, `context_blocks` | Context tags; context-block filter and chart |
| `energy` (1–5) | Energy meter, chart, sorting |
| `language` | Details (`inconnu` is shown as Unknown) |
| `description`, `keywords` | Text analysed by NLP, search |
| `source`, `mood_source`, `description_source` | Provenance panel and details |
| `popularity`, `danceability`, `energy_raw`, `valence`, `acousticness`, `instrumentalness`, `tempo` | Audio profile (optional, may be `null`) |
| `muse_valence`, `muse_arousal`, `russell_quadrant` | Emotion map (optional, may be `null`) |
| `cover_url` | Album artwork on cards and details (optional, produced by `dataset_builder/covers.py`; empty → genre icon) |

Multi-valued columns use `|`. Numeric audio columns may be `null` for hand-written ("gold") entries.

## Quality checks shown on the page

Catalogue size (≥ 70), descriptions of at least 15 words, required fields, energy between 1 and 5, duplicates (ID or title + artist), documented source, Spotify audio feature coverage and known language.
