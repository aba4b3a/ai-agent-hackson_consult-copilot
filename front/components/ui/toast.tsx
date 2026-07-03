"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { cn } from "./cn";

type ToastTone = "success" | "danger" | "info";

type ToastItem = {
  id: number;
  message: string;
  tone: ToastTone;
};

type ToastFn = (toast: { message: string; tone?: ToastTone }) => void;

const ToastContext = createContext<ToastFn | null>(null);

const TONE_CLASSES: Record<ToastTone, string> = {
  success: "border-success/40 text-success",
  danger: "border-danger/40 text-danger",
  info: "border-border text-text",
};

const DISMISS_MS = 4000;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextId = useRef(1);

  const toast = useCallback<ToastFn>(({ message, tone = "info" }) => {
    const id = nextId.current++;
    setToasts((prev) => [...prev, { id, message, tone }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, DISMISS_MS);
  }, []);

  const value = useMemo(() => toast, [toast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed right-4 top-16 z-40 flex w-[min(360px,calc(100vw-2rem))] flex-col gap-2">
        {toasts.map((item) => (
          <div
            key={item.id}
            role="status"
            className={cn(
              "pointer-events-auto rounded-md border bg-surface px-3 py-2 text-sm shadow-sm",
              TONE_CLASSES[item.tone],
            )}
          >
            {item.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastFn {
  const toast = useContext(ToastContext);
  if (toast === null) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return toast;
}
