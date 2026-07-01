import type { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";

import { cn } from "./cn";

/** Labeled field wrapper with optional helper/optional markers. */
export function Field({
  label,
  htmlFor,
  optional,
  hint,
  children,
}: {
  label: string;
  htmlFor?: string;
  optional?: boolean;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="flex items-center gap-2 text-sm font-medium">
        {label}
        {optional ? <span className="text-xs font-normal text-text-muted">任意</span> : null}
      </label>
      {children}
      {hint ? <p className="text-xs text-text-muted">{hint}</p> : null}
    </div>
  );
}

const fieldClass =
  "w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text outline-none placeholder:text-text-muted focus:border-accent";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(fieldClass, className)} {...props} />;
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn(fieldClass, "resize-none", className)} {...props} />;
}
