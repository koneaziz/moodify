import type { CatalogResponse } from "@/types/dataset";
import { normalizeCatalog } from "@/lib/catalog-normalizer";

export interface DatasetService {
  getCatalog(): Promise<CatalogResponse>;
}

async function fetchJson(url: string, label: string) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { error?: string } | null;
    throw new Error(body?.error ?? `${label} returned ${response.status}.`);
  }
  return await response.json() as unknown;
}

// Until the API serves the catalogue, Demo Mode reads data/moodify_dataset.json through app/api/tracks.
const localDatasetService: DatasetService = {
  async getCatalog() {
    const payload = await fetchJson("/api/tracks", "The local dataset route");
    return { tracks: normalizeCatalog(payload), source: "data/moodify_dataset.json (team dataset)", isDemo: false };
  },
};

class FastApiDatasetService implements DatasetService {
  async getCatalog(): Promise<CatalogResponse> {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!baseUrl) throw new Error("Set NEXT_PUBLIC_API_URL to connect the FastAPI backend.");

    // Proposed contract (see docs/dataset-contract.md): rows as exported, as an array or { tracks: [...] }.
    const payload = await fetchJson(`${baseUrl.replace(/\/$/, "")}/tracks`, "Dataset service");
    const meta = !Array.isArray(payload) && payload && typeof payload === "object" ? payload as { source?: string; updatedAt?: string } : {};
    return { tracks: normalizeCatalog(payload), source: meta.source ?? "Moodify API", updatedAt: meta.updatedAt, isDemo: false };
  }
}

export const datasetService: DatasetService =
  process.env.NEXT_PUBLIC_USE_MOCKS === "false"
    ? new FastApiDatasetService()
    : localDatasetService;
