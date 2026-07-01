import type { ReactNode } from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "./cn";

const pill = cva(
  "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium",
  {
    variants: {
      tone: {
        neutral: "border-border bg-surface text-text-muted",
        info: "border-border bg-surface text-text",
        success: "border-success/30 bg-success/10 text-success",
        warning: "border-warning/30 bg-warning/10 text-warning",
        danger: "border-danger/30 bg-danger/10 text-danger",
      },
    },
    defaultVariants: {
      tone: "neutral",
    },
  },
);

export type PillProps = VariantProps<typeof pill> & {
  children: ReactNode;
  className?: string;
};

export function Pill({ tone, children, className }: PillProps) {
  return <span className={cn(pill({ tone }), className)}>{children}</span>;
}
