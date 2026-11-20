import type { Metadata } from "next";
import "geist/font/sans";
import "./globals.css";

export const metadata: Metadata = {
  title: "Moodify — Your mood, your music.",
  description: "Discover music made for your mood. A semantic music recommendation experience.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
