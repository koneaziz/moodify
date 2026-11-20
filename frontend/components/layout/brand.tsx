import Link from "next/link";
import { AudioLines } from "lucide-react";
import { cn } from "@/lib/utils";

export function Brand({ compact = false, className = "" }: { compact?: boolean; className?: string }) {
  return (
    <Link href="/" className={cn("inline-flex items-center gap-3 rounded-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#CFCBFF]", className)} aria-label="Moodify home">
      <span className="brand-mark flex h-10 w-10 items-center justify-center rounded-[15px] text-white"><AudioLines size={23} strokeWidth={2.4} /></span>
      {!compact && <span className="text-[1.35rem] font-bold tracking-[-.055em] text-white">moodify<span className="text-[#E94E9A]">.</span></span>}
    </Link>
  );
}
