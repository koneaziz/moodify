"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Affinity } from "@/types/music";

export function AffinityChart({ data }: { data: Affinity[] }) {
  return <div className="h-[235px] w-full" role="img" aria-label={`Demo affinity scores: ${data.map((item) => `${item.label} ${item.score} percent`).join(", ")}`}><ResponsiveContainer width="100%" height="100%"><BarChart data={data} margin={{ top: 10, right: 4, bottom: 0, left: -23 }} barCategoryGap="35%"><defs><linearGradient id="scoreGradient" x1="0" y1="1" x2="0" y2="0"><stop offset="0%" stopColor="#6C63FF" /><stop offset="100%" stopColor="#E94E9A" /></linearGradient></defs><CartesianGrid vertical={false} stroke="rgba(255,255,255,.07)" strokeDasharray="3 7" /><XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: "#a7a3bd", fontSize: 12 }} dy={12} /><YAxis domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} axisLine={false} tickLine={false} tick={{ fill: "#77758f", fontSize: 11 }} /><Tooltip cursor={{ fill: "rgba(255,255,255,.04)" }} contentStyle={{ background: "#222238", border: "1px solid rgba(255,255,255,.1)", borderRadius: 12, color: "#fff" }} formatter={(value) => [`${value}%`, "Demo score"]} /><Bar dataKey="score" fill="url(#scoreGradient)" radius={[8, 8, 0, 0]} maxBarSize={48} /></BarChart></ResponsiveContainer></div>;
}
