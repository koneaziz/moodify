# Proposed recommendation API contract

This is a **frontend proposal** for the FastAPI team to agree or adjust before integration. No backend endpoint is created by the frontend.

## Request

`POST /recommendations` with `Content-Type: application/json`.

```json
{
  "moods": ["Focused", "Calm"],
  "description": "I need soft, atmospheric music while studying tonight.",
  "genres": ["Ambient", "Lo-Fi"],
  "listeningContext": "Studying",
  "contextDescription": "Late evening before an exam",
  "energyLevel": 2,
  "favoriteArtists": "",
  "vocalPreference": "Instrumental",
  "additionalPreferences": "No heavy percussion"
}
```

The frontend validates at least one mood, a description of 20–1000 characters, at least one genre, and one listening context. `energyLevel` is an integer from 1 to 5.

## Response

```json
{
  "recommendations": [
    {
      "id": "track-001",
      "rank": 1,
      "title": "Example title",
      "artist": "Example artist",
      "coverUrl": "/covers/example.svg",
      "genre": "Ambient",
      "mood": "Calm",
      "score": 93,
      "moodScore": 95,
      "genreScore": 89,
      "contextScore": 96,
      "explanation": "A text explanation grounded in semantic results and contributing criteria.",
      "reasons": ["Soft atmosphere", "Study context"]
    }
  ],
  "affinities": [
    { "label": "Mood", "score": 95 },
    { "label": "Genre", "score": 89 },
    { "label": "Context", "score": 96 },
    { "label": "Overall", "score": 93 }
  ],
  "profileSummary": "A concise description of the user's listening profile.",
  "scenario": "semantic",
  "isDemo": false
}
```

The backend also returns an optional `profile` object (part 6), shown in the "Inside your vibe" section of `/discover`:

```json
"profile": {
  "dominantMood": "Calme & détente", "dominantContext": "Étude & travail",
  "moodBlocks": { "Calme & détente": 100, "Concentration": 64 },
  "contextBlocks": { "Étude & travail": 100 },
  "emotion": "stress", "strategy": "réguler", "strategySource": "texte", "intensity": 2,
  "excludedGenres": ["Hip-hop / Rap"], "instrumental": true, "archetype": "Le Focus Chill"
}
```

Return up to three ranked recommendations. All scores are percentages from 0 to 100. The backend should derive explanations from actual NLP and scoring results. `coverUrl` must be a URL that the frontend is configured to display. Omit optional audio and external music fields when unavailable; do not send null unless the response schema explicitly permits it.

For Spotify playback, `spotifyTrackId` must be a genuine 22-character track ID. For Apple Music, `appleMusicEmbedUrl` must use `https://embed.music.apple.com/`. For local audio, only return authorized files or URLs.

The frontend's `FastApiRecommendationService` currently assumes this response shape and route. If the backend adopts a different schema, adapt only that service layer and retain the UI types.
