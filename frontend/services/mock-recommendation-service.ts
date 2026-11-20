import type { RecommendationService } from "@/services/recommendation-service";
import { createDemoResults } from "@/mocks/recommendations";

export const mockRecommendationService: RecommendationService = {
  async getRecommendations(answers) {
    // A short pause makes the transition visible; it is not NLP processing.
    await new Promise((resolve) => setTimeout(resolve, 350));
    return createDemoResults(answers);
  },
};
