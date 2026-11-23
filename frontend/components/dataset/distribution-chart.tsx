"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CountItem } from "@/lib/dataset-stats";

export function DistributionChart({ data, label, gradientId, layout = "horizontal", unit = "tracks", labelWidth = 170 }: { data: CountItem[]; label: string; gradientId: string; layout?: "horizontal" | "vertical"; unit?: string; labelWidth?: number }) {
  const vertical = layout === "vertical";
  const height = vertical ? Math.max(220, data.length * 34) : 235;
  return (
    <div className="w-full" style={{ height }} role="img" aria-label={`${label}: ${data.map((item) => `${item.label} ${item.count}`).join(", ")}`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout={vertical ? "vertical" : "horizontal"} margin={vertical ? { top: 4, right: 12, bottom: 0, left: 0 } : { top: 10, right: 4, bottom: 0, left: -23 }} barCategoryGap="30%">
          <defs>
            <linearGradient id={gradientId} x1="0" y1={vertical ? "0" : "1"} x2={vertical ? "1" : "0"} y2="0">
              <stop offset="0%" stopColor="#6C63FF" />
              <stop offset="100%" stopColor="#E94E9A" />
            </linearGradient>
          </defs>
          <CartesianGrid horizontal={!vertical} vertical={vertical} stroke="rgba(255,255,255,.07)" strokeDasharray="3 7" />
          {vertical ? (
            <>
              <XAxis type="number" allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill: "#77758f", fontSize: 11 }} />
              <YAxis type="category" dataKey="label" width={labelWidth} axisLine={false} tickLine={false} tick={{ fill: "#a7a3bd", fontSize: 12 }} />
            </>
          ) : (
            <>
              <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: "#a7a3bd", fontSize: 12 }} dy={12} />
              <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill: "#77758f", fontSize: 11 }} />
            </>
          )}
          <Tooltip cursor={{ fill: "rgba(255,255,255,.04)" }} contentStyle={{ background: "#222238", border: "1px solid rgba(255,255,255,.1)", borderRadius: 12, color: "#fff" }} formatter={(value) => [`${value} ${unit}`, label]} />
          <Bar dataKey="count" fill={`url(#${gradientId})`} radius={vertical ? [0, 8, 8, 0] : [8, 8, 0, 0]} maxBarSize={vertical ? 20 : 48} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
