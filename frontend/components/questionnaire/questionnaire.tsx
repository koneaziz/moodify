"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useForm, useWatch, type FieldPath } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, ArrowRight, AudioLines, BookOpen, Brain, Check, CircleHelp, CloudMoon, Coffee, Dumbbell, Flame, Headphones, Heart, HeartCrack, Laptop, Moon, Music2, PartyPopper, Play, Radio, RotateCcw, Sparkles, Sun, Waves, Zap, type LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Slider } from "@/components/ui/slider";
import { Brand } from "@/components/layout/brand";
import { DemoBadge } from "@/components/layout/demo-badge";
import { cn } from "@/lib/utils";
import { questionnaireSchema } from "@/lib/questionnaire-schema";
import { loadAnswers, saveAnswers, saveResults } from "@/lib/session";
import { recommendationService } from "@/services/recommendation-service";
import { CONTEXTS, defaultAnswers, GENRES, MOODS, VOCAL_PREFERENCES, type Genre, type Mood, type QuestionnaireAnswers } from "@/types/questionnaire";

const steps = ["Your mood", "Your story", "Genres", "Listening", "Energy", "Fine-tune", "Your vibe"] as const;
const stepFields: FieldPath<QuestionnaireAnswers>[][] = [
  ["moods"], ["description"], ["genres"], ["listeningContext", "contextDescription"], ["energyLevel"], ["favoriteArtists", "vocalPreference", "additionalPreferences"], [],
];
const headings = [
  { eyebrow: "01 / THE FEELING", title: "How are you feeling today?", description: "Pick the moods that feel closest to you right now. You can choose more than one." },
  { eyebrow: "02 / IN YOUR WORDS", title: "Tell us what's on your mind.", description: "Your own words give the recommendation engine the context that categories cannot capture." },
  { eyebrow: "03 / YOUR SOUND", title: "What kind of music moves you?", description: "Choose a few genres you gravitate toward. We’ll keep your options open." },
  { eyebrow: "04 / THE MOMENT", title: "What's the occasion?", description: "The right soundtrack depends on what you’re doing, too." },
  { eyebrow: "05 / THE PULSE", title: "What energy are you looking for?", description: "Set the pace of the music you want to hear." },
  { eyebrow: "06 / THE DETAILS", title: "Let's fine-tune your sound.", description: "A few last details can make your music feel more like yours." },
  { eyebrow: "07 / READY TO LISTEN", title: "Your vibe, perfectly captured.", description: "Take a quick look. You can go back and change anything before discovering your music." },
];
const moodIcons: Record<Mood, LucideIcon> = { Happy: Sun, Sad: HeartCrack, Calm: Waves, Stressed: Brain, Energetic: Zap, Focused: BookOpen, Melancholic: CloudMoon, Romantic: Heart };
const moodTones: Record<Mood, string> = { Happy: "tone-gold", Sad: "tone-blue", Calm: "tone-teal", Stressed: "tone-pink", Energetic: "tone-orange", Focused: "tone-violet", Melancholic: "tone-purple", Romantic: "tone-rose" };
const contextIcons: LucideIcon[] = [BookOpen, Laptop, Coffee, Dumbbell, Radio, Moon, PartyPopper, Headphones];
const energies = ["Very calm", "Calm", "Balanced", "Energetic", "Very energetic"];

function ChoiceCard({ label, selected, onClick, icon: Icon, tone = "", compact = false }: { label: string; selected: boolean; onClick: () => void; icon?: LucideIcon; tone?: string; compact?: boolean }) {
  return (
    <motion.button type="button" whileHover={{ y: -3 }} whileTap={{ scale: .98 }} aria-pressed={selected} onClick={onClick} className={cn("choice-card group relative flex items-center gap-3 rounded-[20px] border text-left transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#CFCBFF]", compact ? "min-h-15 px-4 py-3" : "min-h-26 flex-col items-start justify-between p-4 sm:min-h-30 sm:p-5", selected ? "border-[#8d86ff] bg-[#6C63FF]/16 shadow-[inset_0_0_0_1px_rgba(141,134,255,.25),0_12px_35px_rgba(0,0,0,.13)]" : "border-white/[.09] bg-white/[.035] hover:border-white/25 hover:bg-white/[.065]") }>
      {Icon && <span className={cn("flex h-10 w-10 items-center justify-center rounded-[13px]", tone || "tone-violet")}><Icon size={21} strokeWidth={1.8} /></span>}
      <span className="text-[.94rem] font-semibold text-[#F8F8FC]">{label}</span>
      {selected && <span className="absolute right-3 top-3 flex h-5 w-5 items-center justify-center rounded-full bg-[#8f87ff] text-white"><Check size={12} strokeWidth={3} /></span>}
    </motion.button>
  );
}

function FieldError({ message }: { message?: string }) {
  return message ? <p className="mt-2 text-sm text-[#ff9dbf]" role="alert">{message}</p> : null;
}

function SummaryRow({ label, value, onEdit }: { label: string; value: string; onEdit: () => void }) {
  return <div className="flex items-start justify-between gap-5 border-b border-white/[.08] py-4 last:border-none"><div><p className="text-xs font-semibold uppercase tracking-[.16em] text-[#8c89a7]">{label}</p><p className="mt-1.5 whitespace-pre-wrap text-[.95rem] leading-relaxed text-white">{value || "No preference"}</p></div><button type="button" onClick={onEdit} className="rounded-md px-2 py-1 text-xs font-semibold text-[#b9b4ff] hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#CFCBFF]">Edit</button></div>;
}

export function Questionnaire() {
  const router = useRouter();
  const reduceMotion = useReducedMotion();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const { register, control, setValue, trigger, handleSubmit, reset, formState: { errors } } = useForm<QuestionnaireAnswers>({ resolver: zodResolver(questionnaireSchema), defaultValues: defaultAnswers, mode: "onTouched" });
  const values = useWatch({ control, defaultValue: defaultAnswers }) as QuestionnaireAnswers;

  useEffect(() => {
    const saved = loadAnswers();
    if (saved) reset({ ...defaultAnswers, ...saved });
  }, [reset]);

  useEffect(() => {
    saveAnswers(values);
  }, [values]);

  async function next() {
    if (step === 6) return;
    const valid = await trigger(stepFields[step]);
    if (valid) setStep((current) => current + 1);
  }

  function toggleMood(mood: Mood) {
    setValue("moods", values.moods.includes(mood) ? values.moods.filter((item) => item !== mood) : [...values.moods, mood], { shouldValidate: true, shouldDirty: true });
  }

  function toggleGenre(genre: Genre) {
    setValue("genres", values.genres.includes(genre) ? values.genres.filter((item) => item !== genre) : [...values.genres, genre], { shouldValidate: true, shouldDirty: true });
  }

  async function submit(answers: QuestionnaireAnswers) {
    saveAnswers(answers);
    setSubmitError("");
    setSubmitting(true);
    try {
      const results = await recommendationService.getRecommendations(answers);
      saveResults(results);
      router.push("/discover");
    } catch (error) {
      setSubmitting(false);
      setSubmitError(error instanceof Error ? error.message : "Something went wrong. Please try again.");
    }
  }

  return (
    <main className="questionnaire-shell relative min-h-dvh overflow-hidden text-white">
      <div className="ambient-glow ambient-glow-one" aria-hidden="true" /><div className="ambient-glow ambient-glow-two" aria-hidden="true" />
      <div className="relative mx-auto flex min-h-dvh max-w-[1500px] flex-col lg:flex-row">
        <aside className="questionnaire-aside flex w-full flex-col border-b border-white/[.07] px-6 py-5 sm:px-10 lg:min-h-dvh lg:w-[36%] lg:max-w-[490px] lg:border-b-0 lg:border-r lg:px-12 lg:py-10">
          <div className="flex items-center justify-between"><Brand />{process.env.NEXT_PUBLIC_USE_MOCKS !== "false" && <DemoBadge />}</div>
          <div className="relative hidden flex-1 flex-col justify-center lg:flex">
            <div className="orb-scene" aria-hidden="true"><div className="orb-ring orb-ring-outer" /><div className="orb-ring orb-ring-inner" /><div className="orb-core"><AudioLines size={45} strokeWidth={1.2} /></div><span className="orb-star orb-star-one" /><span className="orb-star orb-star-two" /></div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-[.26em] text-[#E27DBB]">A listening experience made for you</p>
            <h2 className="max-w-[360px] text-[clamp(2rem,3.2vw,3.3rem)] font-semibold leading-[1.08] tracking-[-.065em]">Every feeling has a <span className="text-gradient">soundtrack.</span></h2>
            <p className="mt-5 max-w-[330px] text-sm leading-7 text-[#a7a5bc]">Tell us how you feel. We’ll help you find music that fits the moment.</p>
          </div>
          <div className="hidden lg:block"><p className="text-xs font-semibold uppercase tracking-[.2em] text-[#89869e]">Your journey</p><div className="mt-4 flex flex-wrap gap-2">{steps.map((name, index) => <span key={name} className={cn("rounded-full border px-3 py-1.5 text-xs", index === step ? "border-[#8b83ff]/55 bg-[#6C63FF]/17 text-[#dfdcff]" : index < step ? "border-white/10 text-[#9a97b2]" : "border-transparent text-[#77748d]")}>{index < step ? "✓" : String(index + 1).padStart(2, "0")} {name}</span>)}</div></div>
          <p className="mt-8 hidden text-xs text-[#77758e] lg:block">Your mood, your music.</p>
        </aside>

        <section className="flex flex-1 flex-col px-5 pb-7 pt-7 sm:px-10 sm:pt-10 lg:px-[min(6vw,90px)] lg:pb-10" aria-label="Music preferences questionnaire">
          <div className="mx-auto w-full max-w-[780px]"><div className="flex items-center justify-between gap-4 text-xs font-semibold uppercase tracking-[.18em] text-[#a9a6c2]"><span>Find your sound</span><span>Step {step + 1} of 7</span></div><Progress value={((step + 1) / 7) * 100} className="mt-4" aria-label="Questionnaire progress" /></div>
          <div className="mx-auto flex w-full max-w-[780px] flex-1 flex-col justify-center py-9 sm:py-12">
            <AnimatePresence mode="wait">
              {submitting ? <AnalysisState key="analysis" isDemo={process.env.NEXT_PUBLIC_USE_MOCKS !== "false"} /> : (
                <motion.div key={step} initial={reduceMotion ? false : { opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={reduceMotion ? undefined : { opacity: 0, x: -18 }} transition={{ duration: reduceMotion ? 0 : .28, ease: "easeOut" }}>
                  <div className="mb-7 sm:mb-9"><p className="mb-4 text-xs font-bold uppercase tracking-[.24em] text-[#b4acff]">{headings[step].eyebrow}</p><h1 className="max-w-[720px] text-[clamp(2.35rem,4.4vw,4.55rem)] font-semibold leading-[1.05] tracking-[-.066em] text-[#F8F8FC]">{headings[step].title}</h1><p className="mt-5 max-w-[560px] text-[.98rem] leading-7 text-[#aaa8be]">{headings[step].description}</p></div>

                  {step === 0 && <><div className="grid grid-cols-2 gap-3 sm:grid-cols-4">{MOODS.map((mood) => <ChoiceCard key={mood} label={mood} icon={moodIcons[mood]} tone={moodTones[mood]} selected={values.moods.includes(mood)} onClick={() => toggleMood(mood)} />)}</div><FieldError message={errors.moods?.message} /></>}

                  {step === 1 && <div><label htmlFor="description" className="mb-3 block text-sm font-semibold text-[#e8e6f5]">Describe your mood or the music you need <span className="text-[#E94E9A]">*</span></label><textarea id="description" {...register("description")} maxLength={1000} rows={7} placeholder="I'm feeling a little stressed and looking for something soft and atmospheric to help me focus while studying." className="input-surface min-h-[210px] w-full resize-y rounded-[22px] p-5 text-base leading-7 sm:p-6" aria-invalid={!!errors.description} aria-describedby={errors.description ? "description-error" : undefined} /><div className="mt-2 flex justify-between gap-3"><span id="description-error"><FieldError message={errors.description?.message} /></span><span className="text-xs text-[#77758f]">{values.description.length} / 1000</span></div><div className="mt-6 flex items-start gap-3 rounded-[18px] border border-[#6C63FF]/20 bg-[#6C63FF]/[.07] p-4 text-sm leading-6 text-[#bdb9da]"><Sparkles size={18} className="mt-0.5 shrink-0 text-[#aaa3ff]" />{process.env.NEXT_PUBLIC_USE_MOCKS === "false" ? "This text will be sent to the recommendation service for semantic analysis." : "The real backend will analyze this text semantically. Demo Mode uses your structured choices only."}</div></div>}

                  {step === 2 && <><div className="flex flex-wrap gap-3">{GENRES.map((genre) => <button key={genre} type="button" aria-pressed={values.genres.includes(genre)} onClick={() => toggleGenre(genre)} className={cn("rounded-full border px-5 py-3 text-sm font-semibold transition-all hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#CFCBFF]", values.genres.includes(genre) ? "border-[#8d86ff] bg-[#6C63FF]/20 text-white" : "border-white/12 bg-white/[.04] text-[#c2c0d3] hover:border-white/30 hover:text-white")}>{genre}</button>)}</div><FieldError message={errors.genres?.message} /><p className="mt-7 text-sm text-[#77758f]">Choose one or more genres.</p></>}

                  {step === 3 && <><div className="grid grid-cols-2 gap-3 sm:grid-cols-4">{CONTEXTS.map((context, index) => <ChoiceCard key={context} label={context} icon={contextIcons[index]} selected={values.listeningContext === context} compact onClick={() => setValue("listeningContext", context, { shouldValidate: true, shouldDirty: true })} />)}</div><FieldError message={errors.listeningContext?.message} /><label htmlFor="contextDescription" className="mb-3 mt-7 block text-sm font-semibold text-[#e8e6f5]">Anything else about the moment? <span className="font-normal text-[#89869e]">Optional</span></label><input id="contextDescription" {...register("contextDescription")} maxLength={300} placeholder="e.g. A late night study session before an exam" className="input-surface h-13 w-full rounded-2xl px-5" /><FieldError message={errors.contextDescription?.message} /></>}

                  {step === 4 && <div className="energy-panel rounded-[25px] border border-white/[.09] p-6 sm:p-8"><div className="mb-8 flex items-center gap-4"><div className="flex h-15 w-15 items-center justify-center rounded-[20px] bg-[#6C63FF]/20 text-[#b8b1ff]"><Flame size={28} /></div><div><p className="text-xs font-semibold uppercase tracking-[.17em] text-[#9e9ab6]">Energy level {values.energyLevel} / 5</p><p className="mt-1 text-2xl font-semibold tracking-tight">{energies[values.energyLevel - 1]}</p></div></div><Slider min={1} max={5} step={1} value={[values.energyLevel]} onValueChange={([value]) => setValue("energyLevel", value, { shouldValidate: true, shouldDirty: true })} aria-label="Desired music energy" /><div className="mt-3 flex justify-between text-xs font-medium text-[#8c89a7]"><span>Very calm</span><span>Very energetic</span></div><div className="mt-8 flex items-center justify-center gap-1.5" aria-hidden="true">{[1, 2, 3, 4, 5].map((item) => <div key={item} className={cn("w-5 rounded-full transition-all duration-300", item <= values.energyLevel ? "bg-gradient-to-t from-[#6C63FF] to-[#E94E9A]" : "bg-white/10")} style={{ height: 12 + item * 8 }} />)}</div></div>}

                  {step === 5 && <div className="space-y-7"><div><label htmlFor="favoriteArtists" className="mb-3 block text-sm font-semibold text-[#e8e6f5]">Favorite artists <span className="font-normal text-[#89869e]">Optional</span></label><input id="favoriteArtists" {...register("favoriteArtists")} maxLength={200} placeholder="e.g. Bon Iver, SZA, ODESZA" className="input-surface h-13 w-full rounded-2xl px-5" /><FieldError message={errors.favoriteArtists?.message} /></div><fieldset><legend className="mb-3 text-sm font-semibold text-[#e8e6f5]">What about vocals?</legend><div className="grid grid-cols-1 gap-3 sm:grid-cols-3">{VOCAL_PREFERENCES.map((preference) => <ChoiceCard key={preference} label={preference} icon={preference === "Instrumental" ? Music2 : preference === "Vocals" ? Radio : CircleHelp} selected={values.vocalPreference === preference} compact onClick={() => setValue("vocalPreference", preference, { shouldValidate: true, shouldDirty: true })} />)}</div></fieldset><div><label htmlFor="additionalPreferences" className="mb-3 block text-sm font-semibold text-[#e8e6f5]">Anything else we should know? <span className="font-normal text-[#89869e]">Optional</span></label><textarea id="additionalPreferences" {...register("additionalPreferences")} maxLength={500} rows={3} placeholder="A specific instrument, atmosphere, or feeling..." className="input-surface w-full resize-y rounded-2xl px-5 py-4" /><FieldError message={errors.additionalPreferences?.message} /></div></div>}

                  {step === 6 && <div className="overflow-hidden rounded-[25px] border border-white/[.09] bg-[#171727]/85 p-5 sm:p-7"><div className="mb-2 flex items-center gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#6C63FF]/20 text-[#c4beff]"><Headphones size={20} /></span><div><p className="font-semibold">Your listening profile</p><p className="text-xs text-[#9390a9]">Ready to discover your sound</p></div></div><SummaryRow label="Mood" value={values.moods.join(", ")} onEdit={() => setStep(0)} /><SummaryRow label="Your words" value={values.description} onEdit={() => setStep(1)} /><SummaryRow label="Genres" value={values.genres.join(", ")} onEdit={() => setStep(2)} /><SummaryRow label="Listening context" value={`${values.listeningContext}${values.contextDescription ? ` · ${values.contextDescription}` : ""}`} onEdit={() => setStep(3)} /><SummaryRow label="Energy" value={`${values.energyLevel}/5 · ${energies[values.energyLevel - 1]}`} onEdit={() => setStep(4)} /><SummaryRow label="Musical preferences" value={[values.favoriteArtists && `Artists: ${values.favoriteArtists}`, `Vocals: ${values.vocalPreference}`, values.additionalPreferences].filter(Boolean).join(" · ")} onEdit={() => setStep(5)} /></div>}

                  <div className="mt-9 flex flex-wrap items-center justify-between gap-4"><Button type="button" variant="ghost" size="lg" onClick={() => setStep((current) => Math.max(0, current - 1))} disabled={step === 0} className={cn(step === 0 && "invisible")}><ArrowLeft size={18} /> Back</Button><Button type="button" size="lg" onClick={step === 6 ? handleSubmit(submit) : next} className="min-w-[180px]">{step === 6 ? <><Play size={17} fill="currentColor" /> Find my music</> : <>Continue <ArrowRight size={18} /></>}</Button></div>
                  {submitError && <p role="alert" className="mt-4 rounded-2xl border border-[#E94E9A]/30 bg-[#E94E9A]/10 p-4 text-sm text-[#ffb4d5]">{submitError}</p>}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          <div className="mx-auto flex w-full max-w-[780px] items-center justify-between gap-4 border-t border-white/[.07] pt-5 text-xs text-[#77758f]"><span>Made for your mood</span><span className="flex items-center gap-1.5"><RotateCcw size={12} /> You can change your answers anytime</span></div>
        </section>
      </div>
    </main>
  );
}

function AnalysisState({ isDemo }: { isDemo: boolean }) {
  const reduceMotion = useReducedMotion();
  return <div className="flex min-h-[440px] flex-col items-center justify-center text-center" role="status" aria-live="polite"><div className="analysis-orb relative mb-10 flex h-44 w-44 items-center justify-center rounded-full"><div className="analysis-ring absolute inset-0 rounded-full border border-[#aaa3ff]/25" /><div className="analysis-ring analysis-ring-two absolute inset-5 rounded-full border border-[#E94E9A]/25" /><AudioLines size={58} className="relative text-[#dedbff]" strokeWidth={1.1} /></div><h2 className="text-4xl font-semibold tracking-[-.055em]">Finding your sound...</h2><p className="mt-4 max-w-sm text-sm leading-6 text-[#aaa8be]">{isDemo ? "Selecting a demo scenario from your choices. No NLP analysis is being performed." : "Waiting for your personalized recommendations."}</p>{!reduceMotion && <div className="mt-7 flex gap-1.5" aria-hidden="true">{[0, 1, 2].map((item) => <motion.span key={item} className="h-2 w-2 rounded-full bg-[#a9a2ff]" animate={{ opacity: [.3, 1, .3], y: [0, -5, 0] }} transition={{ duration: 1.2, repeat: Infinity, delay: item * .15 }} />)}</div>}</div>;
}
