"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { AudioLines, LoaderCircle, MessageCircle, Play, Send, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { canPlay } from "@/components/player/music-player";
import { CoverImage } from "@/components/recommendations/cover-image";
import type { Recommendation } from "@/types/music";

type ChatResponse = { reply: string; recommendations: Recommendation[] };
type ChatTurn = ChatResponse & { message: string };
type Props = { isDemo: boolean; onListen: (track: Recommendation) => void };

const MAX_MESSAGE_LENGTH = 1000;

export function MoodChat({ isDemo, onListen }: Props) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const history = useRef<HTMLDivElement>(null);
  const baseUrl = process.env.NEXT_PUBLIC_API_URL;
  const available = !isDemo && Boolean(baseUrl);

  useEffect(() => {
    const view = history.current;
    if (open && view) view.scrollTop = view.scrollHeight;
  }, [open, turns, pending]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = message.trim();
    if (!baseUrl || !available || pending || text.length < 3 || text.length > MAX_MESSAGE_LENGTH) return;

    setPending(true);
    setError("");
    try {
      const response = await fetch(baseUrl.replace(/\/$/, "") + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      if (!response.ok) throw new Error("Le chat a répondu avec le code " + response.status);
      const reply = (await response.json()) as ChatResponse;
      setTurns((history) => [...history, { ...reply, message: text }]);
      setMessage("");
    } catch (cause) {
      setError(cause instanceof TypeError
        ? "Impossible de joindre le chat. Vérifiez que l’API Moodify est lancée."
        : "Le chat n’a pas pu répondre. Réessayez dans un instant.");
    } finally {
      setPending(false);
    }
  }

  return (
    <Dialog.Root open={open} onOpenChange={setOpen} modal={false}>
      <Dialog.Trigger asChild>
        <button
          type="button"
          aria-label={open ? "Fermer le chat d’humeur" : "Ouvrir le chat d’humeur"}
          className="fixed bottom-[150px] right-4 z-45 grid h-13 w-13 place-items-center rounded-full border border-white/25 bg-[#8461ed] text-white shadow-[0_8px_32px_#7750cf70] transition hover:bg-[#926ffa] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#d9caff] lg:bottom-[104px] lg:right-7"
        >
          {open ? <X size={23} /> : <MessageCircle size={23} />}
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Content className="fixed bottom-[213px] right-4 z-45 flex max-h-[min(34rem,calc(100dvh-14rem))] w-[min(25rem,calc(100vw-2rem))] flex-col overflow-hidden rounded-[24px] border border-[#a999ec]/30 bg-[#1a162b] text-white shadow-[0_18px_75px_#080611b8] outline-none lg:bottom-[167px] lg:right-7 lg:max-h-[min(36rem,calc(100dvh-12rem))]">
          <header className="flex shrink-0 items-center gap-3 border-b border-white/10 bg-[#26203b] p-4">
            <span aria-hidden="true" className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-[#9b87ff]/20 text-[#d6caff]"><AudioLines size={19} /></span>
            <Dialog.Title className="min-w-0 flex-1 text-base font-semibold">Chat d’humeur</Dialog.Title>
            <Dialog.Description className="sr-only">Décrivez ce que vous aimeriez écouter.</Dialog.Description>
            <Dialog.Close aria-label="Fermer le chat" className="rounded-lg p-2 text-[#ded2fa] hover:bg-white/10 focus-visible:outline-2"><X size={17} /></Dialog.Close>
          </header>

          <div ref={history} role="log" aria-label="Conversation" className="min-h-0 flex-1 space-y-4 overflow-y-auto overscroll-contain p-4">
            <p className="mr-6 rounded-2xl rounded-tl-sm bg-white/[.07] px-3 py-2.5 text-sm text-[#eee7fc]">
              {available ? "Qu’aimeriez-vous écouter maintenant ?" : "Le chat est disponible quand Moodify est connecté à l’API."}
            </p>
            {turns.map((turn, index) => (
              <div key={index} className="space-y-2.5">
                <p className="ml-7 break-words rounded-2xl rounded-tr-sm bg-[#6044a4] px-3 py-2.5 text-sm">{turn.message}</p>
                <p className="mr-6 rounded-2xl rounded-tl-sm bg-white/[.07] px-3 py-2.5 text-sm leading-6 text-[#eee7fc]">{turn.reply}</p>
                {turn.recommendations.map((track) => (
                  <button key={track.id} type="button" disabled={!canPlay(track)} onClick={() => { setOpen(false); onListen(track); }}
                    className="flex w-full items-center gap-2.5 rounded-xl border border-white/10 p-2 text-left hover:bg-white/10 focus-visible:outline-2 disabled:opacity-65"
                    aria-label={(canPlay(track) ? "Écouter " : "Lecture indisponible : ") + track.title}>
                    <span className="relative h-9 w-9 shrink-0 overflow-hidden rounded-lg">
                      <CoverImage src={track.coverUrl} alt="" fill sizes="36px" className="object-cover" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-xs font-semibold">{track.title}</span>
                      <span className="block truncate text-xs text-[#bfb4d0]">{track.artist}</span>
                    </span>
                    {canPlay(track) && <Play aria-hidden="true" size={15} className="shrink-0 text-[#d0b8ff]" />}
                  </button>
                ))}
              </div>
            ))}
            {pending && <p className="text-sm text-[#bab0cf]">Recherche de morceaux…</p>}
            {error && <p role="alert" className="text-sm text-[#ffb4d5]">{error}</p>}
          </div>

          {available && (
            <form onSubmit={submit} className="flex shrink-0 items-end gap-2 border-t border-white/10 p-3">
              <label htmlFor="chat-message" className="sr-only">Votre demande musicale</label>
              <textarea id="chat-message" value={message} onChange={(event) => setMessage(event.target.value)}
                placeholder="Par ex. du jazz pour me détendre" required minLength={3} maxLength={MAX_MESSAGE_LENGTH}
                rows={2} readOnly={pending} className="w-full resize-none rounded-xl border border-white/15 bg-[#110f20] px-3 py-2 text-base placeholder:text-[#a29ab8] focus-visible:outline-2 focus-visible:outline-[#c8b9ff]" />
              <Button type="submit" size="icon" aria-label="Envoyer" disabled={pending || message.trim().length < 3} className="shrink-0">
                {pending ? <LoaderCircle size={17} className="motion-safe:animate-spin" /> : <Send size={17} />}
              </Button>
            </form>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
