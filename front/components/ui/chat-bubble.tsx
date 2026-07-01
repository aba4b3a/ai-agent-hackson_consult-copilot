import type { ReactNode } from "react";

import { cn } from "./cn";

/** Conversation bubble. `assistant` aligns left/muted, `user` aligns right/accent. */
export function ChatBubble({
  role,
  children,
  className,
}: {
  role: "assistant" | "user";
  children: ReactNode;
  className?: string;
}) {
  const isUser = role === "user";
  return (
    <div
      className={cn(
        "max-w-[85%] rounded-lg p-3 text-sm leading-6",
        isUser ? "ml-auto bg-accent text-accent-foreground" : "bg-background text-text",
        className,
      )}
    >
      {children}
    </div>
  );
}
