import type { Metadata } from "next";
import { DatasetExplorer } from "@/components/dataset/dataset-explorer";

export const metadata: Metadata = {
  title: "Dataset — Moodify",
  description: "Browse the reference music catalogue used by Moodify's semantic recommendations.",
};

export default function DatasetPage() {
  return <DatasetExplorer />;
}
