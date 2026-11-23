"use client";

import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from "recharts";
import type { CatalogTrack } from "@/types/dataset";

export const QUADRANT_COLORS: Record<string, string> = {
  "joyeux-énergique": "#F7D899",
  "tendu-intense": "#F5A6C8",
  "triste-calme": "#A5C5FF",
  "serein-calme": "#A2EBD8",
};

type Point = { x: number; y: number; title: string; artist: string; quadrant: string };

export function EmotionMap({ tracks }: { tracks: CatalogTrack[] }) {
  const points: Point[] = tracks.flatMap((track) => track.emotion ? [{ x: track.emotion.valence, y: track.emotion.arousal, title: track.title, artist: track.artist, quadrant: track.emotion.quadrant ?? "autre" }] : []);
  const groups = Object.keys(QUADRANT_COLORS).map((quadrant) => ({ quadrant, points: points.filter((point) => point.quadrant === quadrant) }));
  const others = points.filter((point) => !(point.quadrant in QUADRANT_COLORS));

  return (
    <div>
      <div className="h-[290px] w-full" role="img" aria-label={`Carte des émotions de ${points.length} morceaux: ${groups.map((group) => `${group.quadrant} ${group.points.length}`).join(", ")}`}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 10, bottom: 18, left: -18 }}>
            <CartesianGrid stroke="rgba(255,255,255,.07)" strokeDasharray="3 7" />
            <XAxis type="number" dataKey="x" domain={[0, 1]} ticks={[0, .25, .5, .75, 1]} axisLine={false} tickLine={false} tick={{ fill: "#77758f", fontSize: 11 }} label={{ value: "Valence (négative → positive)", position: "insideBottom", offset: -12, fill: "#9996af", fontSize: 11 }} />
            <YAxis type="number" dataKey="y" domain={[0, 1]} ticks={[0, .25, .5, .75, 1]} axisLine={false} tickLine={false} tick={{ fill: "#77758f", fontSize: 11 }} />
            <ZAxis range={[22, 22]} />
            <Tooltip cursor={{ stroke: "rgba(255,255,255,.15)" }} content={({ active, payload }) => {
              const point = active ? payload?.[0]?.payload as Point | undefined : undefined;
              if (!point) return null;
              return <div className="rounded-xl border border-white/10 bg-[#222238] px-3 py-2 text-xs text-white shadow-xl"><p className="font-semibold">{point.title}</p><p className="text-[#a6a3bc]">{point.artist}</p><p className="mt-1 text-[#c9c4ff]">{point.quadrant} · V {point.x.toFixed(2)} · A {point.y.toFixed(2)}</p></div>;
            }} />
            {groups.map((group) => <Scatter key={group.quadrant} name={group.quadrant} data={group.points} fill={QUADRANT_COLORS[group.quadrant]} fillOpacity={.75} isAnimationActive={false} />)}
            {others.length > 0 && <Scatter name="autre" data={others} fill="#8d8aa4" fillOpacity={.6} isAnimationActive={false} />}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-2 text-xs text-[#a7a3bd]">
        {groups.map((group) => <span key={group.quadrant} className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full" style={{ background: QUADRANT_COLORS[group.quadrant] }} />{group.quadrant} ({group.points.length})</span>)}
        <span className="text-[#77758f]">Axe vertical : activation (calme → intense)</span>
      </div>
    </div>
  );
}
