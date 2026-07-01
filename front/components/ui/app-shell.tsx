import type { ReactNode } from "react";

import { cn } from "./cn";

/**
 * Mobile-first vertical scroll shell. Content is centered with a max width so
 * the same layout reads well on phones and widens gracefully on desktop.
 */
export function AppShell({
  header,
  bottomNav,
  children,
  className,
}: {
  header?: ReactNode;
  bottomNav?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className="min-h-screen bg-background text-text">
      {header}
      <main className={cn("mx-auto w-full max-w-6xl px-4 py-6", bottomNav && "pb-24", className)}>
        {children}
      </main>
      {bottomNav}
    </div>
  );
}
