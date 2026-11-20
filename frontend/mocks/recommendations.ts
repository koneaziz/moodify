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
    { id: "calm-1", title: "Quiet Current", artist: "The Violet Hours", genre: "Ambient", mood: "Calm", coverUrl: covers.calm, score: 96, moodScore: 98, genreScore: 92, contextScore: 95, explanation: "A spacious instrumental atmosphere pairs well with a gentle, unhurried listening moment.", reasons: ["Soft atmosphere", "Low energy", "Room to breathe"], durationSeconds: 24, audioPreviewUrl: "/audio/quiet-current-demo.wav" },
    { id: "calm-2", title: "After the Rain", artist: "Mira Sol", genre: "Lo-Fi", mood: "Peaceful", coverUrl: covers.focused, score: 91, moodScore: 94, genreScore: 88, contextScore: 90, explanation: "Warm keys and a steady, understated rhythm make this a mellow companion to your moment.", reasons: ["Warm texture", "Easy rhythm", "Gentle mood"] },
    { id: "calm-3", title: "Blue Haze", artist: "Northline", genre: "Jazz", mood: "Reflective", coverUrl: covers.melancholic, score: 87, moodScore: 90, genreScore: 82, contextScore: 88, explanation: "The intimate arrangement stays relaxed while adding a little color and reflection.", reasons: ["Reflective feel", "Relaxed pacing", "Intimate sound"] },
  ],
  energetic: [
    { id: "energy-1", title: "Neon Run", artist: "Nova Arcade", genre: "Electronic", mood: "Energetic", coverUrl: covers.energetic, score: 97, moodScore: 98, genreScore: 95, contextScore: 96, explanation: "Bright synths and a driving pulse create a high energy soundtrack for active moments.", reasons: ["Driving beat", "High energy", "Bright synths"] },
    { id: "energy-2", title: "Electric Summer", artist: "Glass Avenue", genre: "Pop", mood: "Upbeat", coverUrl: covers.calm, score: 92, moodScore: 94, genreScore: 90, contextScore: 91, explanation: "An upbeat hook and crisp rhythm suit a lively mood without slowing the momentum.", reasons: ["Upbeat feel", "Catchy rhythm", "Lively mood"] },
    { id: "energy-3", title: "Full Color", artist: "Juno Vale", genre: "Indie", mood: "Happy", coverUrl: covers.focused, score: 88, moodScore: 89, genreScore: 87, contextScore: 86, explanation: "A playful guitar led track adds warmth and movement to your high energy mix.", reasons: ["Playful sound", "Quick tempo", "Warm energy"] },
  ],
  melancholic: [
    { id: "mel-1", title: "Between Stars", artist: "Eloise Grey", genre: "Indie", mood: "Melancholic", coverUrl: covers.melancholic, score: 96, moodScore: 98, genreScore: 92, contextScore: 94, explanation: "A delicate arrangement leaves space for reflection and a quieter emotional moment.", reasons: ["Reflective mood", "Delicate arrangement", "Soft pacing"] },
    { id: "mel-2", title: "The Long Way Home", artist: "Low Tide Club", genre: "Soul", mood: "Wistful", coverUrl: covers.calm, score: 91, moodScore: 93, genreScore: 89, contextScore: 90, explanation: "A gentle vocal and warm instrumentation support a thoughtful late night mood.", reasons: ["Warm vocal", "Thoughtful feel", "Easy tempo"] },
    { id: "mel-3", title: "Faded Polaroid", artist: "June & The Sea", genre: "Lo-Fi", mood: "Nostalgic", coverUrl: covers.focused, score: 86, moodScore: 89, genreScore: 84, contextScore: 85, explanation: "Soft textures and a nostalgic tone make this a good fit for reflective listening.", reasons: ["Nostalgic tone", "Soft texture", "Low energy"] },
  ],
  focused: [
    { id: "focus-1", title: "Open Tabs", artist: "Stillframe", genre: "Lo-Fi", mood: "Focused", coverUrl: covers.focused, score: 97, moodScore: 96, genreScore: 94, contextScore: 99, explanation: "A consistent, unobtrusive groove makes space for concentrating without demanding attention.", reasons: ["Steady rhythm", "Minimal vocals", "Study friendly"] },
    { id: "focus-2", title: "Quiet Current", artist: "The Violet Hours", genre: "Ambient", mood: "Calm", coverUrl: covers.calm, score: 93, moodScore: 92, genreScore: 91, contextScore: 98, explanation: "The wide ambient texture supports longer periods of focus with very little distraction.", reasons: ["Instrumental", "Low distraction", "Soft atmosphere"], durationSeconds: 24, audioPreviewUrl: "/audio/quiet-current-demo.wav" },
    { id: "focus-3", title: "Paper Lanterns", artist: "Aster Moss", genre: "Classical", mood: "Serene", coverUrl: covers.melancholic, score: 89, moodScore: 88, genreScore: 86, contextScore: 94, explanation: "A restrained piano arrangement provides a calm backdrop for working or studying.", reasons: ["Piano led", "Quiet energy", "Work friendly"] },
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
  const mood = answers.moods.join(" & ").toLowerCase();
  const activity = answers.listeningContext.toLowerCase();

  return {
    recommendations,
    scenario,
    profileSummary: `A ${mood} mood, music for ${activity}, and an energy level of ${answers.energyLevel}/5.`,
    affinities: [
      { label: "Mood", score: recommendations[0].moodScore },
      { label: "Genre", score: recommendations[0].genreScore },
      { label: "Context", score: recommendations[0].contextScore },
      { label: "Overall", score: recommendations[0].score },
    ],
    isDemo: true,
  };
}
