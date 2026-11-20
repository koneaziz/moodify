export type Recommendation = {
  id: string;
  rank: number;
  title: string;
  artist: string;
  coverUrl: string;
  genre: string;
  mood: string;
  durationSeconds?: number;
  score: number;
  moodScore: number;
  genreScore: number;
  contextScore: number;
  explanation: string;
  reasons: string[];
  spotifyUrl?: string;
  spotifyTrackId?: string;
  appleMusicEmbedUrl?: string;
  audioPreviewUrl?: string;
};

export type Affinity = { label: string; score: number };

export type RecommendationResponse = {
  recommendations: Recommendation[];
  affinities: Affinity[];
  profileSummary: string;
  scenario: string;
  isDemo: boolean;
};
