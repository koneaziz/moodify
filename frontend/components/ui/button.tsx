import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva("inline-flex items-center justify-center gap-2 rounded-full font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#CFCBFF] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0D0D18] disabled:pointer-events-none disabled:opacity-45", {
  variants: {
    variant: {
      default: "bg-[#6C63FF] text-white shadow-[0_12px_32px_rgba(108,99,255,.25)] hover:bg-[#827aff] hover:shadow-[0_14px_38px_rgba(108,99,255,.35)]",
      secondary: "border border-white/12 bg-white/[.07] text-[#F8F8FC] hover:bg-white/[.12]",
      ghost: "text-[#c4c2d4] hover:bg-white/[.07] hover:text-white",
      outline: "border border-[#6C63FF]/50 bg-[#6C63FF]/10 text-[#d4d1ff] hover:bg-[#6C63FF]/20",
    },
    size: {
      default: "h-11 px-5 text-sm",
      sm: "h-9 px-4 text-sm",
      lg: "h-13 px-7 text-base",
      icon: "h-10 w-10",
    },
  },
  defaultVariants: { variant: "default", size: "default" },
});

export function Button({ className, variant, size, asChild = false, ...props }: React.ComponentProps<"button"> & VariantProps<typeof buttonVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : "button";
  return <Comp data-slot="button" className={cn(buttonVariants({ variant, size, className }))} {...props} />;
}
