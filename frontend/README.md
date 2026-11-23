# Moodify frontend

Next.js App Router frontend for **Moodify — Your mood, your music.** It starts on a seven-step questionnaire, shows three recommendations on `/discover`, and lets users browse the reference catalogue on `/dataset`.

## Run locally

Requirements: Node.js 20.9 or newer and npm.

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open <http://localhost:3000>. The default configuration uses **Demo Mode** and needs no backend or Spotify key.

Useful checks:

```bash
npm run typecheck
npm run lint
npm run build
```

## Demo Mode

The mock service in `services/mock-recommendation-service.ts` returns one of four fixed scenarios (`calm`, `energetic`, `melancholic`, `focused`) based on the questionnaire's structured choices. Text answers are collected and shown in the recap but **are not analyzed semantically in Demo Mode**. All demo tracks and scores are fictional. The interface labels both the mode and its illustrative scores.

Questionnaire answers and the last result are kept temporarily in browser `sessionStorage`. Closing the tab ends that session. `/discover` shows an empty state when no result is available.

The local `public/audio/quiet-current-demo.wav` is an original synthetic instrumental sample generated for this project. Other fictional tracks intentionally display an unavailable audio state. When the backend later returns an authorized local audio URL, a valid Spotify track ID, or an official Apple Music embed URL, the player supports those sources without a Spotify API key. Commercial audio is never downloaded or proxied by this frontend.

## Connecting FastAPI

The components call the `RecommendationService` interface in `services/recommendation-service.ts`; they never import mock data directly. Set `NEXT_PUBLIC_USE_MOCKS=false` and `NEXT_PUBLIC_API_URL` in `.env.local` after the backend team implements the agreed endpoint. The current HTTP adapter uses a **proposed** `POST /recommendations` route; it is not implemented in this repository. Adapt that file if the team chooses another route or payload.

The proposed request and response contract is in [API contract](./docs/api-contract.md). The music library page (`/dataset`) uses `services/dataset-service.ts` and a proposed `GET /tracks` route described in [Dataset contract](./docs/dataset-contract.md); in Demo Mode it reads `data/moodify_dataset.json` at the repository root through the local route `app/api/tracks/route.ts` (no copy in the frontend). The backend must allow the frontend origin through CORS if the two apps run on separate local ports.

## Code map

- `app/`: routes and global theme.
- `components/questionnaire/`: guided form and analysis transition.
- `components/recommendations/`: dashboard, recommendation cards and Recharts chart.
- `components/dataset/`: music library page, distribution charts, emotion map, provenance and data quality checks.
- `components/player/`: HTML5 audio and official embed player.
- `components/ui/`: customized shadcn/ui-style Radix primitives.
- `types/`, `lib/`, `services/`, `mocks/`: models, validation, persistence, service adapters and fictional data.
- `public/`: original demo artwork and audio.
