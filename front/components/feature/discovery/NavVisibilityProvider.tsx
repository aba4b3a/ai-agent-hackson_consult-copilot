"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "consult-copilot.nav-collapsed";

type NavVisibilityContextValue = {
  isNavCollapsed: boolean;
  toggleNav: () => void;
};

const NavVisibilityContext = createContext<NavVisibilityContextValue | null>(null);

export const NavVisibilityProvider = ({ children }: { children: React.ReactNode }) => {
  const [isNavCollapsed, setIsNavCollapsed] = useState(false);

  useEffect(() => {
    // localStorage is only readable client-side; this app is a static export
    // (no per-request SSR), so reading it here (post-mount, post-hydration)
    // rather than a lazy useState initializer avoids a hydration mismatch.
    if (window.localStorage.getItem(STORAGE_KEY) === "true") {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setIsNavCollapsed(true);
    }
  }, []);

  const toggleNav = useCallback(() => {
    setIsNavCollapsed((prev) => {
      const next = !prev;
      window.localStorage.setItem(STORAGE_KEY, String(next));
      return next;
    });
  }, []);

  const value = useMemo(() => ({ isNavCollapsed, toggleNav }), [isNavCollapsed, toggleNav]);

  return <NavVisibilityContext.Provider value={value}>{children}</NavVisibilityContext.Provider>;
};

export const useNavVisibility = () => {
  const context = useContext(NavVisibilityContext);
  if (!context) {
    throw new Error("useNavVisibility must be used within NavVisibilityProvider");
  }
  return context;
};
