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
const energyLabels = ["Très calme", "Calme", "Équilibrée", "Énergique", "Très énergique"];
const genreTones = ["tone-violet", "tone-pink", "tone-teal", "tone-gold", "tone-blue", "tone-orange", "tone-purple", "tone-rose"];
const sortOptions = {
  popularity: { label: "Les plus populaires", compare: (a: CatalogTrack, b: CatalogTrack) => (b.popularity ?? -1) - (a.popularity ?? -1) },
  title: { label: "Titres de A à Z", compare: (a: CatalogTrack, b: CatalogTrack) => a.title.localeCompare(b.title) },
  calm: { label: "Les plus calmes", compare: (a: CatalogTrack, b: CatalogTrack) => a.energy - b.energy },
  energetic: { label: "Les plus énergiques", compare: (a: CatalogTrack, b: CatalogTrack) => b.energy - a.energy },
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
      .catch((error: unknown) => { if (!cancelled) setState({ status: "error", message: error instanceof Error ? error.message : "Erreur inconnue." }); });
    return () => { cancelled = true; };
  }, [attempt]);

  return (
    <div className="min-h-dvh overflow-x-hidden bg-[#0D0D18] text-[#F8F8FC]">
      <header className="sticky top-0 z-20 flex h-[73px] items-center justify-between gap-4 border-b border-white/[.06] bg-[#0D0D18]/85 px-5 backdrop-blur-xl sm:px-9 lg:px-11">
        <div className="flex items-center gap-5"><Brand /><div className="hidden items-center gap-2 text-sm text-[#8d8aa4] md:flex"><span className="text-[#5f5c76]">/</span><Database size={15} /><span className="font-medium text-[#e7e5f4]">Bibliothèque</span></div></div>
        <div className="flex items-center gap-3">{state.status === "ready" && state.data.isDemo && <DemoBadge />}<Button asChild size="sm" variant="secondary"><Link href="/discover"><ArrowLeft size={15} /> <span className="hidden sm:inline">Retour aux</span> recommandations</Link></Button></div>
      </header>

      <main className="mx-auto max-w-[1510px] px-5 pb-24 pt-8 sm:px-9 sm:pt-11 lg:px-11">
        {state.status === "loading" && <p className="py-32 text-center text-[#c7c3de]" role="status">Chargement de la bibliothèque…</p>}
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
    { label: "Morceaux", value: stats.total, icon: Library },
    { label: "Artistes", value: stats.artists, icon: Mic2 },
    { label: "Genres", value: stats.genres.length, icon: Shapes },
    { label: "Étiquettes d’humeur", value: stats.moods.length, icon: Tags },
    { label: "Mots par description en moyenne", value: stats.averageWords, icon: FileText },
  ];

  return (
    <>
      <motion.section initial={reduceMotion ? false : { opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .5 }} className="relative overflow-hidden rounded-[30px] border border-white/[.08] bg-[#171727] px-6 py-8 sm:px-9 sm:py-10 xl:px-12">
        <div className="hero-grid absolute inset-0 opacity-40" aria-hidden="true" />
        <div className="hero-halo absolute -right-15 -top-35 h-[380px] w-[420px] rounded-full" aria-hidden="true" />
        <div className="relative z-10">
          <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-[.23em] text-[#bbb5ff]"><Database size={15} /> Le catalogue de référence</p>
          <h1 className="mt-5 max-w-[760px] text-[clamp(2.3rem,4.3vw,4.4rem)] font-semibold leading-[1.04] tracking-[-.068em]">Explorez la <span className="text-gradient">bibliothèque musicale.</span></h1>
          <p className="mt-5 max-w-[620px] text-base leading-7 text-[#b8b5ca]">Retrouvez les morceaux du catalogue et les descriptions que le moteur compare à vos réponses.</p>
          <p className="mt-3 text-xs text-[#85819d]">Source : {data.source}{data.updatedAt ? ` · Mis à jour le ${new Date(data.updatedAt).toLocaleDateString("fr-FR")}` : ""}</p>
          <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {tiles.map((tile) => <div key={tile.label} className="rounded-[20px] border border-white/[.08] bg-[#0D0D18]/45 p-4 backdrop-blur-sm"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#6C63FF]/15 text-[#b9b2ff]"><tile.icon size={17} /></span><p className="mt-4 text-3xl font-semibold tracking-[-.05em]">{tile.value}</p><p className="mt-1 text-xs text-[#9996af]">{tile.label}</p></div>)}
          </div>
        </div>
      </motion.section>

      <section id="overview" className="scroll-mt-24 pt-11 sm:pt-14">
        <SectionHeading kicker="VUE D’ENSEMBLE" title="La répartition du catalogue" subtitle="Répartition des morceaux par genre, humeur, contexte et niveau d’énergie." />
        <div className="mt-6 grid gap-5 xl:grid-cols-2">
          <ChartCard title="Morceaux par genre" subtitle={`${stats.genres.length} genres`}><DistributionChart data={stats.genres} label="Morceaux par genre" gradientId="genreGradient" layout="vertical" /></ChartCard>
          <ChartCard title="Groupes d’humeurs" subtitle="Un morceau peut appartenir à plusieurs groupes"><DistributionChart data={stats.moodBlocks} label="Morceaux par groupe d’humeurs" gradientId="moodGradient" layout="vertical" /></ChartCard>
          <ChartCard title="Contextes d’écoute" subtitle="Contextes utilisés pour les recommandations"><DistributionChart data={stats.contextBlocks} label="Morceaux par contexte" gradientId="contextGradient" layout="vertical" /></ChartCard>
          <ChartCard title="Niveaux d’énergie" subtitle="1 = très calme · 5 = très énergique"><DistributionChart data={stats.energy} label="Morceaux par niveau d’énergie" gradientId="energyGradient" /></ChartCard>
          <ChartCard title="Carte des émotions" subtitle="Valence et activation de chaque morceau, par quadrant de Russell"><EmotionMap tracks={data.tracks} /></ChartCard>
          <QualityCard checks={checks} />
        </div>
        <ProvenanceCard provenance={stats.provenance} total={stats.total} />
      </section>

      <section id="browse" className="scroll-mt-24 pt-11 sm:pt-14">
        <SectionHeading kicker="EXPLORATION" title="Parcourez les morceaux" subtitle="Recherchez un titre, un artiste, un album ou un mot-clé, puis filtrez par genre, humeur ou contexte." aside={`${filtered.length} sur ${stats.total} morceaux`} />
        <div className="mt-6 rounded-[25px] border border-white/[.08] bg-[#171727] p-5 sm:p-6">
          <div className="flex flex-col gap-3 sm:flex-row">
            <label className="relative block flex-1"><span className="sr-only">Rechercher dans le catalogue</span><Search size={18} className="pointer-events-none absolute left-5 top-1/2 -translate-y-1/2 text-[#77758f]" /><input type="search" value={query} onChange={(event) => { setQuery(event.target.value); resetPage(); }} placeholder="Essayez « piano », « pluie » ou le nom d’un artiste" className="input-surface h-13 w-full rounded-2xl pl-13 pr-5" /></label>
            <label className="relative block sm:w-[220px]"><span className="sr-only">Trier les morceaux</span><select value={sort} onChange={(event) => { setSort(event.target.value as SortKey); resetPage(); }} className="input-surface h-13 w-full cursor-pointer appearance-none rounded-2xl px-5 text-sm">{Object.entries(sortOptions).map(([key, option]) => <option key={key} value={key} className="bg-[#171727]">{option.label}</option>)}</select></label>
          </div>
          <FilterRow label="Genre" options={stats.genres.map((item) => item.label)} value={genre} onChange={(value) => { setGenre(value); resetPage(); }} />
          <FilterRow label="Humeur" options={stats.moodBlocks.map((item) => item.label)} value={moodBlock} onChange={(value) => { setMoodBlock(value); resetPage(); }} />
          <FilterRow label="Contexte" options={stats.contextBlocks.map((item) => item.label)} value={contextBlock} onChange={(value) => { setContextBlock(value); resetPage(); }} />
          {hasFilters && <button type="button" onClick={resetFilters} className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-[#bcb5ff] hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#CFCBFF]"><X size={15} /> Effacer les filtres</button>}
        </div>

        {filtered.length === 0 ? (
          <div className="mt-6 flex flex-col items-center rounded-[25px] border border-dashed border-white/[.12] px-6 py-14 text-center"><span className="flex h-14 w-14 items-center justify-center rounded-[18px] bg-[#6C63FF]/10 text-[#bcb5ff]"><Music2 size={24} /></span><p className="mt-4 text-lg font-semibold">Aucun morceau ne correspond à ces filtres.</p><p className="mt-1 text-sm text-[#9e9bb1]">Essayez un autre mot ou effacez les filtres.</p></div>
        ) : (
          <>
            <div className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-3">{filtered.slice(0, visible).map((track) => <TrackCard key={track.id} track={track} tone={genreToneMap.get(track.genre) ?? "tone-violet"} />)}</div>
            {visible < filtered.length && <div className="mt-8 flex justify-center"><Button type="button" variant="secondary" onClick={() => setVisible((value) => value + PAGE_SIZE)}>Afficher la suite ({filtered.length - visible} à voir)</Button></div>}
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
        <div className="flex items-center justify-between gap-4"><div><p className="text-lg font-semibold tracking-tight">Qualité des données</p><p className="mt-1 text-sm text-[#9996af]">{passed} contrôles réussis sur {checks.length}</p></div><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#E94E9A]/12 text-[#f18fbd]"><CircleCheck size={18} /></span></div>
        <ul className="mt-5 divide-y divide-white/[.08]">
          {checks.map((check) => <li key={check.label} className="flex items-center justify-between gap-4 py-3"><div className="flex items-center gap-3">{check.ok ? <CircleCheck size={17} className="shrink-0 text-[#A2EBD8]" /> : <CircleAlert size={17} className="shrink-0 text-[#F7D899]" />}<span className="text-sm font-medium text-[#e7e5f4]">{check.label}</span></div><span className={cn("text-right text-xs", check.ok ? "text-[#9996af]" : "text-[#F7D899]")}>{check.detail}</span></li>)}
        </ul>
      </div>
    </div>
  );
}

function ProvenanceCard({ provenance, total }: { provenance: ReturnType<typeof computeDatasetStats>["provenance"]; total: number }) {
  const groups: { title: string; items: CountItem[] }[] = [
    { title: "Source du catalogue", items: provenance.source },
    { title: "Étiquettes d’humeur", items: provenance.moodSource },
    { title: "Descriptions", items: provenance.descriptionSource },
  ];
  return (
    <div className="mt-5 rounded-[25px] border border-white/[.08] bg-[#171727] p-6 sm:p-7">
      <div className="flex items-center justify-between gap-4"><div><p className="text-lg font-semibold tracking-tight">Provenance des données</p><p className="mt-1 text-sm text-[#9996af]">Origine des morceaux, des humeurs et des descriptions</p></div><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#6C63FF]/15 text-[#b9b2ff]"><Fingerprint size={18} /></span></div>
      <div className="mt-6 grid gap-6 md:grid-cols-3">
        {groups.map((group) => <div key={group.title}><p className="text-xs font-semibold uppercase tracking-[.18em] text-[#85819d]">{group.title}</p><ul className="mt-3 space-y-3">{group.items.map((item) => <li key={item.label}><div className="mb-1.5 flex justify-between gap-3 text-sm"><span className="truncate text-[#d6d3e6]">{item.label}</span><span className="shrink-0 text-[#9996af]">{item.count}</span></div><div className="h-1.5 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-gradient-to-r from-[#6C63FF] to-[#E94E9A]" style={{ width: `${(item.count / total) * 100}%` }} /></div></li>)}</ul></div>)}
      </div>
    </div>
  );
}

function FilterRow({ label, options, value, onChange }: { label: string; options: string[]; value: string | null; onChange: (value: string | null) => void }) {
  const chip = (selected: boolean) => cn("rounded-full border px-3 py-1.5 text-xs font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#CFCBFF]", selected ? "border-[#8d86ff] bg-[#6C63FF]/20 text-[#e3dfff]" : "border-white/10 bg-white/[.04] text-[#b5b2c9] hover:border-white/25 hover:text-white");
  return (
    <div className="mt-5" role="group" aria-label={`Filtrer par ${label.toLowerCase()}`}>
      <p className="text-xs font-semibold uppercase tracking-[.18em] text-[#85819d]">{label}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <button type="button" aria-pressed={value === null} onClick={() => onChange(null)} className={chip(value === null)}>Tout</button>
        {options.map((option) => <button key={option} type="button" aria-pressed={value === option} onClick={() => onChange(value === option ? null : option)} className={chip(value === option)}>{option}</button>)}
      </div>
    </div>
  );
}

function EnergyMeter({ level }: { level: number }) {
  return <span className="inline-flex items-end gap-[3px]" role="img" aria-label={`Énergie ${level} sur 5`}>{[1, 2, 3, 4, 5].map((bar) => <span key={bar} className={cn("w-[5px] rounded-full", bar <= level ? "bg-gradient-to-t from-[#6C63FF] to-[#E94E9A]" : "bg-white/12")} style={{ height: 6 + bar * 2.5 }} />)}</span>;
}

function TrackCard({ track, tone }: { track: CatalogTrack; tone: string }) {
  const byline = [track.artist, ...track.featuredArtists].join(", ");
  return (
    <motion.article whileHover={{ y: -4 }} transition={{ duration: .2 }} className="flex min-w-0 flex-col rounded-[25px] border border-white/[.08] bg-[#1a1a2c] p-5 shadow-[0_15px_40px_rgba(0,0,0,.14)]">
      <div className="flex items-start gap-4">
        <TrackCover track={track} tone={tone} className="h-12 w-12 rounded-[15px]" iconSize={21} />
        <div className="min-w-0 flex-1"><h3 className="truncate text-lg font-semibold tracking-[-.03em] text-white">{track.title}</h3><p className="mt-0.5 truncate text-sm text-[#a6a3bc]">{byline}{track.album ? <span className="text-[#77758f]"> · {track.album}</span> : null}</p></div>
        <span className="max-w-[40%] shrink-0 truncate rounded-full bg-white/[.06] px-3 py-1 text-xs text-[#c7c3dc]" title={track.genre}>{track.genre}</span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">{track.moods.slice(0, 3).map((mood) => <span key={mood} className="rounded-full border border-[#6C63FF]/15 bg-[#6C63FF]/10 px-2.5 py-1 text-xs text-[#c9c4ff]">{mood}</span>)}</div>
      <p className="mt-4 line-clamp-3 flex-1 text-sm leading-6 text-[#aaa8c0]">{track.description}</p>
      <div className="mt-5 flex items-center justify-between gap-3 border-t border-white/[.07] pt-4">
        <div className="flex items-center gap-2.5 text-xs text-[#9996af]"><EnergyMeter level={track.energy} /><span>{energyLabels[track.energy - 1] ?? `Énergie ${track.energy}`}</span></div>
        <TrackDetails track={track} tone={tone} />
      </div>
    </motion.article>
  );
}

function TrackCover({ track, tone, className, iconSize }: { track: CatalogTrack; tone: string; className: string; iconSize: number }) {
  const [failed, setFailed] = useState(false);
  if (track.coverUrl && !failed) {
    // Plain <img>: artwork is served by Spotify's CDN and does not need Next.js image optimisation.
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={track.coverUrl} alt={`Pochette de ${track.title}`} loading="lazy" onError={() => setFailed(true)} className={cn("shrink-0 bg-[#26263b] object-cover", className)} />;
  }
  return <span className={cn("flex shrink-0 items-center justify-center", tone, className)}><Music2 size={iconSize} strokeWidth={1.8} /></span>;
}

function TrackDetails({ track, tone }: { track: CatalogTrack; tone: string }) {
  const facts = [
    { label: "Identifiant du morceau", value: track.id },
    { label: "Album", value: track.album ?? "—" },
    { label: "Énergie", value: `${track.energy}/5 · ${energyLabels[track.energy - 1] ?? "—"}` },
    { label: "Langue", value: track.language ?? "Inconnue" },
    { label: "Popularité", value: track.popularity !== undefined ? `${Math.round(track.popularity)}/100` : "—" },
    { label: "Description", value: `${wordCount(track.description)} mots · ${track.descriptionSource ?? "source inconnue"}` },
    { label: "Étiquettes d’humeur", value: track.moodSource ?? "Non renseignée" },
    { label: "Source", value: track.source ?? "Non renseignée" },
  ];
  const audio = track.audio ? [
    { label: "Aptitude à la danse", value: track.audio.danceability },
    { label: "Énergie", value: track.audio.energy },
    { label: "Valence (positivité)", value: track.audio.valence },
    { label: "Caractère acoustique", value: track.audio.acousticness },
    { label: "Caractère instrumental", value: track.audio.instrumentalness },
  ] : [];

  return (
    <Dialog>
      <DialogTrigger asChild><Button type="button" size="sm" variant="secondary" aria-label={`Détails de ${track.title}`}><Info size={15} /> Détails</Button></DialogTrigger>
      <DialogContent className="max-w-2xl">
        <div className="pr-9">
          <div className="mb-5 flex items-center gap-4"><TrackCover track={track} tone={tone} className="h-16 w-16 rounded-xl" iconSize={26} /><div className="min-w-0"><p className="mb-1 text-xs font-semibold uppercase tracking-[.2em] text-[#ada7ff]">{track.genre}</p><DialogTitle className="text-2xl font-semibold tracking-tight text-white">{track.title}</DialogTitle><DialogDescription className="mt-1 text-sm text-[#aaa8be]">{[track.artist, ...track.featuredArtists].join(", ")}{track.album ? ` · ${track.album}` : ""}</DialogDescription></div></div>
          {track.spotifyTrackId && <div className="mb-5"><iframe title={`Lecteur Spotify de ${track.title}`} src={`https://open.spotify.com/embed/track/${track.spotifyTrackId}?utm_source=generator&theme=0`} width="100%" height="80" loading="lazy" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" className="rounded-xl border-0 bg-[#222238]" /><a href={`https://open.spotify.com/track/${track.spotifyTrackId}`} target="_blank" rel="noopener noreferrer" className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-[#bcb5ff] hover:text-white">Ouvrir dans Spotify <ArrowUpRight size={14} /></a></div>}
          <div className="rounded-2xl border border-[#6C63FF]/20 bg-[#6C63FF]/[.08] p-4"><div className="mb-2 flex items-center gap-2 text-sm font-semibold text-[#d1ccff]"><FileText size={15} /> Description analysée par le moteur de recommandation</div><p className="text-sm leading-6 text-[#c6c3d9]">{track.description}</p></div>
          <TagGroup title="Humeurs" values={track.moods} accent />
          <TagGroup title="Groupes d’humeurs" values={track.moodBlocks} />
          <TagGroup title="Contextes d’écoute" values={track.contexts} />
          <TagGroup title="Groupes de contextes" values={track.contextBlocks} />
          <TagGroup title="Sous-genres" values={track.subGenres} />
          <TagGroup title="Mots-clés" values={track.keywords} />
          {(audio.length > 0 || track.emotion) && (
            <div className="mt-6 border-t border-white/[.08] pt-5">
              <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[.18em] text-[#85819d]"><AudioLines size={14} /> Profil audio</p>
              <div className="mt-4 space-y-3.5">{audio.map((metric) => <div key={metric.label}><div className="mb-1.5 flex justify-between text-sm"><span className="text-[#b8b5ca]">{metric.label}</span><span className="font-semibold text-white">{Math.round(metric.value * 100)}%</span></div><div className="h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-gradient-to-r from-[#6C63FF] to-[#E94E9A]" style={{ width: `${metric.value * 100}%` }} /></div></div>)}</div>
              <div className="mt-4 flex flex-wrap gap-2 text-xs">
                {track.audio && <span className="rounded-full border border-white/10 bg-white/[.05] px-3 py-1.5 font-semibold text-[#c7c3d8]">{Math.round(track.audio.tempo)} BPM</span>}
                {track.emotion && <span className="rounded-full border border-white/10 bg-white/[.05] px-3 py-1.5 font-semibold text-[#c7c3d8]">Valence {track.emotion.valence.toFixed(2)} · Activation {track.emotion.arousal.toFixed(2)}</span>}
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
  return <div className="flex flex-col items-center py-24 text-center"><span className="flex h-20 w-20 items-center justify-center rounded-[26px] border border-[#E94E9A]/25 bg-[#E94E9A]/10 text-[#f18fbd]"><CircleAlert size={34} /></span><h1 className="mt-6 text-3xl font-semibold tracking-[-.05em]">Impossible de charger la bibliothèque.</h1><p className="mt-3 max-w-md text-sm leading-7 text-[#a9a6bd]">{message}</p><Button type="button" className="mt-7" onClick={onRetry}><RotateCcw size={16} /> Réessayer</Button></div>;
}
