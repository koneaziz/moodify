export type Recommendation = {
  id: string;
  rank: number;
  title: string;
  artist: string;
  /** Local path or Spotify CDN URL; empty or missing shows a default cover. */
  coverUrl?: string;
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

/** Listening profile computed by the backend (part 6). Absent in Demo Mode. */
export type ListeningProfile = {
  dominantMood: string;
  dominantContext?: string | null;
  /** Mood block -> affinity (0-100). */
  moodBlocks: Record<string, number>;
  /** Context block -> affinity (0-100). */
  contextBlocks: Record<string, number>;
  /** Detected emotion (French key from data/blocks.json: colère, tristesse, stress…). */
  emotion?: string | null;
  /** "réguler" (change the mood) or "accompagner" (match the mood). */
  strategy?: string | null;
  /** "texte" when the user wrote it, "défaut" otherwise. */
  strategySource?: string | null;
  intensity?: number | null;
  excludedGenres?: string[];
  instrumental?: boolean;
  archetype?: string | null;
};

export type RecommendationResponse = {
  recommendations: Recommendation[];
  affinities: Affinity[];
  profileSummary: string;
  scenario: string;
  isDemo: boolean;
  profile?: ListeningProfile;
};
