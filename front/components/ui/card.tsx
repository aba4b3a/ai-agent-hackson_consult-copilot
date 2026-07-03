import type { ReactNode } from "react";

import { cn } from "./cn";

/** Surface container used across the app. */
export function Card({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("rounded-card border border-border bg-surface p-4", className)}>
      {children}
    </div>
  );
}

/** Section wrapper with an icon + title header, used to group related cards.
 *  `id` enables sidebar anchor jumps; scroll-mt offsets the sticky header. */
export function Section({
  id,
  title,
  icon,
  children,
  className,
}: {
  id?: string;
  title: string;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section id={id} className={cn("scroll-mt-20 space-y-4 border-t border-border py-6", className)}>
      <div className="flex items-center gap-2">
        {icon ? (
          <span className="grid h-9 w-9 place-items-center rounded-md border border-border bg-surface text-text">
            {icon}
          </span>
        ) : null}
        <h2 className="text-lg font-semibold">{title}</h2>
      </div>
      {children}
    </section>
  );
}
