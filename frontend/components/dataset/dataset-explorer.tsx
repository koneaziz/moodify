"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import { ArrowLeft, ArrowUpRight, AudioLines, CircleAlert, CircleCheck, Database, FileText, Fingerprint, Info, Library, Mic2, Music2, RotateCcw, Search, Shapes, Tags, X } from "lucide-react";
import { Brand } from "@/components/layout/brand";
import { DemoBadge } from "@/components/layout/demo-badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { DistributionChart } from "@/components/dataset/distribution-chart";
import { EmotionMap, QUADRANT_COLORS } from "@/components/dataset/emotion-map";
import { computeDatasetStats, computeQualityChecks, wordCount, type CountItem } from "@/lib/dataset-stats";
import { cn } from "@/lib/utils";
import { datasetService } from "@/services/dataset-service";
import type { CatalogResponse, CatalogTrack } from "@/types/dataset";

const PAGE_SIZE = 12;
const energyLabels = ["Very calm", "Calm", "Balanced", "Energetic", "Very energetic"];
const genreTones = ["tone-violet", "tone-pink", "tone-teal", "tone-gold", "tone-blue", "tone-orange", "tone-purple", "tone-rose"];
const sortOptions = {
  popularity: { label: "Most popular", compare: (a: CatalogTrack, b: CatalogTrack) => (b.popularity ?? -1) - (a.popularity ?? -1) },
  title: { label: "Title A–Z", compare: (a: CatalogTrack, b: CatalogTrack) => a.title.localeCompare(b.title) },
  calm: { label: "Calmest first", compare: (a: CatalogTrack, b: CatalogTrack) => a.energy - b.energy },
  energetic: { label: "Most energetic first", compare: (a: CatalogTrack, b: CatalogTrack) => b.energy - a.energy },
} as const;
type SortKey = keyof typeof sortOptions;

type LoadState = { status: "loading" } | { status: "error"; message: string } | { status: "ready"; data: CatalogResponse };

export function DatasetExplorer() {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    datasetService.getCatalog()
      .then((data) => { if (!cancelled) setState({ status: "ready", data }); })
      .catch((error: unknown) => { if (!cancelled) setState({ status: "error", message: error instanceof Error ? error.message : "Unknown error." }); });
    return () => { cancelled = true; };
  }, [attempt]);

  return (
    <div className="min-h-dvh overflow-x-hidden bg-[#0D0D18] text-[#F8F8FC]">
      <header className="sticky top-0 z-20 flex h-[73px] items-center justify-between gap-4 border-b border-white/[.06] bg-[#0D0D18]/85 px-5 backdrop-blur-xl sm:px-9 lg:px-11">
        <div className="flex items-center gap-5"><Brand /><div className="hidden items-center gap-2 text-sm text-[#8d8aa4] md:flex"><span className="text-[#5f5c76]">/</span><Database size={15} /><span className="font-medium text-[#e7e5f4]">Dataset</span></div></div>
        <div className="flex items-center gap-3">{state.status === "ready" && state.data.isDemo && <DemoBadge />}<Button asChild size="sm" variant="secondary"><Link href="/discover"><ArrowLeft size={15} /> <span className="hidden sm:inline">Back to</span> Discover</Link></Button></div>
      </header>

      <main className="mx-auto max-w-[1510px] px-5 pb-24 pt-8 sm:px-9 sm:pt-11 lg:px-11">
        {state.status === "loading" && <p className="py-32 text-center text-[#c7c3de]" role="status">Loading the music library...</p>}
        {state.status === "error" && <ErrorState message={state.message} onRetry={() => { setState({ status: "loading" }); setAttempt((value) => value + 1); }} />}
        {state.status === "ready" && <DatasetContent data={state.data} />}
      </main>
    </div>
  );
}

function DatasetContent({ data }: { data: CatalogResponse }) {
  const reduceMotion = useReducedMotion();
  const [query, setQuery] = useState("");
  const [genre, setGenre] = useState<string | null>(null);
  const [moodBlock, setMoodBlock] = useState<string | null>(null);
  const [contextBlock, setContextBlock] = useState<string | null>(null);
  const [sort, setSort] = useState<SortKey>("popularity");
  const [visible, setVisible] = useState(PAGE_SIZE);

  const stats = useMemo(() => computeDatasetStats(data.tracks), [data.tracks]);
  const checks = useMemo(() => computeQualityChecks(data.tracks), [data.tracks]);
  const genreToneMap = useMemo(() => new Map(stats.genres.map((item, index) => [item.label, genreTones[index % genreTones.length]])), [stats.genres]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return data.tracks.filter((track) => {
      if (genre && track.genre !== genre) return false;
      if (moodBlock && !track.moodBlocks.includes(moodBlock)) return false;
      if (contextBlock && !track.contextBlocks.includes(contextBlock)) return false;
      if (!needle) return true;
      return [track.title, track.artist, track.album ?? "", track.genre, track.description, ...track.featuredArtists, ...track.subGenres, ...track.moods, ...track.contexts, ...track.keywords].some((value) => value.toLowerCase().includes(needle));
    }).sort(sortOptions[sort].compare);
  }, [data.tracks, query, genre, moodBlock, contextBlock, sort]);

  const hasFilters = Boolean(query || genre || moodBlock || contextBlock);
  const resetPage = () => setVisible(PAGE_SIZE);
  const resetFilters = () => { setQuery(""); setGenre(null); setMoodBlock(null); setContextBlock(null); resetPage(); };

  const tiles = [
    { label: "Tracks", value: stats.total, icon: Library },
    { label: "Artists", value: stats.artists, icon: Mic2 },
    { label: "Genres", value: stats.genres.length, icon: Shapes },
    { label: "Mood tags", value: stats.moods.length, icon: Tags },
    { label: "Avg. words / description", value: stats.averageWords, icon: FileText },
  ];

  return (
    <>
      <motion.section initial={reduceMotion ? false : { opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .5 }} className="relative overflow-hidden rounded-[30px] border border-white/[.08] bg-[#171727] px-6 py-8 sm:px-9 sm:py-10 xl:px-12">
        <div className="hero-grid absolute inset-0 opacity-40" aria-hidden="true" />
        <div className="hero-halo absolute -right-15 -top-35 h-[380px] w-[420px] rounded-full" aria-hidden="true" />
        <div className="relative z-10">
          <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-[.23em] text-[#bbb5ff]"><Database size={15} /> The reference catalogue</p>
          <h1 className="mt-5 max-w-[760px] text-[clamp(2.3rem,4.3vw,4.4rem)] font-semibold leading-[1.04] tracking-[-.068em]">Inside the <span className="text-gradient">music library.</span></h1>
          <p className="mt-5 max-w-[620px] text-base leading-7 text-[#b8b5ca]">Every track the engine can recommend, with the text description that semantic analysis compares to your answers.</p>
          <p className="mt-3 text-xs text-[#85819d]">Source: {data.source}{data.updatedAt ? ` · Updated ${new Date(data.updatedAt).toLocaleDateString("en-GB")}` : ""}</p>
          <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {tiles.map((tile) => <div key={tile.label} className="rounded-[20px] border border-white/[.08] bg-[#0D0D18]/45 p-4 backdrop-blur-sm"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#6C63FF]/15 text-[#b9b2ff]"><tile.icon size={17} /></span><p className="mt-4 text-3xl font-semibold tracking-[-.05em]">{tile.value}</p><p className="mt-1 text-xs text-[#9996af]">{tile.label}</p></div>)}
          </div>
        </div>
      </motion.section>

      <section id="overview" className="scroll-mt-24 pt-11 sm:pt-14">
        <SectionHeading kicker="AT A GLANCE" title="How the catalogue is balanced" subtitle="Coverage across genres, moods, contexts and energy helps every profile find a match." />
        <div className="mt-6 grid gap-5 xl:grid-cols-2">
          <ChartCard title="Tracks per genre" subtitle={`${stats.genres.length} genres`}><DistributionChart data={stats.genres} label="Tracks per genre" gradientId="genreGradient" layout="vertical" /></ChartCard>
          <ChartCard title="Mood blocks" subtitle="A track can belong to several blocks"><DistributionChart data={stats.moodBlocks} label="Tracks per mood block" gradientId="moodGradient" layout="vertical" /></ChartCard>
          <ChartCard title="Listening contexts" subtitle="Context blocks used for matching"><DistributionChart data={stats.contextBlocks} label="Tracks per context block" gradientId="contextGradient" layout="vertical" /></ChartCard>
          <ChartCard title="Energy levels" subtitle="1 = very calm · 5 = very energetic"><DistributionChart data={stats.energy} label="Tracks per energy level" gradientId="energyGradient" /></ChartCard>
          <ChartCard title="Emotion map" subtitle="Valence and arousal of each track, grouped by Russell quadrant"><EmotionMap tracks={data.tracks} /></ChartCard>
          <QualityCard checks={checks} />
        </div>
        <ProvenanceCard provenance={stats.provenance} total={stats.total} />
      </section>

      <section id="browse" className="scroll-mt-24 pt-11 sm:pt-14">
        <SectionHeading kicker="BROWSE" title="Explore every track" subtitle="Search titles, artists, albums, descriptions or keywords, then filter by genre, mood and context." aside={`${filtered.length} of ${stats.total} tracks`} />
        <div className="mt-6 rounded-[25px] border border-white/[.08] bg-[#171727] p-5 sm:p-6">
          <div className="flex flex-col gap-3 sm:flex-row">
            <label className="relative block flex-1"><span className="sr-only">Search the catalogue</span><Search size={18} className="pointer-events-none absolute left-5 top-1/2 -translate-y-1/2 text-[#77758f]" /><input type="search" value={query} onChange={(event) => { setQuery(event.target.value); resetPage(); }} placeholder="Try “piano”, “pluie” or an artist name" className="input-surface h-13 w-full rounded-2xl pl-13 pr-5" /></label>
            <label className="relative block sm:w-[220px]"><span className="sr-only">Sort tracks</span><select value={sort} onChange={(event) => { setSort(event.target.value as SortKey); resetPage(); }} className="input-surface h-13 w-full cursor-pointer appearance-none rounded-2xl px-5 text-sm">{Object.entries(sortOptions).map(([key, option]) => <option key={key} value={key} className="bg-[#171727]">{option.label}</option>)}</select></label>
          </div>
          <FilterRow label="Genre" options={stats.genres.map((item) => item.label)} value={genre} onChange={(value) => { setGenre(value); resetPage(); }} />
          <FilterRow label="Mood" options={stats.moodBlocks.map((item) => item.label)} value={moodBlock} onChange={(value) => { setMoodBlock(value); resetPage(); }} />
          <FilterRow label="Context" options={stats.contextBlocks.map((item) => item.label)} value={contextBlock} onChange={(value) => { setContextBlock(value); resetPage(); }} />
          {hasFilters && <button type="button" onClick={resetFilters} className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-[#bcb5ff] hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#CFCBFF]"><X size={15} /> Clear filters</button>}
        </div>

        {filtered.length === 0 ? (
          <div className="mt-6 flex flex-col items-center rounded-[25px] border border-dashed border-white/[.12] px-6 py-14 text-center"><span className="flex h-14 w-14 items-center justify-center rounded-[18px] bg-[#6C63FF]/10 text-[#bcb5ff]"><Music2 size={24} /></span><p className="mt-4 text-lg font-semibold">No track matches these filters.</p><p className="mt-1 text-sm text-[#9e9bb1]">Try another word or clear the filters.</p></div>
        ) : (
          <>
            <div className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-3">{filtered.slice(0, visible).map((track) => <TrackCard key={track.id} track={track} tone={genreToneMap.get(track.genre) ?? "tone-violet"} />)}</div>
            {visible < filtered.length && <div className="mt-8 flex justify-center"><Button type="button" variant="secondary" onClick={() => setVisible((value) => value + PAGE_SIZE)}>Show more ({filtered.length - visible} left)</Button></div>}
          </>
        )}
      </section>
    </>
  );
}

function SectionHeading({ kicker, title, subtitle, aside }: { kicker: string; title: string; subtitle: string; aside?: string }) {
  return <div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-[.22em] text-[#aaa3ff]">{kicker}</p><h2 className="mt-2 text-[clamp(1.8rem,3vw,2.65rem)] font-semibold tracking-[-.055em]">{title}</h2><p className="mt-2 text-sm text-[#9e9bb1]">{subtitle}</p></div>{aside && <span className="rounded-full border border-white/10 bg-white/[.04] px-3 py-1.5 text-xs text-[#a8a5bd]">{aside}</span>}</div>;
}

function ChartCard({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return <div className="min-w-0 rounded-[25px] border border-white/[.08] bg-[#171727] p-6 sm:p-7"><p className="text-lg font-semibold tracking-tight">{title}</p><p className="mt-1 text-sm text-[#9996af]">{subtitle}</p><div className="mt-5">{children}</div></div>;
}

function QualityCard({ checks }: { checks: ReturnType<typeof computeQualityChecks> }) {
  const passed = checks.filter((check) => check.ok).length;
  return (
    <div className="relative overflow-hidden rounded-[25px] border border-white/[.08] bg-[#171727] p-6 sm:p-7">
      <div className="absolute -right-20 -top-20 h-56 w-56 rounded-full bg-[#E94E9A]/10 blur-3xl" aria-hidden="true" />
      <div className="relative">
        <div className="flex items-center justify-between gap-4"><div><p className="text-lg font-semibold tracking-tight">Data quality</p><p className="mt-1 text-sm text-[#9996af]">{passed} of {checks.length} checks passed</p></div><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#E94E9A]/12 text-[#f18fbd]"><CircleCheck size={18} /></span></div>
        <ul className="mt-5 divide-y divide-white/[.08]">
          {checks.map((check) => <li key={check.label} className="flex items-center justify-between gap-4 py-3"><div className="flex items-center gap-3">{check.ok ? <CircleCheck size={17} className="shrink-0 text-[#A2EBD8]" /> : <CircleAlert size={17} className="shrink-0 text-[#F7D899]" />}<span className="text-sm font-medium text-[#e7e5f4]">{check.label}</span></div><span className={cn("text-right text-xs", check.ok ? "text-[#9996af]" : "text-[#F7D899]")}>{check.detail}</span></li>)}
        </ul>
      </div>
    </div>
  );
}

function ProvenanceCard({ provenance, total }: { provenance: ReturnType<typeof computeDatasetStats>["provenance"]; total: number }) {
  const groups: { title: string; items: CountItem[] }[] = [
    { title: "Dataset source", items: provenance.source },
    { title: "Mood labels", items: provenance.moodSource },
    { title: "Descriptions", items: provenance.descriptionSource },
  ];
  return (
    <div className="mt-5 rounded-[25px] border border-white/[.08] bg-[#171727] p-6 sm:p-7">
      <div className="flex items-center justify-between gap-4"><div><p className="text-lg font-semibold tracking-tight">Sources & provenance</p><p className="mt-1 text-sm text-[#9996af]">Where each part of the data comes from</p></div><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#6C63FF]/15 text-[#b9b2ff]"><Fingerprint size={18} /></span></div>
      <div className="mt-6 grid gap-6 md:grid-cols-3">
        {groups.map((group) => <div key={group.title}><p className="text-xs font-semibold uppercase tracking-[.18em] text-[#85819d]">{group.title}</p><ul className="mt-3 space-y-3">{group.items.map((item) => <li key={item.label}><div className="mb-1.5 flex justify-between gap-3 text-sm"><span className="truncate text-[#d6d3e6]">{item.label}</span><span className="shrink-0 text-[#9996af]">{item.count}</span></div><div className="h-1.5 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-gradient-to-r from-[#6C63FF] to-[#E94E9A]" style={{ width: `${(item.count / total) * 100}%` }} /></div></li>)}</ul></div>)}
      </div>
    </div>
  );
}

function FilterRow({ label, options, value, onChange }: { label: string; options: string[]; value: string | null; onChange: (value: string | null) => void }) {
  const chip = (selected: boolean) => cn("rounded-full border px-3 py-1.5 text-xs font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#CFCBFF]", selected ? "border-[#8d86ff] bg-[#6C63FF]/20 text-[#e3dfff]" : "border-white/10 bg-white/[.04] text-[#b5b2c9] hover:border-white/25 hover:text-white");
  return (
    <div className="mt-5" role="group" aria-label={`Filter by ${label.toLowerCase()}`}>
      <p className="text-xs font-semibold uppercase tracking-[.18em] text-[#85819d]">{label}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <button type="button" aria-pressed={value === null} onClick={() => onChange(null)} className={chip(value === null)}>All</button>
        {options.map((option) => <button key={option} type="button" aria-pressed={value === option} onClick={() => onChange(value === option ? null : option)} className={chip(value === option)}>{option}</button>)}
      </div>
    </div>
  );
}

function EnergyMeter({ level }: { level: number }) {
  return <span className="inline-flex items-end gap-[3px]" role="img" aria-label={`Energy ${level} of 5`}>{[1, 2, 3, 4, 5].map((bar) => <span key={bar} className={cn("w-[5px] rounded-full", bar <= level ? "bg-gradient-to-t from-[#6C63FF] to-[#E94E9A]" : "bg-white/12")} style={{ height: 6 + bar * 2.5 }} />)}</span>;
}

function TrackCard({ track, tone }: { track: CatalogTrack; tone: string }) {
  const byline = [track.artist, ...track.featuredArtists].join(", ");
  return (
    <motion.article whileHover={{ y: -4 }} transition={{ duration: .2 }} className="flex min-w-0 flex-col rounded-[25px] border border-white/[.08] bg-[#1a1a2c] p-5 shadow-[0_15px_40px_rgba(0,0,0,.14)]">
      <div className="flex items-start gap-4">
        <span className={cn("flex h-12 w-12 shrink-0 items-center justify-center rounded-[15px]", tone)}><Music2 size={21} strokeWidth={1.8} /></span>
        <div className="min-w-0 flex-1"><h3 className="truncate text-lg font-semibold tracking-[-.03em] text-white">{track.title}</h3><p className="mt-0.5 truncate text-sm text-[#a6a3bc]">{byline}{track.album ? <span className="text-[#77758f]"> · {track.album}</span> : null}</p></div>
        <span className="max-w-[40%] shrink-0 truncate rounded-full bg-white/[.06] px-3 py-1 text-xs text-[#c7c3dc]" title={track.genre}>{track.genre}</span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">{track.moods.slice(0, 3).map((mood) => <span key={mood} className="rounded-full border border-[#6C63FF]/15 bg-[#6C63FF]/10 px-2.5 py-1 text-xs text-[#c9c4ff]">{mood}</span>)}</div>
      <p className="mt-4 line-clamp-3 flex-1 text-sm leading-6 text-[#aaa8c0]">{track.description}</p>
      <div className="mt-5 flex items-center justify-between gap-3 border-t border-white/[.07] pt-4">
        <div className="flex items-center gap-2.5 text-xs text-[#9996af]"><EnergyMeter level={track.energy} /><span>{energyLabels[track.energy - 1] ?? `Energy ${track.energy}`}</span></div>
        <TrackDetails track={track} tone={tone} />
      </div>
    </motion.article>
  );
}

function TrackDetails({ track, tone }: { track: CatalogTrack; tone: string }) {
  const facts = [
    { label: "Track ID", value: track.id },
    { label: "Album", value: track.album ?? "—" },
    { label: "Energy", value: `${track.energy}/5 · ${energyLabels[track.energy - 1] ?? "—"}` },
    { label: "Language", value: track.language ?? "Unknown" },
    { label: "Popularity", value: track.popularity !== undefined ? `${Math.round(track.popularity)}/100` : "—" },
    { label: "Description", value: `${wordCount(track.description)} words · ${track.descriptionSource ?? "source unknown"}` },
    { label: "Mood labels", value: track.moodSource ?? "Not documented" },
    { label: "Source", value: track.source ?? "Not documented" },
  ];
  const audio = track.audio ? [
    { label: "Danceability", value: track.audio.danceability },
    { label: "Energy", value: track.audio.energy },
    { label: "Valence (positivity)", value: track.audio.valence },
    { label: "Acousticness", value: track.audio.acousticness },
    { label: "Instrumentalness", value: track.audio.instrumentalness },
  ] : [];

  return (
    <Dialog>
      <DialogTrigger asChild><Button type="button" size="sm" variant="secondary" aria-label={`Details for ${track.title}`}><Info size={15} /> Details</Button></DialogTrigger>
      <DialogContent className="max-w-2xl">
        <div className="pr-9">
          <div className="mb-5 flex items-center gap-4"><span className={cn("flex h-16 w-16 shrink-0 items-center justify-center rounded-xl", tone)}><Music2 size={26} strokeWidth={1.8} /></span><div className="min-w-0"><p className="mb-1 text-xs font-semibold uppercase tracking-[.2em] text-[#ada7ff]">{track.genre}</p><DialogTitle className="text-2xl font-semibold tracking-tight text-white">{track.title}</DialogTitle><DialogDescription className="mt-1 text-sm text-[#aaa8be]">{[track.artist, ...track.featuredArtists].join(", ")}{track.album ? ` · ${track.album}` : ""}</DialogDescription></div></div>
          {track.spotifyTrackId && <div className="mb-5"><iframe title={`Spotify player for ${track.title}`} src={`https://open.spotify.com/embed/track/${track.spotifyTrackId}?utm_source=generator&theme=0`} width="100%" height="80" loading="lazy" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" className="rounded-xl border-0 bg-[#222238]" /><a href={`https://open.spotify.com/track/${track.spotifyTrackId}`} target="_blank" rel="noopener noreferrer" className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-[#bcb5ff] hover:text-white">Open in Spotify <ArrowUpRight size={14} /></a></div>}
          <div className="rounded-2xl border border-[#6C63FF]/20 bg-[#6C63FF]/[.08] p-4"><div className="mb-2 flex items-center gap-2 text-sm font-semibold text-[#d1ccff]"><FileText size={15} /> Description analysed by NLP</div><p className="text-sm leading-6 text-[#c6c3d9]">{track.description}</p></div>
          <TagGroup title="Moods" values={track.moods} accent />
          <TagGroup title="Mood blocks" values={track.moodBlocks} />
          <TagGroup title="Listening contexts" values={track.contexts} />
          <TagGroup title="Context blocks" values={track.contextBlocks} />
          <TagGroup title="Sub-genres" values={track.subGenres} />
          <TagGroup title="Keywords" values={track.keywords} />
          {(audio.length > 0 || track.emotion) && (
            <div className="mt-6 border-t border-white/[.08] pt-5">
              <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[.18em] text-[#85819d]"><AudioLines size={14} /> Audio profile</p>
              <div className="mt-4 space-y-3.5">{audio.map((metric) => <div key={metric.label}><div className="mb-1.5 flex justify-between text-sm"><span className="text-[#b8b5ca]">{metric.label}</span><span className="font-semibold text-white">{Math.round(metric.value * 100)}%</span></div><div className="h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-gradient-to-r from-[#6C63FF] to-[#E94E9A]" style={{ width: `${metric.value * 100}%` }} /></div></div>)}</div>
              <div className="mt-4 flex flex-wrap gap-2 text-xs">
                {track.audio && <span className="rounded-full border border-white/10 bg-white/[.05] px-3 py-1.5 font-semibold text-[#c7c3d8]">{Math.round(track.audio.tempo)} BPM</span>}
                {track.emotion && <span className="rounded-full border border-white/10 bg-white/[.05] px-3 py-1.5 font-semibold text-[#c7c3d8]">Valence {track.emotion.valence.toFixed(2)} · Arousal {track.emotion.arousal.toFixed(2)}</span>}
                {track.emotion?.quadrant && <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[.05] px-3 py-1.5 font-semibold text-[#c7c3d8]"><span className="h-2 w-2 rounded-full" style={{ background: QUADRANT_COLORS[track.emotion.quadrant] ?? "#8d8aa4" }} />{track.emotion.quadrant}</span>}
              </div>
            </div>
          )}
          <dl className="mt-6 grid grid-cols-2 gap-x-5 gap-y-4 border-t border-white/[.08] pt-5">{facts.map((fact) => <div key={fact.label} className="min-w-0"><dt className="text-xs font-semibold uppercase tracking-[.16em] text-[#85819d]">{fact.label}</dt><dd className="mt-1 break-words text-sm text-white">{fact.value}</dd></div>)}</dl>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function TagGroup({ title, values, accent = false }: { title: string; values: string[]; accent?: boolean }) {
  if (values.length === 0) return null;
  return <div className="mt-5"><p className="text-xs font-semibold uppercase tracking-[.18em] text-[#85819d]">{title}</p><div className="mt-2.5 flex flex-wrap gap-2">{values.map((value) => <span key={value} className={cn("rounded-full border px-3 py-1.5 text-xs font-semibold", accent ? "border-[#6C63FF]/25 bg-[#6C63FF]/10 text-[#d1ccff]" : "border-white/10 bg-white/[.05] text-[#c7c3d8]")}>{value}</span>)}</div></div>;
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return <div className="flex flex-col items-center py-24 text-center"><span className="flex h-20 w-20 items-center justify-center rounded-[26px] border border-[#E94E9A]/25 bg-[#E94E9A]/10 text-[#f18fbd]"><CircleAlert size={34} /></span><h1 className="mt-6 text-3xl font-semibold tracking-[-.05em]">The library could not be loaded.</h1><p className="mt-3 max-w-md text-sm leading-7 text-[#a9a6bd]">{message}</p><Button type="button" className="mt-7" onClick={onRetry}><RotateCcw size={16} /> Try again</Button></div>;
}
