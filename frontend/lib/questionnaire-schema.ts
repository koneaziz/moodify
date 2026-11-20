import { z } from "zod";
import { CONTEXTS, GENRES, MOODS, VOCAL_PREFERENCES } from "@/types/questionnaire";

export const questionnaireSchema = z.object({
  moods: z.array(z.enum(MOODS)).min(1, "Choose at least one mood."),
  description: z.string().trim().min(20, "Write at least 20 characters so we can understand your mood.").max(1000, "Keep this under 1,000 characters."),
  genres: z.array(z.enum(GENRES)).min(1, "Choose at least one genre."),
  listeningContext: z.union([z.enum(CONTEXTS), z.literal("")]).refine(Boolean, "Choose a listening context."),
  contextDescription: z.string().max(300, "Keep this under 300 characters."),
  energyLevel: z.number().int().min(1).max(5),
  favoriteArtists: z.string().max(200, "Keep this under 200 characters."),
  vocalPreference: z.enum(VOCAL_PREFERENCES),
  additionalPreferences: z.string().max(500, "Keep this under 500 characters."),
});
