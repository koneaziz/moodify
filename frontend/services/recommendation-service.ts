import type { QuestionnaireAnswers } from "@/types/questionnaire";
import type { RecommendationResponse } from "@/types/music";
import { mockRecommendationService } from "@/services/mock-recommendation-service";

export interface RecommendationService {
  getRecommendations(answers: QuestionnaireAnswers): Promise<RecommendationResponse>;
}

class FastApiRecommendationService implements RecommendationService {
  async getRecommendations(answers: QuestionnaireAnswers): Promise<RecommendationResponse> {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!baseUrl) throw new Error("Set NEXT_PUBLIC_API_URL to connect the FastAPI backend.");

    // Proposed contract; the backend team can change this adapter without touching the UI.
    const response = await fetch(`${baseUrl.replace(/\/$/, "")}/recommendations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(answers),
    });
    if (!response.ok) throw new Error(`Recommendation service returned ${response.status}.`);
    return await response.json() as RecommendationResponse;
  }
}

export const recommendationService: RecommendationService =
  process.env.NEXT_PUBLIC_USE_MOCKS === "false"
    ? new FastApiRecommendationService()
    : mockRecommendationService;
