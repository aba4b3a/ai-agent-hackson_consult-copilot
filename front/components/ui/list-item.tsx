import type { ReactNode } from "react";

import { cn } from "./cn";

/** Titled list row with optional supporting text and a trailing slot. */
export function ListItem({
  title,
  detail,
  trailing,
  className,
}: {
  title: ReactNode;
  detail?: ReactNode;
  trailing?: ReactNode;
  className?: string;
}) {
  return (
    <article className={cn("rounded-card border border-border bg-surface p-4", className)}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-medium">{title}</h3>
          {detail ? <p className="mt-1 text-sm leading-6 text-text-muted">{detail}</p> : null}
        </div>
        {trailing}
      </div>
    </article>
  );
}
