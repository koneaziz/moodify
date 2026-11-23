"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

type YouTubePlayer = {
  mute: () => void;
  playVideo: () => void;
  pauseVideo: () => void;
  destroy: () => void;
};

type YouTubeAPI = {
  Player: new (iframe: HTMLIFrameElement, options: {
    events: {
      onReady: (event: { target: YouTubePlayer }) => void;
      onError: () => void;
      onStateChange: (event: { data: number }) => void;
    };
  }) => YouTubePlayer;
};

type YouTubeWindow = Window & {
  YT?: YouTubeAPI;
  onYouTubeIframeAPIReady?: () => void;
};

let request: Promise<YouTubeAPI> | undefined;

function loadYouTubeAPI() {
  const apiWindow = window as YouTubeWindow;
  if (apiWindow.YT?.Player) return Promise.resolve(apiWindow.YT);

  if (!request) {
    request = new Promise<YouTubeAPI>((resolve, reject) => {
      const script = document.createElement("script");
      const previous = apiWindow.onYouTubeIframeAPIReady;
      const timeout = window.setTimeout(fail, 10_000);

      function restore() {
        window.clearTimeout(timeout);
        apiWindow.onYouTubeIframeAPIReady = previous;
      }

      function fail() {
        restore();
        script.remove();
        request = undefined;
        reject(new Error("Impossible de charger le lecteur YouTube."));
      }

      apiWindow.onYouTubeIframeAPIReady = () => {
        if (apiWindow.YT?.Player) {
          restore();
          resolve(apiWindow.YT);
        } else {
          fail();
        }
        previous?.();
      };
      script.src = "https://www.youtube.com/iframe_api";
      script.onerror = fail;
      document.head.appendChild(script);
    });
  }
  return request;
}

type ClipProps = {
  videoId: string;
  title: string;
  fallback: ReactNode;
};

export function MutedClip({ videoId, title, fallback }: ClipProps) {
  const host = useRef<HTMLDivElement>(null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    const container = host.current;
    if (!container || unavailable) return;

    let disposed = false;
    let visible = false;
    let finished = false;
    let player: YouTubePlayer | undefined;
    let readyPlayer: YouTubePlayer | undefined;
    let readyTimeout: number | undefined;

    function syncPlayback() {
      if (!readyPlayer || finished) return;
      if (visible) {
        readyPlayer.mute();
        readyPlayer.playVideo();
      } else {
        readyPlayer.pauseVideo();
      }
    }

    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting && entry.intersectionRatio > .5;
      syncPlayback();
    }, { threshold: [.51] });
    observer.observe(container);

    loadYouTubeAPI().then((api) => {
      if (disposed) return;
      const frame = document.createElement("iframe");
      const params = new URLSearchParams({
        enablejsapi: "1", origin: window.location.origin, end: "35", playsinline: "1", hl: "fr",
      });
      frame.src = "https://www.youtube-nocookie.com/embed/" + videoId + "?" + params;
      frame.title = "Extrait du clip de " + title;
      frame.allow = "autoplay; encrypted-media; picture-in-picture";
      frame.allowFullscreen = true;
      frame.className = "absolute inset-0 h-full w-full border-0";
      container.appendChild(frame);

      readyTimeout = window.setTimeout(() => { if (!disposed) setUnavailable(true); }, 8_000);
      player = new api.Player(frame, {
        events: {
          onReady: ({ target }) => {
            if (disposed) return;
            window.clearTimeout(readyTimeout);
            target.mute();
            readyPlayer = target;
            syncPlayback();
          },
          onError: () => { if (!disposed) setUnavailable(true); },
          onStateChange: ({ data }) => { if (data === 0) finished = true; },
        },
      });
    }).catch(() => { if (!disposed) setUnavailable(true); });

    return () => {
      disposed = true;
      observer.disconnect();
      window.clearTimeout(readyTimeout);
      player?.destroy();
      container.replaceChildren();
    };
  }, [title, videoId, unavailable]);

  return unavailable ? fallback : (
    <div ref={host} className="relative aspect-video min-h-[200px] w-full shrink-0 overflow-hidden rounded-2xl border border-white/10 bg-[#1a1428] shadow-[0_12px_34px_#0a051298]" />
  );
}
