import { readFile } from "node:fs/promises";
import path from "node:path";

// Serves the team's dataset (repository root: data/moodify_dataset.json) without copying it into the frontend.
// Used in Demo Mode until the FastAPI backend exposes GET /tracks.
export const dynamic = "force-dynamic";

const DATASET_PATH = process.env.MOODIFY_DATASET_PATH ?? path.join(process.cwd(), "..", "data", "moodify_dataset.json");

export async function GET() {
  try {
    const content = await readFile(DATASET_PATH, "utf-8");
    return new Response(content, { headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" } });
  } catch {
    return Response.json({ error: "Catalogue introuvable. Vérifiez data/moodify_dataset.json ou configurez MOODIFY_DATASET_PATH." }, { status: 404 });
  }
}
