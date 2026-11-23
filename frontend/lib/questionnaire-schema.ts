import { z } from "zod";
import { CONTEXTS, GENRES, MOODS, VOCAL_PREFERENCES } from "@/types/questionnaire";

export const questionnaireSchema = z.object({
  moods: z.array(z.enum(MOODS)).min(1, "Choisissez au moins une humeur."),
  description: z.string().trim().min(20, "Décrivez votre humeur en au moins 20 caractères.").max(1000, "Limitez votre réponse à 1 000 caractères."),
  genres: z.array(z.enum(GENRES)).min(1, "Choisissez au moins un genre."),
  listeningContext: z.union([z.enum(CONTEXTS), z.literal("")]).refine(Boolean, "Choisissez un contexte d’écoute."),
  contextDescription: z.string().max(300, "Limitez votre réponse à 300 caractères."),
  energyLevel: z.number().int().min(1).max(5),
  favoriteArtists: z.string().max(200, "Limitez votre réponse à 200 caractères."),
  vocalPreference: z.enum(VOCAL_PREFERENCES),
  additionalPreferences: z.string().max(500, "Limitez votre réponse à 500 caractères."),
});
