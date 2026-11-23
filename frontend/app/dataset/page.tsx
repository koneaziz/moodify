import type { Metadata } from "next";
import { DatasetExplorer } from "@/components/dataset/dataset-explorer";

export const metadata: Metadata = {
  title: "Bibliothèque musicale — Moodify",
  description: "Explorez le catalogue musical utilisé pour les recommandations de Moodify.",
};

export default function DatasetPage() {
  return <DatasetExplorer />;
}
