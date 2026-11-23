"use client";

import { motion } from "motion/react";
import { Headphones, Info, Play, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CoverImage } from "@/components/recommendations/cover-image";
import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import type { Recommendation } from "@/types/music";

export function canPlay(track: Recommendation) {
  return Boolean(track.audioPreviewUrl || (track.spotifyTrackId && /^[A-Za-z0-9]{22}$/.test(track.spotifyTrackId)) || track.appleMusicEmbedUrl);
}

export function RecommendationCard({ track, onListen, featured = false }: { track: Recommendation; onListen: (track: Recommendation) => void; featured?: boolean }) {
  const playable = canPlay(track);
  return (
    <motion.article whileHover={{ y: -4 }} transition={{ duration: .2 }} className={`recommendation-card group overflow-hidden rounded-[25px] border border-white/[.08] bg-[#1a1a2c] p-4 shadow-[0_15px_40px_rgba(0,0,0,.14)] ${featured ? "featured-card" : ""}`}>
      <div className="relative aspect-[1.42] overflow-hidden rounded-[18px] bg-[#26263b]"><CoverImage src={track.coverUrl} alt={`Artwork for ${track.title}`} fill className="object-cover transition-transform duration-500 group-hover:scale-105" sizes="(max-width: 640px) 100vw, (max-width: 1100px) 50vw, 33vw" /><div className="absolute left-3 top-3 rounded-full border border-white/20 bg-[#0d0d18]/70 px-3 py-1.5 text-xs font-bold text-white backdrop-blur-md">#{track.rank} match</div><div className="absolute bottom-3 right-3 flex h-13 w-13 items-center justify-center rounded-full border border-white/20 bg-[#131320]/80 text-white backdrop-blur-md"><span className="text-sm font-bold">{track.score}%</span></div></div>
      <div className="px-1 pb-1 pt-5"><div className="flex items-start justify-between gap-3"><div className="min-w-0"><h3 className="truncate text-xl font-semibold tracking-[-.035em] text-white">{track.title}</h3><p className="mt-1 truncate text-sm text-[#a6a3bc]">{track.artist}</p></div><span className="shrink-0 rounded-full bg-white/[.06] px-3 py-1 text-xs text-[#c7c3dc]">{track.genre}</span></div><div className="mt-4 flex flex-wrap gap-2">{track.reasons.slice(0, 2).map((reason) => <span key={reason} className="rounded-full border border-[#6C63FF]/15 bg-[#6C63FF]/10 px-2.5 py-1 text-xs text-[#c9c4ff]">{reason}</span>)}</div><p className="mt-4 line-clamp-2 min-h-10 text-sm leading-5 text-[#aaa8c0]">{track.explanation}</p><div className="mt-5 flex items-center gap-2"><Button type="button" size="sm" disabled={!playable} onClick={() => onListen(track)} className="flex-1">{playable ? <><Play size={14} fill="currentColor" /> Listen</> : <><Headphones size={14} /> No audio</>}</Button><DetailsDialog track={track} /></div></div>
    </motion.article>
  );
}

function DetailsDialog({ track }: { track: Recommendation }) {
  const metrics = [
    { label: "Overall affinity", value: track.score },
    { label: "Mood match", value: track.moodScore },
    { label: "Genre match", value: track.genreScore },
    { label: "Context match", value: track.contextScore },
  ];
  return <Dialog><DialogTrigger asChild><Button type="button" size="sm" variant="secondary" aria-label={`Details for ${track.title}`}><Info size={15} /> Details</Button></DialogTrigger><DialogContent><div className="pr-9"><div className="mb-5 flex items-center gap-4"><div className="relative h-16 w-16 shrink-0 overflow-hidden rounded-xl"><CoverImage src={track.coverUrl} alt="" fill className="object-cover" sizes="64px" /></div><div><p className="mb-1 text-xs font-semibold uppercase tracking-[.2em] text-[#ada7ff]">#{track.rank} · Demo recommendation</p><DialogTitle className="text-2xl font-semibold tracking-tight text-white">{track.title}</DialogTitle><DialogDescription className="mt-1 text-sm text-[#aaa8be]">{track.artist} · {track.genre} · {track.mood}</DialogDescription></div></div><div className="rounded-2xl border border-[#6C63FF]/20 bg-[#6C63FF]/[.08] p-4"><div className="mb-2 flex items-center gap-2 text-sm font-semibold text-[#d1ccff]"><Sparkles size={15} /> Why this fits</div><p className="text-sm leading-6 text-[#c6c3d9]">{track.explanation}</p></div><div className="mt-6 space-y-4">{metrics.map((metric) => <div key={metric.label}><div className="mb-2 flex justify-between text-sm"><span className="text-[#b8b5ca]">{metric.label}</span><span className="font-semibold text-white">{metric.value}%</span></div><div className="h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-gradient-to-r from-[#6C63FF] to-[#E94E9A]" style={{ width: `${metric.value}%` }} /></div></div>)}</div><p className="mt-6 text-xs leading-5 text-[#77758f]">Illustrative scores only. These values are not the result of NLP analysis.</p></div></DialogContent></Dialog>;
}
