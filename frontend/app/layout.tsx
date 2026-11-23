import type { Metadata } from "next";
import "geist/font/sans";
import "./globals.css";

export const metadata: Metadata = {
  title: "Moodify — Votre humeur, votre musique.",
  description: "Des recommandations musicales adaptées à votre humeur.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="fr"><body>{children}</body></html>;
}
