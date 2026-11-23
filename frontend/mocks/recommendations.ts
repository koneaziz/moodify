import { contextLabels, moodLabels } from "@/lib/labels-fr";
import type { Recommendation, RecommendationResponse } from "@/types/music";
import type { QuestionnaireAnswers } from "@/types/questionnaire";

type Scenario = "calm" | "energetic" | "melancholic" | "focused";

const covers = {
  calm: "/covers/calm.svg",
  energetic: "/covers/energetic.svg",
  melancholic: "/covers/melancholic.svg",
  focused: "/covers/focused.svg",
};

const catalog: Record<Scenario, Omit<Recommendation, "rank">[]> = {
  calm: [
    { id: "calm-1", title: "Quiet Current", artist: "The Violet Hours", genre: "Ambient", mood: "Calme", coverUrl: covers.calm, score: 96, moodScore: 98, genreScore: 92, contextScore: 95, explanation: "Un arrangement instrumental aéré pour un moment d’écoute tout en douceur.", reasons: ["Ambiance douce", "Faible énergie", "Respiration"], durationSeconds: 24, audioPreviewUrl: "/audio/quiet-current-demo.wav" },
    { id: "calm-2", title: "After the Rain", artist: "Mira Sol", genre: "Lo-Fi", mood: "Paisible", coverUrl: covers.focused, score: 91, moodScore: 94, genreScore: 88, contextScore: 90, explanation: "Des claviers chaleureux et un rythme discret pour accompagner un moment calme.", reasons: ["Texture chaleureuse", "Rythme tranquille", "Ambiance paisible"] },
    { id: "calm-3", title: "Blue Haze", artist: "Northline", genre: "Jazz", mood: "Contemplatif", coverUrl: covers.melancholic, score: 87, moodScore: 90, genreScore: 82, contextScore: 88, explanation: "Un arrangement intimiste et paisible qui invite à la réflexion.", reasons: ["Invitation à la réflexion", "Tempo détendu", "Son intimiste"] },
  ],
  energetic: [
    { id: "energy-1", title: "Neon Run", artist: "Nova Arcade", genre: "Électronique", mood: "Énergique", coverUrl: covers.energetic, score: 97, moodScore: 98, genreScore: 95, contextScore: 96, explanation: "Des synthés lumineux et un rythme soutenu pour les moments où vous bougez.", reasons: ["Rythme soutenu", "Forte énergie", "Synthés lumineux"] },
    { id: "energy-2", title: "Electric Summer", artist: "Glass Avenue", genre: "Pop", mood: "Entraînant", coverUrl: covers.calm, score: 92, moodScore: 94, genreScore: 90, contextScore: 91, explanation: "Un refrain entraînant et un rythme net qui gardent l’élan.", reasons: ["Ambiance entraînante", "Rythme accrocheur", "Ambiance vive"] },
    { id: "energy-3", title: "Full Color", artist: "Juno Vale", genre: "Indé", mood: "Joyeux", coverUrl: covers.focused, score: 88, moodScore: 89, genreScore: 87, contextScore: 86, explanation: "Une guitare espiègle et chaleureuse qui donne du mouvement à la sélection.", reasons: ["Son espiègle", "Tempo rapide", "Énergie chaleureuse"] },
  ],
  melancholic: [
    { id: "mel-1", title: "Between Stars", artist: "Eloise Grey", genre: "Indé", mood: "Mélancolique", coverUrl: covers.melancholic, score: 96, moodScore: 98, genreScore: 92, contextScore: 94, explanation: "Un arrangement délicat qui laisse de la place aux émotions et à la réflexion.", reasons: ["Ambiance contemplative", "Arrangement délicat", "Tempo doux"] },
    { id: "mel-2", title: "The Long Way Home", artist: "Low Tide Club", genre: "Soul", mood: "Rêveur", coverUrl: covers.calm, score: 91, moodScore: 93, genreScore: 89, contextScore: 90, explanation: "Une voix douce et des instruments chaleureux pour une soirée contemplative.", reasons: ["Voix chaleureuse", "Ambiance méditative", "Tempo tranquille"] },
    { id: "mel-3", title: "Faded Polaroid", artist: "June & The Sea", genre: "Lo-Fi", mood: "Nostalgique", coverUrl: covers.focused, score: 86, moodScore: 89, genreScore: 84, contextScore: 85, explanation: "Des textures douces et une touche de nostalgie pour les moments de réflexion.", reasons: ["Tonalité nostalgique", "Texture douce", "Faible énergie"] },
  ],
  focused: [
    { id: "focus-1", title: "Open Tabs", artist: "Stillframe", genre: "Lo-Fi", mood: "Concentré", coverUrl: covers.focused, score: 97, moodScore: 96, genreScore: 94, contextScore: 99, explanation: "Un rythme régulier et discret qui aide à se concentrer.", reasons: ["Rythme régulier", "Peu de chant", "Adapté aux révisions"] },
    { id: "focus-2", title: "Quiet Current", artist: "The Violet Hours", genre: "Ambient", mood: "Calme", coverUrl: covers.calm, score: 93, moodScore: 92, genreScore: 91, contextScore: 98, explanation: "Une ambiance feutrée propice aux longues périodes de concentration.", reasons: ["Instrumental", "Peu de distractions", "Ambiance douce"], durationSeconds: 24, audioPreviewUrl: "/audio/quiet-current-demo.wav" },
    { id: "focus-3", title: "Paper Lanterns", artist: "Aster Moss", genre: "Classique", mood: "Serein", coverUrl: covers.melancholic, score: 89, moodScore: 88, genreScore: 86, contextScore: 94, explanation: "Un piano épuré qui accompagne calmement le travail ou les révisions.", reasons: ["Piano au premier plan", "Énergie douce", "Adapté au travail"] },
  ],
};

export function selectScenario(answers: QuestionnaireAnswers): Scenario {
  if (answers.moods.includes("Focused") || answers.listeningContext === "Studying" || answers.listeningContext === "Working") return "focused";
  if (answers.moods.includes("Energetic") || answers.moods.includes("Happy") || answers.energyLevel >= 4 || answers.listeningContext === "Exercising" || answers.listeningContext === "Partying") return "energetic";
  if (answers.moods.includes("Melancholic") || answers.moods.includes("Sad")) return "melancholic";
  return "calm";
}

export function createDemoResults(answers: QuestionnaireAnswers): RecommendationResponse {
  const scenario = selectScenario(answers);
  const recommendations = catalog[scenario].map((track, index) => ({ ...track, rank: index + 1 }));
  const mood = answers.moods.map((value) => moodLabels[value]).join(" et ").toLowerCase();
  const activity = (answers.listeningContext ? contextLabels[answers.listeningContext].toLowerCase() : "écouter de la musique");

  return {
    recommendations,
    scenario,
    profileSummary: `Humeur : ${mood}. Musique pour ${activity}, avec un niveau d’énergie de ${answers.energyLevel}/5.`,
    affinities: [
      { label: "Mood", score: recommendations[0].moodScore },
      { label: "Genre", score: recommendations[0].genreScore },
      { label: "Context", score: recommendations[0].contextScore },
      { label: "Overall", score: recommendations[0].score },
    ],
    isDemo: true,
  };
}
