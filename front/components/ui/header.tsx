import type { ReactNode } from "react";

import { cn } from "./cn";

/** Sticky top header with optional leading slot (e.g. hamburger), eyebrow, title, trailing slot. */
export function Header({
  leading,
  eyebrow,
  title,
  trailing,
  className,
}: {
  leading?: ReactNode;
  eyebrow?: string;
  title: string;
  trailing?: ReactNode;
  className?: string;
}) {
  return (
    <header
      className={cn(
        "sticky top-0 z-10 border-b border-border bg-surface/95 backdrop-blur",
        className,
      )}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
        <div className="flex items-center gap-3">
          {leading}
          <div>
            {eyebrow ? (
              <p className="text-xs font-medium uppercase tracking-[0.12em] text-text-muted">
                {eyebrow}
              </p>
            ) : null}
            <h1 className="text-xl font-semibold">{title}</h1>
          </div>
        </div>
        {trailing}
      </div>
    </header>
  );
}
