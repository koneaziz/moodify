import type { CatalogResponse } from "@/types/dataset";
import { normalizeCatalog } from "@/lib/catalog-normalizer";

export interface DatasetService {
  getCatalog(): Promise<CatalogResponse>;
}

async function fetchJson(url: string, label: string) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { error?: string } | null;
    throw new Error(body?.error ?? `${label} a répondu avec le code ${response.status}.`);
  }
  return await response.json() as unknown;
}

// Until the API serves the catalogue, Demo Mode reads data/moodify_dataset.json through app/api/tracks.
const localDatasetService: DatasetService = {
  async getCatalog() {
    const payload = await fetchJson("/api/tracks", "Le catalogue local");
    return { tracks: normalizeCatalog(payload), source: "data/moodify_dataset.json (catalogue de l’équipe)", isDemo: false };
  },
};

class FastApiDatasetService implements DatasetService {
  async getCatalog(): Promise<CatalogResponse> {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!baseUrl) throw new Error("Configurez NEXT_PUBLIC_API_URL pour connecter l’API.");

    // Proposed contract (see docs/dataset-contract.md): rows as exported, as an array or { tracks: [...] }.
    // The API does not list the catalogue yet: fall back to the local route reading data/moodify_dataset.json.
    let payload: unknown;
    try {
      payload = await fetchJson(`${baseUrl.replace(/\/$/, "")}/tracks`, "L’API du catalogue");
    } catch {
      return localDatasetService.getCatalog();
    }
    const meta = !Array.isArray(payload) && payload && typeof payload === "object" ? payload as { source?: string; updatedAt?: string } : {};
    return { tracks: normalizeCatalog(payload), source: meta.source ?? "API Moodify", updatedAt: meta.updatedAt, isDemo: false };
  }
}

export const datasetService: DatasetService =
  process.env.NEXT_PUBLIC_USE_MOCKS === "false"
    ? new FastApiDatasetService()
    : localDatasetService;
