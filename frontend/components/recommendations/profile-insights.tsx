"use client";

import { Activity, Ban, Compass, MicOff, Repeat, Smile, UserRound } from "lucide-react";
import type { ListeningProfile } from "@/types/music";

const EMOTIONS: Record<string, string> = {
  "colère": "angry", tristesse: "sad", stress: "stressed", fatigue: "tired",
  joie: "happy", ennui: "bored", amour: "in love", nostalgie: "nostalgic",
};
const INTENSITY: Record<number, string> = { 2: "quite ", 3: "very " };

function Badge({ icon: Icon, children, tone = "violet" }: { icon: typeof Smile; children: React.ReactNode; tone?: "violet" | "pink" | "neutral" }) {
  const tones = {
    violet: "border-[#6C63FF]/25 bg-[#6C63FF]/10 text-[#d1ccff]",
    pink: "border-[#E94E9A]/25 bg-[#E94E9A]/10 text-[#f5a6c8]",
    neutral: "border-white/10 bg-white/[.05] text-[#c7c3d8]",
  };
  return <span className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold ${tones[tone]}`}><Icon size={13} />{children}</span>;
}

/** What the engine understood from the questionnaire: emotion, intent, constraints, listener type. */
export function ProfileBadges({ profile }: { profile: ListeningProfile }) {
  const emotion = profile.emotion ? EMOTIONS[profile.emotion] ?? profile.emotion : null;
  const intent = profile.emotion && profile.strategySource === "texte"
    ? profile.strategy === "réguler" ? "Wants to change mood" : "Wants to stay in the mood"
    : null;
  const excluded = profile.excludedGenres ?? [];
  if (!emotion && !intent && !profile.archetype && !excluded.length && !profile.instrumental) return null;

  return (
    <div className="mt-6 border-t border-white/[.08] pt-5">
      <p className="text-xs font-semibold uppercase tracking-[.18em] text-[#85819d]">What we understood</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {emotion && <Badge icon={Smile}>Feeling {INTENSITY[profile.intensity ?? 1] ?? ""}{emotion}</Badge>}
        {intent && <Badge icon={Repeat} tone="pink">{intent}</Badge>}
        {profile.archetype && <Badge icon={UserRound} tone="neutral">{profile.archetype}</Badge>}
        {excluded.map((genre) => <Badge key={genre} icon={Ban} tone="neutral">No {genre}</Badge>)}
        {profile.instrumental && <Badge icon={MicOff} tone="neutral">Instrumental</Badge>}
      </div>
    </div>
  );
}

function ScoreBars({ items }: { items: [string, number][] }) {
  return (
    <ul className="mt-6 space-y-4">
      {items.map(([block, score]) => <li key={block}><div className="mb-2 flex justify-between gap-3 text-sm"><span className="truncate text-[#d6d3e6]">{block}</span><span className="shrink-0 font-semibold text-white">{score}%</span></div><div className="h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-gradient-to-r from-[#6C63FF] to-[#E94E9A]" style={{ width: `${score}%` }} /></div></li>)}
    </ul>
  );
}

function topBlocks(blocks: Record<string, number>, n: number) {
  return Object.entries(blocks).sort((a, b) => b[1] - a[1]).slice(0, n);
}

/** Strongest mood blocks and listening contexts of the profile. */
export function MoodMap({ profile }: { profile: ListeningProfile }) {
  const moods = topBlocks(profile.moodBlocks, 5);
  const contexts = topBlocks(profile.contextBlocks, 4);
  if (!moods.length) return null;

  return (
    <div className="mt-5 grid gap-8 rounded-[25px] border border-white/[.08] bg-[#171727] p-6 sm:p-7 xl:grid-cols-2 xl:gap-6">
      <div className="min-w-0">
        <div className="flex items-center justify-between gap-4">
          <div><p className="text-lg font-semibold tracking-tight">Your mood map</p><p className="mt-1 text-sm text-[#9996af]">The moods your answers are closest to</p></div>
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#6C63FF]/15 text-[#b9b2ff]"><Activity size={19} /></span>
        </div>
        <ScoreBars items={moods} />
      </div>
      <div className="min-w-0 xl:border-l xl:border-white/[.08] xl:pl-6">
        <div className="flex items-center justify-between gap-4">
          <div><p className="text-lg font-semibold tracking-tight">Listening context</p><p className="mt-1 text-sm text-[#9996af]">Where and when you want this music</p></div>
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#E94E9A]/12 text-[#f18fbd]"><Compass size={18} /></span>
        </div>
        {contexts.length ? <ScoreBars items={contexts} /> : <p className="mt-6 text-sm leading-6 text-[#9996af]">No listening context was given, so the recommendations rely on your mood only.</p>}
      </div>
    </div>
  );
}
