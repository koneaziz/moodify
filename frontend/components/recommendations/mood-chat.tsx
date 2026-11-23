"use client";

import { useState, type FormEvent } from "react";
import { AudioLines, LoaderCircle, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { RecommendationCard } from "@/components/recommendations/recommendation-card";
import type { Recommendation } from "@/types/music";

type ChatResponse = { reply: string; recommendations: Recommendation[] };
type ChatResult = ChatResponse & { message: string };
type Props = { isDemo: boolean; onListen: (track: Recommendation) => void };

const MAX_MESSAGE_LENGTH = 1000;

export function MoodChat({ isDemo, onListen }: Props) {
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<ChatResult | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const baseUrl = process.env.NEXT_PUBLIC_API_URL;
  const available = !isDemo && Boolean(baseUrl);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = message.trim();
    if (!baseUrl || !available || pending || text.length < 3 || text.length > MAX_MESSAGE_LENGTH) return;

    setPending(true);
    setError("");
    try {
      const response = await fetch(`${baseUrl.replace(/\/$/, "")}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      if (!response.ok) throw new Error(`Le chat a répondu avec le code ${response.status}.`);
      const reply = (await response.json()) as ChatResponse;
      setResult({ ...reply, message: text });
      setMessage("");
    } catch (cause) {
      setError(cause instanceof TypeError
        ? "Impossible de joindre le chat. Vérifiez que l’API Moodify est lancée, puis réessayez."
        : "Le chat n’a pas pu répondre. Réessayez dans un instant.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section id="chat" aria-labelledby="chat-title" className="mt-11 scroll-mt-24 rounded-[30px] border border-[#a597ff]/20 bg-[linear-gradient(125deg,#201b37,#171727_65%)] p-5 sm:mt-14 sm:p-8">
      <div className="flex items-center gap-4">
        <span aria-hidden="true" className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[#9b87ff]/20 text-[#d6caff]">
          <AudioLines size={23} />
        </span>
        <div>
          <p className="text-sm font-medium text-[#c9b9f5]">Chat d’humeur</p>
          <h2 id="chat-title" className="text-xl font-semibold text-white sm:text-2xl">Qu’aimeriez-vous écouter maintenant ?</h2>
        </div>
      </div>

      {available ? (
        <>
          <form onSubmit={submit} className="mt-5 space-y-3">
            <label htmlFor="chat-message" className="sr-only">Votre demande musicale</label>
            <textarea
              id="chat-message"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Je suis stressé et j’aimerais écouter quelque chose de calme pour réviser, sans rap."
              required
              minLength={3}
              maxLength={MAX_MESSAGE_LENGTH}
              rows={3}
              disabled={pending}
              className="w-full resize-y rounded-2xl border border-white/15 bg-[#110f20] px-4 py-3 text-base text-white placeholder:text-[#a29ab8] focus-visible:outline-2 focus-visible:outline-[#c8b9ff]"
            />
            <div className="flex justify-end">
              <Button type="submit" disabled={pending || message.trim().length < 3}>
                {pending ? <LoaderCircle size={17} className="motion-safe:animate-spin" /> : <Send size={17} />}
                {pending ? "Recherche en cours…" : "Envoyer"}
              </Button>
            </div>
          </form>

          {error && <p role="alert" className="mt-4 text-sm text-[#ffb4d5]">{error}</p>}
          <div aria-live="polite" className="sr-only">{pending ? "Recherche de morceaux en cours." : result?.reply}</div>
          {result && (
            <div className="mt-5 space-y-4 border-t border-white/10 pt-5">
              <div>
                <p className="break-words text-sm text-[#bab0cf]"><span className="font-semibold">Votre demande :</span> {result.message}</p>
                <p className="mt-2 text-base leading-7 text-[#f0ebff]">{result.reply}</p>
              </div>
              {result.recommendations.length > 0 && (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {result.recommendations.map((track) => <RecommendationCard key={track.id} track={track} isDemo={false} onListen={onListen} />)}
                </div>
              )}
            </div>
          )}
        </>
      ) : (
        <p className="mt-4 text-sm text-[#bab0cf]">Le chat est disponible quand l’interface est connectée à l’API Moodify.</p>
      )}
    </section>
  );
}
