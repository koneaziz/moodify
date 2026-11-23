/**
 * One row of the reference dataset exactly as the data team exports it
 * (moodify_dataset.json / moodify_dataset.csv). Multi-valued fields use "|".
 */
export type RawCatalogRow = {
  track_id: string;
  title: string;
  artist: string;
  featured_artists: string;
  album: string;
  genre: string;
  sub_genres: string;
  mood: string;
  context: string;
  energy: number;
  language: string;
  description: string;
  keywords: string;
  mood_blocks: string;
  context_blocks: string;
  tags_mood_human: string;
  mood_source: string;
  description_source: string;
  source: string;
  popularity: number | null;
  danceability: number | null;
  energy_raw: number | null;
  valence: number | null;
  acousticness: number | null;
  instrumentalness: number | null;
  tempo: number | null;
  muse_valence: number | null;
  muse_arousal: number | null;
  russell_quadrant: string | null;
};

export type AudioFeatures = {
  danceability: number;
  energy: number;
  valence: number;
  acousticness: number;
  instrumentalness: number;
  tempo: number;
};

/** Normalized entry used by the interface (see lib/catalog-normalizer.ts). */
export type CatalogTrack = {
  id: string;
  title: string;
  artist: string;
  featuredArtists: string[];
  album?: string;
  genre: string;
  subGenres: string[];
  moods: string[];
  contexts: string[];
  moodBlocks: string[];
  contextBlocks: string[];
  /** Structured energy attribute from 1 (very calm) to 5 (very energetic). */
  energy: number;
  language?: string;
  /** Natural-language description used by the NLP module. */
  description: string;
  keywords: string[];
  source?: string;
  moodSource?: string;
  descriptionSource?: string;
  /** Present only when track_id is a genuine 22-character Spotify ID. */
  spotifyTrackId?: string;
  popularity?: number;
  audio?: AudioFeatures;
  /** Valence / arousal (0–1) and Russell quadrant. */
  emotion?: { valence: number; arousal: number; quadrant?: string };
};

export type CatalogResponse = {
  tracks: CatalogTrack[];
  /** Human-readable origin of the whole dataset, shown in the interface. */
  source: string;
  updatedAt?: string;
  isDemo: boolean;
};
