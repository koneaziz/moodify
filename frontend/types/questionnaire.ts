export const MOODS = ["Happy", "Sad", "Calm", "Stressed", "Energetic", "Focused", "Melancholic", "Romantic"] as const;
export const GENRES = ["Pop", "Hip-Hop", "R&B", "Rock", "Jazz", "Classical", "Electronic", "Lo-Fi", "Indie", "Ambient", "Soul", "Other"] as const;
export const CONTEXTS = ["Studying", "Working", "Relaxing", "Exercising", "Driving", "Sleeping", "Partying", "Just vibing"] as const;
export const VOCAL_PREFERENCES = ["Instrumental", "Vocals", "No preference"] as const;

export type Mood = (typeof MOODS)[number];
export type Genre = (typeof GENRES)[number];
export type ListeningContext = (typeof CONTEXTS)[number];
export type VocalPreference = (typeof VOCAL_PREFERENCES)[number];

export type QuestionnaireAnswers = {
  moods: Mood[];
  description: string;
  genres: Genre[];
  listeningContext: ListeningContext | "";
  contextDescription: string;
  energyLevel: number;
  favoriteArtists: string;
  vocalPreference: VocalPreference;
  additionalPreferences: string;
};

export const defaultAnswers: QuestionnaireAnswers = {
  moods: [],
  description: "",
  genres: [],
  listeningContext: "",
  contextDescription: "",
  energyLevel: 3,
  favoriteArtists: "",
  vocalPreference: "No preference",
  additionalPreferences: "",
};
