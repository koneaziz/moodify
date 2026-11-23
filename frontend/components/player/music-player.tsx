"use client";

import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "motion/react";
import { MutedClip } from "@/components/player/muted-clip";
import { ArrowUpRight, AudioLines, Film, Headphones, Maximize2, Minimize2, Pause, Play, SkipBack, SkipForward, Volume2, VolumeX, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatTime } from "@/lib/utils";
import { CoverImage } from "@/components/recommendations/cover-image";
import type { Recommendation } from "@/types/music";

const SPOTIFY_ID = /^[A-Za-z0-9]{22}$/;
const APPLE_EMBED = "https://embed.music.apple.com/";

// Official uploads verified against the tracks in the catalogue.
const OFFICIAL_CLIPS = new Map([
  ["0pqnGHJpmpxLKifKRmU6WP", "7wtfhZwyrcc"], // Imagine Dragons — Believer
  ["5FVd6KXrgO9B3JPmC8OPst", "bpOSxM0rNPM"], // Arctic Monkeys — Do I Wanna Know?
]);

export function canPlay(track: Recommendation) {
  return Boolean(
    track.audioPreviewUrl ||
    (track.spotifyTrackId && SPOTIFY_ID.test(track.spotifyTrackId)) ||
    track.appleMusicEmbedUrl?.startsWith(APPLE_EMBED)
  );
}

type MusicPlayerProps = {
  track: Recommendation | null;
  expanded: boolean;
  onExpandedChange: (expanded: boolean) => void;
  onClose: () => void;
  autoPlay?: boolean;
  playRequest: number;
  onPrevious?: () => void;
  onNext?: () => void;
};

export function MusicPlayer({ track, expanded, onExpandedChange, onClose, autoPlay, playRequest, onPrevious, onNext }: MusicPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const expandButton = useRef<HTMLButtonElement>(null);
  const reduceButton = useRef<HTMLButtonElement>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(.8);
  const [audioError, setAudioError] = useState(false);
  const [clipPreference, setClipPreference] = useState<{ trackId: string; visible: boolean } | null>(null);
  const reduceMotion = useReducedMotion();

  const spotifyId = track?.spotifyTrackId && SPOTIFY_ID.test(track.spotifyTrackId) ? track.spotifyTrackId : null;
  const spotifyEmbed = spotifyId ? "https://open.spotify.com/embed/track/" + spotifyId + "?utm_source=generator&theme=0" : null;
  const appleEmbed = track?.appleMusicEmbedUrl?.startsWith(APPLE_EMBED) ? track.appleMusicEmbedUrl : null;
  const embedUrl = spotifyEmbed ?? appleEmbed;
  const clipId = spotifyId ? OFFICIAL_CLIPS.get(spotifyId) : undefined;
  const showClip = Boolean(clipId && track && (
    clipPreference?.trackId === track.id ? clipPreference.visible : !reduceMotion
  ));
  const hasAudio = Boolean(track?.audioPreviewUrl);

  useEffect(() => {
    if (!expanded) return;
    const button = expandButton.current;
    reduceButton.current?.focus();
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !event.defaultPrevented) onExpandedChange(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      if (button && !button.hidden) button.focus();
    };
  }, [expanded, onExpandedChange]);

  useEffect(() => {
    const update = window.setTimeout(() => {
      const audio = audioRef.current;
      setPlaying(Boolean(audio && !audio.paused));
      setCurrentTime(audio?.currentTime ?? 0);
      setDuration(audio && Number.isFinite(audio.duration) ? audio.duration : 0);
      setAudioError(Boolean(audio?.error));
    }, 0);
    return () => window.clearTimeout(update);
  }, [track?.id, playRequest]);

  useEffect(() => {
    if (audioRef.current) audioRef.current.volume = volume;
  }, [volume, track?.id, playRequest]);

  async function togglePlay() {
    const audio = audioRef.current;
    if (!audio) return;
    if (!audio.paused) {
      audio.pause();
      return;
    }
    try {
      await audio.play();
      setAudioError(false);
    } catch {
      setAudioError(true);
    }
  }

  return (
    <div className={expanded
      ? "fixed inset-y-3 right-3 z-60 flex w-[min(27rem,calc(100%-1.5rem))] flex-col overflow-hidden rounded-[24px] border border-white/15 bg-[#151121] text-white shadow-[0_18px_75px_#080611bf] sm:inset-y-5 sm:right-5"
      : "player-dock fixed inset-x-0 bottom-0 z-40 border-t border-white/10 bg-[#11111f]/95 text-white backdrop-blur-xl"}
      role="region"
      aria-label="Lecteur Moodify"
    >
      {track && expanded && (
        <div className="relative isolate flex min-h-0 flex-1 flex-col overflow-y-auto overscroll-contain">
          <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10 overflow-hidden opacity-35">
            <CoverImage key={track.coverUrl} src={track.coverUrl} alt="" fill sizes="432px" className="scale-125 object-cover blur-[70px]" />
          </div>
          <header className="flex shrink-0 items-center justify-between gap-3 px-4 pt-3 sm:px-5">
            <p className="flex items-center gap-2 text-sm font-semibold text-[#e1d5ff]"><AudioLines size={21} /> En écoute</p>
            <Button ref={reduceButton} type="button" variant="ghost" size="icon" onClick={() => onExpandedChange(false)} aria-label="Réduire le lecteur">
              <Minimize2 size={20} />
            </Button>
          </header>
          <div className="flex flex-col gap-5 px-4 pb-5 pt-3 sm:px-5">
            {showClip && clipId ? (
              <MutedClip key={clipId} videoId={clipId} title={track.title} fallback={<AlbumArtwork track={track} />} />
            ) : <AlbumArtwork track={track} />}
            <div className="min-w-0">
              <p className="mb-2 text-sm font-medium text-[#d0bafa]">{track.genre}</p>
              <h2 className="break-words text-[clamp(1.7rem,5vw,2.7rem)] leading-[1.02] font-semibold tracking-[-.055em]">{track.title}</h2>
              <p className="mt-3 break-words text-lg text-[#dbd0ec]">{track.artist}</p>
              {spotifyId && (
                <a href={"https://open.spotify.com/track/" + spotifyId} target="_blank" rel="noreferrer"
                  className="mt-5 inline-flex items-center gap-1.5 rounded-full border border-white/15 px-3.5 py-2 text-sm text-[#dfd2fa] hover:bg-white/10">
                  Ouvrir dans Spotify <ArrowUpRight size={14} />
                </a>
              )}
              {clipId && (
                <Button type="button" variant="secondary" size="sm" className="mx-1 mt-3" aria-pressed={showClip}
                  onClick={() => setClipPreference({ trackId: track.id, visible: !showClip })}>
                  <Film size={16} />
                  {showClip ? "Masquer le clip muet" : "Afficher le clip sans son"}
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      <div className={"border-white/10 bg-[#11111f]/95 " + (expanded ? "border-t" : "")}>
        <div className={"mx-auto flex max-w-[1600px] items-center gap-2 " + (expanded ? "flex-wrap px-3 py-2" : "min-h-[78px] px-3 sm:min-h-[88px] sm:gap-5 sm:px-7 lg:px-9")}>
          {!expanded && (
            <>
              <div className="relative h-10 w-10 shrink-0 overflow-hidden rounded-xl bg-[#222238] sm:h-14 sm:w-14">
                {track ? <CoverImage key={track.coverUrl} src={track.coverUrl} alt="" fill sizes="56px" className="object-cover" />
                  : <div className="grid h-full place-items-center text-[#77758f]"><Headphones size={21} /></div>}
              </div>
              <div className="min-w-0 flex-1 sm:max-w-[230px]">
                <p className="truncate text-sm font-semibold">{track?.title ?? "Aucun morceau en cours"}</p>
                <p className="truncate text-xs text-[#a29fb8]">{track?.artist}</p>
              </div>
            </>
          )}

          <div className={"min-w-0 " + (expanded ? "basis-full" : track ? "flex-1" : "")}>
            {hasAudio && track ? (
              <div className="mx-auto flex w-full max-w-xl items-center gap-2 sm:gap-4">
                <Button type="button" size="icon" className="shrink-0 rounded-full" onClick={togglePlay} aria-label={playing ? "Mettre en pause" : "Lire l’extrait"}>
                  {playing ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}
                </Button>
                <div className={"min-w-0 grow items-center gap-2 text-xs text-[#b1aac7] " + (expanded ? "flex" : "hidden sm:flex")}>
                  <span>{formatTime(currentTime)}</span>
                  <input type="range" min={0} max={duration || track.durationSeconds || 1} step="0.1" value={currentTime}
                    onChange={(event) => { if (audioRef.current) audioRef.current.currentTime = Number(event.target.value); }}
                    aria-label="Position de lecture" className="player-range min-w-0 flex-1" />
                  <span>{formatTime(duration || track.durationSeconds || 0)}</span>
                </div>
                {audioError && <span role="alert" className="sr-only">Impossible de lire l’extrait.</span>}
              </div>
            ) : embedUrl ? (
              <iframe
                key={playRequest}
                title={"Lecteur de " + track?.title}
                src={embedUrl}
                width="100%"
                height="78"
                allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                className="mx-auto block max-w-[580px] rounded-xl border-0"
              />
            ) : track ? (
              <p className="text-center text-xs text-[#b1aac7]">Audio indisponible pour ce morceau</p>
            ) : null}
          </div>

          {hasAudio && track && (
            <audio
              key={track.id + "-" + playRequest}
              ref={audioRef}
              src={track.audioPreviewUrl}
              autoPlay={autoPlay}
              preload="metadata"
              onPlay={() => setPlaying(true)}
              onPause={() => setPlaying(false)}
              onLoadedMetadata={(event) => setDuration(event.currentTarget.duration)}
              onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
              onEnded={() => { setPlaying(false); onNext?.(); }}
              onError={() => { setAudioError(true); setPlaying(false); }}
            />
          )}

          {hasAudio && (
            <div className="hidden shrink-0 items-center gap-2 sm:flex">
              <Button type="button" size="icon" variant="ghost" onClick={() => setVolume(volume === 0 ? .8 : 0)} aria-label={volume === 0 ? "Rétablir le son" : "Couper le son"}>
                {volume === 0 ? <VolumeX size={17} /> : <Volume2 size={17} />}
              </Button>
              <input type="range" min={0} max={1} step={.05} value={volume} onChange={(event) => setVolume(Number(event.target.value))} aria-label="Volume" className="player-range w-16" />
            </div>
          )}
          {(onPrevious || onNext) && (
            <div className="flex shrink-0 items-center">
              <button type="button" onClick={onPrevious} disabled={!onPrevious} aria-label="Morceau précédent" className="rounded-lg p-1.5 hover:bg-white/10 focus-visible:outline-2 disabled:opacity-30"><SkipBack size={17} /></button>
              <button type="button" onClick={onNext} disabled={!onNext} aria-label="Morceau suivant" className="rounded-lg p-1.5 hover:bg-white/10 focus-visible:outline-2 disabled:opacity-30"><SkipForward size={17} /></button>
            </div>
          )}
          {track && (
            <div className={"flex shrink-0 items-center " + (expanded ? "ml-auto" : "")}>
              <button ref={expandButton} hidden={expanded} type="button" onClick={() => onExpandedChange(true)} aria-label="Agrandir le lecteur" className="rounded-lg p-2 hover:bg-white/10 focus-visible:outline-2"><Maximize2 size={17} /></button>
              <button type="button" onClick={onClose} aria-label="Fermer le lecteur" className="rounded-lg p-2 hover:bg-white/10 focus-visible:outline-2"><X size={18} /></button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AlbumArtwork({ track }: { track: Recommendation }) {
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[300px] shrink-0 overflow-hidden rounded-2xl border border-white/15 bg-[#241d37] shadow-[0_16px_40px_#0a051298]">
      <CoverImage key={track.coverUrl} src={track.coverUrl} alt={"Pochette de " + track.title} fill sizes="300px" className="object-cover" />
    </div>
  );
}
