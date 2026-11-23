import type { QuestionnaireAnswers } from "@/types/questionnaire";
import type { RecommendationResponse } from "@/types/music";
import { mockRecommendationService } from "@/services/mock-recommendation-service";

export interface RecommendationService {
  getRecommendations(answers: QuestionnaireAnswers): Promise<RecommendationResponse>;
}

class FastApiRecommendationService implements RecommendationService {
  async getRecommendations(answers: QuestionnaireAnswers): Promise<RecommendationResponse> {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!baseUrl) throw new Error("Configurez NEXT_PUBLIC_API_URL pour connecter l’API.");

    // Proposed contract; the backend team can change this adapter without touching the UI.
    const url = `${baseUrl.replace(/\/$/, "")}/recommendations`;
    let response: Response;
    try {
      response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(answers),
      });
    } catch {
      throw new Error(`Impossible de joindre l’API de recommandation à l’adresse ${baseUrl}. Lancez le serveur FastAPI ou activez le mode démo.`);
    }
    if (!response.ok) throw new Error(`L’API de recommandation a répondu avec le code ${response.status}.`);
    return await response.json() as RecommendationResponse;
  }
}

export const recommendationService: RecommendationService =
  process.env.NEXT_PUBLIC_USE_MOCKS === "false"
    ? new FastApiRecommendationService()
    : mockRecommendationService;
