"use client";

import { useState } from "react";
import Image, { type ImageProps } from "next/image";
import { coverSrc, FALLBACK_COVER, isRemoteCover } from "@/lib/covers";

/** next/image for album artwork: accepts empty or unknown URLs and falls back to a local cover on error. */
export function CoverImage({ src, alt, ...props }: Omit<ImageProps, "src"> & { src?: string | null }) {
  const [failed, setFailed] = useState(false);
  const resolved = failed ? FALLBACK_COVER : coverSrc(src);
  // Spotify artwork is loaded directly from its CDN rather than proxied through the Next.js server.
  return <Image {...props} src={resolved} alt={alt} unoptimized={isRemoteCover(resolved)} onError={() => setFailed(true)} />;
}
