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
    source: countBy(tracks.map((track) => track.source ?? "Non renseignée")),
    moodSource: countBy(tracks.map((track) => track.moodSource ?? "Non renseignée")),
    descriptionSource: countBy(tracks.map((track) => track.descriptionSource ?? "Non renseignée")),
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
    { label: "Taille du catalogue", detail: `${tracks.length} entrées (minimum ${TARGET_ENTRIES})`, ok: tracks.length >= TARGET_ENTRIES },
    { label: "Descriptions détaillées", detail: short.length ? `${short.length} de moins de ${MIN_DESCRIPTION_WORDS} mots` : `Au moins ${MIN_DESCRIPTION_WORDS} mots par description`, ok: short.length === 0 },
    { label: "Champs obligatoires", detail: incomplete.length ? `${incomplete.length} entrées incomplètes` : "Titre, artiste, genre, humeur, description", ok: incomplete.length === 0 },
    { label: "Niveaux d’énergie", detail: invalidEnergy.length ? `${invalidEnergy.length} hors de l’intervalle 1–5` : "Toutes les valeurs sont entre 1 et 5", ok: invalidEnergy.length === 0 },
    { label: "Doublons", detail: duplicates ? `${duplicates} doublons d’identifiant ou de couple titre–artiste` : "Aucun identifiant ni couple titre–artiste en double", ok: duplicates === 0 },
    { label: "Source documentée", detail: withoutSource.length ? `${withoutSource.length} sans source` : "Chaque entrée indique sa source", ok: withoutSource.length === 0 },
    { label: "Caractéristiques audio", detail: `${withAudio} / ${tracks.length} avec des données audio Spotify`, ok: withAudio === tracks.length },
    { label: "Langue", detail: `${withLanguage} / ${tracks.length} avec une langue renseignée`, ok: withLanguage === tracks.length },
  ];
}
