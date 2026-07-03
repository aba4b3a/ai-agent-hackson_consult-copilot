"use client";

import Link from "next/link";
import { X } from "lucide-react";

import { cn } from "./cn";

export type SidebarItem = {
  label: string;
  href: string;
};

function NavList({
  items,
  pages,
  onNavigate,
}: {
  items: SidebarItem[];
  pages: SidebarItem[];
  onNavigate?: () => void;
}) {
  return (
    <nav className="space-y-6">
      <div>
        <p className="px-3 text-xs font-medium uppercase tracking-[0.12em] text-text-muted">
          セクション
        </p>
        <ul className="mt-2 space-y-0.5">
          {items.map((item) => (
            <li key={item.href}>
              <a
                href={item.href}
                onClick={onNavigate}
                className="block rounded-md px-3 py-2 text-sm text-text hover:bg-background"
              >
                {item.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <p className="px-3 text-xs font-medium uppercase tracking-[0.12em] text-text-muted">
          ページ
        </p>
        <ul className="mt-2 space-y-0.5">
          {pages.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                onClick={onNavigate}
                className="block rounded-md px-3 py-2 text-sm text-text-muted hover:bg-background hover:text-text"
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}

/**
 * Consultant navigation. Rendered as a sticky column on large screens and as a
 * hamburger-controlled overlay drawer on narrow screens.
 */
export function Sidebar({
  items,
  pages,
  open,
  onClose,
  className,
}: {
  items: SidebarItem[];
  pages: SidebarItem[];
  open: boolean;
  onClose: () => void;
  className?: string;
}) {
  return (
    <>
      {/* Desktop: always-visible sticky column */}
      <aside
        className={cn(
          "hidden w-56 shrink-0 lg:block",
          className,
        )}
      >
        <div className="sticky top-20 rounded-card border border-border bg-surface p-3">
          <NavList items={items} pages={pages} />
        </div>
      </aside>

      {/* Mobile: overlay drawer */}
      {open ? (
        <div className="fixed inset-0 z-30 lg:hidden" role="dialog" aria-modal="true">
          <button
            type="button"
            aria-label="Close navigation"
            onClick={onClose}
            className="absolute inset-0 bg-text/30"
          />
          <div className="absolute inset-y-0 left-0 w-64 overflow-y-auto border-r border-border bg-surface p-3">
            <div className="mb-2 flex items-center justify-between px-3">
              <p className="text-sm font-semibold">メニュー</p>
              <button
                type="button"
                aria-label="Close"
                onClick={onClose}
                className="grid h-8 w-8 place-items-center rounded-md text-text-muted hover:bg-background"
              >
                <X size={16} />
              </button>
            </div>
            <NavList items={items} pages={pages} onNavigate={onClose} />
          </div>
        </div>
      ) : null}
    </>
  );
}
