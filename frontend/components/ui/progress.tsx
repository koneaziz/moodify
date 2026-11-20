"use client";

import * as React from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";
import { cn } from "@/lib/utils";

export function Progress({ value = 0, className, ...props }: React.ComponentProps<typeof ProgressPrimitive.Root>) {
  return (
    <ProgressPrimitive.Root className={cn("relative h-1.5 w-full overflow-hidden rounded-full bg-white/10", className)} value={value} {...props}>
      <ProgressPrimitive.Indicator className="h-full w-full rounded-full bg-gradient-to-r from-[#6C63FF] to-[#E94E9A] transition-transform duration-500 ease-out" style={{ transform: `translateX(-${100 - (value ?? 0)}%)` }} />
    </ProgressPrimitive.Root>
  );
}
