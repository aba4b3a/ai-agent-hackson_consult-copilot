import { cn } from "./cn";

/** Compact KPI-style tile: label, large value, and a short caption. */
export function MetricCard({
  label,
  value,
  caption,
  className,
}: {
  label: string;
  value: string | number;
  caption?: string;
  className?: string;
}) {
  return (
    <div className={cn("rounded-card border border-border bg-surface p-4", className)}>
      <p className="text-sm text-text-muted">{label}</p>
      <p className="mt-2 text-3xl font-semibold">{value}</p>
      {caption ? <p className="mt-2 text-xs leading-5 text-text-muted">{caption}</p> : null}
    </div>
  );
}
