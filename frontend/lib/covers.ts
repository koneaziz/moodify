/** Hosts allowed for album artwork returned by the API (Spotify image CDNs). Keep in sync with next.config.ts. */
const REMOTE_COVER = /^https:\/\/(i\.scdn\.co|mosaic\.scdn\.co|[a-z0-9-]+\.spotifycdn\.com)\//;

/** Shown when a track has no artwork (e.g. hand-written "gold" tracks) or its image fails to load. */
export const FALLBACK_COVER = "/covers/calm.svg";

export function isRemoteCover(url: string) {
  return REMOTE_COVER.test(url);
}

/** Returns a URL next/image can display: a local path, an allowed Spotify CDN URL, or the fallback. */
export function coverSrc(url?: string | null) {
  const value = url?.trim();
  if (value && (value.startsWith("/") || isRemoteCover(value))) return value;
  return FALLBACK_COVER;
}
