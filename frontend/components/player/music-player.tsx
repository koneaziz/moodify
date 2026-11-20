"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { Headphones, Pause, Play, Volume2, VolumeX, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatTime } from "@/lib/utils";
import type { Recommendation } from "@/types/music";

export function MusicPlayer({ track, onClose }: { track: Recommendation | null; onClose: () => void }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(.8);
  const [audioError, setAudioError] = useState(false);

  useEffect(() => {
    const audio = audioRef.current;
    if (audio) { audio.pause(); audio.currentTime = 0; }
    const update = window.setTimeout(() => { setPlaying(false); setCurrentTime(0); setDuration(0); setAudioError(false); }, 0);
    return () => window.clearTimeout(update);
  }, [track?.id]);

  useEffect(() => {
    if (audioRef.current) audioRef.current.volume = volume;
  }, [volume, track?.id]);

  async function togglePlay() {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) {
      try { await audio.play(); setPlaying(true); setAudioError(false); }
      catch { setPlaying(false); setAudioError(true); }
    } else { audio.pause(); setPlaying(false); }
  }

  const spotifyId = track?.spotifyTrackId && /^[A-Za-z0-9]{22}$/.test(track.spotifyTrackId) ? track.spotifyTrackId : null;
  const spotifyEmbed = spotifyId ? `https://open.spotify.com/embed/track/${spotifyId}?utm_source=generator&theme=0` : null;
  const appleEmbed = track?.appleMusicEmbedUrl?.startsWith("https://embed.music.apple.com/") ? track.appleMusicEmbedUrl : null;
  const hasAudio = Boolean(track?.audioPreviewUrl);

  return <div className="player-dock fixed inset-x-0 bottom-0 z-40 border-t border-white/10 bg-[#11111f]/95 shadow-[0_-12px_40px_rgba(0,0,0,.22)] backdrop-blur-xl"><div className="mx-auto flex h-[78px] max-w-[1600px] items-center gap-3 px-4 sm:h-[88px] sm:gap-5 sm:px-7 lg:px-9"><div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-xl bg-[#222238] sm:h-14 sm:w-14">{track ? <Image src={track.coverUrl} alt="" fill sizes="56px" className="object-cover" /> : <div className="flex h-full w-full items-center justify-center text-[#77758f]"><Headphones size={22} /></div>}</div><div className="min-w-0 flex-1 sm:max-w-[230px]"><p className="truncate text-sm font-semibold text-white">{track?.title ?? "Nothing playing"}</p><p className="mt-0.5 truncate text-xs text-[#9290aa]">{track?.artist ?? "Choose a track to listen"}</p></div><div className="flex min-w-0 flex-1 flex-col items-center gap-1.5">{hasAudio && track ? <><div className="flex items-center gap-3"><button type="button" onClick={togglePlay} className="flex h-10 w-10 items-center justify-center rounded-full bg-[#F8F8FC] text-[#11111f] transition hover:scale-105 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#CFCBFF]" aria-label={playing ? "Pause audio" : "Play audio"}>{playing ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}</button><span className="hidden text-xs text-[#b8b5cb] sm:inline">Original demo audio</span></div><div className="hidden w-full max-w-[380px] items-center gap-2 text-[11px] text-[#85829c] sm:flex"><span>{formatTime(currentTime)}</span><input type="range" min={0} max={duration || track.durationSeconds || 1} step="0.1" value={currentTime} onChange={(event) => { if (audioRef.current) audioRef.current.currentTime = Number(event.target.value); }} aria-label="Audio progress" className="player-range w-full" /><span>{formatTime(duration || track.durationSeconds || 0)}</span></div><audio key={track.id} ref={audioRef} src={track.audioPreviewUrl} preload="metadata" onLoadedMetadata={(event) => setDuration(event.currentTarget.duration)} onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)} onEnded={() => setPlaying(false)} onError={() => { setAudioError(true); setPlaying(false); }} />{audioError && <span className="sr-only" role="alert">Audio could not be played.</span>}</> : spotifyEmbed || appleEmbed ? <div className="w-full max-w-[500px]"><iframe title={`Official player for ${track?.title}`} src={spotifyEmbed ?? appleEmbed ?? ""} width="100%" height="78" loading="lazy" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" className="rounded-xl border-0" /></div> : <span className="text-center text-xs text-[#8d8aa5]">{track ? "Audio unavailable for this track" : "Select a playable demo track"}</span>}</div><div className="hidden min-w-[130px] items-center gap-3 sm:flex">{hasAudio ? <><button type="button" onClick={() => setVolume(volume === 0 ? .8 : 0)} aria-label={volume === 0 ? "Unmute" : "Mute"} className="text-[#aaa7bf] hover:text-white">{volume === 0 ? <VolumeX size={18} /> : <Volume2 size={18} />}</button><input type="range" min={0} max={1} step={.05} value={volume} onChange={(event) => { const next = Number(event.target.value); setVolume(next); if (audioRef.current) audioRef.current.volume = next; }} aria-label="Volume" className="player-range w-20" /></> : null}</div>{track && <Button type="button" variant="ghost" size="icon" onClick={onClose} aria-label="Close player" className="shrink-0"><X size={17} /></Button>}</div></div>;
}
