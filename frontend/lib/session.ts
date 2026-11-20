import type { QuestionnaireAnswers } from "@/types/questionnaire";
import type { RecommendationResponse } from "@/types/music";

const ANSWERS_KEY = "moodify.answers.v1";
const RESULTS_KEY = "moodify.results.v1";

export function saveAnswers(answers: QuestionnaireAnswers) {
  sessionStorage.setItem(ANSWERS_KEY, JSON.stringify(answers));
}

export function loadAnswers(): QuestionnaireAnswers | null {
  try {
    const saved = sessionStorage.getItem(ANSWERS_KEY);
    return saved ? JSON.parse(saved) as QuestionnaireAnswers : null;
  } catch {
    return null;
  }
}

export function saveResults(results: RecommendationResponse) {
  sessionStorage.setItem(RESULTS_KEY, JSON.stringify(results));
}

export function loadResults(): RecommendationResponse | null {
  try {
    const saved = sessionStorage.getItem(RESULTS_KEY);
    return saved ? JSON.parse(saved) as RecommendationResponse : null;
  } catch {
    return null;
  }
}
