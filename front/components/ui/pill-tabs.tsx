"use client";

import { cn } from "./cn";

/**
 * Horizontal pill-style tab strip. Controlled via `value`/`onChange`; renders
 * as a scrollable row so it stays usable on narrow mobile widths.
 */
export function PillTabs({
  tabs,
  value,
  onChange,
  className,
}: {
  tabs: string[];
  value?: string;
  onChange?: (tab: string) => void;
  className?: string;
}) {
  const active = value ?? tabs[0];
  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {tabs.map((tab) => {
        const isActive = tab === active;
        return (
          <button
            key={tab}
            type="button"
            onClick={() => onChange?.(tab)}
            aria-pressed={isActive}
            className={cn(
              "rounded-full border px-2.5 py-1 text-xs font-medium transition-colors",
              isActive
                ? "border-accent bg-accent text-accent-foreground"
                : "border-border bg-surface text-text-muted hover:text-text",
            )}
          >
            {tab}
          </button>
        );
      })}
    </div>
  );
}
