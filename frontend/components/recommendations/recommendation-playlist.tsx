"use client";

import { AudioLines, ListMusic, Play } from "lucide-react";
import { canPlay } from "@/components/player/music-player";
import { CoverImage } from "@/components/recommendations/cover-image";
import type { Recommendation } from "@/types/music";

type PlaylistProps = {
  tracks: Recommendation[];
  selectedTrack: Recommendation | null;
  onPlay: (track: Recommendation) => void;
};

export function RecommendationPlaylist({ tracks, selectedTrack, onPlay }: PlaylistProps) {
  const firstPlayable = tracks.find(canPlay);

  return (
    <section aria-labelledby="playlist-title" className="mt-11 overflow-hidden rounded-[30px] border border-[#9b8bfd]/25 bg-[#171625] shadow-[0_20px_80px_rgba(7,5,18,.28)] sm:mt-14">
      <div className="relative isolate flex items-center gap-5 overflow-hidden border-b border-white/10 bg-[linear-gradient(120deg,#30235e_0%,#251c43_55%,#3c2142_100%)] px-5 py-7 sm:gap-8 sm:px-9 sm:py-9">
        <div aria-hidden="true" className="pointer-events-none absolute -right-14 -top-28 -z-10 h-[320px] w-[320px] rounded-full border-[36px] border-[#e39adc]/10 shadow-[0_0_0_22px_rgba(227,154,220,.07),0_0_0_48px_rgba(227,154,220,.05)]" />
        <div aria-hidden="true" className="relative grid h-20 w-20 shrink-0 place-items-center rounded-2xl border border-white/20 bg-[linear-gradient(150deg,#ac8bff,#7356dc_50%,#a44797)] text-white shadow-[0_16px_42px_rgba(12,8,38,.45)] sm:h-32 sm:w-32 sm:rounded-[24px]">
          <div className="grid h-[72%] w-[72%] place-items-center rounded-full border border-white/20 bg-[#24163c]/55 ring-4 ring-white/10">
            <AudioLines className="h-6 w-6 sm:h-10 sm:w-10" strokeWidth={1.6} />
          </div>
        </div>
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-xs font-semibold text-[#ded1ff]"><ListMusic size={15} /> Votre liste de lecture</p>
          <h2 id="playlist-title" className="mt-1.5 text-2xl font-semibold tracking-[-.055em] text-white sm:text-4xl">Votre mix Moodify</h2>
          <p className="mt-2 text-sm text-[#ded6ee]">{tracks.length} {tracks.length === 1 ? "morceau sélectionné" : "morceaux sélectionnés"} pour vous</p>
          <button type="button" disabled={!firstPlayable} onClick={() => firstPlayable && onPlay(firstPlayable)} className="mt-4 inline-flex min-h-10 items-center gap-2 rounded-full bg-[#eee7ff] px-4 text-sm font-bold text-[#2b1d50] transition hover:bg-white focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#e1ceff] disabled:opacity-50">
            <Play size={15} fill="currentColor" /> {firstPlayable ? "Lancer la liste" : "Lecture indisponible"}
          </button>
        </div>
      </div>

      <ol className="space-y-1 p-2 sm:p-4">
        {tracks.map((track, index) => {
          const active = selectedTrack?.id === track.id;
          const playable = canPlay(track);
          return (
            <li key={track.id}>
              <button
                type="button"
                onClick={() => onPlay(track)}
                disabled={!playable}
                aria-current={active ? "true" : undefined}
                aria-label={playable ? `Écouter ${track.title} de ${track.artist}` : `${track.title} de ${track.artist}, lecture indisponible`}
                className={`group flex w-full items-center gap-2 rounded-xl px-2 py-2.5 text-left transition hover:bg-white/[.07] focus-visible:outline-2 focus-visible:outline-[#cfc4ff] disabled:hover:bg-transparent sm:gap-4 sm:px-4 ${active ? "bg-[#8470ea]/15" : ""}`}
              >
                <span className="w-6 shrink-0 text-center text-xs tabular-nums text-[#bab2d4]">{active ? <AudioLines size={16} className="mx-auto text-[#c6adff]" /> : index + 1}</span>
                <span className="relative h-11 w-11 shrink-0 overflow-hidden rounded-lg bg-[#292341]">
                  <CoverImage src={track.coverUrl} alt="" fill sizes="44px" className="object-cover" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-semibold text-[#f5efff]">{track.title}</span>
                  <span className="block truncate text-xs text-[#aaa2be]">{track.artist}</span>
                </span>
                <span className="hidden text-xs text-[#aaa2be] sm:inline">{track.genre}</span>
                {playable ? (
                  <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-white/[.06] text-[#d1bfff] group-hover:bg-[#a68ffb]/25"><Play size={13} fill="currentColor" /></span>
                ) : (
                  <span className="shrink-0 text-xs text-[#aaa2be]">Indisponible</span>
                )}
              </button>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
