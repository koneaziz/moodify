import type { Genre, ListeningContext, Mood, VocalPreference } from "@/types/questionnaire";

// Only the labels change. Form state and API payloads keep their original values.
export const moodLabels: Record<Mood, string> = {
  Happy: "Joyeux",
  Sad: "Triste",
  Calm: "Calme",
  Stressed: "Stressé",
  Energetic: "Énergique",
  Focused: "Concentré",
  Melancholic: "Mélancolique",
  Romantic: "Romantique",
};

export const genreLabels: Record<Genre, string> = {
  Pop: "Pop",
  "Hip-Hop": "Hip-hop",
  "R&B": "R&B",
  Rock: "Rock",
  Jazz: "Jazz",
  Classical: "Classique",
  Electronic: "Électronique",
  "Lo-Fi": "Lo-fi",
  Indie: "Indé",
  Ambient: "Ambient",
  Soul: "Soul",
  Other: "Autre",
};

export const contextLabels: Record<ListeningContext, string> = {
  Studying: "Étudier",
  Working: "Travailler",
  Relaxing: "Se détendre",
  Exercising: "Faire du sport",
  Driving: "Conduire",
  Sleeping: "Dormir",
  Partying: "Faire la fête",
  "Just vibing": "Écouter pour le plaisir",
};

export const vocalLabels: Record<VocalPreference, string> = {
  Instrumental: "Instrumental",
  Vocals: "Avec chant",
  "No preference": "Sans préférence",
};

const affinityLabels: Record<string, string> = {
  Mood: "Humeur",
  Genre: "Genre",
  Context: "Contexte",
  Overall: "Global",
};

export function affinityLabel(label: string) {
  return affinityLabels[label] ?? label;
}
