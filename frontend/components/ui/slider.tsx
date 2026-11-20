"use client";

import * as React from "react";
import * as SliderPrimitive from "@radix-ui/react-slider";
import { cn } from "@/lib/utils";

export function Slider({ className, ...props }: React.ComponentProps<typeof SliderPrimitive.Root>) {
  return (
    <SliderPrimitive.Root className={cn("relative flex w-full touch-none select-none items-center py-3", className)} {...props}>
      <SliderPrimitive.Track className="relative h-2 w-full grow overflow-hidden rounded-full bg-white/12">
        <SliderPrimitive.Range className="absolute h-full bg-gradient-to-r from-[#6C63FF] to-[#E94E9A]" />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb className="block h-6 w-6 rounded-full border-4 border-[#0D0D18] bg-[#CFCBFF] shadow-[0_0_0_2px_#8d86ff,0_0_26px_rgba(108,99,255,.5)] outline-none focus-visible:shadow-[0_0_0_4px_#cfcBff]" />
    </SliderPrimitive.Root>
  );
}
