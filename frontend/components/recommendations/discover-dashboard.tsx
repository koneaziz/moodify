"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion, useReducedMotion } from "motion/react";
import { ArrowUpRight, AudioLines, ChartNoAxesColumn, Database, Disc3, Heart, Headphones, House, ListMusic, Music2, RotateCcw, Sparkles, Waves } from "lucide-react";
import { Brand } from "@/components/layout/brand";
import { DemoBadge } from "@/components/layout/demo-badge";
import { Button } from "@/components/ui/button";
import { RecommendationCard } from "@/components/recommendations/recommendation-card";
import { AffinityChart } from "@/components/recommendations/affinity-chart";
import { MoodMap, ProfileBadges } from "@/components/recommendations/profile-insights";
import { MusicPlayer } from "@/components/player/music-player";
import { loadAnswers, loadResults } from "@/lib/session";
import type { Recommendation, RecommendationResponse } from "@/types/music";
import type { QuestionnaireAnswers } from "@/types/questionnaire";

const navigation = [
  { label: "Discover", href: "#top", icon: House },
  { label: "My Recommendations", href: "#matches", icon: ListMusic },
  { label: "Explore", href: "#explore", icon: Disc3 },
  { label: "My Vibe", href: "#vibe", icon: Heart },
];

const scenes = [
  { label: "Slow down", subtitle: "Soft sounds for softer moments", cover: "/covers/calm.svg", tone: "scene-violet" },
  { label: "Find your flow", subtitle: "Get into the zone", cover: "/covers/focused.svg", tone: "scene-teal" },
  { label: "Feel everything", subtitle: "For the reflective hours", cover: "/covers/melancholic.svg", tone: "scene-pink" },
  { label: "Turn it up", subtitle: "For brighter energy", cover: "/covers/energetic.svg", tone: "scene-orange" },
];

export function DiscoverDashboard() {
  const [results, setResults] = useState<RecommendationResponse | null | undefined>(undefined);
  const [answers, setAnswers] = useState<QuestionnaireAnswers | null>(null);
  const [selectedTrack, setSelectedTrack] = useState<Recommendation | null>(null);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      setResults(loadResults());
      setAnswers(loadAnswers());
    });
    return () => window.cancelAnimationFrame(frame);
  }, []);

  if (results === undefined) return <main className="flex min-h-dvh items-center justify-center bg-[#0D0D18] text-[#c7c3de]" role="status">Loading your music...</main>;
  if (!results || !answers) return <EmptyDiscover />;

  const top = results.recommendations[0];
  if (!top) return <EmptyDiscover />;

  return <div id="top" className="discover-shell min-h-dvh overflow-x-hidden bg-[#0D0D18] text-[#F8F8FC]">
    <aside className="discover-sidebar fixed bottom-[88px] left-0 top-0 z-30 hidden w-[245px] flex-col border-r border-white/[.07] bg-[#11111e] px-5 py-8 lg:flex"><Brand className="ml-3" /><div className="mt-15"><p className="px-3 text-xs font-bold uppercase tracking-[.2em] text-[#77758f]">Your space</p><nav aria-label="Main navigation" className="mt-4 space-y-1">{navigation.map((item, index) => <a key={item.label} href={item.href} className={`sidebar-link flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold transition ${index === 0 ? "bg-[#6C63FF]/15 text-[#dcd8ff]" : "text-[#a5a2b9] hover:bg-white/[.06] hover:text-white"}`}><item.icon size={18} />{item.label}</a>)}</nav></div><div className="mt-7 border-t border-white/[.08] pt-5"><Link href="/" className="sidebar-link flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold text-[#a5a2b9] hover:bg-white/[.06] hover:text-white"><RotateCcw size={18} /> Change My Mood</Link><Link href="/dataset" className="sidebar-link flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold text-[#a5a2b9] hover:bg-white/[.06] hover:text-white"><Database size={18} /> Music Library</Link></div><div className="mt-auto rounded-[22px] border border-[#6C63FF]/20 bg-gradient-to-br from-[#6C63FF]/20 to-[#E94E9A]/10 p-5"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10 text-[#d9d4ff]"><Waves size={19} /></span><p className="mt-4 text-sm font-semibold">Your sound starts here.</p><p className="mt-2 text-xs leading-5 text-[#a7a2c2]">Made around the mood you shared today.</p></div><p className="mt-5 px-3 text-xs text-[#706e85]">Your mood, your music.</p></aside>

    <div className="lg:ml-[245px]"><header className="sticky top-0 z-20 flex h-[73px] items-center justify-between gap-4 border-b border-white/[.06] bg-[#0D0D18]/85 px-5 backdrop-blur-xl sm:px-9 lg:px-11"><div className="lg:hidden"><Brand /></div><div className="hidden items-center gap-2 text-sm text-[#8d8aa4] lg:flex"><House size={15} /><span className="text-[#5f5c76]">/</span><span className="font-medium text-[#e7e5f4]">Discover</span></div><div className="flex items-center gap-3">{results.isDemo && <DemoBadge />}<div className="hidden h-8 w-px bg-white/10 sm:block" /><span className="hidden h-9 w-9 items-center justify-center rounded-full border border-[#a397ff]/25 bg-[#6C63FF]/20 text-xs font-bold text-[#d4cfff] sm:flex">MY</span></div></header>

      <main className="mx-auto max-w-[1510px] px-5 pb-[200px] pt-8 sm:px-9 sm:pt-11 lg:px-11 lg:pb-[135px]">
        {results.isDemo && <div className="mb-7 flex items-start gap-3 rounded-2xl border border-[#a49eff]/20 bg-[#6C63FF]/[.08] px-4 py-3.5 text-sm leading-6 text-[#c4c0dc]"><Sparkles size={16} className="mt-0.5 shrink-0 text-[#b8b1ff]" /><p><strong className="font-semibold text-[#e3dfff]">Demo data:</strong> tracks, affinity scores and explanations are illustrative. This screen did not run semantic NLP analysis.</p></div>}

        <motion.section initial={reduceMotion ? false : { opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .5 }} className="relative overflow-hidden rounded-[30px] border border-white/[.08] bg-[#171727] px-6 py-8 sm:px-9 sm:py-10 xl:px-12"><div className="hero-grid absolute inset-0 opacity-40" aria-hidden="true" /><div className="hero-halo absolute -right-15 -top-35 h-[380px] w-[420px] rounded-full" aria-hidden="true" /><div className="relative grid items-center gap-8 md:grid-cols-[minmax(0,1fr)_minmax(260px,.72fr)]"><div className="relative z-10"><p className="flex items-center gap-2 text-xs font-bold uppercase tracking-[.23em] text-[#bbb5ff]"><Sparkles size={15} /> Your personal soundtrack</p><h1 className="mt-5 max-w-[650px] text-[clamp(2.45rem,4.6vw,4.8rem)] font-semibold leading-[1.04] tracking-[-.068em]">Made for <span className="text-gradient">your mood.</span></h1><p className="mt-5 max-w-[540px] text-base leading-7 text-[#b8b5ca]">{results.profileSummary}</p><div className="mt-7 flex flex-wrap items-center gap-3"><a href="#matches" className="inline-flex h-11 items-center justify-center gap-2 rounded-full bg-[#6C63FF] px-5 text-sm font-semibold text-white shadow-[0_10px_28px_rgba(108,99,255,.25)] transition hover:bg-[#827aff] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#CFCBFF]"><Music2 size={17} /> Explore matches</a><Link href="/" className="inline-flex h-11 items-center justify-center gap-2 rounded-full border border-white/15 px-5 text-sm font-semibold text-[#e0deee] transition hover:bg-white/[.07]"><RotateCcw size={16} /> Change mood</Link></div></div><div className="hero-art relative mx-auto flex aspect-square w-full max-w-[330px] items-center justify-center"><div className="hero-art-ring absolute inset-[6%] rounded-full border border-[#b4aaff]/15" /><div className="hero-art-ring absolute inset-[19%] rounded-full border border-[#b4aaff]/20" /><div className="hero-art-disc relative flex h-[58%] w-[58%] items-center justify-center rounded-full border-[12px] border-[#171727]/80 bg-[radial-gradient(circle_at_35%_30%,#E94E9A,#6559D9_52%,#27254e_78%)] shadow-[0_25px_75px_rgba(108,99,255,.3)]"><div className="flex h-[37%] w-[37%] items-center justify-center rounded-full border-[8px] border-[#171727]/70 bg-[#bcb4ff] text-[#22203c]"><AudioLines size={28} strokeWidth={1.7} /></div></div><span className="absolute bottom-[9%] left-[7%] rounded-full border border-white/15 bg-[#24243a]/85 px-4 py-2 text-xs font-semibold text-[#e8e5ff] backdrop-blur-sm">{answers.moods[0]} mood</span><span className="absolute right-[3%] top-[17%] flex h-9 w-9 items-center justify-center rounded-full bg-[#E94E9A]/85 text-white"><Music2 size={16} /></span></div></div></motion.section>

        <section id="matches" className="scroll-mt-24 pt-11 sm:pt-14"><SectionHeading kicker="CURATED FOR YOU" title="Your Top Matches" subtitle="Three tracks shaped around the vibe you shared." aside={results.isDemo ? "Illustrative ranking" : "Ranked for you"} /><div className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-3">{results.recommendations.slice(0, 3).map((track, index) => <RecommendationCard key={track.id} track={track} featured={index === 0} onListen={setSelectedTrack} />)}</div></section>

        <section id="vibe" className="scroll-mt-24 pt-11 sm:pt-14"><SectionHeading kicker="THE BIG PICTURE" title="Inside your vibe" subtitle="A closer look at the preferences behind your music." /><div className="mt-6 grid gap-5 xl:grid-cols-[1.15fr_.85fr]"><div className="rounded-[25px] border border-white/[.08] bg-[#171727] p-6 sm:p-7"><div className="flex items-center justify-between gap-4"><div><p className="text-lg font-semibold tracking-tight">Affinity snapshot</p><p className="mt-1 text-sm text-[#9996af]">{results.isDemo ? "Based on the top demo match" : "Average of your top matches"}</p></div><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#6C63FF]/15 text-[#b9b2ff]"><ChartNoAxesColumn size={19} /></span></div><div className="mt-3"><AffinityChart data={results.affinities} /></div><p className="mt-2 text-xs text-[#7f7c96]">{results.isDemo ? "Scores are fictional and shown for interface demonstration." : "Scores supplied by the recommendation service."}</p></div><div className="relative overflow-hidden rounded-[25px] border border-white/[.08] bg-[#171727] p-6 sm:p-7"><div className="absolute -right-20 -top-20 h-56 w-56 rounded-full bg-[#E94E9A]/10 blur-3xl" aria-hidden="true" /><div className="relative"><div className="flex items-center justify-between"><p className="text-lg font-semibold tracking-tight">Your listening profile</p><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#E94E9A]/12 text-[#f18fbd]"><Heart size={18} /></span></div><p className="mt-4 text-sm leading-7 text-[#b5b2c9]">{results.profileSummary}</p>{results.profile && <ProfileBadges profile={results.profile} />}<div className="mt-6 border-t border-white/[.08] pt-5"><p className="text-xs font-semibold uppercase tracking-[.18em] text-[#85819d]">Current mood</p><div className="mt-3 flex flex-wrap gap-2">{answers.moods.map((mood) => <span key={mood} className="rounded-full border border-[#6C63FF]/25 bg-[#6C63FF]/10 px-3 py-1.5 text-xs font-semibold text-[#d1ccff]">{mood}</span>)}</div></div><div className="mt-6 border-t border-white/[.08] pt-5"><p className="text-xs font-semibold uppercase tracking-[.18em] text-[#85819d]">Genres you chose</p><div className="mt-3 flex flex-wrap gap-2">{answers.genres.map((genre) => <span key={genre} className="rounded-full border border-white/10 bg-white/[.05] px-3 py-1.5 text-xs font-semibold text-[#c7c3d8]">{genre}</span>)}</div></div><Link href="/" className="mt-7 inline-flex items-center gap-2 text-sm font-semibold text-[#bcb5ff] hover:text-white">Refine your answers <ArrowUpRight size={16} /></Link></div></div></div>{results.profile && <MoodMap profile={results.profile} />}</section>

        <section id="explore" className="scroll-mt-24 pt-11 sm:pt-14"><SectionHeading kicker="A LITTLE INSPIRATION" title="Explore Your Sound" subtitle="Four moods in our demo collection, from low-key to full energy." /><div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{scenes.map((scene) => <div key={scene.label} className="scene-card relative min-h-[188px] overflow-hidden rounded-[23px] border border-white/[.08] p-5"><Image src={scene.cover} alt="" fill sizes="(max-width: 640px) 100vw, 25vw" className="object-cover opacity-65" /><div className="absolute inset-0 bg-gradient-to-t from-[#11111f] via-[#11111f]/40 to-transparent" /><div className="relative flex h-full flex-col justify-end"><p className="text-lg font-semibold">{scene.label}</p><p className="mt-1 text-xs text-[#c2bed2]">{scene.subtitle}</p></div></div>)}</div><p className="mt-4 text-xs text-[#77758f]">These are visual examples. Select “Change mood” to get a different demo scenario, or <Link href="/dataset" className="font-semibold text-[#bcb5ff] hover:text-white">browse the full music library</Link>.</p></section>
      </main>
    </div>
    <nav aria-label="Mobile navigation" className="fixed inset-x-0 bottom-[78px] z-30 flex h-[60px] items-center justify-around border-t border-white/[.08] bg-[#11111e]/95 backdrop-blur-xl lg:hidden"><a href="#top" className="mobile-nav-link"><House size={20} /><span>Discover</span></a><a href="#matches" className="mobile-nav-link"><ListMusic size={20} /><span>Matches</span></a><a href="#vibe" className="mobile-nav-link"><Heart size={20} /><span>My vibe</span></a><Link href="/dataset" className="mobile-nav-link"><Database size={20} /><span>Library</span></Link><Link href="/" className="mobile-nav-link"><RotateCcw size={20} /><span>Change</span></Link></nav>
    <MusicPlayer track={selectedTrack} onClose={() => setSelectedTrack(null)} />
  </div>;
}

function SectionHeading({ kicker, title, subtitle, aside }: { kicker: string; title: string; subtitle: string; aside?: string }) {
  return <div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-[.22em] text-[#aaa3ff]">{kicker}</p><h2 className="mt-2 text-[clamp(1.8rem,3vw,2.65rem)] font-semibold tracking-[-.055em]">{title}</h2><p className="mt-2 text-sm text-[#9e9bb1]">{subtitle}</p></div>{aside && <span className="rounded-full border border-white/10 bg-white/[.04] px-3 py-1.5 text-xs text-[#a8a5bd]">{aside}</span>}</div>;
}

function EmptyDiscover() {
  return <main className="flex min-h-dvh flex-col items-center justify-center bg-[#0D0D18] px-6 text-center text-white"><Brand /><div className="mt-12 flex h-24 w-24 items-center justify-center rounded-[28px] border border-[#6C63FF]/25 bg-[#6C63FF]/10 text-[#bcb5ff]"><Headphones size={39} /></div><h1 className="mt-7 text-4xl font-semibold tracking-[-.055em]">Your music is waiting.</h1><p className="mt-4 max-w-md text-sm leading-7 text-[#a9a6bd]">Tell us about your mood first, and your recommendations will appear here.</p><Button asChild size="lg" className="mt-8"><Link href="/">Start questionnaire</Link></Button></main>;
}
