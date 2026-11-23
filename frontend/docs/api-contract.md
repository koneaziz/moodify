# Recommendation API contract

FastAPI serves this contract in `backend/main.py`.

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

Return up to ten ranked recommendations for the playlist. Discover highlights the first three and shows their average scores as affinities. All scores are percentages from 0 to 100. The backend should derive explanations from actual NLP and scoring results. `coverUrl` must be a URL that the frontend is configured to display. Omit optional audio and external music fields when unavailable; do not send null unless the response schema explicitly permits it.

For Spotify playback, `spotifyTrackId` must be a genuine 22-character track ID. For Apple Music, `appleMusicEmbedUrl` must use `https://embed.music.apple.com/`. For local audio, only return authorized files or URLs.

The frontend's `FastApiRecommendationService` uses this response shape and route. If the backend adopts a different schema, adapt only that service layer and retain the UI types.

## Mood chat

POST /chat accepts a JSON object with a message (3 to 1,000 characters). It returns a French reply and up to three recommendations with the same fields as above. When the engine asks the user to clarify, the recommendations array is empty. Each message is analysed independently.
