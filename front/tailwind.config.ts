import type { Config } from "tailwindcss";

/**
 * Design tokens are declared as CSS variables in app/globals.css and referenced
 * here so components use semantic color names (bg-surface, text-muted, ...)
 * instead of hard-coded palette values. Tailwind's default palette (slate, ...)
 * remains available for one-off cases.
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "var(--color-background)",
        surface: "var(--color-surface)",
        border: "var(--color-border)",
        text: {
          DEFAULT: "var(--color-text)",
          muted: "var(--color-text-muted)",
        },
        accent: {
          DEFAULT: "var(--color-accent)",
          foreground: "var(--color-accent-foreground)",
        },
        success: "var(--color-success)",
        warning: "var(--color-warning)",
        danger: "var(--color-danger)",
      },
      borderRadius: {
        card: "0.5rem",
      },
    },
  },
  plugins: [],
};

export default config;
