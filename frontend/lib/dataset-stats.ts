import type { CatalogTrack } from "@/types/dataset";

export const TARGET_ENTRIES = 70;
export const MIN_DESCRIPTION_WORDS = 15;

export type CountItem = { label: string; count: number };

export function wordCount(text: string) {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

export function countBy(values: string[]): CountItem[] {
  const counts = new Map<string, number>();
  for (const value of values) counts.set(value, (counts.get(value) ?? 0) + 1);
  return [...counts.entries()].map(([label, count]) => ({ label, count })).sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
}

export function computeDatasetStats(tracks: CatalogTrack[]) {
  const genres = countBy(tracks.map((track) => track.genre));
  const moods = countBy(tracks.flatMap((track) => track.moods));
  const moodBlocks = countBy(tracks.flatMap((track) => track.moodBlocks));
  const contextBlocks = countBy(tracks.flatMap((track) => track.contextBlocks));
  const energy = [1, 2, 3, 4, 5].map((level) => ({ label: String(level), count: tracks.filter((track) => track.energy === level).length }));
  const artists = new Set(tracks.map((track) => track.artist.toLowerCase())).size;
  const averageWords = tracks.length ? Math.round(tracks.reduce((sum, track) => sum + wordCount(track.description), 0) / tracks.length) : 0;
  const provenance = {
    source: countBy(tracks.map((track) => track.source ?? "Not documented")),
    moodSource: countBy(tracks.map((track) => track.moodSource ?? "Not documented")),
    descriptionSource: countBy(tracks.map((track) => track.descriptionSource ?? "Not documented")),
  };
  return { total: tracks.length, artists, genres, moods, moodBlocks, contextBlocks, energy, averageWords, provenance };
}

export type QualityCheck = { label: string; detail: string; ok: boolean };

/** Lightweight checks that help the data team spot entries to clean before NLP processing. */
export function computeQualityChecks(tracks: CatalogTrack[]): QualityCheck[] {
  const short = tracks.filter((track) => wordCount(track.description) < MIN_DESCRIPTION_WORDS);
  const incomplete = tracks.filter((track) => !track.title || !track.artist || !track.genre || !track.description || track.moods.length === 0);
  const invalidEnergy = tracks.filter((track) => !Number.isInteger(track.energy) || track.energy < 1 || track.energy > 5);
  const ids = new Set<string>();
  const pairs = new Set<string>();
  let duplicates = 0;
  for (const track of tracks) {
    const pair = `${track.title.toLowerCase()}::${track.artist.toLowerCase()}`;
    if (ids.has(track.id) || pairs.has(pair)) duplicates += 1;
    ids.add(track.id);
    pairs.add(pair);
  }
  const withoutSource = tracks.filter((track) => !track.source);
  const withAudio = tracks.filter((track) => track.audio).length;
  const withLanguage = tracks.filter((track) => track.language).length;

  return [
    { label: "Catalogue size", detail: `${tracks.length} entries (minimum ${TARGET_ENTRIES})`, ok: tracks.length >= TARGET_ENTRIES },
    { label: "Rich descriptions", detail: short.length ? `${short.length} under ${MIN_DESCRIPTION_WORDS} words` : `All have ${MIN_DESCRIPTION_WORDS}+ words`, ok: short.length === 0 },
    { label: "Required fields", detail: incomplete.length ? `${incomplete.length} incomplete entries` : "Title, artist, genre, mood, description", ok: incomplete.length === 0 },
    { label: "Energy values", detail: invalidEnergy.length ? `${invalidEnergy.length} outside 1–5` : "All between 1 and 5", ok: invalidEnergy.length === 0 },
    { label: "Duplicates", detail: duplicates ? `${duplicates} repeated ID or title + artist` : "No repeated ID or title + artist", ok: duplicates === 0 },
    { label: "Documented source", detail: withoutSource.length ? `${withoutSource.length} without a source` : "Every entry has a source", ok: withoutSource.length === 0 },
    { label: "Audio features", detail: `${withAudio} / ${tracks.length} with Spotify features`, ok: withAudio === tracks.length },
    { label: "Language", detail: `${withLanguage} / ${tracks.length} with a known language`, ok: withLanguage === tracks.length },
  ];
}
