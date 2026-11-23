import type { CatalogTrack, RawCatalogRow } from "@/types/dataset";

const SPOTIFY_ID = /^[A-Za-z0-9]{22}$/;

function list(value: string | null | undefined) {
  return (value ?? "").split("|").map((item) => item.trim()).filter(Boolean);
}

function num(value: number | null | undefined) {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function text(value: string | null | undefined) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : undefined;
}

/** Converts one exported dataset row (snake_case, "|" lists) to the interface model. */
export function normalizeRow(row: RawCatalogRow): CatalogTrack {
  const danceability = num(row.danceability);
  const energyRaw = num(row.energy_raw);
  const valence = num(row.valence);
  const acousticness = num(row.acousticness);
  const instrumentalness = num(row.instrumentalness);
  const tempo = num(row.tempo);
  const museValence = num(row.muse_valence);
  const museArousal = num(row.muse_arousal);
  const language = text(row.language);

  return {
    id: row.track_id,
    title: row.title.trim(),
    artist: row.artist.trim(),
    featuredArtists: list(row.featured_artists),
    album: text(row.album),
    genre: row.genre.trim(),
    subGenres: list(row.sub_genres),
    moods: list(row.mood),
    contexts: list(row.context),
    moodBlocks: list(row.mood_blocks),
    contextBlocks: list(row.context_blocks),
    energy: Number(row.energy),
    language: language && language !== "inconnu" ? language : undefined,
    description: row.description.trim(),
    keywords: list(row.keywords),
    source: text(row.source),
    moodSource: text(row.mood_source),
    descriptionSource: text(row.description_source),
    spotifyTrackId: SPOTIFY_ID.test(row.track_id) ? row.track_id : undefined,
    popularity: num(row.popularity),
    audio: danceability !== undefined && energyRaw !== undefined && valence !== undefined && acousticness !== undefined && instrumentalness !== undefined && tempo !== undefined
      ? { danceability, energy: energyRaw, valence, acousticness, instrumentalness, tempo }
      : undefined,
    emotion: museValence !== undefined && museArousal !== undefined
      ? { valence: museValence, arousal: museArousal, quadrant: text(row.russell_quadrant) }
      : undefined,
  };
}

/** Accepts either a bare array of rows or an object with a `tracks` array. */
export function normalizeCatalog(payload: unknown): CatalogTrack[] {
  const rows = Array.isArray(payload) ? payload : (payload as { tracks?: unknown })?.tracks;
  if (!Array.isArray(rows)) throw new Error("The dataset response is not a list of tracks.");
  return (rows as RawCatalogRow[]).map(normalizeRow);
}
