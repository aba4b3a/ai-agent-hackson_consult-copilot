import { cn } from "./cn";

/** Pulsing placeholder shown while content loads. Size via className. */
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-md bg-border/60", className)} />;
}
