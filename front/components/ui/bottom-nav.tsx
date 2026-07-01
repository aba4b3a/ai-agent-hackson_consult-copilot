"use client";

import type { ReactNode } from "react";

import { cn } from "./cn";

export type BottomNavItem = {
  key: string;
  label: string;
  icon: ReactNode;
};

/**
 * Fixed mobile bottom navigation. Hidden on large screens where the content
 * uses a wider multi-column layout instead.
 */
export function BottomNav({
  items,
  value,
  onChange,
  className,
}: {
  items: BottomNavItem[];
  value?: string;
  onChange?: (key: string) => void;
  className?: string;
}) {
  const active = value ?? items[0]?.key;
  return (
    <nav
      className={cn(
        "fixed inset-x-0 bottom-0 z-10 border-t border-border bg-surface/95 backdrop-blur lg:hidden",
        className,
      )}
    >
      <ul className="mx-auto flex max-w-6xl items-stretch justify-around">
        {items.map((item) => {
          const isActive = item.key === active;
          return (
            <li key={item.key} className="flex-1">
              <button
                type="button"
                onClick={() => onChange?.(item.key)}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "flex w-full flex-col items-center gap-1 py-2 text-[11px] font-medium",
                  isActive ? "text-accent" : "text-text-muted",
                )}
              >
                {item.icon}
                {item.label}
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
